"""
Niveles de autoaprobación (Spec 009).
Decide si una herramienta necesita aprobación del usuario según el nivel de la sesión.

Reglas de seguridad que NUNCA cambian (constitución art. III):
  - delete_path SIEMPRE pide aprobación, en todos los niveles.
  - La lista negra de comandos se aplica en la propia herramienta, no aquí.
"""

# Nivel por sesión. Por defecto, el más seguro.
_levels: dict[str, str] = {}

VALID_LEVELS = {"cauto", "normal", "confianza"}

# Qué herramientas se auto-aprueban en cada nivel (el resto pide confirmación).
# delete_path nunca aparece aquí: siempre pide.
_AUTO = {
    "cauto":     set(),
    "normal":    {"write_file", "make_dir", "move_path", "copy_path"},
    "confianza": {"write_file", "make_dir", "move_path", "copy_path", "run_shell"},
}

# Siempre requieren aprobación, pase lo que pase.
# set_target: fijar un objetivo exige confirmar la autorización por escrito (Spec 025).
_ALWAYS_ASK = {"delete_path", "set_target"}


def get_level(sid: str) -> str:
    return _levels.get(sid, "cauto")


def set_level(sid: str, level: str) -> str:
    level = level if level in VALID_LEVELS else "cauto"
    _levels[sid] = level
    return level


def needs_approval(sid: str, tool: str, base_needs_approval: bool) -> bool:
    """True si la herramienta debe pedir aprobación al usuario."""
    if not base_needs_approval:
        return False               # herramientas de solo lectura: nunca piden
    if tool in _ALWAYS_ASK:
        return True                # delete siempre pide
    level = get_level(sid)
    return tool not in _AUTO.get(level, set())
