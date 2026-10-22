"""Exercise interrupted transfers, bad hashes and storage failures without large downloads."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'app'), str(PROJECT / 'build/common')]
import downloads
import install

DATA = b'virtual-human-test-' * 4096


class Handler(BaseHTTPRequestHandler):
    ranges = []
    ignore_range = False
    corrupt = False

    def log_message(self, *args):
        pass

    def do_GET(self):
        requested = self.headers.get('Range')
        self.ranges.append(requested)
        offset = int(requested.split('=')[1].split('-')[0]) if requested and not self.ignore_range else 0
        data = (b'X' * len(DATA) if self.corrupt else DATA)[offset:]
        self.send_response(206 if offset else 200)
        if offset:
            self.send_header('Content-Range', f'bytes {offset}-{len(DATA)-1}/{len(DATA)}')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class DownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / 'model.bin'
        self.item = {'url': f'http://127.0.0.1:{self.server.server_port}/model',
                     'size': len(DATA), 'hash': hashlib.sha256(DATA).hexdigest()}
        Handler.ranges.clear(); Handler.ignore_range = Handler.corrupt = False

    def partial(self):
        self.target.with_name('model.bin.part').write_bytes(DATA[:1024])
        self.target.with_name('model.bin.part.json').write_text(json.dumps(self.item))

    def test_metadata_retries_transient_errors_and_reuses_response(self):
        from io import BytesIO
        downloads.read_json.cache_clear()
        with patch.object(downloads, 'open_url', side_effect=[OSError('connection reset'), BytesIO(b'{"ok": true}')]) as request, \
             patch.object(downloads.time, 'sleep'):
            self.assertEqual(downloads.read_json('https://example.invalid/metadata'), {'ok': True})
            self.assertEqual(downloads.read_json('https://example.invalid/metadata'), {'ok': True})
            self.assertEqual(request.call_count, 2)
        downloads.read_json.cache_clear()

    def test_resumes_and_skips_verified_files(self):
        self.partial()
        downloads.download(self.item, self.target, report=lambda _: None)
        self.assertEqual(Handler.ranges, ['bytes=1024-'])
        self.assertEqual(self.target.read_bytes(), DATA)
        downloads.download(self.item, self.target, report=lambda _: None)
        self.assertEqual(len(Handler.ranges), 1)

    def test_host_ignoring_range_restarts_without_appending(self):
        self.partial(); Handler.ignore_range = True
        downloads.download(self.item, self.target, report=lambda _: None)
        self.assertEqual(self.target.read_bytes(), DATA)

    def test_corruption_never_replaces_existing_file(self):
        self.target.write_bytes(b'existing model')
        Handler.corrupt = True
        with self.assertRaises(OSError):
            downloads.download(self.item, self.target, attempts=1, report=lambda _: None)
        self.assertEqual(self.target.read_bytes(), b'existing model')

    def test_low_disk_stops_before_network(self):
        with patch.object(downloads.shutil, 'disk_usage', return_value=type('Disk', (), {'free': 10})()):
            with self.assertRaisesRegex(OSError, 'Not enough disk space'):
                downloads.download(self.item, self.target, report=lambda _: None)
        self.assertEqual(Handler.ranges, [])

    def test_changed_hash_does_not_resume_old_partial(self):
        self.partial()
        identity = self.target.with_name('model.bin.part.json')
        identity.write_text('{}')
        downloads.download(self.item, self.target, report=lambda _: None)
        self.assertEqual(Handler.ranges, [None])

    def test_failed_run_keeps_partial_and_next_run_resumes(self):
        self.partial()
        with patch.object(downloads, 'open_url', side_effect=OSError('connection reset')):
            with self.assertRaisesRegex(OSError, 'Download incomplete'):
                downloads.download(self.item, self.target, attempts=1, report=lambda _: None)
        self.assertEqual(self.target.with_name('model.bin.part').stat().st_size, 1024)
        self.assertFalse(self.target.exists())
        downloads.download(self.item, self.target, report=lambda _: None)
        self.assertEqual(Handler.ranges, ['bytes=1024-'])
        self.assertEqual(self.target.read_bytes(), DATA)

    def test_github_is_first_source_and_original_source_is_backup(self):
        item = dict(self.item, primary_url='https://github.com/course/project/releases/download/v1/model.bin')
        self.assertEqual(downloads.download_url(item, 0), item['primary_url'])
        self.assertEqual(downloads.download_url(item, 1), item['primary_url'])
        self.assertEqual(downloads.download_url(item, 2), item['url'])

    def test_ipv4_fallback_preserves_tls_verification_and_normal_host_name(self):
        import ssl
        connection = downloads.IPv4HTTPSConnection('huggingface.co')
        self.assertEqual(connection.host, 'huggingface.co')
        self.assertEqual(connection._context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(connection._context.check_hostname)
        with patch.object(downloads.socket, 'gethostbyname', return_value='192.0.2.1'), \
             patch.object(downloads.socket, 'create_connection') as connect:
            connection._create_connection(('huggingface.co', 443), 45)
            connect.assert_called_once_with(('192.0.2.1', 443), 45)

    def test_hugging_face_retry_uses_alternate_route_and_checks_hash(self):
        from io import BytesIO
        from urllib.error import URLError
        item = dict(self.item, url='https://huggingface.co/example/resolve/pinned/model.bin')
        reply = BytesIO(DATA)
        reply.status = 200
        reply.headers = {}
        with patch.object(downloads, 'open_url', side_effect=[URLError('reset'), reply]) as request, \
             patch.object(downloads.time, 'sleep'):
            downloads.download(item, self.target, report=lambda _: None)
        self.assertEqual(request.call_args_list[1].args[0].full_url, item['url']+'?download=true')
        self.assertFalse(request.call_args_list[0].kwargs['ipv4'])
        self.assertTrue(request.call_args_list[1].kwargs['ipv4'])
        self.assertEqual(self.target.read_bytes(), DATA)

    @unittest.skipUnless(sys.platform == 'win32', 'Windows installer')
    def test_connection_error_does_not_switch_to_cpu(self):
        from types import SimpleNamespace
        args = SimpleNamespace(profile='gpu', plan=False)
        with patch.object(install, 'ROOT', Path(self.temp.name)), patch.object(install, 'SETUP', Path(self.temp.name)), \
             patch.object(install.course_environment, 'environment', return_value=Path(self.temp.name) / '.venv-vh-course'), \
             patch.object(install.course_environment, 'python_path', return_value=Path(self.temp.name) / '.venv-vh-course/Scripts/python.exe'), \
             patch.object(install, 'install', side_effect=OSError('Download incomplete')) as perform:
            with self.assertRaisesRegex(OSError, 'Download incomplete'):
                install.main(args)
        self.assertEqual(perform.call_count, 1)

    @unittest.skipUnless(sys.platform == 'win32', 'Windows installer')
    def test_gpu_setup_failure_automatically_tries_cpu(self):
        from types import SimpleNamespace
        args = SimpleNamespace(profile='gpu', plan=False, yes=True, voice_device='auto', transcription_device='auto')
        with patch.object(install, 'ROOT', Path(self.temp.name)), patch.object(install, 'SETUP', Path(self.temp.name)), \
             patch.object(install.course_environment, 'environment', return_value=Path(self.temp.name) / '.venv-vh-course'), \
             patch.object(install.course_environment, 'python_path', return_value=Path(self.temp.name) / '.venv-vh-course/Scripts/python.exe'), \
             patch.object(install, 'log'), patch.object(install, 'install', side_effect=[install.GPUSetupError('CUDA missing'), None]) as perform:
            install.main(args)
        self.assertEqual(perform.call_count, 2)
        self.assertEqual(perform.call_args.args[0].profile, 'cpu')
        self.assertEqual(perform.call_args.args[0].voice_device, 'cpu')
        self.assertIn('CUDA missing', (Path(self.temp.name) / 'setup-result.json').read_text())


if __name__ == '__main__':
    unittest.main()
