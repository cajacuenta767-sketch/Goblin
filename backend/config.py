"""
GOBLIN — Configuración central.
Lee variables de entorno (.env) con valores por defecto pensados para el
equipo objetivo: i7-10700, 16 GB RAM, sin GPU. Modelo por defecto: DeepHat-V1-7B.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Raíz del proyecto (carpeta goblin/)
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# --- Servidor ---
HOST = os.getenv("GOBLIN_HOST", "127.0.0.1")
PORT = int(os.getenv("GOBLIN_PORT", "8800"))

# --- Ollama / modelo ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
# Modelo por defecto: DeepHat-V1-7B (ciberseguridad/pentesting, sin censura)
DEFAULT_MODEL = os.getenv("GOBLIN_MODEL", "hf.co/mradermacher/DeepHat-V1-7B-GGUF:Q4_K_M")
NUM_CTX = int(os.getenv("GOBLIN_NUM_CTX", "4096"))      # contexto reducido para ahorrar RAM
KEEP_ALIVE = os.getenv("GOBLIN_KEEP_ALIVE", "10m")      # descarga el modelo tras 10 min inactivo
NUM_THREAD = int(os.getenv("GOBLIN_NUM_THREAD", "8"))    # hilos de CPU (núcleos físicos del i7-10700)
# Modelo pequeño SOLO para saludos cortos (Spec 032). Vacío = desactivado.
FAST_MODEL = os.getenv("GOBLIN_FAST_MODEL", "").strip()

# --- Workspace y acceso ---
WORKSPACE = Path(os.getenv("GOBLIN_WORKSPACE", ROOT / "workspace")).expanduser().resolve()
# FULL_ACCESS=true → la IA puede tocar cualquier ruta del usuario (con aprobaciones).
# FULL_ACCESS=false → solo dentro de workspace/.
FULL_ACCESS = os.getenv("GOBLIN_FULL_ACCESS", "true").lower() == "true"

# --- Agente ---
MAX_STEPS = int(os.getenv("GOBLIN_MAX_STEPS", "15"))    # tope de iteraciones (evita bucles)
SHELL_TIMEOUT = int(os.getenv("GOBLIN_SHELL_TIMEOUT", "180"))  # segundos por comando
# Tope de caracteres de una salida de herramienta que vuelve al modelo (Spec 032).
TOOL_OUTPUT_CHARS = int(os.getenv("GOBLIN_TOOL_OUTPUT_CHARS", "6000"))
# Tope de tokens de respuesta cuando el turno no usa herramientas (charla, preguntas).
CHAT_MAX_TOKENS = int(os.getenv("GOBLIN_CHAT_MAX_TOKENS", "300"))

# --- Router híbrido / Gemini (Spec 008, opcional) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# --- Estado hacia la Polybar (Fase 9) ---
# GOBLIN escribe aquí el target actual; el módulo de Polybar lo lee.
STATE_DIR = Path(os.getenv("GOBLIN_STATE_DIR", "~/.cache/goblin")).expanduser()
TARGET_FILE = STATE_DIR / "target"

# Asegura que las carpetas existan
WORKSPACE.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# --- Lista negra de comandos (bloqueo duro, aunque la IA los proponga) ---
BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    ":(){ :|:& };:",     # fork bomb
    "mkfs",
    "dd if=/dev/zero of=/dev/",
    "dd of=/dev/sd",
    "> /dev/sda",
    "chmod -R 000 /",
    "mv / ",
]
