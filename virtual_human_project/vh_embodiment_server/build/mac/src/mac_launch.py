"""Visible Terminal launcher with single instance and process-group cleanup."""
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.request import urlopen
import webbrowser

ROOT = Path(__file__).resolve().parent


def existing_server():
    try:
        with urlopen('http://127.0.0.1:8899/heartbeat', timeout=1) as response:
            return json.load(response).get('service') == 'VH Embodiment Server'
    except (OSError, ValueError, AttributeError):
        return False


def main():
    if sys.platform != 'darwin':
        raise RuntimeError('This launcher requires macOS.')
    with (ROOT / '.server.lock').open('a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            if existing_server():
                webbrowser.open('http://127.0.0.1:8899/')
                return
            raise RuntimeError('VH Embodiment Server or its installer is already running.')
        if existing_server():
            webbrowser.open('http://127.0.0.1:8899/')
            return
        # These variables are intentionally absent: CPU-only is enforced by macOS schemas.
        process = subprocess.Popen([sys.executable, '-u', str(ROOT / 'server.py')], cwd=ROOT,
                                   start_new_session=True, env={**os.environ, 'VH_PORT': '8899', 'VH_OPEN_BROWSER': '0'})
        def stop(signum=None, frame=None):
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
            if signum is not None:
                raise SystemExit(0)
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            signal.signal(sig, stop)
        # A pipe watchdog also cleans up if this launcher is killed without a signal handler.
        read_fd, write_fd = os.pipe()
        watcher = subprocess.Popen([sys.executable, '-c',
            'import os,signal,sys; os.read(int(sys.argv[1]),1); '
            '\ntry: os.killpg(int(sys.argv[2]),signal.SIGTERM)\nexcept ProcessLookupError: pass',
            str(read_fd), str(process.pid)], pass_fds=(read_fd,), start_new_session=True)
        os.close(read_fd)
        try:
            for _ in range(120):
                if process.poll() is not None:
                    raise RuntimeError('The server did not start: read the message above.')
                try:
                    with urlopen('http://127.0.0.1:8899/api/status', timeout=1):
                        break
                except OSError:
                    time.sleep(.5)
            else:
                raise RuntimeError('The server did not respond within the expected time.')
            webbrowser.open('http://127.0.0.1:8899/')
            print('Server ready. Close the avatar page, this window or press Ctrl+C to stop.')
            process.wait()
        finally:
            stop()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            os.close(write_fd)
            watcher.wait(timeout=5)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ERROR:', exc)
        input('Press Enter to close.')
        sys.exit(1)
