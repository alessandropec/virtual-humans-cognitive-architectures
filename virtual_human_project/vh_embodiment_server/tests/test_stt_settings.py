from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'app'), str(PROJECT / 'build/common')]
from fastapi.testclient import TestClient
import server

with TemporaryDirectory() as temporary, patch.object(server, 'CONFIG', Path(temporary) / 'settings.json'), TestClient(server.app) as client:
    settings = client.get('/api/settings').json()
    assert settings['stt_model'] == 'small'
    assert settings['language'] == settings['stt_language'] == 'en'
    for voice, transcription in (('en', 'it'), ('it', 'en'), ('it', 'it'), ('en', 'en')):
        settings.update(language=voice, stt_language=transcription)
        assert client.put('/api/settings', json=settings).status_code == 200
        persisted = client.get('/api/settings').json()
        assert persisted['language'] == voice
        assert persisted['stt_language'] == transcription
    for field in ('language', 'stt_language'):
        assert client.put('/api/settings', json={**settings, field: 'auto'}).status_code == 422
    for name in ('tiny', 'small'):
        for live in (True, False):
            settings.update(stt_model=name, live_transcription=live)
            assert client.put('/api/settings', json=settings).status_code == 200
            persisted = client.get('/api/settings').json()
            assert persisted['stt_model'] == name and persisted['live_transcription'] is live
    settings['stt_model'] = 'invalid'
    assert client.put('/api/settings', json=settings).status_code == 422
    assert client.get('/api/settings').json()['stt_model'] == 'small'
print('PASS Small default, model/live mode persistence, invalid model rejection')
