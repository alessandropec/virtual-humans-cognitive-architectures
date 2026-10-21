"""Speech to text using the Whisper small model included in the course ZIP."""
from functools import lru_cache
from pathlib import Path
from schemas import load_speech_settings

MODEL_DIR = Path(__file__).resolve().parent / "models" / "faster-whisper-small"


@lru_cache(maxsize=1)
def _model():
    if not (MODEL_DIR / "model.bin").is_file():
        raise FileNotFoundError("Whisper is missing. Extract the complete course download first.")
    from faster_whisper import WhisperModel
    return WhisperModel(str(MODEL_DIR), device="cpu", compute_type="int8", local_files_only=True)


def transcribe(audio_path: str | Path) -> str:
    """Read a recording and return its words. The model is loaded once, on first use."""
    language = load_speech_settings().stt_language
    segments, _ = _model().transcribe(
        str(audio_path), language=None if language == "auto" else language,
        task="transcribe", vad_filter=True)
    return " ".join(segment.text.strip() for segment in segments).strip()
