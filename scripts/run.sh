#!/usr/bin/env bash
# === GOBLIN — Arranque ===
# Levanta Ollama (si hace falta) y el servidor de GOBLIN.
set -e

cd "$(dirname "$0")/.."

GREEN='\033[0;32m'; NC='\033[0m'
info() { echo -e "${GREEN}[GOBLIN]${NC} $1"; }

# --- Ajustes de Ollama para 16 GB RAM / CPU (del PLAN.md §8.4) ---
export OLLAMA_NUM_PARALLEL=1        # un solo request a la vez
export OLLAMA_MAX_LOADED_MODELS=1   # no mantener 2 modelos en RAM
export OLLAMA_NUM_THREADS="${OLLAMA_NUM_THREADS:-8}"  # los 8 núcleos físicos
export OLLAMA_FLASH_ATTENTION="${OLLAMA_FLASH_ATTENTION:-1}"  # atención más rápida, misma calidad (Spec 032)

# --- Entorno virtual ---
if [ ! -d .venv ]; then
  echo "No existe .venv. Ejecuta primero: ./scripts/install.sh"
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# --- Ollama ---
if ! curl -s http://127.0.0.1:11434 >/dev/null 2>&1; then
  info "Iniciando Ollama en segundo plano..."
  (ollama serve >/dev/null 2>&1 &)
  sleep 3
fi

# --- Puerto (lee .env si existe) ---
PORT="$(grep -E '^GOBLIN_PORT=' .env 2>/dev/null | cut -d= -f2)"
PORT="${PORT:-8800}"

info "GOBLIN arrancando en http://127.0.0.1:$PORT"
info "Pulsa Ctrl+C para detener."

cd backend
exec uvicorn main:app --host 127.0.0.1 --port "$PORT"
