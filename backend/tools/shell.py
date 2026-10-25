"""
Herramienta de shell para GOBLIN.
Ejecuta comandos con timeout y bloqueo duro de comandos peligrosos.
Cada comando corre en su propio grupo de procesos para poder detenerlo entero
con el botón Detener (Spec 024).
(La terminal persistente/pty real vive en terminal.py / term_session.py.)
"""
import re
import subprocess

import config
import cancel
from .filesystem import resolve


_RAIZ_RM = {"/", "/*", "~", "~/", "*", "/.", "$home", "${home}"}
_APAGADO = {"shutdown", "reboot", "halt", "poweroff"}


def _normalizar(command: str) -> str:
    """Minúsculas, sin comillas y con espacios colapsados: "RM  -rf '/'" → "rm -rf /"."""
    return re.sub(r"\s+", " ", command.replace('"', "").replace("'", "").lower()).strip()


def _segmentos(cmd: str) -> list[list[str]]:
    """Comandos separados por ; && || | y saltos de línea, cada uno como lista de palabras."""
    out = []
    for parte in re.split(r"[;&|\n]+", cmd):
        palabras = [p for p in parte.split() if p not in ("sudo", "env", "exec", "nohup", "time")]
        if palabras:
            out.append(palabras)
    return out


def _es_rm_recursivo_raiz(palabras: list[str]) -> bool:
    if not palabras or palabras[0].rsplit("/", 1)[-1] != "rm":
        return False
    flags = [p for p in palabras[1:] if p.startswith("-")]
    recursivo = any("r" in f.lower() for f in flags if not f.startswith("--")) or "--recursive" in flags
    rutas = [p for p in palabras[1:] if not p.startswith("-")]
    return recursivo and any(r in _RAIZ_RM for r in rutas)


def _is_blocked(command: str) -> bool:
    cmd = _normalizar(command)
    if any(_normalizar(bad) in cmd for bad in config.BLOCKED_PATTERNS):
        return True
    if re.search(r"\bmkfs(\.\w+)?\b", cmd) or re.search(r"\bdd\b.*\bof=/dev/", cmd):
        return True
    if re.search(r":\(\)\s*\{\s*:\|:&\s*\};:", cmd) or re.search(r">\s*/dev/sd[a-z]", cmd):
        return True
    for palabras in _segmentos(cmd):
        if palabras[0].rsplit("/", 1)[-1] in _APAGADO:
            return True
        if _es_rm_recursivo_raiz(palabras):
            return True
    return False


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
