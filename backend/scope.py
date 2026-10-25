"""
Alcance del engagement y detección de destinos de red (Spec 036, RF1–RF4).

Decide si un comando o una URL apunta dentro de los objetivos autorizados de la sesión.
La IA no puede ampliar el alcance: solo el usuario lo edita desde la interfaz.
Loopback (127.0.0.1, ::1, localhost) siempre se permite.
"""
from __future__ import annotations

import ipaddress
import re
import shlex
from urllib.parse import urlsplit

# Extensiones que parecen dominio ("notas.txt") pero son archivos.
_FILE_EXT = {
    "txt", "py", "sh", "json", "log", "xml", "md", "csv", "lst", "conf", "cfg", "ini", "html",
    "htm", "js", "css", "png", "jpg", "jpeg", "gif", "gz", "zip", "tar", "pdf", "doc", "docx",
    "xls", "xlsx", "db", "bak", "out", "nmap", "gnmap", "yaml", "yml", "toml", "rb", "php",
    "c", "h", "cpp", "java", "go", "rs", "exe", "dll", "so", "bin", "dic", "rule", "pot",
}

# Herramientas que pueden tocar la red. Si una aparece en un comando, sus destinos se comprueban.
NETWORK_CMDS = {
    # escaneo y ataque (Spec 025, approvals.SECURITY_COMMANDS)
    "nmap", "masscan", "sqlmap", "nikto", "gobuster", "ffuf", "feroxbuster", "dirb",
    "hydra", "medusa", "msfconsole", "msfvenom", "hping3", "wpscan", "enum4linux",
    "crackmapexec", "responder", "burpsuite", "nc", "ncat", "netcat",
    # red común
    "curl", "wget", "ssh", "scp", "sftp", "ftp", "telnet", "rsync", "ping", "traceroute",
    "dig", "host", "nslookup", "whois", "smbclient", "rpcclient", "ldapsearch", "snmpwalk",
}

_DOMAIN_RE = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
_CIDR_LIKE_RE = re.compile(r"^[0-9a-f:.]+/\d{1,3}$")
# Destinos que no se pueden comprobar: variables, sustitución de comandos, listas de archivo.
_UNVERIFIABLE_RE = re.compile(r"\$|`|(?:^|\s)--?i[LR](?:\s|$)|--input-file|--random-targets")
_PREFIXES = {"sudo", "env", "timeout", "nohup", "time", "exec"}


def _classify(token: str):
    """Clasifica un token: ('ip', ip) · ('net', red) · ('domain', nombre) · ('loopback', None) · None."""
    t = (token or "").strip().strip("'\"`,;()[]<>").lower().rstrip(".")
    if not t:
        return None
    if "://" in t:
        t = (urlsplit(t).hostname or "").rstrip(".")
        if not t:
            return None
    if "/" in t and not _CIDR_LIKE_RE.match(t):
        t = t.split("/", 1)[0]            # quitar ruta: host/path
    if t.startswith("[") and "]" in t:    # [ipv6]:puerto
        t = t[1:t.index("]")]
    elif t.count(":") == 1:               # host:puerto
        t = t.split(":", 1)[0]
    if t in ("localhost", "localhost.localdomain"):
        return ("loopback", None)
    try:
        if "/" in t:
            return ("net", ipaddress.ip_network(t, strict=False))
        return ("ip", ipaddress.ip_address(t))
    except ValueError:
        pass
    if _DOMAIN_RE.match(t) and t.rsplit(".", 1)[-1] not in _FILE_EXT:
        return ("domain", t)
    return None


def normalize_entry(text: str) -> str | None:
    """Convierte lo que escribe el usuario (IP, rango, dominio o URL) en una entrada canónica."""
    c = _classify(text)
    if c is None or c[0] == "loopback":
        return None
    kind, val = c
    if kind == "domain":
        return val
    return str(val)


def in_scope(target: str, entries: list[str]) -> bool:
    """True si el destino está dentro de alguna entrada de alcance."""
    c = _classify(target)
    if c is None:
        return False
    kind, val = c
    if kind == "loopback" or (kind == "ip" and val.is_loopback):
        return True
    for entry in entries:
        ec = _classify(entry)
        if ec is None:
            continue
        ek, ev = ec
        if ek == "domain":
            if kind == "domain" and (val == ev or val.endswith("." + ev)):
                return True
        elif ek == "ip":
            if kind == "ip" and val == ev:
                return True
        elif ek == "net":
            if kind == "ip" and val in ev:
                return True
            if kind == "net":
                try:
                    if val.subnet_of(ev):
                        return True
                except TypeError:   # versiones distintas (IPv4 vs IPv6)
                    pass
    return False


def command_name(command: str) -> str:
    """Nombre de la herramienta de un comando, saltando sudo/env/variables."""
    try:
        tokens = shlex.split(command or "")
    except ValueError:
        tokens = (command or "").split()
    for tok in tokens:
        if tok in _PREFIXES or re.match(r"^\w+=", tok) or tok.startswith("-"):
            continue
        return tok.rsplit("/", 1)[-1]
    return ""


def extract_targets(command: str) -> list[str]:
    """Destinos (IP, rangos, dominios, URLs) que aparecen como argumentos del comando."""
    try:
        tokens = shlex.split(command or "")
    except ValueError:
        tokens = (command or "").split()
    out = []
    for tok in tokens:
        if tok.startswith("-"):
            continue
        c = _classify(tok)
        if c is not None and c[0] != "loopback":
            out.append(tok)
    return out


def check_command(command: str, entries: list[str]) -> str | None:
    """Mensaje de bloqueo si el comando sale del alcance, o None si puede ejecutarse."""
    if command_name(command) not in NETWORK_CMDS:
        return None
    if _UNVERIFIABLE_RE.search(command or ""):
        return ("BLOQUEADO por alcance: el comando usa variables, sustitución o listas de destinos y "
                "no se puede comprobar que apunte dentro del alcance. Escribe los objetivos literales.")
    targets = extract_targets(command)
    if not targets:
        return None
    if not entries:
        return ("BLOQUEADO por alcance: no hay alcance definido para este engagement. Pide al usuario "
                "que añada el objetivo en el panel Alcance de la interfaz.")
    fuera = [t for t in targets if not in_scope(t, entries)]
    if fuera:
        return (f"BLOQUEADO por alcance: {', '.join(fuera)} no está en el alcance del engagement. "
                "No lo intentes de otra forma; pide al usuario que lo añada si está autorizado.")
    return None


def check_url(url: str, entries: list[str]) -> str | None:
    """Mensaje de bloqueo para una URL fuera del alcance, o None."""
    host = urlsplit((url or "").strip()).hostname
    if not host:
        return "BLOQUEADO: la URL no tiene un host válido."
    if not in_scope(host, entries):
        return (f"BLOQUEADO por alcance: {host} no está en el alcance del engagement. "
                "Pide al usuario que lo añada si está autorizado.")
    return None
