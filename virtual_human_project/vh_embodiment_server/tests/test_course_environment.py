"""Repository discovery, automatic venv creation and explicit reuse without pip."""
from pathlib import Path
import sys
import tempfile
from unittest.mock import Mock
root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root / 'app'), str(root / 'build/common')]
from course_environment import configure, prepare
from project_paths import find_repository

with tempfile.TemporaryDirectory(prefix="course root with spaces '") as directory:
    repo = Path(directory).resolve()
    (repo / 'requirements.txt').write_text('fastapi\n')
    project = repo / 'virtual_human_project'
    installation = project / 'installation'
    installation.mkdir(parents=True)
    (project / 'vh_embodiment_server/dist/win').mkdir(parents=True)
    cognitive = project / 'vh_cognitive_architecture_server/vh_cognitive_server.py'
    cognitive.parent.mkdir()
    cognitive.write_text('')
    python = project / '.venv-vh-course' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    calls = []
    def run(command, cwd=None):
        calls.append((command, cwd))
        if command[1:3] == ['-m', 'venv']:
            python.parent.mkdir(parents=True)
            python.write_text('')
            (project / '.venv-vh-course/pyvenv.cfg').write_text('home = python')
    assert find_repository(project / 'vh_embodiment_server/dist/win') == repo
    config = {}
    prepare(installation, run, Mock())
    configure(installation, config)
    assert calls[0][0][1:3] == ['-m', 'venv']
    assert config['agent_python'] == str(python)
    assert config['agent_script'] == str(cognitive)
    assert any(command[1:4] == ['-m', 'pip', 'install'] and cwd == repo for command, cwd in calls)
    calls.clear()
    prepare(installation, run, Mock())
    configure(installation, config)
    assert any(command[1:4] == ['-m', 'pip', 'install'] for command, cwd in calls)
    # A broken existing folder must be retained and identified in the error.
    (project / '.venv-vh-course/pyvenv.cfg').unlink()
    try:
        prepare(installation, run, Mock())
    except RuntimeError as error:
        assert str(project / '.venv-vh-course') in str(error) and 'rename or remove' in str(error)
    else:
        raise AssertionError('Invalid environment accepted')
    assert python.exists()
print('PASS portable discovery, single shared environment, dependency completion and incompatible environment preservation')
