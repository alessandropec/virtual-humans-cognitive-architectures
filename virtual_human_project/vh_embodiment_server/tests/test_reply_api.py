"""Contract, image upload and complete response delivery without STT/TTS models."""
from pathlib import Path
import sys
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import httpx
from PIL import Image
from fastapi.testclient import TestClient

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'app'), str(PROJECT / 'build/common')]
import server
from schemas import Settings

with TestClient(server.app) as client:
    picture = BytesIO()
    Image.new('RGB', (8, 8), 'red').save(picture, 'PNG')
    uploaded = client.post('/api/whiteboard/images', files={'file': ('test.png', picture.getvalue(), 'image/png')})
    assert uploaded.status_code == 200, uploaded.text
    board = {'type': 'image', **uploaded.json()}
    assert (server.MEDIA / Path(board['image_url']).name).is_file()
    assert client.post('/api/whiteboard/images', files={'file': ('bad.png', b'not an image')}).status_code == 422
    assert client.post('/api/whiteboard/images', files={'file': ('empty.png', b'')}).status_code == 413
    settings = Settings(speech_enabled=False, agent_url='http://agent.test/agent')
    reply = {'speech_text': 'Guarda lo schema', 'emotion': 'HAPPY',
             'expression': '😉',
             'gesture': 'handup', 'whiteboard': board}
    original = httpx.AsyncClient
    with patch.object(server, 'get_settings', return_value=settings), \
         patch.object(server.httpx, 'AsyncClient', side_effect=lambda **kw: original(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=reply)), **kw)):
        result = client.post('/api/chat', json={'text': 'Spiega'})
        assert result.status_code == 200, result.text
        assert all(result.json()['reply'][key] == value for key, value in reply.items())
        assert result.json()['reply']['whiteboard'] == board
        with client.websocket_connect('/ws') as socket, ThreadPoolExecutor() as workers:
            def perform(payload):
                job = workers.submit(client.post, '/api/speak', json=payload)
                command = socket.receive_json()
                assert command['kind'] == 'receive'
                socket.send_json({'id': command['id'], 'state': {'whiteboard': board}})
                response = job.result(timeout=5)
                assert response.status_code == 200, response.text
                return command['data']
            data = perform(reply)
            assert data['whiteboard'] == board and data['expression'] == reply['expression']
            assert perform({'whiteboard': {'type': 'clear'}})['whiteboard'] == {'type': 'clear'}
            assert perform({'speech_text': 'Continuiamo'})['whiteboard'] is None
            simple = perform({'expression': '\U0001f609', 'gesture': 'handup'})
            assert simple['expression'] == '\U0001f609'
            assert simple['gesture'] == 'handup'
            with patch.object(server, 'get_settings', return_value=Settings(speech_enabled=True)), patch.object(server.speech, 'synthesize', side_effect=AssertionError('TTS must not run without text')):
                for payload in [{}, {'emotion':'HAPPY'}, {'speech_text':None,'emotion':None,'expression':None,'gesture':None,'whiteboard':None}]:
                    data = perform(payload)
                    assert data['audio_url'] is None
            assert client.post('/api/animations/upload').status_code == 404
            for bad in [
                {'gesture': {'name': 'pose:unknown'}},
                {'gesture': {'name': 'animation:unknown'}},
                {'gesture': {'name': 'gesture:unknown'}},
                {'gesture': 'stop'},
                {'gesture': {'name': 'gesture:👍'}},
                {'expression': {'name': '👍'}},
                {'whiteboard': {'type': 'image', 'image_url': '/media/board-' + 'a' * 32 + '.png'}},
                {'whiteboard': {'type': 'image', 'image_url': 'https://example.com/image.png'}},
            ]:
                assert client.post('/api/speak', json=bad).status_code == 422, bad
    properties = client.get('/openapi.json').json()['components']['schemas']['SpeakRequest']['properties']
    assert 'gesture' in properties and 'action' not in properties
    catalog = client.get('/api/catalog').json()
    assert 'gestures' in catalog
    assert not any(key in catalog for key in ('body_animations', 'poses', 'animations'))
    assert all(':' not in item['id'] for item in catalog['gestures'])
    assert all(item['id'] != 'stop' for item in catalog['gestures'])
    assert all('combined' not in item for item in catalog['expressions'])
    assert not any(item['id'] == '👍' for item in catalog['expressions'])
    for endpoint, payload in [('/api/expression', {'expression': '👍'}), ('/api/gesture', {'gesture': 'gesture:👍'})]:
        assert client.post(endpoint, json=payload).status_code == 422
    assert client.post('/api/body-animation', json={'name':'handup'}).status_code == 404
print('PASS response contract, agent forwarding, upload, WebSocket delivery and invalid requests')
