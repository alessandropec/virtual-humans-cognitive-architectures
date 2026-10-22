"""A managed agent exits and releases its port when its parent pipe closes."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import httpx

script = Path(__file__).resolve().parents[2] / 'vh_cognitive_architecture_server/vh_cognitive_server.py'
with socket.socket() as listener:
    listener.bind(('127.0.0.1', 0))
    port = listener.getsockname()[1]
process = subprocess.Popen([sys.executable, '-B', str(script)], stdin=subprocess.PIPE,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           env={**os.environ, 'VH_AGENT_MANAGED': '1', 'VH_AGENT_PORT': str(port)})
try:
    with httpx.Client(trust_env=False, timeout=1) as http:
        for _ in range(50):
            try:
                response = http.get(f'http://127.0.0.1:{port}/heartbeat')
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            assert process.poll() is None, 'Agent exited before startup'
            time.sleep(.1)
        else:
            raise AssertionError('Agent did not become ready')
        assert response.json()['service'] == 'VH Cognitive Architecture Server'
    process.stdin.close()
    assert process.wait(timeout=10) == 0
    with socket.socket() as check:
        assert check.connect_ex(('127.0.0.1', port)) != 0
    print('PASS parent pipe closure stops the real agent and frees its port')
finally:
    if process.poll() is None:
        process.terminate()
        process.wait(timeout=5)

# A separately launched local server supports the same graceful shutdown.
import asyncio
sys.path.insert(0, str(script.parent.parent / 'vh_embodiment_server/app'))
from cognitive_connection import CognitiveConnection
from schemas import Settings
with socket.socket() as listener:
    listener.bind(('127.0.0.1', 0))
    port = listener.getsockname()[1]
process = subprocess.Popen([sys.executable, '-B', str(script)], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           env={**os.environ, 'VH_AGENT_MANAGED': '0', 'VH_AGENT_PORT': str(port)})
try:
    with httpx.Client(trust_env=False, timeout=1) as http:
        for _ in range(100):
            try:
                if http.get(f'http://127.0.0.1:{port}/heartbeat').status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            assert process.poll() is None
            time.sleep(.1)
        else:
            raise AssertionError('Independent server did not start')
        assert http.post(f'http://127.0.0.1:{port}/shutdown').status_code == 403
    settings = Settings(agent_heartbeat_url=f'http://127.0.0.1:{port}/heartbeat')
    asyncio.run(CognitiveConnection(lambda: settings).stop())
    assert process.wait(timeout=10) == 0
    with socket.socket() as check:
        assert check.connect_ex(('127.0.0.1', port)) != 0
    print('PASS separately started local cognitive server shuts down gracefully and releases its port')
finally:
    if process.poll() is None:
        process.terminate()
        process.wait(timeout=5)
