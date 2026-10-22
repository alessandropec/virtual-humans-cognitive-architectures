from pathlib import Path
import sys
import asyncio
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import httpx
PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'app'), str(PROJECT / 'build/common')]
from fastapi import HTTPException
from fastapi.testclient import TestClient
import server
from schemas import Settings, ChatResult

release = threading.Event()
async def slow_agent(text, settings):
    await asyncio.to_thread(release.wait, 10)
    return ChatResult(text=text)

with tempfile.TemporaryDirectory() as temporary, TestClient(server.app) as client, \
     patch.object(server, 'MEDIA', Path(temporary)), \
     patch.object(server.speech, 'transcribe', return_value='Testo disponibile subito'), \
     patch.object(server, 'ask_agent', side_effect=slow_agent):
    with client.websocket_connect('/ws') as socket, ThreadPoolExecutor() as workers:
        job = workers.submit(client.post, '/api/voice-chat',
            files={'audio': ('recording.wav', b'test', 'audio/wav')}, data={'request_id': 'voice-123'})
        assert socket.receive_json()['kind'] == 'progress'
        event = socket.receive_json()
        assert event == {'kind': 'transcript', 'data': {'text': 'Testo disponibile subito', 'request_id': 'voice-123'}}
        assert not job.done(), 'Transcript must arrive before the agent finishes'
        release.set()
        assert job.result(timeout=10).json()['text'] == 'Testo disponibile subito'
    with patch.object(server, 'ask_agent', side_effect=HTTPException(502, 'Agent unavailable')):
        result = client.post('/api/voice-chat', files={'audio': ('test.wav', b'test', 'audio/wav')})
        assert result.status_code == 502
        assert result.json()['detail']['transcript'] == 'Testo disponibile subito'

    original = httpx.AsyncClient
    calls = []
    def agent(request):
        calls.append((str(request.url), request.content))
        return httpx.Response(200, json={'status': 'ok'})
    settings = Settings(agent_url='http://agent.test/agent')
    with patch.object(server, 'get_settings', return_value=settings), \
         patch.object(server.httpx, 'AsyncClient', side_effect=lambda **kw: original(transport=httpx.MockTransport(agent), **kw)):
        server.add_input(kind='text', text='old')
        assert client.post('/api/conversation/clear', json={}).json() == {'status': 'ok'}
        assert not server.inputs
        assert calls == [('http://agent.test/conversation/clear', b'{}')]
    with patch.object(server, 'get_settings', return_value=Settings()):
        assert client.post('/api/conversation/clear', json={}).status_code == 200
    def failure(request):
        return httpx.Response(500)
    with patch.object(server, 'get_settings', return_value=settings), \
         patch.object(server.httpx, 'AsyncClient', side_effect=lambda **kw: original(transport=httpx.MockTransport(failure), **kw)):
        server.add_input(kind='text', text='keep on failure')
        assert client.post('/api/conversation/clear', json={}).status_code == 200
        assert not server.inputs
    def timeout(request):
        raise httpx.ReadTimeout('Agent unavailable', request=request)
    with patch.object(server, 'get_settings', return_value=settings), \
         patch.object(server.httpx, 'AsyncClient', side_effect=lambda **kw: original(transport=httpx.MockTransport(timeout), **kw)):
        server.add_input(kind='text', text='clear despite timeout')
        assert client.post('/api/conversation/clear', json={}).status_code == 200
        assert not server.inputs
print('PASS early transcript, HTTP fallback/error, reset proxy; local history clears despite agent failure or timeout')
