"""
Operaciones de Git con lista de acciones cerrada (Spec 039, RF4). Sin shell y sin opciones
destructivas: nunca --force, reset, clean ni checkout.
"""
import subprocess

from .filesystem import resolve

_ACCIONES = {
    "status": ["status", "--short"],
    "log": ["log", "--oneline", "-n", "20"],
    "init": ["init"],
    "add": ["add", "-A"],
    "push": ["push"],
}


def git_ops(action: str, path: str = ".", message: str = "") -> str:
    accion = (action or "").strip().lower()
    if accion == "commit":
        if not (message or "").strip():
            raise ValueError("commit necesita un mensaje")
        args = ["commit", "-m", message.strip()]
    elif accion in _ACCIONES:
        args = list(_ACCIONES[accion])
    else:
        raise ValueError(f"acción git no permitida: {action}. Usa status, log, init, add, commit o push.")
    cwd = resolve(path)
    if not cwd.is_dir():
        raise ValueError(f"no es una carpeta: {path}")
    proc = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=120)
    salida = (proc.stdout + proc.stderr).strip()
    return f"[exit {proc.returncode}]\n{salida[:6000]}" if salida else f"[exit {proc.returncode}] (sin salida)"
