#!/usr/bin/env bash
# === GOBLIN — Subir a GitHub ===
# Sube el proyecto al repositorio de GitHub. Pensado para ejecutarse una vez.
set -e

cd "$(dirname "$0")/.."

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() { echo -e "${GREEN}[GOBLIN]${NC} $1"; }
warn() { echo -e "${YELLOW}[GOBLIN]${NC} $1"; }

REPO="${GOBLIN_REPO:-https://github.com/cajacuenta767-sketch/Goblin.git}"

# --- 1. Inicializar git si hace falta ---
if [ ! -d .git ]; then
  info "Inicializando repositorio git..."
  git init -q
  git add -A
  git commit -q -m "GOBLIN: backend + frontend + SDD"
fi

# --- 2. Rama main ---
git branch -M main

# --- 3. Remoto ---
if git remote | grep -q origin; then
  info "El remoto 'origin' ya existe, actualizándolo a: $REPO"
  git remote set-url origin "$REPO"
else
  info "Añadiendo remoto: $REPO"
  git remote add origin "$REPO"
fi

# --- 4. Push ---
info "Subiendo a GitHub..."
warn "Si te pide usuario/contraseña, usa tu usuario de GitHub y un TOKEN PERSONAL"
warn "(Settings → Developer settings → Personal access tokens → classic → permiso 'repo')."
git push -u origin main

echo ""
info "✅ Subido. Revisa: $REPO"
