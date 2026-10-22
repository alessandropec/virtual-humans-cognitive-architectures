"""macOS CPU-only installer, invoked by the bundled private Python."""
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
from pathlib import Path
import platform
import plistlib
import subprocess
import sys
import venv

import install as common
from downloads import check_space, download, valid

ROOT = Path(__file__).resolve().parent


def main():
    if sys.platform != 'darwin' or int(platform.mac_ver()[0].split('.')[0]) < 14:
        raise RuntimeError('This preview requires macOS 14 or later.')
    if sys.version_info[:2] != (3, 12) or platform.machine() not in ('arm64', 'x86_64'):
        raise RuntimeError('Unsupported Python version or architecture.')
    common.SETUP.mkdir(exist_ok=True)
    with (common.SETUP / 'install.lock').open('a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another installer is running.')
        # Use the same lock as the launcher, so packages are not changed while in use.
        with (ROOT / '.server.lock').open('a+b') as server_lock:
            try:
                fcntl.flock(server_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('Close VH Embodiment Server before updating.')
            perform_install()
    subprocess.run(['/usr/bin/open', str(Path.home() / 'Applications/Virtual Human.app')], check=True)


def perform_install():
    config_path = ROOT / 'settings.json'
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    selected_models = ['small', 'tiny']
    model = 'small'
    models = (ROOT / config.get('models_dir', 'models')).resolve()
    python = common.course_environment.python_path(ROOT)
    requirements = [line for line in (ROOT / 'requirements.txt').read_text().splitlines()
                    if line and not line.startswith('#')]
    plan_path = common.SETUP / f'plan-mac-{platform.machine()}-{"-".join(selected_models)}.json'
    plan = json.loads(plan_path.read_text()) if plan_path.exists() else {}
    common.log('Checking CPU dependencies and models. No NVIDIA components.')
    if plan.get('requirements') != requirements or plan.get('voices') != list(common.VOICE_SOURCES.values()):
        with ThreadPoolExecutor(max_workers=4) as pool:
            wheels = list(pool.map(common.wheel, requirements))
        plan = {'requirements': requirements, 'wheels': wheels, 'models': common.model_plan(selected_models),
                'voices': list(common.VOICE_SOURCES.values())}
        common.atomic_json(plan_path, plan)
    plan['models'] = common.model_plan(selected_models)
    wheel_bytes = sum(x['size'] for x in plan['wheels'] if not valid(common.WHEELS / x['name'], x))
    model_bytes = sum(x['size'] for x in plan['models'] if not valid(models / x['relative'], x))
    needed = wheel_bytes + model_bytes + 4 * sum(x['size'] for x in plan['wheels']) + 512 * 1024**2
    common.log(f'Remaining downloads: {(wheel_bytes+model_bytes)/1024**3:.2f} GB. '
               f'Estimated space required: {needed/1024**3:.2f} GB plus a safety margin.')
    # Conservative on both destinations, including configurations on external volumes.
    check_space(ROOT, needed)
    check_space(models, model_bytes)
    common.WHEELS.mkdir(exist_ok=True)
    for item in plan['wheels']:
        download(item, common.WHEELS / item['name'], common.log)
    for item in plan['models']:
        download(item, models / item['relative'], common.log)
    common.course_environment.prepare(ROOT, common.run, common.log)
    common.run([python, '-m', 'pip', 'install', '--no-index', '--no-deps', '--disable-pip-version-check',
                *[common.WHEELS / x['name'] for x in plan['wheels']]])
    common.run([python, ROOT / 'verify_install.py', '--profile', 'cpu', '--models', models, '--model', *selected_models])
    config.update(models_dir=str(models), stt_model=model, stt_device='cpu', tts_device='cpu')
    config.setdefault('language', 'en')
    config.setdefault('character', 'julia')
    if config.get('stt_language') not in ('it', 'en'):
        config['stt_language'] = 'en'
    common.course_environment.configure(ROOT, config)
    common.atomic_json(config_path, config)
    common.atomic_json(ROOT / 'runtime.json', {'python': '../.venv-vh-course/bin/python', 'profile': 'cpu', 'platform': 'macos', 'models': selected_models})
    create_launcher()
    common.log('Installation completed and verified. Open VH Embodiment Server in your Applications folder.')


def create_launcher():
    bundle = Path.home() / 'Applications/Virtual Human.app/Contents'
    (bundle / 'MacOS').mkdir(parents=True, exist_ok=True)
    (bundle / 'Resources').mkdir(exist_ok=True)
    import shutil
    shutil.copy2(ROOT / 'assets/branding/vh-icon.icns', bundle / 'Resources/vh-icon.icns')
    # The app opens Terminal so progress/errors and the server lifetime stay visible.
    import shlex
    command = bundle / 'Resources/Start.command'
    command.write_text('#!/bin/bash\ncd ' + shlex.quote(str(ROOT)) + '\nexec ' +
                       shlex.quote(str(ROOT / '../.venv-vh-course/bin/python')) + ' -u mac_launch.py\n')
    command.chmod(0o755)
    executable = bundle / 'MacOS/VirtualHuman'
    executable.write_text('#!/bin/bash\nHERE="$(cd "$(dirname "$0")/../Resources" && pwd)"\nexec /usr/bin/open -a Terminal "$HERE/Start.command"\n')
    executable.chmod(0o755)
    with (bundle / 'Info.plist').open('wb') as output:
        plistlib.dump({'CFBundleExecutable': 'VirtualHuman', 'CFBundleIdentifier': 'local.virtualhuman.app',
                      'CFBundleName': 'VH Embodiment Server', 'CFBundleIconFile': 'vh-icon.icns', 'CFBundlePackageType': 'APPL',
                      'CFBundleShortVersionString': '0.1', 'CFBundleVersion': '1',
                      'LSMinimumSystemVersion': '14.0'}, output)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nInterrupted: reopen the installer to resume downloads.')
        sys.exit(130)
    except Exception as exc:
        print(f'\nINSTALLATION INCOMPLETE: {exc}\nReopen the installer to retry. Verified files are retained.')
        sys.exit(1)
