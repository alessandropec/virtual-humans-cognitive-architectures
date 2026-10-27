@echo off
cd /d "%~dp0"
if exist "VirtualHuman-Setup.exe" (
  start "" "%~dp0VirtualHuman-Setup.exe"
  exit /b
)
set "POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%POWERSHELL%" set "POWERSHELL=powershell"
"%POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
if errorlevel 1 pause
