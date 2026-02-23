#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "[ERROR] ${PYTHON_BIN} wurde nicht gefunden. Bitte Python 3 installieren."
  exit 1
fi

echo "[INFO] Projektpfad: ${PROJECT_DIR}"
cd "${PROJECT_DIR}"

if [ ! -d "${VENV_DIR}" ]; then
  echo "[INFO] Erstelle virtuelle Umgebung in ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "[INFO] Aktualisiere pip"
python -m pip install --upgrade pip

echo "[INFO] Installiere Abhängigkeiten"
pip install -r requirements.txt

echo "[INFO] Starte AgendaInv auf http://${HOST}:${PORT}"
exec uvicorn app.main:app --host "${HOST}" --port "${PORT}"
