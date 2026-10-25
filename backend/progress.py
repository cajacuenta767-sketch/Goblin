"""
Progreso en vivo por sesión (Spec 037, RF3): qué herramienta corre y desde cuándo.
La interfaz lo consulta con GET /api/chat/status/{sid} mientras GOBLIN responde.
"""
import threading
import time

_lock = threading.Lock()
_current: dict[str, dict] = {}


def start(sid: str, action: str) -> None:
    with _lock:
        _current[sid] = {"action": action, "since": time.time()}


def finish(sid: str) -> None:
    with _lock:
        _current.pop(sid, None)


def status(sid: str) -> dict:
    with _lock:
        cur = _current.get(sid)
    if not cur:
        return {"action": None, "elapsed_s": 0}
    return {"action": cur["action"], "elapsed_s": round(time.time() - cur["since"], 1)}
