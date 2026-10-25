"""
Dictado por voz con Whisper local (Spec 042).

El navegador graba el audio y lo envía a POST /api/transcribe (solo desde este equipo).
faster-whisper lo transcribe en CPU con un modelo guardado en data/models/. El audio nunca
sale de la máquina. Si la librería o el modelo faltan, status() dice por qué y la interfaz
oculta el botón 🎤.
"""
from __future__ import annotations

import importlib.util
import os
import tempfile
import threading
from pathlib import Path

import config

MODEL_NAME = os.environ.get("GOBLIN_WHISPER_MODEL", "base")
MODEL_DIR = config.ROOT / "data" / "models"
MAX_SECONDS = 60                      # RF2: grabaciones de más de 60 s se rechazan
MAX_BYTES = 12 * 1024 * 1024          # holgado para 60 s de audio comprimido
THREADS = int(os.environ.get("GOBLIN_WHISPER_THREADS", "4"))

# Tipos de audio que el navegador puede enviar y la extensión que necesita el decodificador.
TIPOS = {
    "audio/webm": ".webm", "audio/ogg": ".ogg", "audio/mp4": ".m4a",
    "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/mpeg": ".mp3",
}


class VoiceError(Exception):
    """Motivo claro para el usuario; se devuelve tal cual en la API."""


_lock = threading.Lock()       # carga del modelo
_uso = threading.Lock()        # una transcripción a la vez (CPU)
_modelo = None
_transcriptor = None           # (ruta) -> (texto, duración_s); lo inyectan las pruebas


def modelo_path() -> Path:
    return MODEL_DIR / f"faster-whisper-{MODEL_NAME}"


def _hay_libreria() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def _hay_modelo() -> bool:
    return (modelo_path() / "model.bin").exists()


def status() -> dict:
    """RF5: si el dictado está listo y, si no, por qué."""
    if _transcriptor is not None:
        return {"available": True, "model": "simulado", "reason": ""}
    if not _hay_libreria():
        return {"available": False, "model": MODEL_NAME,
                "reason": "Falta faster-whisper: pip install faster-whisper"}
    if not _hay_modelo():
        return {"available": False, "model": MODEL_NAME,
                "reason": f"Falta el modelo {MODEL_NAME}: ./scripts/fetch-whisper.sh"}
    return {"available": True, "model": MODEL_NAME, "reason": ""}


def set_transcriber(fn) -> None:
    """Solo para pruebas: sustituye faster-whisper por una función (None lo quita)."""
    global _transcriptor
    _transcriptor = fn


def _cargar():
    global _modelo
    with _lock:
        if _modelo is None:
            from faster_whisper import WhisperModel
            _modelo = WhisperModel(str(modelo_path()), device="cpu",
                                   compute_type="int8", cpu_threads=THREADS)
        return _modelo


def _transcribir_real(ruta: str) -> tuple[str, float]:
    segmentos, info = _cargar().transcribe(ruta, language="es", beam_size=1, vad_filter=True)
    duracion = float(getattr(info, "duration", 0.0) or 0.0)
    if duracion > MAX_SECONDS:      # se comprueba antes de transcribir nada
        raise VoiceError(f"La grabación dura {duracion:.0f} s; el máximo es {MAX_SECONDS} s.")
    texto = " ".join(s.text.strip() for s in segmentos).strip()
    return texto, duracion


def transcribe_bytes(datos: bytes, mime: str) -> str:
    """Transcribe una grabación en memoria. El archivo temporal se borra siempre."""
    tipo = (mime or "").split(";")[0].strip().lower()
    if tipo not in TIPOS:
        raise VoiceError("Formato de audio no admitido (usa webm, ogg, mp4 o wav).")
    if not datos:
        raise VoiceError("La grabación está vacía.")
    if len(datos) > MAX_BYTES:
        raise VoiceError("La grabación es demasiado grande.")
    st = status()
    if not st["available"]:
        raise VoiceError(st["reason"])

    fd, ruta = tempfile.mkstemp(suffix=TIPOS[tipo], prefix="goblin-voz-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(datos)
        with _uso:
            texto, duracion = (_transcriptor or _transcribir_real)(ruta)
        if duracion > MAX_SECONDS:
            raise VoiceError(f"La grabación dura {duracion:.0f} s; el máximo es {MAX_SECONDS} s.")
        return (texto or "").strip()
    finally:
        try:
            os.unlink(ruta)
        except OSError:
            pass
