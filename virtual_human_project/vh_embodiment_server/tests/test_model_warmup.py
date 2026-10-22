"""Selected model caches are reused; changes prepare only the affected channel."""
import asyncio
from contextlib import suppress
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from model_warmup import ModelWarmup
from schemas import Settings


async def main():
    settings = Settings(stt_device='cpu')
    warmer = ModelWarmup(lambda: settings, Path('.'))
    async def finished():
        for _ in range(200):
            if warmer.status['state'] != 'loading':
                return
            await asyncio.sleep(.01)
        raise AssertionError('Warmup did not finish')
    with patch('speech.prepare_preview') as stt, patch('speech.reset_transcription'), \
         patch('tts_device.reset'), patch.object(warmer, 'voice') as voice:
        task = asyncio.create_task(warmer.run())
        try:
            warmer.request()
            await finished()
            assert warmer.status['state'] == 'ready'
            stt.assert_called_once()
            voice.assert_called_once()
            warmer.request()
            await asyncio.sleep(.02)
            assert stt.call_count == voice.call_count == 1
            settings = settings.model_copy(update={'stt_model': 'tiny'})
            warmer.request()
            await finished()
            assert stt.call_count == 2 and voice.call_count == 1
            settings = settings.model_copy(update={'language': 'it'})
            warmer.request()
            await finished()
            assert stt.call_count == 2 and voice.call_count == 2
            settings = settings.model_copy(update={'character': 'david'})
            voice.side_effect = FileNotFoundError('Voice is missing')
            warmer.request()
            await finished()
            assert warmer.status['state'] == 'error'
            assert 'Voice is missing' in warmer.status['errors']['voice']
            assert warmer.status['missing'] is True
            assert 'Speech models not found in:' in warmer.status['message']
            assert 'continue without speech models' in warmer.status['message']
            warmer.request()
            assert not warmer.event.is_set(), 'Unchanged settings must not retry a failed warmup'
            voice.side_effect = None
            warmer.request(force=True)
            await finished()
            assert warmer.status['state'] == 'ready'
            assert stt.call_count == 2
            warmer.skip()
            assert warmer.disabled and warmer.status['state'] == 'skipped'
            warmer.request()
            assert not warmer.event.is_set()
            settings = settings.model_copy(update={'language':'en'})
            warmer.request()
            assert not warmer.disabled
            await finished()
            assert warmer.status['state'] == 'ready'
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
    print('PASS initial warmup, cache reuse, selective changes and visible errors')


asyncio.run(main())
