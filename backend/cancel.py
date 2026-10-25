"""
Cancelación de la IA por sesión (Spec 024).

El botón Detener marca la sesión como cancelada y mata los procesos de shell que
GOBLIN tenga en curso (con todo su grupo de procesos). El bucle del agente comprueba
la marca en cada paso y se detiene sin ejecutar nada más.

Uso típico:
  - agent.user_message() llama a clear(sid) y set_session(sid) al empezar.
  - tools/shell.py llama a register(proc) / unregister(proc) alrededor de cada comando.
  - main.py /api/stop llama a request(sid).
"""
import os
import re
import signal
import subprocess
import threading

try:
    import psutil
except ImportError:  # psutil está en requirements.txt; sin él solo se pierde la limpieza de la terminal
    psutil = None

# Variable que term_session exporta mientras la IA ejecuta un comando en la terminal viva.
TERM_TAG_VAR = "GOBLIN_TERM_TAG"

_lock = threading.Lock()
_cancelled: set[str] = set()                    # sesiones con Detener pedido
_procs: set[subprocess.Popen] = set()           # procesos de shell en curso
_killed: set[subprocess.Popen] = set()          # procesos que matamos por Detener
_current: str | None = None                     # sesión que está ejecutando herramientas


def set_session(sid: str | None) -> None:
    """Indica qué sesión está ejecutando herramientas (una a la vez)."""
    global _current
    _current = sid


def clear(sid: str) -> None:
    """Quita la marca de cancelación al empezar un turno nuevo."""
    with _lock:
        _cancelled.discard(sid)


def is_cancelled(sid: str | None) -> bool:
    return bool(sid) and sid in _cancelled


def register(proc: subprocess.Popen) -> None:
    with _lock:
        _procs.add(proc)


def unregister(proc: subprocess.Popen) -> None:
    with _lock:
        _procs.discard(proc)


def was_killed(proc: subprocess.Popen) -> bool:
    """True si el proceso fue matado por Detener. Consume la marca."""
    with _lock:
        if proc in _killed:
            _killed.discard(proc)
            return True
        return False


def kill_group(proc: subprocess.Popen) -> None:
    """Mata el shell y todo lo que lanzó (requiere start_new_session=True)."""
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except OSError:
        try:
            proc.kill()
        except OSError:
            pass


def safe_tag(sid: str) -> str:
    """Etiqueta segura para la variable de entorno de la terminal viva (Spec 043 RF1)."""
    return re.sub(r"[^A-Za-z0-9_-]", "", sid or "")[:64] or "main"


def kill_terminal_tree(sid: str) -> int:
    """Mata los procesos que la IA lanzó en la terminal viva de la sesión (Spec 043 RF1).

    term_session exporta GOBLIN_TERM_TAG=<sesión> solo mientras ejecuta un comando de la
    IA, así que cualquier proceso que ese comando deje en marcha lleva la etiqueta en su
    entorno, aunque se haya desdoblado. Se matan esos procesos y sus descendientes. La
    shell del usuario y sus procesos no llevan la etiqueta y no se tocan.
    """
    if not psutil:
        return 0
    tag = safe_tag(sid)
    marcados = []
    for p in psutil.process_iter():
        try:
            if p.environ().get(TERM_TAG_VAR) == tag:
                marcados.append(p)
        except (psutil.Error, OSError):
            continue
    pids: set[int] = set()
    for p in marcados:
        pids.add(p.pid)
        try:
            pids.update(h.pid for h in p.children(recursive=True))
        except psutil.Error:
            pass
    matados = 0
    for pid in pids:
        try:
            psutil.Process(pid).kill()
            matados += 1
        except psutil.Error:
            pass
    return matados


def request(sid: str) -> int:
    """Marca la sesión como cancelada y mata sus procesos de shell y de terminal viva.

    Devuelve cuántos procesos mató. Como GOBLIN atiende una sesión a la vez en el
    shell, se matan todos los procesos registrados de run_shell; los de la terminal
    viva se localizan por su etiqueta de sesión (no se mata la shell del usuario).
    """
    with _lock:
        _cancelled.add(sid)
        procs = list(_procs)
        _killed.update(procs)
    for p in procs:
        kill_group(p)
    return len(procs) + kill_terminal_tree(sid)
