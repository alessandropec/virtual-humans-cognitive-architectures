#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE=""
VH_SEARCH_DIR="$HERE"
while [ "$VH_SEARCH_DIR" != / ]; do
  if [ -f "$VH_SEARCH_DIR/requirements.txt" ] && [ -f "$VH_SEARCH_DIR/virtual_human_project/vh_cognitive_architecture_server/vh_cognitive_server.py" ]; then
    BASE="$VH_SEARCH_DIR/virtual_human_project/installation"; break
  fi
  VH_SEARCH_DIR="$(dirname "$VH_SEARCH_DIR")"
done
if [ -z "$BASE" ]; then
  echo 'Open this installer from inside the cloned course repository.'; exit 1
fi
finish() {
  code="${1:-$?}"
  if [ "$code" -ne 0 ]; then
    printf '\nInstallation interrupted. Reopen the installer to retry.\n'
    read -r -p 'Press Enter to close.' unused || true
  fi
  return "$code"
}
trap finish EXIT
if [ "$(uname -s)" != Darwin ]; then echo 'macOS is required.'; exit 1; fi
major="$(sw_vers -productVersion | cut -d. -f1)"
if [ "$major" -lt 14 ]; then echo 'This preview requires macOS 14 or later.'; exit 1; fi
ARCH="$(uname -m)"
if [ "$(/usr/sbin/sysctl -n hw.optional.arm64 2>/dev/null || true)" = 1 ]; then ARCH=arm64; fi
case "$ARCH" in
  arm64)
    URL='https://github.com/astral-sh/python-build-standalone/releases/download/20261021/cpython-3.12.15%2B20261021-aarch64-apple-darwin-install_only_stripped.tar.gz'
    SHA='7b8d00b751db21cea87dc551a8f8165147c5fbc5251d5537d7e5497dde00a219';;
  x86_64)
    URL='https://github.com/astral-sh/python-build-standalone/releases/download/20261021/cpython-3.12.15%2B20261021-x86_64-apple-darwin-install_only_stripped.tar.gz'
    SHA='f12e0504397683d6be0745ffd4c39ef45a455cec169adf35c628840d06133773';;
  *) echo "Unsupported architecture: $ARCH"; exit 1;;
esac
printf 'Application and speech models: %s\n' "$BASE"
printf 'Shared course environment: %s/.venv-vh-course\n' "$(dirname "$BASE")"
mkdir -p "$BASE/.setup"
available="$(df -Pk "$BASE" | awk 'END { print $4 }')"
if [ "$available" -lt 2097152 ]; then echo 'At least 2 GB free is required to start. No downloads started.'; exit 1; fi
printf 'VH Embodiment Server for Mac — CPU only\nDestination: %s\nArchitecture: %s\n' "$BASE" "$ARCH"
printf 'Setup will download private Python, dependencies, Whisper Small + Tiny and four voices (English/Italian, female/male).\n'
read -r -p 'Continue? [y/N] ' answer
case "$answer" in y|Y|yes|YES) ;; *) exit 0;; esac
# A dedicated lock also protects the Python bootstrap before Python is available.
LOCK="$BASE/.setup/bootstrap.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  owner="$(cat "$LOCK/pid" 2>/dev/null || true)"
  if [ -z "$owner" ]; then echo 'Bootstrap busy. Wait and retry.'; exit 1; fi
  if [ -n "$owner" ] && kill -0 "$owner" 2>/dev/null; then echo 'Another installer is running.'; exit 1; fi
  rm -f "$LOCK/pid"
  rmdir "$LOCK"
  mkdir "$LOCK"
fi
echo $$ > "$LOCK/pid"
trap 'code=$?; rm -f "$LOCK/pid"; rmdir "$LOCK"; finish "$code"' EXIT
PYTHON="$BASE/.python/bin/python3.12"
if [ ! -x "$PYTHON" ]; then
  ARCHIVE="$BASE/.setup/python-$ARCH.tar.gz.part"
  echo 'Downloading private Python (with SHA-256 verification)…'
  if [ ! -f "$ARCHIVE" ] || [ "$(shasum -a 256 "$ARCHIVE" | awk '{print $1}')" != "$SHA" ]; then
    /usr/bin/curl --fail --location --retry 3 --connect-timeout 30 --speed-time 60 --speed-limit 1024 --continue-at - --output "$ARCHIVE" "$URL"
  fi
  if [ "$(shasum -a 256 "$ARCHIVE" | awk '{print $1}')" != "$SHA" ]; then
    mv "$ARCHIVE" "$ARCHIVE.corrupt"
    echo 'Python verification failed. Reopen the installer to download again.'; exit 1
  fi
  STAGE="$(mktemp -d "$BASE/.setup/python-stage.XXXXXX")"
  /usr/bin/tar -xzf "$ARCHIVE" -C "$STAGE"
  mv "$STAGE/python" "$BASE/.python"
  rmdir "$STAGE"
fi
"$PYTHON" -c 'import sys,platform; assert sys.version_info[:2]==(3,12); print("Python ready:",platform.machine())'
# Do not replace application files while an installed server is using them.
"$PYTHON" - "$HERE/payload.zip" "$BASE" <<'PY'
import fcntl,pathlib,sys,zipfile
root=pathlib.Path(sys.argv[2]).resolve()
with (root/'.server.lock').open('a+b') as lock:
    try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError: raise SystemExit('Close VH Embodiment Server before installing or updating.')
    with zipfile.ZipFile(sys.argv[1]) as archive:
        for entry in archive.infolist():
            target=(root/entry.filename).resolve()
            if not target.is_relative_to(root): raise SystemExit('Invalid archive path.')
            target.parent.mkdir(parents=True,exist_ok=True)
            temporary=target.with_name(target.name+'.setup-new')
            temporary.write_bytes(archive.read(entry))
            temporary.replace(target)
PY
cd "$BASE"
if [ -f /etc/ssl/cert.pem ]; then export SSL_CERT_FILE=/etc/ssl/cert.pem; fi
"$PYTHON" -u mac_install.py
