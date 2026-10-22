"""Local Whisper/Piper speech. Model weights stay outside this small prototype."""
from pathlib import Path
import threading
import uuid
import time
import math
import gc
import stt_device
from stt_device import SpeechDeviceError
from model_files import require_whisper, voice_path


class AudioInputError(ValueError):
    """A readable recording without usable speech."""

ROOT = Path(__file__).resolve().parent
stt_lock = threading.Lock()


def models_path(settings):
    return (ROOT / settings.models_dir).resolve()


_whisper = None
_whisper_key = None


def release_whisper():
    """Caller holds stt_lock; unload GPU weights before loading another device/model."""
    global _whisper, _whisper_key
    if _whisper is not None:
        _whisper.model.unload_model()
    _whisper = None
    _whisper_key = None
    gc.collect()


def reset_transcription():
    with stt_lock:
        release_whisper()
        stt_device.gpu_failures.clear()
        stt_device.last_run.clear()


def load_whisper(path, device='cpu'):
    global _whisper, _whisper_key
    from faster_whisper import WhisperModel
    if not (Path(path) / 'model.bin').is_file():
        raise FileNotFoundError('Whisper is missing. Check the model folder in Settings.')
    key = (path, device)
    if _whisper_key != key:
        release_whisper()
        if device == 'cuda':
            stt_device.configure_cuda()
        _whisper = WhisperModel(path, device=device,
            compute_type='float16' if device == 'cuda' else 'int8', local_files_only=True,
            cpu_threads=4 if Path(path).name == 'faster-whisper-tiny' else 2)
        _whisper_key = key
    return _whisper


def recognize(audio, path, settings, options, stats):
    """Consume lazy segments inside the GPU error boundary, then retry only in Auto."""
    requested = settings.stt_device
    device, reason = stt_device.choose(path, requested)
    stats.update(requested_device=requested, device=device,
                 compute_type='float16' if device == 'cuda' else 'int8')
    if reason:
        stats['fallback_reason'] = reason
    def run(selected):
        model = load_whisper(path, selected)
        segments, info = model.transcribe(audio, **options)
        return ' '.join(segment.text.strip() for segment in segments).strip(), info
    try:
        result = run(device)
    except (RuntimeError, OSError) as exc:
        if device != 'cuda':
            raise
        reason = str(exc)
        release_whisper()
        if requested == 'cuda':
            raise SpeechDeviceError('GPU transcription failed: ' + reason + '. Select CPU or Auto in Settings.') from exc
        stt_device.gpu_failures[path] = reason
        stats.update(device='cpu', compute_type='int8', fallback_reason=reason)
        result = run('cpu')
    return result


def prepare_preview(settings):
    import numpy as np
    from faster_whisper.vad import get_vad_model
    with stt_lock:
        folder = require_whisper(models_path(settings) / f'faster-whisper-{settings.stt_model}')
        stats = {'model': settings.stt_model}
        # A real inference catches missing cuBLAS/cuDNN, unlike model loading alone.
        recognize(np.zeros(16000, dtype=np.float32), str(folder), settings,
                  {'language':'en', 'beam_size':1, 'max_new_tokens':1, 'without_timestamps':True}, stats)
        get_vad_model()
        stt_device.last_run.clear()
        stt_device.last_run.update(stats)
        return stats


def synthesize(text, settings, output_dir):
    target = output_dir / (uuid.uuid4().hex + '.wav')
    import tts_device
    local = settings.model_copy(update={'models_dir': str(models_path(settings))})
    tts_device.synthesize(text, str(voice_path(local)), target, settings)
    tts_device.last_run['model'] = voice_path(local).stem
    return '/media/' + target.name


def transcribe(path, settings, diagnostics=None, *, preview=False):
    """Decode once, boost quiet input, trim silence at the edges, then transcribe."""
    import numpy as np
    from faster_whisper.audio import decode_audio
    from faster_whisper.vad import get_speech_timestamps, VadOptions
    stats = diagnostics if diagnostics is not None else {}
    stats['model'] = settings.stt_model
    started = time.perf_counter()
    try:
        audio = decode_audio(str(path), sampling_rate=16000)
        if len(audio) < 1600:
            raise AudioInputError('Recording too short. Wait for Listening and say a sentence.')
        peak = float(np.max(np.abs(audio)))
        rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
        stats.update(duration_seconds=round(len(audio) / 16000, 2),
                     peak_dbfs=round(20 * math.log10(max(peak, 1e-6)), 1),
                     rms_dbfs=round(20 * math.log10(max(rms, 1e-6)), 1))
        if peak < 1e-5:
            raise AudioInputError('No microphone signal. Check the input device and level in Settings.')
        gain = min(8.0, max(1.0, 0.8 / peak))
        audio = np.clip(audio * gain, -1.0, 1.0)
        stats['gain_db'] = round(20 * math.log10(gain), 1)
        with stt_lock:
            spans = get_speech_timestamps(audio, VadOptions(
                threshold=settings.vad_threshold, min_speech_duration_ms=100,
                min_silence_duration_ms=500, speech_pad_ms=300))
            if not spans:
                raise AudioInputError('No speech detected. Replay the recording and check the microphone, level and language in Settings.')
            start, end = spans[0]['start'], spans[-1]['end']
            stats.update(trimmed_start_seconds=round(start / 16000, 2),
                         trimmed_end_seconds=round((len(audio) - end) / 16000, 2),
                         speech_seconds=round(sum(span['end'] - span['start'] for span in spans) / 16000, 2))
            model_name = f'faster-whisper-{settings.stt_model}'
            text, info = recognize(audio[start:end], str(models_path(settings) / model_name), settings,
                dict(task='transcribe', vad_filter=False, beam_size=1 if preview else 5,
                     **({'temperature': 0.0, 'without_timestamps': True} if preview else {}),
                     condition_on_previous_text=False,
                     language=settings.stt_language), stats)
            stats['language'] = info.language
            if not text:
                raise AudioInputError('Speech detected but transcription failed. Select the language and replay the recording.')
            return text
    finally:
        stats['processing_seconds'] = round(time.perf_counter() - started, 2)
        if 'device' in stats:
            stt_device.last_run.clear()
            stt_device.last_run.update(stats)
