"""
Vista previa de cambios para la aprobación (Spec 037, RF1). Calcula el diff sin tocar el archivo.
"""
import difflib

from tools.filesystem import resolve
from tools.editing import apply_edit

MAX_DIFF_LINES = 200
MAX_CHARS = 2_000_000


def _unified(old: str, new: str, path: str) -> str:
    if len(old) + len(new) > MAX_CHARS:
        return f"(archivo muy grande: {len(old)} → {len(new)} caracteres; diff omitido)"
    lineas = list(difflib.unified_diff(
        old.splitlines(), new.splitlines(),
        fromfile=f"{path} (actual)", tofile=f"{path} (nuevo)", lineterm="",
    ))
    if not lineas:
        return "(sin cambios en el contenido)"
    if len(lineas) > MAX_DIFF_LINES:
        resto = len(lineas) - MAX_DIFF_LINES
        lineas = lineas[:MAX_DIFF_LINES] + [f"… {resto} líneas más"]
    return "\n".join(lineas)


def _read_or_empty(path: str) -> str:
    p = resolve(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def diff_for(name: str, args: dict) -> str | None:
    """Diff previsto de una herramienta de escritura, o None si no aplica."""
    try:
        if name == "write_file":
            path = str(args.get("path", ""))
            return _unified(_read_or_empty(path), str(args.get("content", "")), path)
        if name == "edit_lines":
            path = str(args.get("path", ""))
            actual = _read_or_empty(path)
            nuevo = apply_edit(actual, int(args.get("start_line", 0)), int(args.get("end_line", 0)),
                               str(args.get("new_text", "")))
            return _unified(actual, nuevo, path)
    except Exception as e:   # la aprobación se muestra igual, con el motivo
        return f"(no se pudo calcular el diff: {e})"
    return None
