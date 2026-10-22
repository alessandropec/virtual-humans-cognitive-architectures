"""Refresh keeps the servers alive; closing the tab stops both and frees ports."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import httpx
from websockets.sync.client import connect

project = Path(__file__).resolve().parents[2]
def free_port():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]

with tempfile.TemporaryDirectory(prefix='vh-shutdown-test-') as directory:
    stage = Path(directory)
    for file in (project / 'vh_embodiment_server/app').glob('*.py'):
        shutil.copy2(file, stage / file.name)
    for name in ('assets', 'lib'):
        (stage / name).mkdir()
    shutil.copy2(project / 'vh_embodiment_server/app/assets/motion-catalog.json', stage / 'assets/motion-catalog.json')
    cognitive = stage / 'cognitive'
    cognitive.mkdir()
    source = project / 'vh_cognitive_architecture_server'
    shutil.copy2(source / 'schemas.py', cognitive / 'schemas.py')
    code = (source / 'vh_cognitive_server.py').read_text(encoding='utf-8')
    code = code.replace('from agents.naive_agent import response', 'from agents.mock_agent import response')
    (cognitive / 'vh_cognitive_server.py').write_text(code, encoding='utf-8')
    (cognitive / 'agents').mkdir()
    shutil.copy2(source / 'agents/mock_agent.py', cognitive / 'agents/mock_agent.py')
    avatar_port, cognitive_port = free_port(), free_port()
    (stage / 'settings.json').write_text(json.dumps(dict(
        agent_python=sys.executable, agent_script=str(cognitive / 'vh_cognitive_server.py'),
        agent_heartbeat_url=f'http://127.0.0.1:{cognitive_port}/heartbeat',
        agent_url=f'http://127.0.0.1:{cognitive_port}/agent',
        models_dir=str(stage / 'missing-models'), speech_enabled=False)))
    with (stage / 'test.log').open('w') as log:
        process = subprocess.Popen([sys.executable, '-B', str(stage / 'server.py')],
            stdout=log, stderr=log, env={**os.environ, 'VH_OPEN_BROWSER':'0', 'VH_PORT':str(avatar_port)})
        try:
            with httpx.Client(trust_env=False, timeout=1) as http:
                for _ in range(150):
                    try:
                        ready = http.get(f'http://127.0.0.1:{avatar_port}/api/agent/status').json()
                        if ready.get('connected'):
                            break
                    except (httpx.HTTPError, ValueError):
                        pass
                    assert process.poll() is None, (stage / 'test.log').read_text(encoding='utf-8')
                    time.sleep(.1)
                else:
                    raise AssertionError('Both servers did not become ready')
                with connect(f'ws://127.0.0.1:{avatar_port}/ws'):
                    pass
                time.sleep(1)
                with connect(f'ws://127.0.0.1:{avatar_port}/ws'):
                    time.sleep(8.5)
                    assert process.poll() is None, 'Refresh stopped the server'
                assert process.wait(timeout=20) == 0
            for port in (avatar_port, cognitive_port):
                with socket.socket() as listener:
                    assert listener.connect_ex(('127.0.0.1', port)) != 0, f'Port {port} remains occupied'
            text = (stage / 'embodiment-server.log').read_text(encoding='utf-8')
            assert 'GET /api/agent/status HTTP' not in text
            cog_log = (cognitive / 'cognitive-server.log').read_text(encoding='utf-8')
            assert 'GET /heartbeat HTTP' not in cog_log
            print('PASS browser refresh, automatic shutdown of both real servers, released ports and quiet polling')
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
