@echo off
setlocal
REM ============================================================
REM  DocGuard AI - Backend launcher (works on any developer machine)
REM
REM  Behavior:
REM    1. Uses a local virtual environment (venv) if one exists.
REM    2. Otherwise uses the first available 'python' on PATH.
REM    3. If required packages are missing, offers to install them.
REM ============================================================

cd /d "%~dp0"

REM ---- 1. Find a Python interpreter -----------------------------------
set "PYTHON="

REM Prefer a local virtual environment
if exist "venv\Scripts\python.exe" set "PYTHON=venv\Scripts\python.exe"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"

REM Otherwise use whatever 'python' is on PATH
if not defined PYTHON (
    where python >nul 2>nul
    if not errorlevel 1 (
        if exist "venv\Scripts\python.exe" (set "PYTHON=venv\Scripts\python.exe") else (
            set "PYTHON=python"
        )
    )
)

if not defined PYTHON (
    echo [ERROR] Python was not found.
    echo Install Python 3.9+ from https://python.org and re-run this script.
    echo If using a venv, create it first:  python -m venv venv
    pause
    exit /b 1
)

echo Using Python: %PYTHON%

REM ---- 2. Check for required packages ----------------------------------
"%PYTHON%" -c "import uvicorn, fastapi, cv2" >nul 2>nul
if errorlevel 1 (
    echo.
    echo [INFO] Required packages are not installed in this environment.
    set /p INSTALL="Install them with pip now? (y/n): "
    if /i "%INSTALL%"=="y" (
        echo Installing dependencies...
        "%PYTHON%" -m pip install -r requirements.txt
        if errorlevel 1 (
            echo [ERROR] Package installation failed.
            pause
            exit /b 1
        )
        echo Packages installed.
    ) else (
        echo.
        echo Install them manually:
        echo   "%PYTHON%" -m pip install -r requirements.txt
        pause
        exit /b 1
    )
)

REM ---- 3. Run the server ------------------------------------------------
echo.
echo Starting DocGuard AI backend...
echo Open http://localhost:8000 in your browser.
echo Press CTRL+C to stop.
echo.
"%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
