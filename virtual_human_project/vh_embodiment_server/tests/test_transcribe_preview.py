from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'app'), str(PROJECT / 'build/common')]
from fastapi.testclient import TestClient
import server

with tempfile.TemporaryDirectory() as temporary, TestClient(server.app) as client, patch.object(server,'MEDIA',Path(temporary)), patch.object(server,'ask_agent',side_effect=AssertionError('Must not call agent')):
    with patch.object(server.speech,'prepare_preview',return_value={'device':'cpu'}) as prepare:
        assert client.post('/api/transcribe/prepare',json={}).json()=={'status':'ready','diagnostics':{'device':'cpu'}}
        prepare.assert_called_once()
    with patch.object(server.speech,'prepare_preview',side_effect=OSError('Offline')):
        assert client.post('/api/transcribe/prepare',json={}).status_code==503
    with patch.object(server.speech,'transcribe',return_value='Anteprima') as transcribe:
        result=client.post('/api/transcribe',files={'audio':('partial.webm',b'partial','audio/webm')})
        assert result.status_code==200,result.text
        assert result.json()['text']=='Anteprima'
        assert result.json()['reply'] is None
        assert transcribe.call_args.kwargs=={'preview':True}
    assert not list(Path(temporary).iterdir())
    with patch.object(server.speech,'transcribe',side_effect=server.speech.AudioInputError('Silenzio')):
        assert client.post('/api/transcribe',files={'audio':('partial.webm',b'partial','audio/webm')}).json()['text']==''
    with patch.object(server.speech,'transcribe',side_effect=FileNotFoundError('Missing model')):
        assert client.post('/api/transcribe',files={'audio':('partial.webm',b'partial','audio/webm')}).status_code==503
    assert client.post('/api/transcribe',files={'audio':('partial.webm',b'','audio/webm')}).status_code==400
    assert not list(Path(temporary).iterdir())
print('PASS model preparation, preview-only transcription, fast mode, silence handling, model errors, no agent/TTS, audio cleanup')
