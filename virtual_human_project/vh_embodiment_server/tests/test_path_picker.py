"""Selected folders resolve to the correct server, Python and model paths."""
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from path_picker import select_path
from fastapi import HTTPException

with tempfile.TemporaryDirectory() as directory:
    folder = Path(directory)
    (folder / 'vh_cognitive_server.py').write_text('')
    for name in ('Scripts/python.exe', 'bin/python'):
        file = folder / name
        file.parent.mkdir(exist_ok=True)
        file.write_text('')
    selected = subprocess.CompletedProcess([], 0, stdout=str(folder), stderr='')
    with patch('path_picker.subprocess.run', return_value=selected):
        assert select_path('cognitive') == str(folder / 'vh_cognitive_server.py')
        assert select_path('models') == str(folder)
        assert select_path('python') == str(folder / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python'))
        (folder / 'vh_cognitive_server.py').unlink()
        try:
            select_path('cognitive')
        except HTTPException as error:
            assert error.status_code == 400
        else:
            raise AssertionError('Wrong folder accepted')
    cancelled = subprocess.CompletedProcess([], 0, stdout='', stderr='')
    with patch('path_picker.subprocess.run', return_value=cancelled):
        assert select_path('models') is None
print('PASS server folder, .venv-vh-course interpreter, models folder, cancellation and wrong-folder handling')
