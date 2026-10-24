#!/usr/bin/env bash
# === GOBLIN — Dependencias para compilar la app nativa (Tauri) ===
# Instala Rust, Node.js, la CLI de Tauri y las librerías de sistema de GTK/WebKit.
set -e

cd "$(dirname "$0")/.."

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() { echo -e "${GREEN}[GOBLIN]${NC} $1"; }
warn() { echo -e "${YELLOW}[GOBLIN]${NC} $1"; }

info "Comprobando dependencias de sistema para Tauri (GTK/WebKit)..."
if pkg-config --exists webkit2gtk-4.1 gtk+-3.0 openssl ayatana-appindicator3-0.1 librsvg-2.0 dbus-1 2>/dev/null; then
  info "Dependencias de sistema ya instaladas."
elif command -v apt >/dev/null 2>&1; then
  sudo apt update -qq
  sudo apt install -y -t echo-backports \
    build-essential curl wget file \
    libwebkit2gtk-4.1-dev \
    libgtk-3-dev \
    libssl-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev \
    libdbus-1-dev \
    pkg-config 2>/dev/null || \
  sudo apt install -y \
    build-essential curl wget file \
    libwebkit2gtk-4.1-dev \
    libgtk-3-dev \
    libssl-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev \
    libdbus-1-dev \
    pkg-config
else
  warn "No se encontró apt. Instala manualmente las libs de GTK/WebKit de Tauri."
fi

# --- Rust ---
if ! command -v cargo >/dev/null 2>&1; then
  info "Instalando Rust (rustup)..."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  # shellcheck disable=SC1091
  source "$HOME/.cargo/env"
else
  info "Rust ya está instalado."
fi

# --- Node.js (para la CLI de Tauri) ---
if ! command -v node >/dev/null 2>&1; then
  info "Instalando Node.js..."
  sudo apt install -y nodejs npm || warn "Instala Node.js manualmente si falla."
else
  info "Node.js ya está instalado."
fi

# --- CLI de Tauri ---
if ! cargo tauri --version >/dev/null 2>&1; then
  info "Instalando la CLI de Tauri (cargo-tauri)..."
  cargo install tauri-cli --version "^2.0" --locked || warn "No se pudo instalar tauri-cli."
else
  info "La CLI de Tauri ya está instalada."
fi

echo ""
info "✅ Dependencias de la app nativa instaladas."
info "Ahora puedes compilar la app con: ./scripts/build.sh"
