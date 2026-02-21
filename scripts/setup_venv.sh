#!/usr/bin/env bash
# Create .venv with Python 3.13. Install python3.13 if missing (Ubuntu/Debian).
set -e
cd "$(dirname "$0")/.."
PYTHON_VERSION=3.13

if command -v python${PYTHON_VERSION} &>/dev/null; then
  echo "Python ${PYTHON_VERSION} found: $(command -v python${PYTHON_VERSION})"
else
  echo "Python ${PYTHON_VERSION} not found. Install it with:"
  echo "  sudo apt-get update"
  echo "  sudo apt-get install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv"
  exit 1
fi

if [[ -d .venv ]]; then
  echo "Removing existing .venv..."
  rm -rf .venv
fi

echo "Creating .venv with python${PYTHON_VERSION}..."
python${PYTHON_VERSION} -m venv .venv
source .venv/bin/activate
echo "Installing dependencies (pip)..."
pip install --upgrade pip
if command -v uv &>/dev/null; then
  echo "Syncing with uv..."
  uv sync
else
  echo "Installing with pip (uv not found)..."
  pip install -e .
  pip install pytest 'anyio>=4' httpx fakeredis pytest-env pytest-cov
fi
echo "Done. Activate with: source .venv/bin/activate"
