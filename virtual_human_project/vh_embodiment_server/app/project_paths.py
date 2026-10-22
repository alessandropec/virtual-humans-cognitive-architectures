"""Locate the course repository without machine-specific paths."""
from pathlib import Path


def find_repository(start):
    start = Path(start).resolve()
    if start.is_file():
        start = start.parent
    for folder in (start, *start.parents):
        project = folder / 'virtual_human_project'
        if ((folder / 'requirements.txt').is_file()
                and (project / 'vh_embodiment_server').is_dir()
                and (project / 'vh_cognitive_architecture_server/vh_cognitive_server.py').is_file()):
            return folder
    raise RuntimeError('Open the installer from inside the cloned course repository.')
