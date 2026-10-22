"""Build a local preview installer. No GitHub, publishing or cloud credentials."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import tempfile
import zipfile

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'build/common'))
from files import application_files
from build_icons import build as build_icons

APP = ROOT / 'app'
FILES = application_files('win')


def run(arguments, **kwargs):
    subprocess.run(list(map(str, arguments)), cwd=ROOT, check=True, **kwargs)


def build(output):
    with tempfile.TemporaryDirectory(prefix='virtual-human-win-build-') as temporary:
        build_package(output, Path(temporary))


def build_package(output, work):
    build_icons()
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    print('[1/5] Controlli Python, download, dispositivi e contratto API', flush=True)
    for source, name in FILES:
        if name.endswith('.py'):
            compile(source.read_text(encoding='utf-8'), str(source), 'exec')
    run([sys.executable, ROOT / 'tests/test_course_environment.py'])
    for pattern in ('test_setup_downloads.py', 'test_*device.py', 'test_model_docs.py', 'test_installer_models.py'):
        run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', pattern])
    if shutil.which('node'):
        for name in ('app.js', 'avatar.js', 'chat-window.js', 'assets/api-playground.js', 'assets/control-panels.js'):
            run(['node', '--input-type=module', '--check'], input=(APP / name).read_bytes())
    for test in ('test_reply_api.py', 'test_transcribe_preview.py', 'test_early_transcript.py'):
        run([sys.executable, ROOT / 'tests' / test])
    if shutil.which('node'):
        run(['node', ROOT / 'tests/test_playground.mjs'])
        run(['node', ROOT / 'tests/test_receive.mjs'])
    compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    if not compiler.is_file():
        raise RuntimeError('Compilatore .NET Framework Windows non disponibile.')
    shared = ROOT / 'build/win/src/DesktopHost.cs'
    flags = ['/win32icon:' + str(APP / 'assets/branding/vh-icon.ico'), '/nologo', '/target:winexe', '/optimize+', '/r:System.Windows.Forms.dll',
             '/r:System.Drawing.dll', '/r:System.Web.Extensions.dll', '/r:System.IO.Compression.dll',
             '/r:System.IO.Compression.FileSystem.dll']
    print('[2/5] Compilazione launcher Windows', flush=True)
    launcher = work / 'VirtualHuman.exe'
    run([compiler, *flags, '/platform:x64', '/out:' + str(launcher), shared, ROOT / 'build/win/src/Launcher.cs'])
    print('[3/5] Pacchetto applicazione (senza configurazioni personali, chiavi, modelli o ambienti)', flush=True)
    bundle = work / 'app.zip'
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for source, name in FILES:
            archive.write(source, name)
        archive.write(launcher, 'VirtualHuman.exe')
        archive.writestr('build-info.json', json.dumps({'version': '0.1-preview', 'built_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}))
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None
        forbidden = {'settings.json', 'runtime.json', 'llm_provider_api_key.yaml', '.env'}
        assert not any(Path(name).name in forbidden for name in archive.namelist())
    print('[4/5] Compilazione installer unico con pacchetto incorporato', flush=True)
    installer = output / 'VirtualHuman-Setup.exe'
    # AnyCPU lets a 32-bit OS show the compatibility message before extraction.
    run([compiler, *flags, '/platform:anycpu', '/out:' + str(installer), '/resource:' + str(bundle) + ',app.zip', shared, ROOT / 'build/win/src/Setup.cs'])
    print('[5/5] Hash e riepilogo build', flush=True)
    sha = hashlib.file_digest(installer.open('rb'), 'sha256').hexdigest()
    installer.with_suffix('.sha256').write_text(sha + '  ' + installer.name + '\n', encoding='ascii')
    (output / 'build-report.json').write_text(json.dumps({'installer': installer.name, 'bytes': installer.stat().st_size,
        'sha256': sha, 'version': '0.1-preview', 'signed': False, 'python': sys.version.split()[0],
        'checks': ['Python compilation', 'Download resume/integrity/disk space', 'CPU/GPU fallback policy', 'Filtered model API', 'Embedded ZIP integrity', 'No personal settings/keys']}, indent=2), encoding='utf-8')
    print(f'PRONTO: {installer} ({installer.stat().st_size / 1024**2:.1f} MB). Nessuna pubblicazione eseguita.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/win')
    args = parser.parse_args()
    build(args.output)
