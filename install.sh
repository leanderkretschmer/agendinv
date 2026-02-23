#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"
ACTIVATE_FILE="${VENV_DIR}/bin/activate"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "[ERROR] ${PYTHON_BIN} wurde nicht gefunden. Bitte Python 3 installieren."
  exit 1
fi

echo "[INFO] Projektpfad: ${PROJECT_DIR}"
cd "${PROJECT_DIR}"

create_venv() {
  echo "[INFO] Erstelle virtuelle Umgebung in ${VENV_DIR}"
  if ! "${PYTHON_BIN}" -m venv "${VENV_DIR}"; then
    echo "[ERROR] Konnte keine virtuelle Umgebung erstellen."
    echo "[HINWEIS] Unter Debian/Ubuntu fehlt oft das Paket python3-venv: apt install python3-venv"
    exit 1
  fi
}

if [ -e "${VENV_DIR}" ] && [ ! -d "${VENV_DIR}" ]; then
  echo "[WARN] ${VENV_DIR} existiert, ist aber kein Verzeichnis. Entferne es."
  rm -f "${VENV_DIR}"
fi

if [ ! -d "${VENV_DIR}" ]; then
  create_venv
fi

if [ ! -f "${ACTIVATE_FILE}" ]; then
  echo "[WARN] ${ACTIVATE_FILE} fehlt. Erstelle virtuelle Umgebung neu."
  rm -rf "${VENV_DIR}"
  create_venv
fi

# shellcheck disable=SC1091
source "${ACTIVATE_FILE}"

echo "[INFO] Aktualisiere pip"
python -m pip install --upgrade pip

echo "[INFO] Installiere Abhängigkeiten"
pip install -r requirements.txt

echo "[INFO] Starte AgendaInv auf http://${HOST}:${PORT}"
exec uvicorn app.main:app --host "${HOST}" --port "${PORT}"
