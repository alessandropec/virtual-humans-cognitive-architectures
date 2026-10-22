"""Model selection and installer wiring, with no downloads or runtime installation."""
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'app'), str(PROJECT / 'build/common')]
import install


class InstallerModelsTests(unittest.TestCase):
    def test_plan_downloads_two_models_but_voices_only_once(self):
        with patch.object(install, 'hf_files', side_effect=AssertionError('Model metadata must be bundled')):
            plan = install.model_plan(['tiny', 'small', 'tiny'])
        self.assertTrue(all(item['primary_url'].startswith('https://github.com/') for item in plan))
        self.assertTrue(all(item['url'].startswith('https://huggingface.co/') for item in plan))
        self.assertEqual(len(plan), 16)
        self.assertEqual(len({item['relative'] for item in plan}), 16)
        self.assertTrue(any(item['relative'].startswith('faster-whisper-tiny/') for item in plan))
        self.assertTrue(any(item['relative'].startswith('faster-whisper-small/') for item in plan))

    def mock_installation(self, stack, root):
        setup = root / '.setup'
        setup.mkdir()
        for name, value in [('ROOT', root), ('SETUP', setup), ('WHEELS', setup / 'wheels')]:
            stack.enter_context(patch.object(install, name, value))
        for name in ('log', 'download', 'check_space'):
            stack.enter_context(patch.object(install, name))
        stack.enter_context(patch.object(install, 'nvidia', return_value=''))
        stack.enter_context(patch.object(install, 'valid', return_value=False))
        stack.enter_context(patch.object(install, 'requirements', return_value=['example==1.0']))
        stack.enter_context(patch.object(install, 'wheel', return_value={'name':'example.whl', 'size':10}))
        stack.enter_context(patch.object(install, 'hf_files', side_effect=lambda repo,names:[{'name':n,'size':10} for n in names]))
        stack.enter_context(patch.object(install.course_environment, 'environment', return_value=root / '.venv-vh-course'))
        stack.enter_context(patch.object(install.course_environment, 'python_path', return_value=root / '.venv-vh-course/bin/python'))
        stack.enter_context(patch.object(install.course_environment, 'prepare'))
        return stack.enter_context(patch.object(install, 'run'))

    def test_windows_selects_small_by_default_when_both_are_downloaded(self):
        for selected, active in [(['small', 'tiny'], 'small')]:
            with self.subTest(selected=selected), tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                run = self.mock_installation(stack, root)
                install.install(SimpleNamespace(profile='cpu', model=None, models=selected, models_dir=None,
                    yes=True, plan=False, voice_device='cpu', transcription_device='cpu'))
                settings = json.loads((root / 'settings.json').read_text())
                runtime = json.loads((root / 'runtime.json').read_text())
                self.assertEqual(settings['stt_model'], active)
                self.assertEqual(set(runtime['models']), set(selected))
                verify = run.call_args_list[-1].args[0]
                self.assertEqual(set(verify[verify.index('--model')+1:verify.index('--voice-device')]), set(selected))

    def test_mac_allows_both_and_keeps_small_as_active_model(self):
        # fcntl is a Mac/POSIX module; the installer body can still be tested on Windows.
        with patch.dict(sys.modules, {'fcntl': Mock()}):
            spec = importlib.util.spec_from_file_location('mac_installer_test', PROJECT / 'build/mac/src/mac_install.py')
            mac = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mac)
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            run = self.mock_installation(stack, root)
            (root / 'requirements.txt').write_text('example==1.0\n')
            stack.enter_context(patch.object(mac, 'ROOT', root))
            stack.enter_context(patch.object(mac, 'check_space'))
            stack.enter_context(patch.object(mac, 'download'))
            stack.enter_context(patch.object(mac, 'create_launcher'))
            stack.enter_context(patch.object(mac.common.course_environment, 'configure'))
            mac.perform_install()
            self.assertEqual(json.loads((root / 'settings.json').read_text())['stt_model'], 'small')
            self.assertEqual(json.loads((root / 'runtime.json').read_text())['models'], ['small', 'tiny'])
            self.assertEqual(run.call_args.args[0][-2:], ['small', 'tiny'])


if __name__ == '__main__':
    unittest.main()
