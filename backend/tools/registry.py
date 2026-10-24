"""
Registro de herramientas: mapea nombres a funciones, define los esquemas
que ve el modelo (formato de tool-calling de Ollama) y marca cuáles
requieren aprobación del usuario antes de ejecutarse.
"""
from . import filesystem as fs
from . import shell as sh
from . import pentest as pt

TOOLS = {
    "list_dir": fs.list_dir,
    "read_file": fs.read_file,
    "write_file": fs.write_file,
    "make_dir": fs.make_dir,
    "move_path": fs.move_path,
    "copy_path": fs.copy_path,
    "delete_path": fs.delete_path,
    "search_files": fs.search_files,
    "disk_usage": fs.disk_usage,
    "run_shell": sh.run_shell,
    "add_finding": pt.add_finding,
    "generate_report": pt.generate_report,
}

# Herramientas que modifican/ejecutan: requieren aprobación del usuario.
# add_finding y generate_report NO requieren aprobación (solo registran/leen datos).
NEEDS_APPROVAL = {
    "write_file", "make_dir", "move_path", "copy_path", "delete_path", "run_shell",
}


def run_tool(name: str, args: dict) -> str:
    fn = TOOLS.get(name)
    if fn is None:
        return f"Error: herramienta desconocida '{name}'"
    try:
        return str(fn(**(args or {})))
    except TypeError as e:
        return f"Error de argumentos en '{name}': {e}"
    except PermissionError as e:
        return f"Permiso denegado: {e}"
    except Exception as e:
        return f"Error en '{name}': {e}"


# --- Esquemas para el modelo (formato tools de Ollama) ---
S = "string"


def _t(name, desc, props, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {"type": "object", "properties": props, "required": required},
        },
    }


SCHEMAS = [
    _t("list_dir", "Lista el contenido de una carpeta.",
       {"path": {"type": S, "description": "Ruta de la carpeta"}}, ["path"]),
    _t("read_file", "Lee el contenido de un archivo de texto.",
       {"path": {"type": S, "description": "Ruta del archivo"}}, ["path"]),
    _t("write_file", "Crea o sobrescribe un archivo de texto con el contenido dado.",
       {"path": {"type": S}, "content": {"type": S}}, ["path", "content"]),
    _t("make_dir", "Crea una carpeta (y las intermedias si faltan).",
       {"path": {"type": S}}, ["path"]),
    _t("move_path", "Mueve o renombra un archivo o carpeta.",
       {"src": {"type": S}, "dst": {"type": S}}, ["src", "dst"]),
    _t("copy_path", "Copia un archivo o carpeta a otra ubicación.",
       {"src": {"type": S}, "dst": {"type": S}}, ["src", "dst"]),
    _t("delete_path", "Elimina un archivo o carpeta (con todo su contenido).",
       {"path": {"type": S}}, ["path"]),
    _t("search_files", "Busca un texto dentro de los archivos de una carpeta (grep recursivo).",
       {"query": {"type": S}, "path": {"type": S, "description": "Carpeta donde buscar"}},
       ["query"]),
    _t("disk_usage", "Muestra el espacio total, usado y libre del disco en una ruta.",
       {"path": {"type": S}}, []),
    _t("run_shell", "Ejecuta un comando de shell en Linux y devuelve su salida.",
       {"command": {"type": S}, "cwd": {"type": S, "description": "Carpeta de ejecución"}},
       ["command"]),
    _t("add_finding",
       "Registra un hallazgo de seguridad encontrado durante el pentest. Úsalo cuando "
       "descubras una vulnerabilidad, mala configuración o dato relevante.",
       {"severity": {"type": S, "description": "critical, high, medium, low o info"},
        "title": {"type": S, "description": "Nombre corto del hallazgo"},
        "host": {"type": S, "description": "IP o host afectado"},
        "port": {"type": S, "description": "Puerto/servicio"},
        "description": {"type": S, "description": "Explicación del hallazgo"},
        "evidence": {"type": S, "description": "Evidencia o salida que lo prueba"}},
       ["severity", "title"]),
    _t("generate_report",
       "Genera el informe de pentest en Markdown con todos los hallazgos registrados "
       "en esta sesión. Úsalo cuando el usuario pida el reporte.",
       {}, []),
]
