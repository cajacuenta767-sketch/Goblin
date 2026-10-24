"""
Trabajos de instalación y desinstalación del marketplace (Spec 027).

La contraseña de administrador la escribe el usuario en un diálogo de GOBLIN y se entrega a
`sudo -S` por stdin, UNA sola vez. Nunca va en argumentos (no aparece en `ps`), nunca se guarda
en el trabajo, nunca se escribe en el registro y nunca vuelve a la UI.

Los comandos salen SOLO del catálogo (toolstore.py); el paquete ya está validado con regex.
"""
import re
import subprocess
import threading
import time
import uuid
from collections import deque

import toolstore

# RLock: algunas rutas toman el candado y llaman a _set() que también lo toma.
_LOCK = threading.RLock()
_JOBS: dict[str, dict] = {}          # id -> trabajo (SIN contraseña)
_PROCS: dict[str, subprocess.Popen] = {}
_FINISHED = {"ok", "error", "cancelled"}
_ACTIVE = {"checking", "needs_password", "running"}
_MAX_LOG = 400
_MAX_JOBS = 20
_LIST_LIMIT = 5
_TIMEOUT_S = 1800
_KILL_AFTER_S = 8
# Líneas de autenticación de sudo: se ocultan del registro.
_AUTH_LINE = re.compile(
    r"incorrect password|Sorry, try again|no password was provided|a password is required",
    re.IGNORECASE,
)


def _script(job: dict) -> str:
    """Comando que corre como root bajo sudo. El paquete viene del catálogo, ya validado."""
    if job["action"] == "install":
        return (f"export DEBIAN_FRONTEND=noninteractive; "
                f"apt-get update && apt-get install -y {job['pkg']}")
    return f"export DEBIAN_FRONTEND=noninteractive; apt-get remove -y {job['pkg']}"


def _build(job: dict) -> dict:
    """Vista segura para la UI. Requiere el candado tomado. Nunca incluye contraseña."""
    return {
        "id": job["id"], "tool_id": job["tool_id"], "name": job["name"], "action": job["action"],
        "status": job["status"], "message": job["message"], "started": job["started"],
        "log": list(job["log"]),
    }


def _snapshot(job: dict) -> dict:
    with _LOCK:
        return _build(job)


def _log(job: dict, line: str) -> None:
    with _LOCK:
        job["log"].append(line)


def _set(job: dict, status: str, message: str) -> None:
    with _LOCK:
        job["status"] = status
        job["message"] = message
        if status in _FINISHED:
            job["ended"] = time.time()
            _trim()


def _trim() -> None:
    """Conserva solo los últimos trabajos terminados. Requiere el candado tomado."""
    finished = [j for j in _JOBS.values() if j["status"] in _FINISHED]
    excess = len(_JOBS) - _MAX_JOBS
    for j in sorted(finished, key=lambda j: j["started"])[:max(excess, 0)]:
        _JOBS.pop(j["id"], None)


def _sudo_needs_password() -> bool:
    """True si sudo pediría contraseña. `sudo -n` solo comprueba; no ejecuta nada."""
    try:
        r = subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return True
    return r.returncode != 0


def start_job(tool_id: str, action: str) -> dict:
    """Crea un trabajo de instalación o desinstalación y devuelve su estado inicial."""
    tool = toolstore._find(tool_id)
    if not tool:
        return {"ok": False, "error": f"Herramienta desconocida: {tool_id}"}
    if action not in ("install", "remove"):
        return {"ok": False, "error": "Acción no válida."}
    if not tool["pkg"]:
        return {"ok": False, "url": tool["url"],
                "error": f"{tool['name']} no se instala con apt. Descárgala de su web oficial: {tool['url']}"}
    installed = toolstore.is_installed(tool)
    if action == "install" and installed:
        return {"ok": False, "error": f"{tool['name']} ya está instalada."}
    if action == "remove" and not installed:
        return {"ok": False, "error": f"{tool['name']} no está instalada."}

    with _LOCK:
        if any(j["status"] in _ACTIVE for j in _JOBS.values()):
            return {"ok": False, "error": "Ya hay una instalación en curso. Espera a que termine o cancélala."}
        job = {"id": uuid.uuid4().hex[:12], "tool_id": tool_id, "name": tool["name"],
               "pkg": tool["pkg"], "action": action, "status": "checking", "message": "",
               "log": deque(maxlen=_MAX_LOG), "started": time.time(), "ended": None,
               "stop": None, "auth_failed": False}
        _JOBS[job["id"]] = job

    needs_password = _sudo_needs_password()
    with _LOCK:
        if job["status"] == "checking":            # nadie lo canceló mientras comprobábamos
            if needs_password:
                _set(job, "needs_password", "Se necesita tu contraseña de administrador.")
            else:
                job["status"] = "running"
                _spawn(job, None)
        return {"ok": True, "job": _build(job)}


