#!/usr/bin/env bash
# === GOBLIN — Instalador completo para Parrot OS / Debian ===
# Instala: dependencias del sistema, Ollama, el modelo DeepHat, Python + venv,
# y (opcional) las herramientas para compilar la app nativa con Tauri.
set -e

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[GOBLIN]${NC} $1"; }
warn()  { echo -e "${YELLOW}[GOBLIN]${NC} $1"; }
err()   { echo -e "${RED}[GOBLIN]${NC} $1"; }

MODEL="${GOBLIN_MODEL:-hf.co/mradermacher/DeepHat-V1-7B-GGUF:Q4_K_M}"

info "Instalando GOBLIN en: $ROOT"

# --- 1. Dependencias base del sistema ---
info "Instalando dependencias base (python3, venv, curl, git)..."
if command -v python3 >/dev/null 2>&1 && python3 -c 'import venv' >/dev/null 2>&1 && command -v curl >/dev/null 2>&1 && command -v git >/dev/null 2>&1; then
  info "Dependencias del sistema ya instaladas."
elif command -v apt >/dev/null 2>&1; then
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

# --- 4. Configuración ---
if [ ! -f .env ]; then
  cp .env.example .env
  info "Creado .env desde la plantilla."
else
  info ".env ya existe, no se toca."
fi

# --- 5. Modelo DeepHat ---
info "Arrancando Ollama para descargar el modelo..."
if ! curl -s http://127.0.0.1:11434 >/dev/null 2>&1; then
  (ollama serve >/dev/null 2>&1 &)
  sleep 3
fi
info "Descargando modelo: $MODEL (~4.5 GB, puede tardar)..."
ollama pull "$MODEL" || warn "No se pudo descargar el modelo. Hazlo manual: ollama pull $MODEL"

# --- 5b. Monaco (editor) para usarlo sin internet (Spec 043 RF2) ---
bash scripts/fetch-monaco.sh || warn "No se pudo descargar Monaco. Hazlo luego con: ./scripts/fetch-monaco.sh"

# --- 6. (Opcional) Dependencias para la app nativa (Tauri) ---
echo ""
read -r -p "¿Instalar también lo necesario para compilar la APP NATIVA (Tauri)? [s/N] " RESP
if [[ "$RESP" =~ ^[sS]$ ]]; then
  bash scripts/install-nativo.sh
else
  info "Omitido. Podrás usar GOBLIN en el navegador con ./scripts/run.sh"
  info "Si luego quieres la app nativa, ejecuta: ./scripts/install-nativo.sh"
fi

# --- 7. Permisos ---
chmod +x scripts/*.sh

echo ""
info "✅ Instalación base completada."
info "Modo navegador:   ./scripts/run.sh   (abre http://127.0.0.1:8800)"
info "App nativa:       ./scripts/build.sh (genera el .deb) tras instalar Tauri"
