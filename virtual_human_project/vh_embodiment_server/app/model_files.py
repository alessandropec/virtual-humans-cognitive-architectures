"""Local model catalog. This module never downloads files."""
from pathlib import Path

STT_MODELS = ('small', 'tiny')
VOICE_SOURCES = {
    'julia_en': 'en/en_US/hfc_female/medium/en_US-hfc_female-medium',
    'julia_it': 'it/it_IT/serena/high/it_IT-serena-high',
    'david_en': 'en/en_US/hfc_male/medium/en_US-hfc_male-medium',
    'david_it': 'it/it_IT/riccardo/x_low/it_IT-riccardo-x_low',
}


def whisper_available(folder):
    return all((folder / name).is_file() for name in ('config.json', 'model.bin', 'tokenizer.json')) and (folder / 'vocabulary.txt').is_file()


def installed_whisper(directory):
    return [name for name in STT_MODELS if whisper_available(directory / f'faster-whisper-{name}')]


def require_whisper(folder):
    if not whisper_available(folder):
        raise FileNotFoundError('Whisper model is missing or incomplete. Run the installer again; the app does not download models.')
    return folder


def voice_path(settings):
    stem = VOICE_SOURCES[f'{settings.character}_{settings.language}'].rsplit('/', 1)[1]
    path = Path(settings.models_dir) / f'piper-voice-{stem}' / f'{stem}.onnx'
    if not path.is_file() or not Path(str(path) + '.json').is_file():
        raise FileNotFoundError('Piper voice is missing or incomplete. Run the installer again; the app does not download voices.')
    return path
