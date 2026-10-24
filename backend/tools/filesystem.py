"""
Herramientas de sistema de archivos para GOBLIN.
Respetan FULL_ACCESS: con true pueden tocar cualquier ruta del usuario;
con false, solo dentro de workspace/.
"""
import os
import shutil
from pathlib import Path

import config


def resolve(path: str) -> Path:
    """Resuelve una ruta. Si es relativa, la ancla al workspace.
    Si FULL_ACCESS es false, impide salir del workspace."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = config.WORKSPACE / p
    p = p.resolve()
    if not config.FULL_ACCESS:
        if p != config.WORKSPACE and config.WORKSPACE not in p.parents:
            raise PermissionError(f"Ruta fuera del workspace (FULL_ACCESS=false): {p}")
    return p


def list_dir(path: str = ".") -> str:
    p = resolve(path)
    if not p.exists():
        return f"No existe: {p}"
    if not p.is_dir():
        return f"No es una carpeta: {p}"
    items = []
    for c in sorted(p.iterdir(), key=lambda c: (not c.is_dir(), c.name.lower())):
        tag = "DIR " if c.is_dir() else "FILE"
        try:
            size = "" if c.is_dir() else f" ({c.stat().st_size} B)"
        except OSError:
            size = ""
        items.append(f"[{tag}] {c.name}{size}")
    return f"Contenido de {p}:\n" + ("\n".join(items) if items else "(vacío)")


def read_file(path: str) -> str:
    p = resolve(path)
    if not p.is_file():
        return f"No es un archivo o no existe: {p}"
    try:
        data = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error leyendo {p}: {e}"
    if len(data) > 30000:
        data = data[:30000] + "\n\n[... truncado, archivo muy grande ...]"
    return data


def write_file(path: str, content: str) -> str:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Archivo escrito: {p} ({len(content)} caracteres)"


def make_dir(path: str) -> str:
    p = resolve(path)
    p.mkdir(parents=True, exist_ok=True)
    return f"Carpeta creada: {p}"


def move_path(src: str, dst: str) -> str:
    s, d = resolve(src), resolve(dst)
    if not s.exists():
        return f"Origen no existe: {s}"
    shutil.move(str(s), str(d))
    return f"Movido: {s} -> {d}"


def copy_path(src: str, dst: str) -> str:
    s, d = resolve(src), resolve(dst)
    if not s.exists():
        return f"Origen no existe: {s}"
    if s.is_dir():
        shutil.copytree(str(s), str(d), dirs_exist_ok=True)
    else:
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(s), str(d))
    return f"Copiado: {s} -> {d}"


def delete_path(path: str) -> str:
    p = resolve(path)
    if not p.exists():
        return f"No existe: {p}"
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()
    return f"Eliminado: {p}"


def search_files(query: str, path: str = ".") -> str:
    """Busca texto dentro de archivos (grep recursivo simple)."""
    base = resolve(path)
    hits = []
    for root, _dirs, files in os.walk(base):
        for name in files:
            fp = Path(root) / name
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        if query in line:
                            hits.append(f"{fp}:{i}: {line.strip()[:200]}")
                            if len(hits) >= 100:
                                return "\n".join(hits) + "\n[... más de 100 coincidencias ...]"
            except (OSError, UnicodeDecodeError):
                continue
    return "\n".join(hits) if hits else f"Sin coincidencias de '{query}' en {base}"


def disk_usage(path: str = ".") -> str:
    p = resolve(path)
    total, used, free = shutil.disk_usage(p)
    gb = 1024 ** 3
    return (f"Disco en {p}:\n"
            f"  Total: {total/gb:.1f} GB\n"
            f"  Usado: {used/gb:.1f} GB\n"
            f"  Libre: {free/gb:.1f} GB")
