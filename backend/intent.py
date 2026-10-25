"""Clasificación de intención por turno (Spec 033).

Decide qué herramientas puede usar el modelo en cada petición. La decisión la toma el código
con palabras clave; el modelo no decide si actúa sobre la computadora.

  - action:   pide hacer algo → todas las herramientas (las de riesgo piden aprobación).
  - analysis: pide analizar, explicar o revisar → solo lectura, y solo si nombra una ruta.
  - chat:     saludos, preguntas y todo lo demás → sin herramientas.
"""
import re

READ_ONLY_TOOLS = {"read_file", "list_dir", "search_files"}

_ACTION_RE = re.compile(
    r"\b(crea|crear|haz|hacer|escribe|escribir|guarda|guardar|borra|borrar|elimina|eliminar|"
    r"mueve|mover|copia|copiar|renombra|renombrar|ejecuta|ejecutar|corre|correr|instala|"
    r"instalar|escanea|escanear|lanza|lanzar|abre|abrir|modifica|modificar|cambia|cambiar|"
    r"edita|editar|actualiza|actualizar|lista|listar|muestra|mostrar|busca|buscar|lee|leer|"
    r"fija|fijar|registra|registrar|genera|generar)\b",
    re.IGNORECASE,
)

_ANALYSIS_RE = re.compile(
    r"\b(analiza|analizar|explica|explicar|resume|resumir|revisa|revisar|compara|comparar|"
    r"describe|describir|evalúa|evaluar|qué es|que es|cómo funciona|como funciona|por qué|por que)\b",
    re.IGNORECASE,
)

# Una ruta o un archivo concreto: ~/algo, /algo, ./algo o nombre.ext
_PATH_RE = re.compile(
    r"(~/|(?<![\w/])/[\w.\-]+|\./|\b[\w.\-]+\.(py|js|ts|txt|md|json|csv|log|html|css|sh|"
    r"yaml|yml|toml|ini|conf|xml|pdf|docx|xlsx|c|h|cpp|java|go|rs|rb|php)\b)"
)


def classify(text: str) -> str:
    """Devuelve 'action', 'analysis' o 'chat'."""
    t = text or ""
    if _ACTION_RE.search(t):
        return "action"
    if _ANALYSIS_RE.search(t):
        return "analysis"
    return "chat"


def mentions_path(text: str) -> bool:
    return bool(_PATH_RE.search(text or ""))


def allowed_tools(text: str) -> set[str] | None:
    """Herramientas permitidas para el turno. None = todas (solo en 'action')."""
    kind = classify(text)
    if kind == "action":
        return None
    if kind == "analysis" and mentions_path(text):
        return set(READ_ONLY_TOOLS)
    return set()


# Preguntas sobre lo que GOBLIN puede hacer (Spec 034, RF1). No piden ninguna acción.
_CAPABILITY_RE = re.compile(
    r"^[\s¿?¡!]*(puedes|puede|podrías|podrias|sabes|eres capaz de|qué puedes hacer|que puedes hacer|"
    r"qué haces|que haces|para qué sirves|para que sirves|quién eres|quien eres|qué eres|que eres)\b",
    re.IGNORECASE,
)

CAPABILITY_REPLY = (
    "Sí. Trabajo con los archivos y carpetas de tu computadora: puedo listarlos, leerlos, buscar "
    "texto, crear, copiar, mover y borrar, y ejecutar comandos. Lo que cambia algo o ejecuta comandos "
    "te lo pido aprobar antes. Para analizar algo, dime la ruta (por ejemplo ~/proyecto/app.py) y "
    "qué quieres saber de ella."
)


def is_capability(text: str) -> bool:
    """True si el mensaje pregunta por las capacidades de GOBLIN y no pide una acción (Spec 034)."""
    t = text or ""
    if not _CAPABILITY_RE.match(t):
        return False
    # Solo cuenta lo que viene DESPUÉS de la fórmula: en "¿qué puedes hacer?" el "hacer" es parte
    # de la pregunta, no una orden.
    resto = _CAPABILITY_RE.sub("", t, count=1)
    return not _ACTION_RE.search(resto)
