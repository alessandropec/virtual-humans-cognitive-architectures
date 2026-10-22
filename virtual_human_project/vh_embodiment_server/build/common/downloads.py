"""Verified, resumable downloads shared by setup and model preparation (stdlib)."""
from functools import lru_cache
import hashlib
from http.client import HTTPException, HTTPSConnection
import socket
import json
import os
from pathlib import Path
import shutil
import time
from urllib.request import Request, urlopen, HTTPSHandler, build_opener
from urllib.error import URLError
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

MARGIN = 256 * 1024**2
progress = {}


class IPv4HTTPSConnection(HTTPSConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Keep normal TLS/hostname verification, but connect using IPv4 DNS.
        self._create_connection = lambda address, *a, **k: socket.create_connection(
            (socket.gethostbyname(address[0]), address[1]), *a, **k)


class IPv4HTTPSHandler(HTTPSHandler):
    def https_open(self, request):
        return self.do_open(IPv4HTTPSConnection, request, context=self._context)


ipv4_opener = build_opener(IPv4HTTPSHandler())


def open_url(request, timeout=45, ipv4=False):
    # Some networks accept IPv6 TCP connections but reset the TLS handshake.
    return (ipv4_opener.open if ipv4 else urlopen)(request, timeout=timeout)


@lru_cache(maxsize=128)
def read_json(url):
    # Reuse metadata within setup; retry brief network interruptions.
    for attempt in range(3):
        try:
            with open_url(Request(url, headers={'User-Agent': 'VirtualHuman-Setup/1'}), ipv4=attempt > 0) as response:
                return json.load(response)
        except (OSError, HTTPException):
            if attempt == 2:
                raise
            time.sleep(1)


def digest(path, git_blob=False):
    hasher = hashlib.sha1() if git_blob else hashlib.sha256()
    if git_blob:
        hasher.update(f'blob {path.stat().st_size}\0'.encode())
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def valid(path, item):
    return path.is_file() and path.stat().st_size == item['size'] and digest(path, item.get('git_blob', False)) == item['hash']


def check_space(path, needed):
    path = Path(path).resolve()
    while not path.exists():
        path = path.parent
    free = shutil.disk_usage(path).free
    if free < needed + MARGIN:
        raise OSError(f'Not enough disk space on {path}: available {free / 1024**3:.1f} GB, '
                      f'required at least {(needed + MARGIN) / 1024**3:.1f} GB. '
                      'Choose another drive or free disk space, then retry.')


def download_url(item, attempt):
    # Two attempts on the course release, then the original pinned source.
    if item.get('primary_url') and attempt < 2:
        return item['primary_url']
    parts = urlsplit(item['url'])
    if not attempt or parts.hostname != 'huggingface.co':
        return item['url']
    query = dict(parse_qsl(parts.query)); query['download'] = 'true'
    return urlunsplit(parts._replace(query=urlencode(query)))


def download(item, target, report=print, attempts=5):
    """Never publish partial/corrupt files. A fixed URL+hash identifies a resume."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if valid(target, item):
        report(f'Already verified: {target.name}')
        return target
    part = target.with_name(target.name + '.part')
    identity = part.with_name(part.name + '.json')
    fingerprint = {key: item[key] for key in ('url', 'hash', 'size')}
    try:
        same = json.loads(identity.read_text()) == fingerprint
    except (OSError, ValueError):
        same = False
    if not same or (part.exists() and part.stat().st_size > item['size']):
        # Only this download's staging file is replaced, never an installed model.
        with part.open('wb'):
            pass
    identity.write_text(json.dumps(fingerprint), encoding='utf-8')
    last_error = None
    for attempt in range(attempts):
        offset = part.stat().st_size if part.exists() else 0
        check_space(target.parent, max(0, item['size'] - offset))
        progress.update(file=target.name, received=offset, total=item['size'], status='downloading')
        source = 'GitHub release' if item.get('primary_url') and attempt < 2 else urlsplit(item['url']).hostname
        report(f'Download source: {source}')
        report(f'Download {target.name}: {offset / 1024**2:.1f}/{item["size"] / 1024**2:.1f} MB')
        try:
            if offset < item['size']:
                headers = {'User-Agent': 'VirtualHuman-Setup/1', 'Accept-Encoding': 'identity'}
                if offset:
                    headers['Range'] = f'bytes={offset}-'
                url = download_url(item, attempt)
                with open_url(Request(url, headers=headers), ipv4=attempt > 0) as response:
                    if response.status == 206:
                        expected = f'bytes {offset}-'
                        if not response.headers.get('Content-Range', '').startswith(expected):
                            raise OSError('The server returned an invalid byte range.')
                    else:
                        offset = 0  # Some hosts ignore Range; restart safely.
                        check_space(target.parent, item['size'])
                    last_report = time.monotonic()
                    with part.open('ab' if offset else 'wb') as output:
                        while chunk := response.read(1024 * 1024):
                            if offset + len(chunk) > item['size']:
                                raise OSError('Download exceeds its expected size.')
                            check_space(target.parent, len(chunk))
                            output.write(chunk)
                            offset += len(chunk)
                            progress.update(received=offset)
                            if time.monotonic() - last_report > 2:
                                report(f'  {target.name}: {100 * offset / item["size"]:.0f}% '
                                       f'({offset / 1024**2:.1f}/{item["size"] / 1024**2:.1f} MB)')
                                last_report = time.monotonic()
            progress.update(status='verifying')
            if not valid(part, item):
                if part.stat().st_size == item['size']:
                    part.unlink()  # Corrupt staging data cannot be resumed.
                raise OSError('Incomplete download or integrity check failed.')
            os.replace(part, target)
            identity.unlink(missing_ok=True)
            progress.update(status='complete', received=item['size'])
            return target
        except (OSError, URLError, HTTPException) as exc:
            last_error = exc
            report(f'Download retry {attempt + 1}/{attempts}: {target.name}. Retrying over IPv4. {exc}' if attempt + 1 < attempts else f'Download failed: {target.name}. {exc}')
            if attempt + 1 < attempts:
                time.sleep(min(2 ** attempt, 8))
    progress.update(status='error', error=str(last_error))
    raise OSError(f'Download incomplete: {target.name}. Run again to resume. {last_error}') from last_error


def hf_files(repo, names):
    metadata = read_json(f'https://huggingface.co/api/models/{repo}?blobs=true')
    entries = {entry['rfilename']: entry for entry in metadata['siblings']}
    result = []
    for name in names:
        entry = entries[name]
        lfs = entry.get('lfs')
        result.append({'name': name, 'url': f'https://huggingface.co/{repo}/resolve/{metadata["sha"]}/{name}',
                       'size': entry['size'], 'hash': lfs['sha256'] if lfs else entry['blobId'],
                       'git_blob': not bool(lfs)})
    return result
