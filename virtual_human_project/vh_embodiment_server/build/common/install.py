"""Windows setup with optional shared course environment preparation."""
import argparse
import copy
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import venv
import course_environment

from downloads import check_space, download, hf_files, read_json, valid

ROOT = Path(__file__).resolve().parent
SETUP = ROOT / '.setup'
WHEELS = SETUP / 'wheels'
from model_files import STT_MODELS, VOICE_SOURCES


class GPUSetupError(RuntimeError):
    """GPU unavailable or its speech verification failed."""


_bar = None  # active Progress, advanced a little for each package pip reports


def log(message):
    print(message, flush=True)
    if _bar and _bar.cap and str(message).startswith(('Collecting ', 'Processing ', 'Downloading ')):
        _bar.creep()
    with (SETUP / 'install.log').open('a', encoding='utf-8') as output:
        output.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} {message}\n')


def atomic_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)


def requirements(profile):
    lines = (ROOT / 'requirements.txt').read_text().splitlines()
    result = [line for line in lines if line and not line.startswith('#')]
    if profile == 'gpu':
        result = [line for line in result if not line.startswith('onnxruntime==')]
        result += [line for line in (ROOT / 'requirements-gpu.txt').read_text().splitlines()
                   if line and not line.startswith('#')]
    return result


def wheel(requirement):
    from pip._vendor.packaging.tags import sys_tags
    from pip._vendor.packaging.utils import parse_wheel_filename
    name, version = requirement.split('==')
    metadata = read_json(f'https://pypi.org/pypi/{name}/{version}/json')
    tags = {tag: index for index, tag in enumerate(sys_tags())}
    matches = []
    for entry in metadata['urls']:
        if entry['packagetype'] != 'bdist_wheel' or entry.get('yanked'):
            continue
        _, _, _, supported = parse_wheel_filename(entry['filename'])
        scores = [tags[tag] for tag in supported if tag in tags]
        if scores:
            matches.append((min(scores), entry))
    if not matches:
        raise RuntimeError(f'No compatible package for {requirement}; automatic source compilation is disabled.')
    entry = min(matches, key=lambda match: match[0])[1]
    return {'name': entry['filename'], 'url': entry['url'], 'size': entry['size'],
            'hash': entry['digests']['sha256']}


def model_plan(model, voices=True):
    selected = [model] if isinstance(model, str) else model
    manifest = json.loads(Path(__file__).with_name('speech-models.json').read_text(encoding='utf-8'))
    if manifest['voices'] != list(VOICE_SOURCES.values()):
        raise RuntimeError('The speech model manifest must match the configured voices.')
    return [item for item in manifest['models']
            if (item['relative'].startswith('piper-voice-') and voices)
            or any(item['relative'].startswith(f'faster-whisper-{name}/') for name in selected)]


class Progress:
    """Overall percentage for the setup window: downloads by bytes, later phases by fixed weight."""
    DOWNLOADS = 60  # downloads end here; course environment 60-85, package install 85-92, checks 92-100

    def __init__(self, total_bytes):
        self.total = total_bytes
        self.done = 0
        self.last = -1
        self.cap = 0  # upper bound for creep() during phases without byte counts
        self.position = 0.0

    def phase(self, start, end):
        self.emit(start)
        self.position, self.cap = float(start), end - 1

    def creep(self):
        self.position = min(self.cap, self.position + 0.4)
        self.emit(self.position)

    def emit(self, percent):
        percent = max(self.last, min(100, int(percent)))
        if percent != self.last:
            self.last = percent
            print(f'PROGRESS {percent}', flush=True)

    def reporter(self):
        """Wrap the download log: lines with 'x/y MB' update the bar for the current file."""
        def report(message):
            log(message)
            match = re.search(r'([\d.]+)/([\d.]+) MB', message)
            if match and self.total:
                current = float(match.group(1)) * 1024**2
                self.emit(5 + (self.DOWNLOADS - 5) * min(1, (self.done + current) / self.total))
        return report

    def finished(self, item):
        self.done += item['size']
        if self.total:
            self.emit(5 + (self.DOWNLOADS - 5) * min(1, self.done / self.total))


def nvidia():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version', '--format=csv,noheader'],
                                capture_output=True, text=True, timeout=15, creationflags=0x08000000)
        return result.stdout.strip() if result.returncode == 0 else ''
    except (OSError, subprocess.TimeoutExpired):
        return ''


