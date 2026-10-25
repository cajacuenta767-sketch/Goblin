#!/usr/bin/env bash
# === GOBLIN — descarga el modelo de Whisper para el dictado por voz (Spec 042) ===
# Requiere faster-whisper instalado en el entorno de GOBLIN:  pip install faster-whisper
# El modelo (por defecto "base", ~140 MB) queda en data/models/ y no se sube a GitHub.
set -euo pipefail

MODELO="${GOBLIN_WHISPER_MODEL:-base}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESTINO="$ROOT/data/models/faster-whisper-$MODELO"

PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

if ! "$PY" -c "import faster_whisper" 2>/dev/null; then
  echo "[GOBLIN] Falta faster-whisper. Instálalo con: pip install faster-whisper"
  exit 1
fi

if [ -f "$DESTINO/model.bin" ]; then
  echo "[GOBLIN] El modelo $MODELO ya está en $DESTINO"
  exit 0
fi

echo "[GOBLIN] Descargando el modelo $MODELO (una sola vez, requiere internet)..."
mkdir -p "$DESTINO"
"$PY" -c "import sys; from faster_whisper.utils import download_model; download_model(sys.argv[1], output_dir=sys.argv[2])" "$MODELO" "$DESTINO"
echo "[GOBLIN] Modelo $MODELO listo en $DESTINO"
