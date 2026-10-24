#!/usr/bin/env bash
# === GOBLIN — Ejecutar la suite de tests ===
set -e
cd "$(dirname "$0")/.."

GREEN='\033[0;32m'; NC='\033[0m'
echo -e "${GREEN}[GOBLIN]${NC} Ejecutando tests..."

# Usar el venv si existe
[ -d .venv ] && source .venv/bin/activate

# Asegurar pytest
python3 -c "import pytest" 2>/dev/null || pip install pytest -q

# Config de prueba
[ -f .env ] || cp .env.example .env

cd backend
python3 -m pytest tests/ -v