def run(command, cwd=None):
    # Log pip output and keep its progress visible. No shell interpolation.
    process = subprocess.Popen(list(map(str, command)), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf-8', errors='replace', cwd=cwd, env={**os.environ, 'PYTHONUTF8': '1'})
    try:
        for line in process.stdout:
            log(line.rstrip())
        if process.wait():
            raise RuntimeError('Command failed; see .setup/install.log. Run the installer again to retry.')
    except BaseException:
        process.terminate()
        process.wait()
        raise


def main(args):
    if sys.version_info[:2] != (3, 12) or platform.machine().lower() not in ('amd64', 'x86_64'):
        raise RuntimeError('64-bit Python 3.12 is required. Run the installer.')
    SETUP.mkdir(exist_ok=True)
    # Windows releases the lock even if the terminal is closed or setup crashes.
    import msvcrt
    with (SETUP / 'install.lock').open('a+b') as lock:
        lock.seek(0)
        if not lock.read(1):
            lock.write(b'0'); lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise RuntimeError('Another installer is already running.')
        folder = course_environment.environment(ROOT)
        python = course_environment.python_path(ROOT)
        if not args.plan and folder.exists():
            error = f'Incompatible course environment: {folder}. Rename or remove it, then run setup again.'
            if not (folder / 'pyvenv.cfg').is_file() or not python.is_file():
                raise RuntimeError(error)
            try:
                run([python, '-c', 'import sys, struct; assert sys.version_info[:2] == (3, 12) and struct.calcsize("P") == 8 and sys.prefix != sys.base_prefix'])
            except Exception as exc:
                raise RuntimeError(error) from exc
        try:
            succeeded = install(args)
        except GPUSetupError as exc:
            if args.profile != 'gpu' or args.plan:
                raise
            log('NVIDIA setup failed: ' + str(exc))
            log('Trying CPU setup without downloading more CUDA components.')
            fallback = copy.copy(args)
            fallback.profile = 'cpu'
            fallback.voice_device = fallback.transcription_device = 'cpu'
            fallback.yes = True
            succeeded = install(fallback)
            atomic_json(ROOT / 'setup-result.json', {'profile': 'cpu', 'gpu_warning': str(exc)})
            log('CPU setup is ready. GPU is optional; you can retry later.')
        if succeeded:
            config_path = ROOT / 'settings.json'
            config = json.loads(config_path.read_text(encoding='utf-8'))
            course_environment.configure(ROOT, config)
            atomic_json(config_path, config)
            log('Installation completed and verified. Open VirtualHuman.exe to start.')


def install(args):
    config_path = ROOT / 'settings.json'
    config = json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
    gpu = nvidia()
    log('VH Embodiment Server - Windows setup, Python 3.12, no administrator privileges')
    log('GPU detected: ' + (gpu or 'no NVIDIA GPU available'))
    if not args.profile:
        answer = input('Profile: [1] CPU, smaller (default), [2] NVIDIA GPU: ').strip()
        args.profile = 'gpu' if answer == '2' else 'cpu'
    if args.profile == 'gpu' and not gpu:
        raise GPUSetupError('NVIDIA GPU not detected: install the official driver or select CPU. Drivers are never installed automatically.')
    models = Path(args.models_dir or config.get('models_dir', str(ROOT / 'models')))
    models = (ROOT / models).resolve()
    if not args.yes and not args.plan:
        chosen = input(f'Model folder [{models}] (Enter to confirm): ').strip().strip('"')
        if chosen:
            models = Path(chosen).expanduser().resolve()
    # Both default to yes, also for callers that predate these options.
    selected_models = list(STT_MODELS) if getattr(args, 'transcription_models', 'yes') == 'yes' else []
    voices = getattr(args, 'voice_models', 'yes') == 'yes'
    selected_model = 'small'
    runtime = course_environment.environment(ROOT)
    python = runtime / 'Scripts/python.exe'
    log('Checking packages and models: reading metadata only, not model weights.')
    # Reuse the exact saved plan after interruption, even if an upstream model changes.
    plan_path = SETUP / f'plan-{args.profile}-{"-".join(selected_models)}.json'
    wanted = requirements(args.profile)
    if plan_path.exists():
        plan = json.loads(plan_path.read_text())
    else:
        plan = {}
    if plan.get('requirements') != wanted or plan.get('voices') != list(VOICE_SOURCES.values()):
        with ThreadPoolExecutor(max_workers=4) as pool:
            wheels = list(pool.map(wheel, wanted))
        plan = {'requirements': wanted, 'wheels': wheels, 'models': model_plan(selected_models, voices),
                'voices': list(VOICE_SOURCES.values())}
        atomic_json(plan_path, plan)
    # Always use the pinned course models and current primary/backup download sources.
    plan['models'] = model_plan(selected_models, voices)
    missing_wheels = [item for item in plan['wheels'] if not valid(WHEELS / item['name'], item)]
    missing_models = [item for item in plan['models'] if not valid(models / item['relative'], item)]
    wheel_bytes = sum(item['size'] for item in missing_wheels)
    model_bytes = sum(item['size'] for item in missing_models)
    # Conservative unpack/install allowance, distinct from network transfer size.
    runtime_space = wheel_bytes + 4 * sum(item['size'] for item in plan['wheels']) + 512 * 1024**2
    log(f'Profile {args.profile.upper()} | Speech recognition: '
        + (f'Whisper {", ".join(selected_models)}' if selected_models else 'not installed')
        + ' | Voices: ' + ('Italian + English' if voices else 'not installed'))
    log(f'Runtime: {runtime}\nModels: {models}\nRemaining downloads: {(wheel_bytes + model_bytes) / 1024**3:.2f} GB '
        '(compatible partial files are resumed).')
    log(f'Estimated disk space: runtime/cache {runtime_space / 1024**3:.2f} GB + models {model_bytes / 1024**3:.2f} GB, '
        'plus a 256 MB margin. Verified cache files are retained for repairs.')
    # Count together if both destinations are on the same Windows volume.
    same_volume = runtime.anchor.lower() == models.anchor.lower()
    check_space(ROOT, runtime_space + (model_bytes if same_volume else 0))
    if not same_volume:
        check_space(models, model_bytes)
    if args.plan:
        log('Plan complete. No packages or models were downloaded or installed.')
        return
    if not args.yes and input('Continue? [y/N]: ').strip().lower() not in ('y', 'yes'):
        log('Installation cancelled before downloads.')
        return
    # Never overwrite a runtime while its server is using DLLs.
    if python.exists():
        probe = subprocess.run(['powershell', '-NoProfile', '-Command',
            'Get-CimInstance Win32_Process | Select-Object -ExpandProperty ExecutablePath'],
            capture_output=True, text=True, creationflags=0x08000000)
        if str(python).lower() in probe.stdout.lower():
            raise RuntimeError('This runtime is in use. Close its server before repair or update.')
    WHEELS.mkdir(exist_ok=True)
    global _bar
    bar = _bar = Progress(wheel_bytes + model_bytes)
    bar.emit(5)
    for index, item in enumerate(plan['wheels'], 1):
        log(f'[Package {index}/{len(plan["wheels"])}]')
        download(item, WHEELS / item['name'], bar.reporter())
        if item in missing_wheels:
            bar.finished(item)
    for index, item in enumerate(plan['models'], 1):
        log(f'[Model/file {index}/{len(plan["models"])}]')
        download(item, models / item['relative'], bar.reporter())
        if item in missing_models:
            bar.finished(item)
    bar.phase(Progress.DOWNLOADS, 85)
    course_environment.prepare(ROOT, run, log)
    bar.phase(85, 92)
    # CPU and GPU ONNX packages share files. Remove the other variant first.
    run([python, '-m', 'pip', 'uninstall', '-y', 'onnxruntime' if args.profile == 'gpu' else 'onnxruntime-gpu'])
    log('Installing verified files without additional downloads…')
    run([python, '-m', 'pip', 'install', '--no-index', '--no-deps', '--disable-pip-version-check',
         *[WHEELS / item['name'] for item in plan['wheels']]])
    bar.phase(92, 100)
    log('Checking imports, dependencies and real speech inference…')
    try:
        run([python, ROOT / 'verify_install.py', '--profile', args.profile, '--models', models, '--model', *selected_models,
             *([] if voices else ['--no-voices']),
             '--voice-device', 'cuda' if args.voice_device == 'auto' else 'cpu',
             '--transcription-device', 'cuda' if args.transcription_device == 'auto' else 'cpu'])
    except RuntimeError as exc:
        if args.profile == 'gpu':
            raise GPUSetupError(str(exc)) from exc
        raise
    # Publish only a successfully verified runtime. Existing settings are retained.
    config.update(models_dir=str(models), stt_model=selected_model)
    config.setdefault('language', 'en')
    if config.get('stt_language') not in ('it', 'en'):
        config['stt_language'] = 'en'
    config.setdefault('character', 'julia')
    if args.transcription_device is not None:
        config['stt_device'] = args.transcription_device
    else:
        config.setdefault('stt_device', 'auto' if args.profile == 'gpu' else 'cpu')
    if args.voice_device is not None:
        config['tts_device'] = args.voice_device
    else:
        config.setdefault('tts_device', 'auto' if args.profile == 'gpu' else 'cpu')
    atomic_json(config_path, config)
    atomic_json(ROOT / 'runtime.json', {'python': os.path.relpath(python, ROOT), 'profile': args.profile, 'models': selected_models})
    atomic_json(ROOT / 'setup-result.json', {'profile': args.profile})
    bar.emit(100)
    log('Embodiment runtime verified.')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['cpu', 'gpu'])
    parser.add_argument('--models-dir')
    parser.add_argument('--voice-device', choices=['cpu', 'auto'])
    parser.add_argument('--transcription-device', choices=['cpu', 'auto'])
    parser.add_argument('--transcription-models', choices=['yes', 'no'], default='yes',
                        help='Download Whisper speech recognition models (about 0.55 GB)')
    parser.add_argument('--voice-models', choices=['yes', 'no'], default='yes',
                        help='Download the four Piper avatar voices (about 0.27 GB)')
    parser.add_argument('--plan', action='store_true', help='Only metadata and space checks')
    parser.add_argument('--yes', action='store_true', help='Accept the displayed plan without interactive prompts')
    try:
        main(parser.parse_args())
    except KeyboardInterrupt:
        print('\nInterrupted. Partial downloads are retained and can be resumed.')
        sys.exit(130)
    except Exception as exc:
        print(f'\nERROR: {exc}\nRun the installer again to retry. Previous runtimes are retained.')
        if SETUP.exists():
            log(str(exc))
        sys.exit(1)
