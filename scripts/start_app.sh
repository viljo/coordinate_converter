#!/usr/bin/env bash
set -euo pipefail

# Determine project root relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PYTHON:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: Python executable '$PYTHON_BIN' not found. Set PYTHON env variable." >&2
  exit 1
fi

PY_VERSION="$($PYTHON_BIN -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')"
REQUIRED_MAJOR=3
REQUIRED_MINOR=11
MAJOR="${PY_VERSION%%.*}"
MINOR="${PY_VERSION#*.}"

if [[ "$MAJOR" -lt "$REQUIRED_MAJOR" ]] || { [[ "$MAJOR" -eq "$REQUIRED_MAJOR" ]] && [[ "$MINOR" -lt "$REQUIRED_MINOR" ]]; }; then
  echo "Error: Python $REQUIRED_MAJOR.$REQUIRED_MINOR or newer is required (found $PY_VERSION)." >&2
  exit 1
fi

VENV_DIR="${PROJECT_ROOT}/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment in $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

PYTHON_BIN="$VENV_DIR/bin/python"

echo "Upgrading pip and installing project dependencies..."
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -e '.[dev]'

echo "Starting the Flet coordinate converter app..."
exec "$PYTHON_BIN" -m app.main "$@"
