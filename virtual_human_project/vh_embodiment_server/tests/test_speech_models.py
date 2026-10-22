"""Both STT modes must honor the user's selected model."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import sys

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'app'), str(PROJECT / 'build/common')]
import speech
from schemas import Settings

model = Mock()
model.transcribe.side_effect = lambda *args, **kwargs: (
    [SimpleNamespace(text='Ciao')], SimpleNamespace(language='it'))
with patch('faster_whisper.audio.decode_audio', return_value=np.full(16000, .1, dtype=np.float32)), \
     patch('faster_whisper.vad.get_speech_timestamps', return_value=[{'start': 0, 'end': 16000}]), \
     patch.object(speech, 'load_whisper', return_value=model) as load:
    for name in ('tiny', 'small'):
        for preview in (True, False):
            diagnostics = {}
            settings = Settings(stt_language='it', stt_model=name)
            assert speech.transcribe(Path('audio.webm'), settings, diagnostics, preview=preview) == 'Ciao'
            assert Path(load.call_args.args[0]).name == f'faster-whisper-{name}'
            assert model.transcribe.call_args.kwargs['beam_size'] == (1 if preview else 5)
            assert model.transcribe.call_args.kwargs['language'] == 'it'
            assert diagnostics['model'] == name
print('PASS both installed models apply to both live and complete transcription')
