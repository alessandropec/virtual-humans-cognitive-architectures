"""Verify the server using the real mock agent, without keys or LLM calls."""
import sys
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from schemas import AgentReply, ModelReply
import vh_cognitive_server as server
from agents.mock_agent import response as mock_response

assert not any(name.startswith('vh_embodiment_server') for name in sys.modules)
schema = AgentReply.model_json_schema()
assert schema['properties']['speech_text']['description']
assert 'whiteboard' in schema['properties']
assert 'whiteboard' not in ModelReply.model_json_schema()['properties']
assert '$defs' not in schema
assert 'stop' not in schema['properties']['gesture']['anyOf'][0]['enum']
assert '\U0001f609' in schema['properties']['expression']['anyOf'][0]['enum']
assert 'handup' in schema['properties']['gesture']['anyOf'][0]['enum']
assert 'body_animation' not in schema['properties']

with TestClient(server.app) as client, patch.object(server, 'response', side_effect=mock_response):
    for endpoint in ('/agent', '/chat'):
        result = client.post(endpoint, json={'text':'Anything'})
        assert result.status_code == 200, result.text
        assert result.json() == AgentReply(speech_text='Hello world').model_dump()
    null_reply = AgentReply(speech_text='Hello', emotion=None, expression=None, gesture=None)
    with patch.object(server, 'response', return_value=null_reply):
        assert client.post('/agent', json={'text':'Hello'}).json() == null_reply.model_dump()
    reply = AgentReply(speech_text='Hello', emotion='HAPPY',
                       expression='\U0001f609', gesture='handup')
    with patch.object(server, 'response', return_value=reply):
        assert client.post('/agent', json={'text':'Hello'}).json() == reply.model_dump()
        assert client.post('/chat', json={'text':'Hello'}).json() == reply.model_dump()
    assert client.post('/agent', json={'text':''}).status_code == 422
    assert client.post('/conversation/clear').json() == {'status':'ok'}
print('PASS real mock agent, common AgentReply contract, structured forwarding and validation')
