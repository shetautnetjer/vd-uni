#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON=${PYTHON:-python3}
"$PYTHON" -m venv "$DIR/.venv"
"$DIR/.venv/bin/python" -m pip install -r "$DIR/requirements.txt"
echo 'Python dependencies installed in the project .venv; no system packages changed.'
"$DIR/scripts/vd" doctor || {
  echo 'Install missing FFmpeg/ffprobe with your OS package manager. VLC is optional.'
  exit 1
}
