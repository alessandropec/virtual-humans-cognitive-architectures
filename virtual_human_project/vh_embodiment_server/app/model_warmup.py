"""Prepare only the selected models, serially, and retain their existing caches."""
import asyncio
from pathlib import Path
from starlette.concurrency import run_in_threadpool
import speech
import tts_device


class ModelWarmup:
    def __init__(self, settings, media):
        self.settings = settings
        self.media = media
        self.event = asyncio.Event()
        self.loaded = {}
        self.completed = None
        self.requested = None
        self.disabled = False
        self.status = {'state': 'loading', 'message': 'Preparing speech models...', 'errors': {}}

    def keys(self, settings):
        return ((str(speech.models_path(settings)), settings.stt_model, settings.stt_device),
                (str(speech.models_path(settings)), settings.character, settings.language, settings.tts_device, settings.speech_enabled))

    def skip(self):
        self.disabled = True
        self.status = {'state':'skipped', 'message':'Ready without speech models.', 'errors':{}}

    def request(self, force=False):
        key = self.keys(self.settings())
        if self.requested == key and self.status['state'] == 'loading':
            return
        if self.disabled and self.keys(self.settings()) == self.completed:
            return
        if self.keys(self.settings()) != self.completed or force:
            self.disabled = False
            self.requested = key
            self.status = {'state': 'loading', 'message': 'Preparing selected speech models...', 'errors': {}}
            self.event.set()

    def voice(self, settings):
        url = speech.synthesize('Ciao.' if settings.language == 'it' else 'Hello.', settings, self.media)
        (self.media / Path(url).name).unlink(missing_ok=True)

    async def run(self):
        while True:
            await self.event.wait()
            self.event.clear()
            settings = self.settings()
            keys = self.keys(settings)
            errors = {}
            missing = False
            for channel, key, reset, prepare in (
                ('transcription', keys[0], speech.reset_transcription, speech.prepare_preview),
                ('voice', keys[1], tts_device.reset, self.voice),
            ):
                if channel == 'voice' and not settings.speech_enabled:
                    continue
                if self.loaded.get(channel) == key:
                    continue
                if self.keys(self.settings()) == keys:
                    self.status['message'] = f'Warming up {channel} model...'
                try:
                    await run_in_threadpool(reset)
                    await run_in_threadpool(prepare, settings)
                    self.loaded[channel] = key
                except Exception as error:
                    self.loaded.pop(channel, None)
                    errors[channel] = str(error)
                    missing = missing or isinstance(error, FileNotFoundError)
            self.completed = keys
            if self.keys(self.settings()) == keys:
                self.status = {'state': 'error' if errors else 'ready',
                               'message': 'Model warmup failed. Check Settings and installed models.' if errors else 'Speech models ready.',
                               'errors': errors, 'missing': missing,
                               'models_dir': str(speech.models_path(settings))}
                if missing:
                    self.status['message'] = ('Speech models not found in:\n' + self.status['models_dir'] +
                        '\nSelect the correct folder or continue without speech models.\n'
                        'To download the models, run the installation setup and launch the application from installation.')
