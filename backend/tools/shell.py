"""
Herramienta de shell para GOBLIN.
Ejecuta comandos con timeout y bloqueo duro de comandos peligrosos.
(La terminal persistente/pty real llega en la Fase 3.)
"""
import subprocess

import config
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
        result = subprocess.run(
            command, shell=True, cwd=str(workdir),
            capture_output=True, text=True, timeout=config.SHELL_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return f"TIMEOUT: el comando superó {config.SHELL_TIMEOUT}s y fue cancelado."
    except Exception as e:
        return f"Error ejecutando el comando: {e}"

    out = (result.stdout or "") + (result.stderr or "")
    out = out.strip()
    if len(out) > 20000:
        out = out[:20000] + "\n[... salida truncada ...]"
    return f"[exit {result.returncode}]\n{out}" if out else f"[exit {result.returncode}] (sin salida)"
