@echo off
cd /d "%~dp0"
if exist "VirtualHuman-Setup.exe" (
  start "" "%~dp0VirtualHuman-Setup.exe"
  exit /b
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
if errorlevel 1 pause
