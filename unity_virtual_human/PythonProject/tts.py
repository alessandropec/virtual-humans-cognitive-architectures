"""Text to speech using the Piper voice included in the course ZIP."""
from functools import lru_cache
from pathlib import Path
import threading
import time
import uuid
import wave
from schemas import Language

PROJECT_DIR = Path(__file__).resolve().parent
VOICES = {
    "en": PROJECT_DIR / "models" / "piper-voice-en_US-hfc_female-medium" / "en_US-hfc_female-medium.onnx",
    "it": PROJECT_DIR / "models" / "piper-voice-it_IT-serena-high" / "it_IT-serena-high.onnx",
}
AUDIO_DIR = PROJECT_DIR / "static" / "audio"
_lock = threading.Lock()


@lru_cache(maxsize=2)
def _voice(language: Language):
    voice_path = VOICES[language]
    if not voice_path.is_file() or not voice_path.with_suffix(".onnx.json").is_file():
        raise FileNotFoundError(f"The {language} Piper voice is missing. Extract the current speech models download first.")
    from piper import PiperVoice
    return PiperVoice.load(str(voice_path))


def synthesize(text: str, language: Language = "en") -> str:
    """Save a WAV and return the relative URL Unity can download."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    name = uuid.uuid4().hex + ".wav"
    with _lock, wave.open(str(AUDIO_DIR / name), "wb") as audio:
        _voice(language).synthesize_wav(text, audio)
    return "/static/audio/" + name


def cleanup(max_age_seconds: int = 3600) -> None:
    """Discard old generated speech while keeping recent audio available to Unity."""
    cutoff = time.time() - max_age_seconds
    for path in AUDIO_DIR.glob("*.wav"):
        if path.stat().st_mtime < cutoff:
            path.unlink(missing_ok=True)
