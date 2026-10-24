#!/usr/bin/env bash
# === GOBLIN — Compilar la app nativa (Tauri) y generar el .deb ===
set -e

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info() { echo -e "${GREEN}[GOBLIN]${NC} $1"; }
warn() { echo -e "${YELLOW}[GOBLIN]${NC} $1"; }
err()  { echo -e "${RED}[GOBLIN]${NC} $1"; }

# Cargar el entorno de Rust si hace falta
[ -f "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"

# --- Comprobaciones ---
if ! command -v cargo >/dev/null 2>&1; then
  err "No se encontró Rust/Cargo. Ejecuta primero: ./scripts/install-nativo.sh"
  exit 1
fi
if ! cargo tauri --version >/dev/null 2>&1; then
  err "No se encontró la CLI de Tauri. Ejecuta: ./scripts/install-nativo.sh"
  exit 1
fi
if [ ! -d .venv ]; then
  warn "No existe el entorno Python (.venv). La app lo necesita en tiempo de ejecución."
  warn "Ejecuta ./scripts/install.sh antes de usar la app."
fi

# --- Aviso importante sobre la ubicación del proyecto ---
ROOT_NAME="$(basename "$ROOT")"
if [ "$ROOT_NAME" != "goblin" ] && [ "$ROOT_NAME" != "Goblin" ]; then
  warn "El proyecto está en '$ROOT'."
  warn "La app nativa busca el backend en: GOBLIN_HOME, la carpeta actual, o ~/goblin."
  warn "Para que la app instalada funcione, el proyecto debe estar en ~/goblin,"
  warn "o exporta GOBLIN_HOME=$ROOT antes de abrir la app."
fi

info "Compilando GOBLIN como app nativa (esto tarda varios minutos la primera vez)..."
cargo tauri build

echo ""
DEB_DIR="src-tauri/target/release/bundle/deb"
if ls "$DEB_DIR"/*.deb >/dev/null 2>&1; then
  info "✅ App compilada. Paquete .deb generado en:"
  ls -1 "$DEB_DIR"/*.deb
  echo ""
  info "Para instalarlo:"
  echo "   sudo dpkg -i $DEB_DIR/*.deb"
  echo "   sudo apt -f install   # si faltan dependencias"
  echo ""
  info "Luego busca 'GOBLIN' en tu menú de aplicaciones."
else
  warn "La compilación terminó pero no se encontró el .deb. Revisa la salida de arriba."
fi
