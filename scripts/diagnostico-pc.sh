#!/usr/bin/env bash
# === GOBLIN — Diagnóstico del equipo y velocidad del modelo local (Spec 046) ===
# Solo lee datos del sistema y consulta Ollama en local. Lo único que escribe es
# workspace/diagnostico-pc.txt. No instala nada, no cambia configuración y no usa sudo.
# Uso: bash scripts/diagnostico-pc.sh [modelo]

cd "$(dirname "$0")/.." || exit 1
ROOT="$(pwd)"
SALIDA="$ROOT/workspace/diagnostico-pc.txt"
MODELO="${1:-${GOBLIN_MODEL:-hf.co/mradermacher/DeepHat-V1-7B-GGUF:Q4_K_M}}"
OLLAMA_URL="${OLLAMA_HOST:-http://127.0.0.1:11434}"
CTX="${GOBLIN_NUM_CTX:-4096}"
HILOS="${BENCH_HILOS:-4 8 16}"

ollama_responde() {
  command -v curl >/dev/null 2>&1 && curl -s -m 3 "$OLLAMA_URL/api/version" >/dev/null 2>&1
}

seccion() { printf '\n=== %s\n' "$1"; }

bench() {
  seccion "Velocidad de $MODELO (num_ctx=$CTX)"
  if ! ollama_responde; then
    echo "Omitido: Ollama no responde en $OLLAMA_URL. Ábrelo y vuelve a ejecutar."
    return 0
  fi
  echo "Cada prueba carga el modelo y genera 96 tokens. Tarda unos minutos."
  for h in $HILOS; do
    python3 - "$OLLAMA_URL" "$MODELO" "$h" "$CTX" <<'PY'
import json, sys, urllib.request

url, modelo, hilos, ctx = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
pedido = {
    "model": modelo,
    "prompt": "Explica en español, en tres frases, qué es un escaneo de puertos y para qué sirve.",
    "stream": False,
    "options": {"num_ctx": ctx, "num_thread": hilos, "num_predict": 96},
}
req = urllib.request.Request(url + "/api/generate", data=json.dumps(pedido).encode(),
                             headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
except Exception as e:
    print(f"hilos={hilos}: error ({e})")
    sys.exit(0)
if "error" in d:
    print(f"hilos={hilos}: {d['error']}")
    sys.exit(0)
n, ns = d.get("eval_count", 0), d.get("eval_duration", 0) or 1
carga = d.get("load_duration", 0) / 1e9
print(f"hilos={hilos}: {n / (ns / 1e9):.2f} tokens/s · {n} tokens · carga {carga:.1f} s")
PY
  done
  if command -v ollama >/dev/null 2>&1; then
    seccion "Memoria que ocupa el modelo cargado (ollama ps)"
    ollama ps 2>&1 | head -n 5
  fi
}

informe() {
  echo "Diagnóstico de GOBLIN — $(date '+%Y-%m-%d %H:%M')"
  echo "Carpeta: $ROOT"

  seccion "Procesador"
  lscpu 2>/dev/null | grep -E '^(Model name|CPU\(s\)|Thread\(s\) per core|Core\(s\) per socket|Socket\(s\)|CPU max MHz):' \
    || echo "lscpu no disponible"

  seccion "Memoria"
  free -h 2>/dev/null || grep -E 'MemTotal|MemAvailable|SwapTotal' /proc/meminfo

  seccion "Disco (carpeta del proyecto)"
  df -h "$ROOT" | tail -n 1

  seccion "Gráficos"
  lspci 2>/dev/null | grep -iE 'vga|3d|display' || echo "lspci no disponible"

  seccion "Ollama"
  if command -v ollama >/dev/null 2>&1; then
    ollama --version 2>&1 | head -n 1
    ollama list 2>&1 | head -n 15
  else
    echo "Ollama no está instalado"
  fi
  if ollama_responde; then
    echo "API local: responde en $OLLAMA_URL"
  else
    echo "API local: no responde en $OLLAMA_URL"
  fi

  seccion "Python y librerías"
  python3 --version 2>&1
  version_genai="$(python3 -m pip show google-genai 2>/dev/null | sed -n '2p')"
  echo "${version_genai:-google-genai: no instalado en este Python}"

  seccion "Configuración de GOBLIN (sin claves)"
  if [ -f .env ]; then
    grep -E '^(GOBLIN_|OLLAMA_|GEMINI_MODEL)' .env || echo "(.env sin variables de rendimiento: se usan los valores por defecto)"
  else
    echo "No hay .env: se usan los valores por defecto"
  fi

  bench
}

mkdir -p "$ROOT/workspace"
informe | tee "$SALIDA"
echo
echo "Informe guardado en: $SALIDA"
