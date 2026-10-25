"""
Edición de archivos por líneas y permisos (Spec 039, RF1–RF2).
"""
import re

from .filesystem import resolve

_MODE_RE = re.compile(r"^[0-7]{3,4}$")
_RAIZ = {"/", "/*", "~", "~/", "*", "/."}


def apply_edit(text: str, start: int, end: int, new_text: str) -> str:
    """Reemplaza las líneas start..end (1-based, inclusivas). Función pura: no toca el disco."""
    lineas = text.splitlines(keepends=True)
    if start < 1 or end < start or end > len(lineas):
        raise ValueError(f"rango {start}-{end} fuera del archivo ({len(lineas)} líneas)")
    reemplazo = new_text if (new_text == "" or new_text.endswith("\n")) else new_text + "\n"
    return "".join(lineas[:start - 1]) + reemplazo + "".join(lineas[end:])


def edit_lines(path: str, start_line: int, end_line: int, new_text: str) -> str:
    p = resolve(path)
    if not p.is_file():
        raise ValueError(f"no existe el archivo: {path}")
    start, end = int(start_line), int(end_line)
    nuevo = apply_edit(p.read_text(encoding="utf-8", errors="replace"), start, end, str(new_text))
    p.write_text(nuevo, encoding="utf-8")
    return f"Líneas {start}-{end} reemplazadas en {path}."


def chmod(path: str, mode: str) -> str:
    m = str(mode).strip()
    if not _MODE_RE.match(m):
        raise ValueError("modo no válido: usa octal de 3 o 4 dígitos, por ejemplo 755")
    if str(path).strip() in _RAIZ:
        raise PermissionError("no se cambian permisos de la raíz ni del home completo")
    p = resolve(path)
    if not p.exists():
        raise ValueError(f"no existe: {path}")
    p.chmod(int(m, 8))
    return f"Permisos de {path} cambiados a {m}."
