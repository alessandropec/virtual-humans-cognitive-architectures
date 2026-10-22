"""Piper CPU/CUDA policy, separate from the transcription device."""
from functools import lru_cache
import json
from pathlib import Path
import threading
import time
import sys
import wave

from stt_device import configure_cuda, SpeechDeviceError

lock = threading.Lock()
last_run = {}
gpu_failures = {}


def availability():
    if sys.platform == "darwin":
        return False, "On macOS, speech and transcription use CPU only."
    import onnxruntime
    if 'CUDAExecutionProvider' not in onnxruntime.get_available_providers():
        return False, 'GPU speech support is not installed. Run the installer and select NVIDIA GPU.'
    from stt_device import availability as cuda_availability
    return cuda_availability()


@lru_cache(maxsize=2)
def load_voice(path, device='cpu'):
    from piper import PiperVoice
    from piper.config import PiperConfig
    import onnxruntime
    if not Path(path).is_file():
        raise FileNotFoundError('Piper voice is missing. Run the installer or check the model folder.')
    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.add_session_config_entry('session.intra_op.allow_spinning', '0')
    providers = ['CPUExecutionProvider']
    if device == 'cuda':
        configure_cuda()
        providers.insert(0, ('CUDAExecutionProvider', {'cudnn_conv_algo_search': 'HEURISTIC'}))
    session = onnxruntime.InferenceSession(path, sess_options=options, providers=providers)
    # ORT can silently fall back during initialization; make that explicit.
    if device == 'cuda' and 'CUDAExecutionProvider' not in session.get_providers():
        raise SpeechDeviceError('ONNX Runtime did not activate CUDA. Check GPU drivers and libraries.')
    config = PiperConfig.from_dict(json.loads(Path(path + '.json').read_text(encoding='utf-8')))
    return PiperVoice(config=config, session=session)


def reset():
    with lock:
        load_voice.cache_clear()
        last_run.clear()
        gpu_failures.clear()


def status(settings):
    available, reason = availability()
    current = last_run if (last_run.get('requested_device') == settings.tts_device
                           and last_run.get('language') == settings.language
                           and last_run.get('character') == settings.character) else {}
    return {'requested_device': settings.tts_device, 'cuda_detected': available,
            'detection_note': reason, 'last_run': dict(current)}


def synthesize(text, path, target, settings):
    with lock:
        started = time.perf_counter()
        requested = settings.tts_device
        reason = None
        device = 'cpu'
        if requested != 'cpu':
            available, reason = availability()
            if requested == 'auto' and path in gpu_failures:
                available, reason = False, gpu_failures[path]
            if available:
                device = 'cuda'
            elif requested == 'cuda':
                raise SpeechDeviceError('Speech GPU unavailable: ' + str(reason))

        def render(selected):
            voice = load_voice(path, selected)
            output = wave.open(str(target), 'wb')
            try:
                voice.synthesize_wav(text, output)
            except Exception:
                # Closing an uninitialized WAV must not mask the CUDA error.
                try:
                    output.close()
                except Exception:
                    pass
                raise
            else:
                output.close()

        try:
            render(device)
        except Exception as exc:
            target.unlink(missing_ok=True)
            if device != 'cuda' or isinstance(exc, FileNotFoundError):
                raise
            load_voice.cache_clear()
            if requested == 'cuda':
                raise SpeechDeviceError('GPU speech generation failed: ' + str(exc)) from exc
            reason = str(exc)
            gpu_failures[path] = reason
            device = 'cpu'
            try:
                render(device)
            except Exception:
                target.unlink(missing_ok=True)
                raise
        last_run.clear()
        last_run.update(requested_device=requested, device=device, language=settings.language, character=settings.character,
                        processing_seconds=round(time.perf_counter() - started, 3))
        if reason:
            last_run['fallback_reason'] = reason
        return dict(last_run)
