"""
Router híbrido de GOBLIN: decide qué modelo responde cada mensaje.
Modos:
  - "local"  : solo DeepHat (local, sin censura). Por defecto y para engagements con NDA.
  - "hybrid" : Gemini primero (rápido); si se niega por censura, reintenta con DeepHat.
  - "manual" : el usuario elige el modelo por mensaje (lo maneja el frontend pasando el modelo).

Por seguridad y privacidad, el modo por defecto es "local": nada sale a la nube salvo que
el usuario active explícitamente el modo híbrido (constitución, art. II).
"""
import re

import config

# Datos sensibles: IPv4 y rangos CIDR (Spec 025). No cubre IPv6 ni nombres de cliente.
_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:/\d{1,2})?\b"
)

# Modo activo por sesión. Por defecto, local puro.
_modes: dict[str, str] = {}

VALID_MODES = {"local", "hybrid", "manual"}

# Frases típicas de rechazo de Gemini (además del error de safety de la API).
_REFUSAL_HINTS = [
    "i can't help with that", "i cannot help with that", "i can't assist",
    "i'm not able to help", "no puedo ayudar con eso", "no puedo asistir",
    "i won't", "against my guidelines", "i'm unable to provide",
]


def get_mode(sid: str) -> str:
    return _modes.get(sid, "local")


def set_mode(sid: str, mode: str) -> str:
    mode = mode if mode in VALID_MODES else "local"
    _modes[sid] = mode
    return mode


def gemini_available() -> bool:
    """Hay Gemini si hay API key configurada."""
    return bool(config.GEMINI_API_KEY)


def looks_like_refusal(text: str) -> bool:
    """Heurística para detectar que Gemini se negó (para caer a DeepHat)."""
    if not text:
        return False
    low = text.lower()
    return any(h in low for h in _REFUSAL_HINTS)


_GREETING_RE = re.compile(
    r"^(hola|holi|buenas|buenos d[ií]as|buenas tardes|buenas noches|hey|hi|hello|"
    r"gracias|muchas gracias|ok|vale|qu[ée] tal|que tal)[\s!.,¡]*$"
)

# Temas de pentest: van directo a DeepHat (Spec 032, RF6). Sin "\b" al final para
# que cubra variantes como "escaneo", "escanea" o "exploits".
_PENTEST_RE = re.compile(
    r"\b(nmap|sqlmap|metasploit|msfconsole|exploit|payload|reverse shell|shell inversa|"
    r"escane|pentest|vulnerab|hashcat|gobuster|ffuf|feroxbuster|burp|privesc|"
    r"escalada de privilegios|enumera|fuzz|cve-\d|hallazgo|post-explot|pivot)",
    re.IGNORECASE,
)


def is_greeting(text: str) -> bool:
    """Saludo o agradecimiento corto, sin pregunta (Spec 032, RF5)."""
    t = (text or "").strip().lower().lstrip("¡¿ ")
    return len(t) <= 40 and "?" not in t and bool(_GREETING_RE.match(t))


def needs_local_intent(text: str) -> bool:
    """Tema de pentest: conviene DeepHat local directo, sin pasar por Gemini (Spec 032, RF6)."""
    return bool(_PENTEST_RE.search(text or ""))


def sensitive_reason(messages, target: str = "") -> str | None:
    """Qué dato sensible aparece en TODO el historial, o None (Spec 025).

    Revisa cada mensaje (usuario, IA, herramientas y llamadas a herramientas), no solo
    el último: un dato que ya salió antes también cuenta. Devuelve solo el tipo de
    dato, nunca el valor.
    """
    text = "\n".join(str(m) for m in messages)
    m = _IPV4_RE.search(text)
    if m:
        return "un rango de red" if "/" in m.group(0) else "una dirección IP"
    objetivo = (target or "").strip()
    if objetivo and objetivo.lower() in text.lower():
        return "el objetivo activo"
    return None
