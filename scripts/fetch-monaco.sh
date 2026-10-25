#!/usr/bin/env bash
# === GOBLIN — descarga Monaco (editor de código) para usarlo SIN internet (Spec 043 RF2) ===
# Solo baja lo necesario de monaco-editor: min/vs (~14 MB) y la licencia MIT.
# Se guarda en frontend/vendor/monaco/ y NO se sube a GitHub (ver .gitignore).
# Ejecútalo una vez con internet; después el editor carga sin conexión.
set -euo pipefail

VERSION="0.52.0"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESTINO="$ROOT/frontend/vendor/monaco"
URL="https://registry.npmjs.org/monaco-editor/-/monaco-editor-${VERSION}.tgz"

if [ -f "$DESTINO/vs/editor/editor.main.js" ]; then
  echo "[GOBLIN] Monaco ${VERSION} ya está en ${DESTINO}"
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "[GOBLIN] Descargando Monaco ${VERSION}..."
curl -fsSL "$URL" -o "$TMP/monaco.tgz"
tar -xzf "$TMP/monaco.tgz" -C "$TMP" package/min/vs package/LICENSE

mkdir -p "$DESTINO"
rm -rf "$DESTINO/vs"
cp -r "$TMP/package/min/vs" "$DESTINO/vs"
cp "$TMP/package/LICENSE" "$DESTINO/LICENSE"

echo "[GOBLIN] Monaco ${VERSION} listo en ${DESTINO}"
