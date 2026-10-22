@echo off
set PYTHONDONTWRITEBYTECODE=1
cd /d "%~dp0"
set "VH_PYTHON=%~dp0..\.venv-vh-course\Scripts\python.exe"
if not exist "%VH_PYTHON%" (
  echo The course .venv-vh-course is missing. Follow Setup once in README.md.
  pause
  exit /b 1
)
"%VH_PYTHON%" -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)"
if errorlevel 1 (
  echo The course environment requires Python 3.12.
  pause
  exit /b 1
)
"%VH_PYTHON%" vh_cognitive_server.py
if errorlevel 1 pause
