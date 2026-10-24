"""
Herramienta de shell para GOBLIN.
Ejecuta comandos con timeout y bloqueo duro de comandos peligrosos.
Cada comando corre en su propio grupo de procesos para poder detenerlo entero
con el botón Detener (Spec 024).
(La terminal persistente/pty real vive en terminal.py / term_session.py.)
"""
import subprocess

import config
import cancel
from .filesystem import resolve


def _is_blocked(command: str) -> bool:
    cmd = command.strip()
    return any(bad in cmd for bad in config.BLOCKED_PATTERNS)


def run_shell(command: str, cwd: str = ".") -> str:
    if _is_blocked(command):
        return (f"BLOQUEADO: el comando contiene un patrón peligroso y GOBLIN no lo ejecutará.\n"
                f"Comando: {command}")
    try:
        workdir = resolve(cwd)
    except Exception as e:
        return f"Error con el directorio de trabajo: {e}"

    try:
        proc = subprocess.Popen(
            command, shell=True, cwd=str(workdir),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            start_new_session=True,
        )
    except Exception as e:
        return f"Error ejecutando el comando: {e}"

    cancel.register(proc)
    try:
        try:
            stdout, stderr = proc.communicate(timeout=config.SHELL_TIMEOUT)
        except subprocess.TimeoutExpired:
            cancel.kill_group(proc)
            proc.communicate()
            return f"TIMEOUT: el comando superó {config.SHELL_TIMEOUT}s y fue cancelado."
        if cancel.was_killed(proc):
            return "CANCELADO: el usuario detuvo a GOBLIN y este comando se interrumpió."
    finally:
        cancel.unregister(proc)

    out = (stdout or "") + (stderr or "")
    out = out.strip()
    if len(out) > 20000:
        out = out[:20000] + "\n[... salida truncada ...]"
    return f"[exit {proc.returncode}]\n{out}" if out else f"[exit {proc.returncode}] (sin salida)"
