#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"
ACTIVATE_FILE="${VENV_DIR}/bin/activate"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

log() { echo "[INFO] $*"; }
warn() { echo "[WARN] $*"; }
err() { echo "[ERROR] $*"; }

as_root() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    err "Root-Rechte erforderlich für: $*"
    exit 1
  fi
}

install_system_packages() {
  if command -v apt-get >/dev/null 2>&1; then
    log "Installiere Systempakete via apt-get (python3, python3-venv, python3-pip, git)"
    as_root apt-get update
    as_root apt-get install -y python3 python3-venv python3-pip git
    return
  fi

  if command -v dnf >/dev/null 2>&1; then
    log "Installiere Systempakete via dnf (python3, python3-pip, python3-virtualenv, git)"
    as_root dnf install -y python3 python3-pip python3-virtualenv git
    return
  fi

  if command -v yum >/dev/null 2>&1; then
    log "Installiere Systempakete via yum (python3, python3-pip, git)"
    as_root yum install -y python3 python3-pip git
    return
  fi

  if command -v apk >/dev/null 2>&1; then
    log "Installiere Systempakete via apk (python3, py3-pip, py3-virtualenv, git)"
    as_root apk add --no-cache python3 py3-pip py3-virtualenv git
    return
  fi

  warn "Kein unterstützter Paketmanager gefunden. Bitte manuell installieren: python3 python3-venv python3-pip git"
}

ensure_python_available() {
  if command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    return
  fi

  warn "${PYTHON_BIN} wurde nicht gefunden. Versuche Systempakete zu installieren."
  install_system_packages

  if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    err "${PYTHON_BIN} konnte nicht installiert/gefunden werden."
    exit 1
  fi
}

create_venv() {
  log "Erstelle virtuelle Umgebung in ${VENV_DIR}"
  if ! "${PYTHON_BIN}" -m venv "${VENV_DIR}"; then
    warn "venv-Erstellung fehlgeschlagen. Versuche benötigte Systempakete zu installieren."
    install_system_packages
    rm -rf "${VENV_DIR}"
    "${PYTHON_BIN}" -m venv "${VENV_DIR}" || {
      err "Konnte keine virtuelle Umgebung erstellen."
      err "Bitte sicherstellen, dass python3-venv installiert ist."
      exit 1
    }
  fi
}

log "Projektpfad: ${PROJECT_DIR}"
cd "${PROJECT_DIR}"

ensure_python_available

if [ -e "${VENV_DIR}" ] && [ ! -d "${VENV_DIR}" ]; then
  warn "${VENV_DIR} existiert, ist aber kein Verzeichnis. Entferne es."
  rm -f "${VENV_DIR}"
fi

if [ ! -d "${VENV_DIR}" ]; then
  create_venv
fi

if [ ! -f "${ACTIVATE_FILE}" ]; then
  warn "${ACTIVATE_FILE} fehlt. Erstelle virtuelle Umgebung neu."
  rm -rf "${VENV_DIR}"
  create_venv
fi

# shellcheck disable=SC1091
source "${ACTIVATE_FILE}"

log "Aktualisiere pip"
python -m pip install --upgrade pip

log "Installiere Python-Abhängigkeiten"
pip install -r requirements.txt

log "Starte AgendaInv auf http://${HOST}:${PORT}"
exec uvicorn app.main:app --host "${HOST}" --port "${PORT}"
