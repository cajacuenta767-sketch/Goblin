"""
Marketplace de herramientas de ciberseguridad (Spec 016).
Catálogo de herramientas de pentest instalables vía apt, con detección de estado.
Solo paquetes de los repos oficiales de Parrot/Debian.
"""
import shutil
import subprocess

# Catálogo: id, nombre, categoría, descripción, binario (para detectar), paquete apt, icono.
CATALOG = [
    {"id": "nmap", "name": "Nmap", "category": "recon", "icon": "nmap",
     "desc": "Escáner de puertos y servicios. La base de todo reconocimiento de red.",
     "bin": "nmap", "pkg": "nmap"},
    {"id": "gobuster", "name": "Gobuster", "category": "web", "icon": "web",
     "desc": "Fuerza bruta de directorios, DNS y subdominios en servidores web.",
     "bin": "gobuster", "pkg": "gobuster"},
    {"id": "nikto", "name": "Nikto", "category": "web", "icon": "web",
     "desc": "Escáner de vulnerabilidades web: configuraciones y archivos peligrosos.",
     "bin": "nikto", "pkg": "nikto"},
    {"id": "sqlmap", "name": "SQLMap", "category": "web", "icon": "db",
     "desc": "Detección y explotación automática de inyecciones SQL.",
     "bin": "sqlmap", "pkg": "sqlmap"},
    {"id": "hydra", "name": "Hydra", "category": "passwords", "icon": "key",
     "desc": "Fuerza bruta de credenciales en SSH, FTP, HTTP y decenas de protocolos.",
     "bin": "hydra", "pkg": "hydra"},
    {"id": "john", "name": "John the Ripper", "category": "passwords", "icon": "key",
     "desc": "Cracking de hashes de contraseñas, rápido y flexible.",
     "bin": "john", "pkg": "john"},
    {"id": "hashcat", "name": "Hashcat", "category": "passwords", "icon": "key",
     "desc": "Cracking de hashes acelerado. El estándar para romper contraseñas.",
     "bin": "hashcat", "pkg": "hashcat"},
    {"id": "metasploit", "name": "Metasploit", "category": "exploitation", "icon": "exploit",
     "desc": "Framework de explotación: exploits, payloads y post-explotación.",
     "bin": "msfconsole", "pkg": "metasploit-framework"},
    {"id": "wireshark", "name": "Wireshark", "category": "network", "icon": "net",
     "desc": "Analizador de tráfico de red. Inspecciona paquetes al detalle.",
     "bin": "wireshark", "pkg": "wireshark"},
    {"id": "tcpdump", "name": "tcpdump", "category": "network", "icon": "net",
     "desc": "Captura de paquetes por línea de comandos, ligero y potente.",
     "bin": "tcpdump", "pkg": "tcpdump"},
    {"id": "netcat", "name": "Netcat", "category": "network", "icon": "net",
     "desc": "La navaja suiza de las redes: conexiones, listeners y transferencias.",
     "bin": "nc", "pkg": "netcat-traditional"},
    {"id": "ffuf", "name": "ffuf", "category": "web", "icon": "web",
     "desc": "Fuzzer web rapidísimo para rutas, parámetros y subdominios.",
     "bin": "ffuf", "pkg": "ffuf"},
    {"id": "wfuzz", "name": "Wfuzz", "category": "web", "icon": "web",
     "desc": "Fuzzing de aplicaciones web para encontrar recursos ocultos.",
     "bin": "wfuzz", "pkg": "wfuzz"},
    {"id": "enum4linux", "name": "enum4linux", "category": "recon", "icon": "search",
     "desc": "Enumeración de información de sistemas Windows/Samba (SMB).",
     "bin": "enum4linux", "pkg": "enum4linux"},
    {"id": "dnsenum", "name": "dnsenum", "category": "recon", "icon": "search",
     "desc": "Enumeración de DNS: registros, subdominios y transferencias de zona.",
     "bin": "dnsenum", "pkg": "dnsenum"},
    {"id": "aircrack", "name": "Aircrack-ng", "category": "wireless", "icon": "wifi",
     "desc": "Suite para auditoría de redes WiFi: captura y crackeo de claves.",
     "bin": "aircrack-ng", "pkg": "aircrack-ng"},
    {"id": "responder", "name": "Responder", "category": "network", "icon": "net",
     "desc": "Envenenamiento LLMNR/NBT-NS para capturar credenciales en red local.",
     "bin": "responder", "pkg": "responder"},
]

CATEGORIES = ["recon", "web", "passwords", "exploitation", "network", "wireless"]


def is_installed(bin_name: str) -> bool:
    return shutil.which(bin_name) is not None


def catalog() -> list[dict]:
    """Devuelve el catálogo con el estado de instalación de cada herramienta."""
    out = []
    for t in CATALOG:
        out.append({**t, "installed": is_installed(t["bin"])})
    return out


def install(tool_id: str) -> dict:
    """Instala una herramienta vía apt. Requiere sudo (la UI avisa)."""
    tool = next((t for t in CATALOG if t["id"] == tool_id), None)
    if not tool:
        return {"ok": False, "error": f"Herramienta desconocida: {tool_id}"}
    if is_installed(tool["bin"]):
        return {"ok": True, "message": f"{tool['name']} ya está instalada.", "installed": True}
    try:
        proc = subprocess.run(
            ["sudo", "apt-get", "install", "-y", tool["pkg"]],
            capture_output=True, text=True, timeout=600,
        )
        ok = proc.returncode == 0
        return {
            "ok": ok,
            "message": (f"{tool['name']} instalada correctamente." if ok
                        else f"No se pudo instalar {tool['name']}."),
            "installed": is_installed(tool["bin"]),
            "output": (proc.stdout + proc.stderr)[-1500:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "La instalación tardó demasiado y se canceló."}
    except Exception as e:
        return {"ok": False, "error": str(e)}
