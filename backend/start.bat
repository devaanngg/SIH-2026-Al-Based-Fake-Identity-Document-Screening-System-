@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM  DocGuard AI - Backend launcher (works on any developer machine)
REM
REM  Behavior:
REM    1. Finds a Python interpreter (venv first, then PATH).
REM    2. If required packages are missing, offers to install them.
REM    3. Starts the FastAPI backend.
REM ============================================================

cd /d "%~dp0"

REM ---- 1. Find a Python interpreter -----------------------------------
if exist "venv\Scripts\python.exe" (
    set "PYTHON=venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python was not found.
        echo Install Python 3.9+ from https://python.org and re-run this script.
        echo Or create a venv first:  python -m venv venv
        pause
        exit /b 1
    )
    set "PYTHON=python"
)

echo Using Python: %PYTHON%

REM ---- 2. Check for required packages ----------------------------------
"%PYTHON%" -c "import uvicorn, fastapi, cv2" >nul 2>nul
if errorlevel 1 (
    echo.
    echo [INFO] Required packages are not installed in this environment.
    set /p INSTALL="Install them with pip now? (y/n): "
    if /I "!INSTALL!"=="y" (
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
