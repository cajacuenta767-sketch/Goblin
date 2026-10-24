#!/usr/bin/env bash
# === GOBLIN — Instalador para Parrot OS / Debian ===
# Instala Ollama, las dependencias de Python y el modelo DeepHat.
set -e

# Ir a la raíz del proyecto (carpeta padre de scripts/)
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[GOBLIN]${NC} $1"; }
warn()  { echo -e "${YELLOW}[GOBLIN]${NC} $1"; }
err()   { echo -e "${RED}[GOBLIN]${NC} $1"; }

MODEL="${GOBLIN_MODEL:-hf.co/mradermacher/DeepHat-V1-7B-GGUF:Q4_K_M}"

info "Instalando GOBLIN en: $ROOT"

# --- 1. Dependencias del sistema ---
info "Comprobando dependencias del sistema (python3, venv, curl, git)..."
if command -v apt >/dev/null 2>&1; then
  sudo apt update -qq
  sudo apt install -y python3 python3-venv python3-pip curl git
else
  warn "No se encontró apt. Instala manualmente: python3, python3-venv, curl, git."
fi

# --- 2. Ollama ---
if ! command -v ollama >/dev/null 2>&1; then
  info "Instalando Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
else
  info "Ollama ya está instalado."
fi

# --- 3. Entorno virtual + dependencias Python ---
info "Creando entorno virtual de Python..."
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip -q
info "Instalando dependencias de Python..."
pip install -r backend/requirements.txt -q

# --- 4. Archivo de configuración ---
if [ ! -f .env ]; then
  cp .env.example .env
  info "Creado .env desde la plantilla. Revísalo si quieres ajustar algo."
else
  info ".env ya existe, no se toca."
fi

# --- 5. Descargar el modelo ---
info "Arrancando Ollama para descargar el modelo..."
if ! curl -s http://127.0.0.1:11434 >/dev/null 2>&1; then
  (ollama serve >/dev/null 2>&1 &)
  sleep 3
fi
info "Descargando modelo: $MODEL (esto puede tardar, ~4.5 GB)..."
ollama pull "$MODEL" || warn "No se pudo descargar el modelo automáticamente. Hazlo manual: ollama pull $MODEL"

# --- 6. Permisos de ejecución ---
chmod +x scripts/run.sh

echo ""
info "✅ Instalación completada."
info "Para arrancar GOBLIN:  ./scripts/run.sh"
info "Luego abre:            http://127.0.0.1:8800"
