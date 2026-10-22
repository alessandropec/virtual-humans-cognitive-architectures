"""Heartbeat polling and one local process owned by this application."""
import asyncio
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse, urlunparse

import httpx
from fastapi import HTTPException


class CognitiveConnection:
    def __init__(self, settings):
        self.settings = settings
        self.process = None
        self.log_window = None
        self.connected = False
        self.message = 'Waiting for heartbeat.'
        self.attempted = None
        self.lock = asyncio.Lock()

    def status(self):
        enabled = self.settings().agent_enabled
        return dict(enabled=enabled, connected=enabled and self.connected,
                    running=self.process is not None and self.process.poll() is None,
                    message=self.message if enabled else 'Agent connection disabled.')

    async def check(self):
        settings = self.settings()
        if not settings.agent_enabled:
            self.connected = False
            return False
        try:
            async with httpx.AsyncClient(timeout=2, trust_env=False) as http:
                response = await http.get(settings.agent_heartbeat_url)
                response.raise_for_status()
            data = response.json()
            self.connected = data.get('status') == 'ok' and data.get('service') == 'VH Cognitive Architecture Server'
            self.message = 'Connected.' if self.connected else 'Unexpected heartbeat response.'
        except (httpx.HTTPError, ValueError, AttributeError):
            self.connected = False
            self.message = 'Not connected. Check the Cognitive Architecture Server settings and port.'
        return self.connected

    async def start(self):
        async with self.lock:
            settings = self.settings()
            if not settings.agent_enabled:
                raise HTTPException(409, 'Enable the agent connection first.')
            if self.process is not None and self.process.poll() is None:
                return
            if await self.check():
                self.message = 'Already connected to an independently started server.'
                return
            if any(urlparse(url).hostname not in ('localhost', '127.0.0.1', '::1')
                   for url in (settings.agent_url, settings.agent_heartbeat_url)):
                raise HTTPException(409, 'Local launch requires local API and heartbeat URLs.')
            target = urlparse(settings.agent_heartbeat_url)
            try:
                _, writer = await asyncio.wait_for(asyncio.open_connection(target.hostname, target.port or (443 if target.scheme == 'https' else 80)), timeout=1)
            except (OSError, asyncio.TimeoutError):
                pass
            else:
                writer.close()
                await writer.wait_closed()
                raise HTTPException(409, 'Heartbeat port already occupied by another service. Check the URLs or stop that service first.')
            script = Path(settings.agent_script).expanduser()
            if not script.is_absolute() or not script.is_file() or script.suffix.lower() != '.py':
                raise HTTPException(400, 'Choose an existing Python server file using its full path.')
            python = Path(settings.agent_python).expanduser()
            if not python.is_absolute() or not python.is_file():
                raise HTTPException(400, 'Select the course .venv-vh-course Python executable in Cognitive Architecture Server settings. See the cognitive server README.')
            try:
                # No shell, no port-based process killing. Logs remain beside the script.
                with (script.parent / 'cognitive-server.log').open('a', encoding='utf-8') as log:
                    self.process = subprocess.Popen([str(python), '-u', str(script)], cwd=script.parent,
                                                    stdout=log, stderr=log, stdin=subprocess.PIPE,
                                                    env={**os.environ, 'VH_AGENT_MANAGED': '1', 'VH_AGENT_PORT': str(target.port or 8000)},
                                                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                if sys.platform == 'win32' and os.environ.get('VH_DEV_CONSOLES') == '1':
                    if self.log_window is None or self.log_window.poll() is not None:
                        log_path = str(script.parent / 'cognitive-server.log').replace("'", "''")
                        self.log_window = subprocess.Popen(['powershell.exe', '-NoProfile', '-Command',
                            "$Host.UI.RawUI.WindowTitle='Cognitive Architecture Server'; $seen=0; while(Get-Process -Id "+str(os.getpid())+" -ErrorAction SilentlyContinue){ $lines=@(Get-Content -LiteralPath '"+log_path+"'); if($lines.Count -lt $seen){$seen=0}; $lines | Select-Object -Skip $seen | ForEach-Object {Write-Host $_}; $seen=$lines.Count; Start-Sleep -Milliseconds 500 }"],
                            creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.message = 'Starting Cognitive Architecture Server; waiting for heartbeat.'
            except OSError as error:
                raise HTTPException(400, f'Cannot start Cognitive Architecture Server: {error}') from error

    async def shutdown_local(self):
        target = urlparse(self.settings().agent_heartbeat_url)
        if target.hostname not in ('localhost', '127.0.0.1', '::1') or not await self.check():
            return
        url = urlunparse(target._replace(path='/shutdown', query='', fragment=''))
        try:
            async with httpx.AsyncClient(timeout=3, trust_env=False) as http:
                reply = await http.post(url, headers={'X-Virtual-Human': 'shutdown'})
                reply.raise_for_status()
            for _ in range(20):
                if not await self.check():
                    return
                await asyncio.sleep(0.1)
        except httpx.HTTPError as error:
            print(f'Cognitive server could not shut down gracefully: {error}', flush=True)

    async def stop(self):
        async with self.lock:
            await self.shutdown_local()
            # Forced termination is limited to the exact child launched here.
            self.attempted = (self.settings().agent_script, self.settings().agent_heartbeat_url, self.settings().agent_python)
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()
                try:
                    await asyncio.to_thread(self.process.wait, timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    await asyncio.to_thread(self.process.wait)
            self.process = None
            if self.log_window is not None and self.log_window.poll() is None:
                self.log_window.terminate()
                try:
                    await asyncio.to_thread(self.log_window.wait, timeout=3)
                except subprocess.TimeoutExpired:
                    self.log_window.kill()
                    await asyncio.to_thread(self.log_window.wait)
            self.log_window = None
            await self.check()
            if self.connected:
                self.message = 'External server connected. Stop it in its own terminal.'
            else:
                self.message = 'Cognitive Architecture Server stopped.'

    async def monitor(self):
        previous = None
        while True:
            settings = self.settings()
            key = (settings.agent_script, settings.agent_heartbeat_url, settings.agent_python)
            if not settings.agent_enabled:
                self.connected = False
                self.attempted = None
            elif not await self.check() and settings.agent_autostart and settings.agent_script and self.attempted != key:
                self.attempted = key
                try:
                    await self.start()
                except HTTPException as error:
                    self.message = str(error.detail)
            if self.process is not None and self.process.poll() is not None:
                self.message = 'Agent process exited. Check cognitive-server.log (dependencies or port already in use).'
            if self.connected != previous:
                print('Cognitive Architecture Server: ' + ('connected.' if self.connected else 'disconnected.'), flush=True)
                previous = self.connected
            await asyncio.sleep(3)
