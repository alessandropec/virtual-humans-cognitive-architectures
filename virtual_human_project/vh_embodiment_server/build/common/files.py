"""One package manifest, shared by the two platform builders."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app'


def application_files(platform):
    files = [(APP / name, name) for name in (
        'app.js', 'avatar.js', 'chat-window.js', 'index.html', 'server.py',
        'schemas.py', 'speech.py', 'stt_device.py', 'tts_device.py',
        'model_files.py', 'cognitive_connection.py', 'path_picker.py', 'model_warmup.py', 'project_paths.py', 'server_logs.py')]
    files += [(ROOT / name, name) for name in ('README.html',)]
    files += [(ROOT / 'build/common' / name, name) for name in ('install.py', 'verify_install.py', 'downloads.py', 'course_environment.py', 'speech-models.json')]
    if platform == 'win':
        files += [(APP / 'start.cmd', 'start.cmd')]
        files += [(ROOT / 'build/win/src' / name, name) for name in ('setup.ps1', 'Install.cmd')]
        files += [(ROOT / 'build/win/requirements.txt', 'requirements.txt'),
                  (ROOT / 'build/win/requirements-gpu.txt', 'requirements-gpu.txt')]
    elif platform == 'mac':
        files += [(ROOT / 'build/mac/src/mac_install.py', 'mac_install.py'),
                  (ROOT / 'build/mac/src/mac_launch.py', 'mac_launch.py'),
                  (ROOT / 'build/mac/requirements.txt', 'requirements.txt')]
    else:
        raise ValueError('Expected win or mac')
    for directory in ('assets', 'lib'):
        files += [(file, file.relative_to(APP).as_posix())
                  for file in sorted((APP / directory).rglob('*'))
                  if file.is_file() and '__pycache__' not in file.parts]
    return files
