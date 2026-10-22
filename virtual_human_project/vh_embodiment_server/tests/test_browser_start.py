"""Source startup opens the browser after readiness, including server reuse."""
import os
from pathlib import Path
import runpy
import sys
from unittest.mock import MagicMock, patch
import httpx

app = Path(__file__).resolve().parents[1] / 'app'
sys.path.insert(0, str(app))
ready = MagicMock()
ready.json.return_value = {'service': 'VH Embodiment Server'}

# Existing server: open its URL once and avoid launching another backend.
with patch.dict(os.environ, {'VH_OPEN_BROWSER': '1'}), \
     patch('httpx.get', return_value=ready), patch('webbrowser.open') as browser, \
     patch('uvicorn.Server') as server:
    try:
        runpy.run_path(str(app / 'server.py'), run_name='__main__')
    except SystemExit as error:
        assert error.code == 0
    browser.assert_called_once()
    server.assert_not_called()

# New source server: browser opens only after the heartbeat answers.
instance = MagicMock()
instance.should_exit = False
with patch.dict(os.environ, {'VH_OPEN_BROWSER': '1'}), \
     patch('httpx.get', side_effect=[httpx.ConnectError('not started'), ready]), \
     patch('webbrowser.open') as browser, patch('uvicorn.Server', return_value=instance), \
     patch('threading.Thread') as thread:
    thread.side_effect = lambda target, **kwargs: MagicMock(start=target)
    runpy.run_path(str(app / 'server.py'), run_name='__main__')
    browser.assert_called_once()
    instance.run.assert_called_once()
print('PASS source browser startup, heartbeat readiness and existing-server reuse')
