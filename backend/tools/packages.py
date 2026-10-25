"""Instalación de paquetes con aprobación (Spec 045, RF5 y RF6).

Solo pip, en el Python del PATH (el mismo que usan los scripts lanzados desde la terminal).
Nunca se usa shell, sudo ni --break-system-packages. La aprobación la pide el agente
(approvals._ALWAYS_ASK); esta función solo valida y ejecuta.
"""
import re
import shutil
import subprocess
import sys

GESTORES = {"pip"}
# Solo un nombre simple: sin URLs, rutas, versiones ni espacios.
_NOMBRE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
_TIMEOUT_S = 300
_MODULO_RE = re.compile(r"No module named '([A-Za-z0-9_.]+)'")


def install_package(manager: str, name: str) -> str:
    gestor = (manager or "").strip().lower()
    if gestor not in GESTORES:
        return f"Gestor no permitido: '{manager}'. Solo se admite: {', '.join(sorted(GESTORES))}."
    nombre = (name or "").strip()
    if not _NOMBRE_RE.match(nombre):
        return (f"Nombre de paquete no válido: '{name}'. Usa solo letras, números, '.', '_' y '-', "
                "sin URLs, rutas ni versiones.")
    python = shutil.which("python3") or sys.executable
    cmd = [python, "-m", "pip", "install", "--no-input", "--disable-pip-version-check", nombre]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=_TIMEOUT_S, shell=False)
    except subprocess.TimeoutExpired:
        return f"pip tardó más de {_TIMEOUT_S} s con '{nombre}' y se detuvo."
    except OSError as e:
        return f"No pude ejecutar pip con {python}: {e}"
    salida = ((p.stdout or "") + (p.stderr or ""))[-2000:]
    if p.returncode != 0:
        if "externally-managed-environment" in salida:
            return ("Este Python no permite instalar paquetes con pip (protección PEP 668 del sistema). "
                    "GOBLIN no la salta. Opción: crear un entorno virtual en la carpeta del proyecto "
                    f"con {python} -m venv, y usar ese Python.\n{salida}")
        return f"pip falló (código {p.returncode}) con '{nombre}':\n{salida}"
    return f"Instalado '{nombre}' con {python}.\n{salida}"


def sugerencia(resultado: str) -> str:
    """Pista para el modelo cuando un comando falla por algo que falta (Spec 045, RF6)."""
    texto = resultado or ""
    m = _MODULO_RE.search(texto)
    if m:
        return (f"\n[GOBLIN: falta el módulo de Python '{m.group(1)}'. Puedes usar install_package con "
                "manager 'pip' y el nombre del paquete (puede no coincidir con el módulo, p. ej. "
                "yaml → PyYAML). Requiere aprobación del usuario.]")
    if "command not found" in texto or "no se encontró el comando" in texto.lower():
        return ("\n[GOBLIN: falta un comando del sistema. install_package solo instala paquetes de pip; "
                "para programas del sistema, dile al usuario el comando exacto para que lo ejecute él.]")
    return ""
