"""Run in the new environment before setup activates it."""
import argparse
import importlib.metadata as metadata
from pathlib import Path
import tempfile


def verify(profile, models, model, voice_device=None, transcription_device=None):
    from packaging.requirements import Requirement
    # Piper/Whisper declare onnxruntime (CPU) by distribution name. The GPU
    # distribution supplies the same API; never install both DLL sets together.
    errors = []
    for dist in metadata.distributions():
        for raw in dist.requires or []:
            req = Requirement(raw)
            if req.marker and not req.marker.evaluate({'extra': ''}):
                continue
            name = 'onnxruntime-gpu' if profile == 'gpu' and req.name == 'onnxruntime' else req.name
            try:
                version = metadata.version(name)
                if req.specifier and version not in req.specifier:
                    errors.append(f'{name} {version} does not satisfy {req.specifier}')
            except metadata.PackageNotFoundError:
                errors.append(f'Missing {name}, required by {dist.metadata["Name"]}')
    if errors:
        raise RuntimeError('; '.join(errors))
    import fastapi, uvicorn, multipart, websockets, httpx
    import speech
    from schemas import Settings
    import tts_device
    settings = Settings(models_dir=str(models), stt_model=model if isinstance(model, str) else model[0],
                        stt_device=transcription_device or ('cuda' if profile == 'gpu' else 'cpu'),
                        tts_device=voice_device or ('cuda' if profile == 'gpu' else 'cpu'))
    with tempfile.TemporaryDirectory(prefix='vh-verify-') as temporary:
        for character in ('julia', 'david'):
            settings.character = character
            for language, text in [('it', 'La voce è pronta.'), ('en', 'The voice is ready.')]:
                settings.language = language
                speech.synthesize(text, settings, Path(temporary))
                print('Speech', character, language, tts_device.last_run, flush=True)
        for selected in ([model] if isinstance(model, str) else model):
            settings.stt_model = selected
            print('Transcription', selected, speech.prepare_preview(settings), flush=True)
    print('Verification complete: dependencies, four voices and both Whisper models.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', choices=['cpu', 'gpu'], required=True)
    parser.add_argument('--models', type=Path, required=True)
    parser.add_argument('--model', nargs='+', required=True)
    parser.add_argument('--voice-device', choices=['cpu', 'cuda'])
    parser.add_argument('--transcription-device', choices=['cpu', 'cuda'])
    args = parser.parse_args()
    verify(args.profile, args.models, args.model, args.voice_device, args.transcription_device)
