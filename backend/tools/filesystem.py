"""
Herramientas de sistema de archivos para GOBLIN.
Respetan FULL_ACCESS: con true pueden tocar cualquier ruta del usuario;
con false, solo dentro de workspace/.
"""
import os
import re
import shutil
from pathlib import Path

import config

# Spec 044 RF2: el editor abre y guarda archivos completos hasta este tamaño.
MAX_EDIT_BYTES = 5 * 1024 * 1024
# Spec 044 RF4: lo que el modelo recibe por cada lectura de read_file.
MAX_READ_CHARS = 5000
ADJUNTOS_DIR = "adjuntos"


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


def read_file(path: str, desde: int = 1, lineas: int = 150) -> str:
    """Lee un tramo de un archivo de texto para el modelo (Spec 044 RF4).

    Un archivo pequeño (≤150 líneas y ≤5 000 caracteres) se devuelve completo. Si no,
    devuelve hasta `lineas` líneas desde `desde` (base 1) sin pasar de 5 000 caracteres,
    e indica desde qué línea seguir.
    """
    p = resolve(path)
    if not p.is_file():
        return f"No es un archivo o no existe: {p}"
    try:
        data = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error leyendo {p}: {e}"
    try:
        desde = max(1, int(desde or 1))
        lineas = min(400, max(1, int(lineas or 150)))
    except (TypeError, ValueError):
        desde, lineas = 1, 150

    todas = data.splitlines(keepends=True)
    total = len(todas)
    if desde == 1 and total <= 150 and len(data) <= MAX_READ_CHARS:
        return data
    ini = desde - 1
    if ini >= total:
        return f"{p.name}: tiene {total} líneas; desde={desde} está fuera del archivo."

    trozo, chars = [], 0
    for linea in todas[ini:ini + lineas]:
        linea = linea[:MAX_READ_CHARS]
        if trozo and chars + len(linea) > MAX_READ_CHARS:
            break
        trozo.append(linea)
        chars += len(linea)
    fin = ini + len(trozo)
    cabecera = f"[{p.name}: líneas {ini + 1}-{fin} de {total}]"
    pie = "" if fin >= total else f"\n[... sigue en la línea {fin + 1}: usa read_file con desde={fin + 1} ...]"
    return cabecera + "\n" + "".join(trozo) + pie


def read_file_completo(path: str) -> str:
    """Contenido entero para el editor (Spec 044 RF2). Sin cortes; más de 5 MB se rechaza."""
    p = resolve(path)
    if not p.is_file():
        raise FileNotFoundError(f"No es un archivo o no existe: {p}")
    tam = p.stat().st_size
    if tam > MAX_EDIT_BYTES:
        raise ValueError(f"El archivo pesa {tam / (1024 * 1024):.1f} MB; el editor abre hasta 5 MB.")
    return p.read_text(encoding="utf-8", errors="replace")


def guardar_adjunto(nombre: str, contenido: str) -> dict:
    """Guarda un adjunto grande dentro de workspace/adjuntos (Spec 044 RF3)."""
    if len(contenido.encode("utf-8")) > MAX_EDIT_BYTES:
        raise ValueError("El adjunto pesa más de 5 MB.")
    base = Path(nombre or "adjunto.txt").name
    stem = re.sub(r"[^\w\-]+", "_", Path(base).stem).strip("_-")[:100] or "adjunto"
    suffix = re.sub(r"[^\w.]", "", Path(base).suffix)[:10]
    limpio = stem + suffix
    carpeta = config.WORKSPACE / ADJUNTOS_DIR
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / limpio
    n = 2
    while destino.exists():
        destino = carpeta / f"{stem}-{n}{suffix}"
        n += 1
    destino.write_text(contenido, encoding="utf-8")
    return {
        "path": str(destino),
        "relative": f"{ADJUNTOS_DIR}/{destino.name}",
        "lines": len(contenido.splitlines()),
    }


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