def submit_password(job_id: str, password: str) -> dict:
    """Entrega la contraseña a sudo una sola vez. No se guarda ni se devuelve."""
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            return {"ok": False, "error": "Trabajo no encontrado."}
        if job["status"] != "needs_password":
            return {"ok": False, "error": "Este trabajo no espera contraseña.", "job": _build(job)}
        if not password:
            return {"ok": False, "error": "La contraseña está vacía.", "job": _build(job)}
        job["status"] = "running"
        job["message"] = ""
        _spawn(job, password)
        return {"ok": True, "job": _build(job)}


def cancel_job(job_id: str) -> dict:
    """Cancela el trabajo. Si todavía espera contraseña, termina sin lanzar nada."""
    with _LOCK:
        if job_id not in _JOBS:
            return {"ok": False, "error": "Trabajo no encontrado."}
    _stop(job_id, "cancelled", "Operación cancelada por el usuario.")
    return {"ok": True, "job": _snapshot(_JOBS[job_id])}


def get_job(job_id: str) -> dict | None:
    with _LOCK:
        job = _JOBS.get(job_id)
        return _build(job) if job else None


def list_jobs() -> list[dict]:
    """Los trabajos más recientes, primero el más nuevo."""
    with _LOCK:
        recientes = sorted(_JOBS.values(), key=lambda j: j["started"], reverse=True)
        return [_build(j) for j in recientes[:_LIST_LIMIT]]


def _spawn(job: dict, password: str | None) -> None:
    """Lanza sudo -S con el comando. Requiere el candado tomado (el proceso queda registrado)."""
    argv = ["sudo", "-S", "-p", "", "sh", "-c", _script(job)]
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, encoding="utf-8", errors="replace",
                                bufsize=1, start_new_session=True)
    except OSError as e:
        _set(job, "error", f"No se pudo ejecutar sudo: {e}")
        return
    _PROCS[job["id"]] = proc
    threading.Thread(target=_run, args=(job, proc, password), daemon=True).start()


def _send_password(proc: subprocess.Popen, password: str | None) -> None:
    """Escribe la contraseña a sudo y cierra stdin. Si sudo ya terminó, no pasa nada."""
    try:
        if password is not None:
            proc.stdin.write(password + "\n")
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        pass


def _read_output(job: dict, proc: subprocess.Popen) -> None:
    """Pasa la salida de apt al registro en vivo. Oculta las líneas de autenticación de sudo."""
    for raw in proc.stdout:
        line = raw.rstrip("\r\n")
        if _AUTH_LINE.search(line):
            with _LOCK:
                job["auth_failed"] = True
            continue
        _log(job, line)


def _run(job: dict, proc: subprocess.Popen, password: str | None) -> None:
    timer = threading.Timer(_TIMEOUT_S, _stop, args=(job["id"], "error",
                            "Tiempo agotado: la operación tardó más de 30 minutos."))
    timer.daemon = True
    timer.start()
    reader = threading.Thread(target=_read_output, args=(job, proc), daemon=True)
    reader.start()
    _send_password(proc, password)
    password = None   # no conservar la referencia más tiempo del necesario
    rc = proc.wait()
    reader.join(timeout=3)
    timer.cancel()
    with _LOCK:
        _PROCS.pop(job["id"], None)
        stop = job["stop"]
        auth_failed = job["auth_failed"]
        job["auth_failed"] = False
    if stop:
        _set(job, *stop)
    elif auth_failed and rc != 0:
        _set(job, "needs_password", "Contraseña incorrecta. Inténtalo de nuevo.")
    elif rc == 0:
        _log(job, "— Operación terminada correctamente.")
        _set(job, "ok", "Operación terminada correctamente.")
    else:
        _log(job, f"— apt terminó con código {rc}.")
        _set(job, "error", f"apt terminó con código {rc}.")


def _stop(job_id: str, status: str, message: str) -> None:
    """Detiene un trabajo. Con proceso: SIGTERM a sudo (lo reenvía). Sin proceso: termina aquí."""
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None or job["status"] in _FINISHED:
            return
        proc = _PROCS.get(job_id)
        if proc is None:
            _set(job, status, message)
            return
        job["stop"] = (status, message)
    proc.terminate()
    killer = threading.Timer(_KILL_AFTER_S, _kill_if_alive, args=(proc,))
    killer.daemon = True
    killer.start()


def _kill_if_alive(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.kill()
