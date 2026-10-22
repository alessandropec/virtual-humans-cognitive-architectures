"""Whisper device selection and process-local CUDA DLL discovery."""
import os
from pathlib import Path
import sys

_dll_handles = []
_initialized = False
last_run = {}
gpu_failures = {}


class SpeechDeviceError(RuntimeError):
    pass


def configure_cuda():
    global _initialized
    if _initialized:
        return
    if os.name == 'nt':
        directories = set()
        for base in sys.path:
            root = Path(base) / 'nvidia'
            if root.is_dir():
                directories.update(path.parent for path in root.glob('**/*.dll'))
        for directory in sorted(directories):
            _dll_handles.append(os.add_dll_directory(str(directory)))
        if directories:
            os.environ['PATH'] = os.pathsep.join(map(str, sorted(directories))) + os.pathsep + os.environ.get('PATH', '')
    _initialized = True


def availability():
    if sys.platform == "darwin":
        return False, "On macOS, speech and transcription use CPU only."
    try:
        configure_cuda()
        import ctranslate2
        if ctranslate2.get_cuda_device_count() < 1:
            return False, 'No compatible NVIDIA GPU detected.'
        return True, None
    except (RuntimeError, OSError) as exc:
        return False, str(exc)


def choose(path, requested):
    if requested == 'cpu':
        return 'cpu', None
    available, reason = availability()
    if requested == 'auto' and path in gpu_failures:
        available, reason = False, gpu_failures[path]
    if available:
        return 'cuda', None
    if requested == 'cuda':
        raise SpeechDeviceError('NVIDIA GPU unavailable: ' + str(reason))
    return 'cpu', reason


def status(settings):
    available, reason = availability()
    current = last_run if (last_run.get('requested_device') == settings.stt_device
                           and last_run.get('model') == settings.stt_model) else {}
    return {'requested_device': settings.stt_device, 'cuda_detected': available,
            'detection_note': reason, 'last_run': current}
