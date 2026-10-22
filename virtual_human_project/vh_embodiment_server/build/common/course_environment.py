"""One course environment shared by the servers and notebooks."""
from pathlib import Path
import sys
from project_paths import find_repository


def environment(start):
    return find_repository(start) / 'virtual_human_project/.venv-vh-course'


def python_path(start):
    return environment(start) / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')


def prepare(start, run, log):
    folder = environment(start)
    python = python_path(start)
    error = f'Incompatible course environment: {folder}. Close the programs using it, rename or remove this folder, then run setup again.'
    if folder.exists() and not (folder / 'pyvenv.cfg').is_file():
        raise RuntimeError(error)
    if not folder.exists():
        log(f'Creating the shared course environment: {folder}')
        run([sys.executable, '-m', 'venv', folder])
    if not python.is_file():
        raise RuntimeError(error)
    try:
        run([python, '-c', 'import sys, struct; assert sys.version_info[:2] == (3, 12) and struct.calcsize("P") == 8 and sys.prefix != sys.base_prefix'])
    except Exception as exc:
        raise RuntimeError(error) from exc
    repository = find_repository(start)
    log('Installing or completing the course notebook dependencies.')
    run([python, '-m', 'pip', 'install', '--disable-pip-version-check', '-r', repository / 'requirements.txt', '-c', Path(start) / 'requirements.txt'], cwd=repository)
    return python


def configure(start, config):
    repository = find_repository(start)
    config['agent_python'] = str(python_path(start))
    config['agent_script'] = str(repository / 'virtual_human_project/vh_cognitive_architecture_server/vh_cognitive_server.py')
