"""Cross-package an unsigned CPU-only macOS installer; native smoke tests still required."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import stat
import subprocess
import sys
import zipfile

from packaging.tags import cpython_tags, compatible_tags, mac_platforms
from packaging.utils import parse_wheel_filename
from packaging.requirements import Requirement
ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.path.insert(0, str(ROOT / 'app'))
sys.path.insert(0, str(ROOT / 'build/common'))
from downloads import read_json
from install import model_plan, VOICE_SOURCES
from files import application_files
from build_icons import build as build_icons

def metadata(requirement):
    name, version = requirement.split('==')
    return requirement, read_json(f'https://pypi.org/pypi/{name}/{version}/json')


def wheel_for(data, arch):
    platforms = list(mac_platforms((14, 0), arch))
    tags = {tag: i for i, tag in enumerate([*cpython_tags((3, 12), platforms=platforms),
                                          *compatible_tags((3, 12), 'cp312', platforms)])}
    choices = []
    for entry in data['urls']:
        if not entry['filename'].endswith('.whl') or entry.get('yanked'):
            continue
        supported = parse_wheel_filename(entry['filename'])[3]
        scores = [tags[tag] for tag in supported if tag in tags]
        if scores:
            choices.append((min(scores), entry))
    if not choices:
        raise RuntimeError(f'Wheel mancante per {data["info"]["name"]} / {arch}')
    entry = min(choices, key=lambda x: x[0])[1]
    return {'name': entry['filename'], 'url': entry['url'], 'size': entry['size'], 'hash': entry['digests']['sha256']}


def write(archive, name, data, mode=0o644):
    info = zipfile.ZipInfo(name)
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, data)


def build():
    build_icons()
    out = ROOT / 'dist/mac'
    out.mkdir(exist_ok=True)
    for name in ('build/mac/src/mac_install.py', 'build/mac/src/mac_launch.py', 'build/mac/build.py'):
        compile((ROOT / name).read_text(encoding='utf-8'), str(ROOT / name), 'exec')
    bash = 'C:/Program Files/Git/bin/bash.exe' if Path('C:/Program Files/Git/bin/bash.exe').exists() else shutil.which('bash')
    if not bash:
        raise RuntimeError('Bash necessario per controllare lo script di bootstrap della build Mac.')
    subprocess.run([bash, '-n', str(ROOT / 'build/mac/src/bootstrap.command')], check=True)
    subprocess.run([sys.executable, ROOT / 'tests/test_course_environment.py'], check=True)
    for pattern in ('test_mac_package.py', 'test_*device.py', 'test_model_docs.py', 'test_installer_models.py'):
        subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT / 'tests'), '-p', pattern], check=True)
    requirements = [x for x in (ROOT / 'build/mac/requirements.txt').read_text().splitlines() if x and not x.startswith('#')]
    print('Verifica delle wheel CPU macOS 14 per Apple Silicon e Intel...', flush=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        packages = dict(pool.map(metadata, requirements))
    pinned = {Requirement(x).name.lower().replace('_', '-'): Requirement(x).specifier for x in requirements}
    # Validate platform-specific transitive requirements, not just filenames.
    for arch in ('arm64', 'x86_64'):
        environment = {'sys_platform': 'darwin', 'platform_system': 'Darwin', 'platform_machine': arch,
                       'python_version': '3.12', 'python_full_version': '3.12.15', 'os_name': 'posix', 'extra': ''}
        for data in packages.values():
            for raw in data['info'].get('requires_dist') or []:
                req = Requirement(raw)
                if req.marker and not req.marker.evaluate(environment):
                    continue
                key = req.name.lower().replace('_', '-')
                if key not in pinned:
                    raise RuntimeError('Dipendenza mancante: ' + raw)
                version = next(iter(pinned[key])).version
                if req.specifier and version not in req.specifier:
                    raise RuntimeError('Versione non compatibile: ' + raw)
    models = model_plan(['small', 'tiny'])
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as payload:
        for source, name in application_files('mac'):
            data = source.read_bytes()
            if name == 'index.html':
                text = data.decode('utf-8')
                for select in ('sttDevice', 'ttsDevice'):
                    text = re.sub(r'(<select[^>]*id="' + select + r'"[^>]*>).*?(</select>)',
                                  r'\1<option value="cpu">CPU — Mac</option>\2', text, flags=re.S)
                text = re.sub(r'<p class="note">[^<]*Auto[^<]*</p>',
                              '<p class="note">On Mac this function uses CPU only.</p>', text)
                data = text.encode('utf-8')
            write(payload, name, data)
        for arch in ('arm64', 'x86_64'):
            plan = {'requirements': requirements, 'wheels': [wheel_for(data, arch) for data in packages.values()],
                    'models': models, 'voices': list(VOICE_SOURCES.values())}
            write(payload, f'.setup/plan-mac-{arch}-small-tiny.json', json.dumps(plan).encode())
    installer = out / 'VirtualHuman-Mac-CPU-preview.zip'
    prefix = 'Install Virtual Human.app/Contents/'
    with zipfile.ZipFile(installer, 'w') as archive:
        write(archive, prefix + 'Info.plist', plistlib.dumps({
            'CFBundleExecutable': 'Install', 'CFBundleIdentifier': 'local.virtualhuman.installer',
            'CFBundleName': 'VH Embodiment Server Setup', 'CFBundleIconFile': 'vh-icon.icns', 'CFBundlePackageType': 'APPL',
            'CFBundleShortVersionString': '0.1', 'CFBundleVersion': '1', 'LSMinimumSystemVersion': '14.0'}))
        write(archive, prefix + 'Resources/vh-icon.icns', (ROOT / 'app/assets/branding/vh-icon.icns').read_bytes())
        write(archive, prefix + 'MacOS/Install', b'#!/bin/bash\nHERE="$(cd "$(dirname "$0")/../Resources" && pwd)"\nexec /usr/bin/open -a Terminal "$HERE/Install.command"\n', 0o755)
        write(archive, prefix + 'Resources/Install.command', (ROOT / 'build/mac/src/bootstrap.command').read_bytes(), 0o755)
        write(archive, prefix + 'Resources/payload.zip', buffer.getvalue())
    with zipfile.ZipFile(installer) as archive:
        assert archive.testzip() is None
        for name in (prefix + 'MacOS/Install', prefix + 'Resources/Install.command'):
            assert (archive.getinfo(name).external_attr >> 16) & 0o111 == 0o111
        with zipfile.ZipFile(io.BytesIO(archive.read(prefix + 'Resources/payload.zip'))) as payload:
            assert payload.testzip() is None
            assert not {'settings.json', 'runtime.json', '.env', 'requirements-gpu.txt'} & set(payload.namelist())
            assert b'value="cuda"' not in payload.read('index.html')
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    installer.with_suffix('.sha256').write_text(digest + '  ' + installer.name + '\n')
    (out / 'build-report.json').write_text(json.dumps({'artifact': installer.name, 'sha256': digest,
        'platforms': ['macOS 14+ arm64 CPU', 'macOS 14+ x86_64 CPU'], 'signed': False, 'notarized': False,
        'native_macos_tested': False, 'checks': ['Python and bootstrap shell syntax', 'CPU-only policy tests', 'wheel availability and dependency closure for both architectures', 'ZIP integrity and executable permissions', 'no personal settings or GPU dependencies']}, indent=2))
    print(f'Creato: {installer} ({installer.stat().st_size / 1024**2:.1f} MB). Da verificare su Mac reale.', flush=True)


if __name__ == '__main__':
    build()
