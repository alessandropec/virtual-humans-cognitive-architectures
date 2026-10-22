@echo off
set PYTHONDONTWRITEBYTECODE=1
set VH_DEV_CONSOLES=1
title VH Embodiment Server
cd /d "%~dp0"
if exist "%~dp0VirtualHuman.exe" (
  start "" "%~dp0VirtualHuman.exe"
  exit /b
)
set "VH_PYTHON=%~dp0..\..\.venv-vh-course\Scripts\python.exe"
set "VH_CONFIG=%~dp0runtime.json"
if exist "%VH_CONFIG%" for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "(Get-Content -LiteralPath $env:VH_CONFIG -Raw ^| ConvertFrom-Json).python"`) do set "VH_PYTHON=%~dp0%%P"
if not exist "%VH_PYTHON%" (
  set "VH_SOURCE_SETTINGS=%~dp0..\..\installation\settings.json"
  if exist "%~dp0..\..\installation\settings.json" for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "(Get-Content -LiteralPath $env:VH_SOURCE_SETTINGS -Raw ^| ConvertFrom-Json).agent_python"`) do set "VH_PYTHON=%%P"
)
if not exist "%VH_PYTHON%" (
  echo The course Python 3.12 environment is missing. Run the installer or prepare the course environment.
  pause
  exit /b 1
)
"%VH_PYTHON%" -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)"
if errorlevel 1 (
  echo The course environment requires Python 3.12.
  pause
  exit /b 1
)
"%VH_PYTHON%" server.py
set "VH_EXIT_CODE=%errorlevel%"
if not "%VH_EXIT_CODE%"=="0" (
  echo Launch failed. If the port is in use, close the existing server.
  pause
)
exit /b %VH_EXIT_CODE%
