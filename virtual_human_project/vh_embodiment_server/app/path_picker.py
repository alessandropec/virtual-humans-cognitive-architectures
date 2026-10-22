"""Local folder picker for the desktop running the embodiment server."""
import subprocess
import sys
from pathlib import Path
from fastapi import HTTPException
from project_paths import find_repository


def select_path(kind):
    titles = {'cognitive': 'Select the Cognitive Architecture Server folder',
              'python': 'Select the course .venv-vh-course folder',
              'models': 'Select the Whisper and Piper models folder'}
    title = titles[kind]
    try:
        repository = find_repository(__file__)
        initial = repository / 'virtual_human_project'
    except RuntimeError:
        initial = Path(__file__).resolve().parent
    quoted_initial = str(initial).replace("'", "''")
    if sys.platform == 'win32':
        script = ("Add-Type -AssemblyName System.Windows.Forms; "
                  "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
                  f"$dialog.Description = '{title}'; "
                  f"$dialog.SelectedPath = '{quoted_initial}'; "
                  "$dialog.ShowNewFolderButton = $false; "
                  "if ($dialog.ShowDialog() -eq 'OK') { "
                  "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
                  "[Console]::Write($dialog.SelectedPath) }")
        command = ['powershell.exe', '-NoProfile', '-STA', '-Command', script]
    elif sys.platform == 'darwin':
        command = ['osascript', '-e', f'on run argv\nPOSIX path of (choose folder with prompt "{title}" default location (POSIX file (item 1 of argv)))\nend run', str(initial)]
    else:
        raise HTTPException(400, 'Folder selection is supported on Windows and Mac. Enter the path manually.')
    try:
        result = subprocess.run(command, capture_output=True, encoding='utf-8',
                                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    except OSError as error:
        raise HTTPException(400, f'Cannot open folder picker: {error}') from error
    if result.returncode:
        if '-128' in result.stderr:  # macOS user cancellation
            return None
        raise HTTPException(400, 'Cannot open folder picker. Enter the path manually.')
    if not result.stdout.strip():
        return None
    path = Path(result.stdout.strip().lstrip('\ufeff'))
    if kind == 'cognitive':
        path /= 'vh_cognitive_server.py'
    elif kind == 'python':
        path /= 'Scripts/python.exe' if sys.platform == 'win32' else 'bin/python'
    if not path.exists():
        raise HTTPException(400, f'The selected folder does not contain {path.name}. Choose the correct folder.')
    return str(path)
