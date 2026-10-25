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


# Herramientas de escaneo y ataque. Si la IA las lanza por run_shell, SIEMPRE pide
# aprobación, incluso en nivel "confianza" (no se ejecutan sin que el usuario lo vea).
SECURITY_COMMANDS = {
    "nmap", "masscan", "sqlmap", "nikto", "gobuster", "ffuf", "feroxbuster", "dirb",
    "hydra", "medusa", "msfconsole", "msfvenom", "hping3", "wpscan", "enum4linux",
    "crackmapexec", "responder", "john", "hashcat", "aircrack-ng", "burpsuite",
    "searchsploit", "nc", "ncat", "netcat",
}


def is_security_command(command: str) -> bool:
    """True si el comando de shell lanza una herramienta de escaneo o ataque."""
    import re
    import shlex
    try:
        tokens = shlex.split(command or "")
    except ValueError:
        tokens = (command or "").split()
    for tok in tokens:
        # Saltar prefijos comunes: sudo, env, variables VAR=valor, timeout, nohup.
        if tok in {"sudo", "env", "timeout", "nohup", "time"} or re.match(r"^\w+=", tok):
            continue
        if tok.startswith("-"):
            continue
        name = tok.rsplit("/", 1)[-1]
        return name in SECURITY_COMMANDS
    return False


def needs_approval(sid: str, tool: str, base_needs_approval: bool, args: dict | None = None) -> bool:
    """True si la herramienta debe pedir aprobación al usuario."""
    if not base_needs_approval:
        return False               # herramientas de solo lectura: nunca piden
    if tool in _ALWAYS_ASK:
        return True                # delete siempre pide
    if tool == "run_shell" and is_security_command((args or {}).get("command", "")):
        return True                # escaneos y ataques: siempre se preguntan
    level = get_level(sid)
    return tool not in _AUTO.get(level, set())
