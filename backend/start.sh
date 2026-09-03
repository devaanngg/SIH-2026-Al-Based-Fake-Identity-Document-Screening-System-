#!/bin/bash
# ============================================================
#  DocGuard AI - Backend launcher for macOS / Linux
#
#  Behavior:
#    1. Finds a Python interpreter (venv first, then PATH).
#    2. If required packages are missing, offers to install them.
#    3. Starts the FastAPI backend.
# ============================================================
set -e

cd "$(dirname "$0")"

# ---- 1. Find a Python interpreter ----
PYTHON=""

if [ -x "venv/bin/python" ]; then
  PYTHON="venv/bin/python"
elif [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
  else
    echo "[ERROR] Python was not found."
    echo "Install Python 3.9+ from https://python.org and re-run this script."
    echo "Or create a venv first:  python3 -m venv venv"
    exit 1
  fi
fi

echo "Using Python: $PYTHON"

# ---- 2. Check for required packages ----
if ! "$PYTHON" -c "import uvicorn, fastapi, cv2" >/dev/null 2>&1; then
  echo
  echo "[INFO] Required packages are not installed in this environment."
  printf "Install them with pip now? (y/n): "
  read -r INSTALL

  if [ "$INSTALL" = "y" ] || [ "$INSTALL" = "Y" ]; then
    echo "Installing dependencies..."
    "$PYTHON" -m pip install -r requirements.txt
    echo "Packages installed."
  else
    echo
    echo "Install them manually:"
    echo "  $PYTHON -m pip install -r requirements.txt"
    exit 1
  fi
fi

# ---- 3. Run the server ----
echo
echo "Starting DocGuard AI backend..."
echo "Open http://localhost:8000 in your browser."
echo "Press CTRL+C to stop."
echo
"$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
