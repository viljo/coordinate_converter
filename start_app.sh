#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PYTHON:-python3}"
UV_BIN="${UV:-uv}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: Python executable '$PYTHON_BIN' not found. Set PYTHON env variable." >&2
  exit 1
fi

if ! command -v "$UV_BIN" >/dev/null 2>&1; then
  cat >&2 <<'MSG'
Error: The 'uv' package manager is required but was not found on PATH.
Install it from https://docs.astral.sh/uv/getting-started/ and re-run this script.
MSG
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
PYTHON_IN_VENV="${VENV_DIR}/bin/python"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment in $VENV_DIR using uv"
  "$UV_BIN" venv --python "$PYTHON_BIN" "$VENV_DIR"
fi

if [[ ! -x "$PYTHON_IN_VENV" ]]; then
  echo "Error: expected Python executable at $PYTHON_IN_VENV after uv venv" >&2
  exit 1
fi

echo "Installing project dependencies with uv pip..."
"$UV_BIN" pip install --python "$PYTHON_IN_VENV" -e '.[dev]'

# Ensure pip is available inside the environment for Flet's runtime helpers.
if ! "$PYTHON_IN_VENV" -m pip --version >/dev/null 2>&1; then
  echo "Bootstrapping pip in the virtual environment via ensurepip..."
  "$PYTHON_IN_VENV" -m ensurepip --upgrade
fi

if ! "$PYTHON_IN_VENV" -m pip --version >/dev/null 2>&1; then
  echo "Error: pip is still unavailable in the virtual environment after ensurepip." >&2
  exit 1
fi

echo "Starting the Flet coordinate converter app..."
exec "$PYTHON_IN_VENV" -m app.main "$@"
