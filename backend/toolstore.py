"""
Marketplace de herramientas de ciberseguridad (Spec 016 / 020).
Catálogo de herramientas de pentest con:
  - enlace vivo a su fuente oficial (web o GitHub releases) para la última versión,
  - logo oficial cargado en vivo desde su web (no incrustado, para no infringir marcas),
  - instalación vía apt (repos oficiales de Parrot/Debian).
Las URLs apuntan a páginas oficiales de cada proyecto.
"""
import shutil
import subprocess

# Cada herramienta: id, nombre, categoría, descripción, binario (detección),
# paquete apt, url_oficial (última versión), logo (url del logo oficial en vivo).
CATALOG = [
    {"id": "nmap", "name": "Nmap", "category": "recon", "bin": "nmap", "pkg": "nmap",
     "desc": "Escáner de puertos y servicios. La base de todo reconocimiento de red.",
     "url": "https://nmap.org/download.html",
     "logo": "https://nmap.org/images/nmap-logo-256x256.png"},
    {"id": "metasploit", "name": "Metasploit Framework", "category": "exploitation",
     "bin": "msfconsole", "pkg": "metasploit-framework",
     "desc": "Framework de explotación: exploits, payloads y post-explotación.",
     "url": "https://github.com/rapid7/metasploit-framework/releases",
     "logo": "https://www.metasploit.com/includes/snippets/metasploit/images/metasploit-logo.svg"},
    {"id": "sqlmap", "name": "SQLMap", "category": "web", "bin": "sqlmap", "pkg": "sqlmap",
     "desc": "Detección y explotación automática de inyecciones SQL.",
     "url": "https://github.com/sqlmapproject/sqlmap/releases",
     "logo": "https://raw.githubusercontent.com/sqlmapproject/sqlmap/master/doc/logo.png"},
    {"id": "gobuster", "name": "Gobuster", "category": "web", "bin": "gobuster", "pkg": "gobuster",
     "desc": "Fuerza bruta de directorios, DNS y subdominios en servidores web.",
     "url": "https://github.com/OJ/gobuster/releases",
     "logo": ""},
    {"id": "ffuf", "name": "ffuf", "category": "web", "bin": "ffuf", "pkg": "ffuf",
     "desc": "Fuzzer web rapidísimo para rutas, parámetros y subdominios.",
     "url": "https://github.com/ffuf/ffuf/releases",
     "logo": "https://raw.githubusercontent.com/ffuf/ffuf/master/_img/ffuf_run_logo_600.png"},
    {"id": "nikto", "name": "Nikto", "category": "web", "bin": "nikto", "pkg": "nikto",
     "desc": "Escáner de vulnerabilidades web: configuraciones y archivos peligrosos.",
     "url": "https://github.com/sullo/nikto/releases",
     "logo": ""},
    {"id": "wfuzz", "name": "Wfuzz", "category": "web", "bin": "wfuzz", "pkg": "wfuzz",
     "desc": "Fuzzing de aplicaciones web para encontrar recursos ocultos.",
     "url": "https://github.com/xmendez/wfuzz/releases",
     "logo": ""},
    {"id": "hydra", "name": "THC-Hydra", "category": "passwords", "bin": "hydra", "pkg": "hydra",
     "desc": "Fuerza bruta de credenciales en SSH, FTP, HTTP y decenas de protocolos.",
     "url": "https://github.com/vanhauser-thc/thc-hydra/releases",
     "logo": ""},
    {"id": "john", "name": "John the Ripper", "category": "passwords", "bin": "john", "pkg": "john",
     "desc": "Cracking de hashes de contraseñas, rápido y flexible.",
     "url": "https://www.openwall.com/john/",
     "logo": "https://www.openwall.com/john/pics/john-the-ripper.png"},
    {"id": "hashcat", "name": "Hashcat", "category": "passwords", "bin": "hashcat", "pkg": "hashcat",
     "desc": "Cracking de hashes acelerado. El estándar para romper contraseñas.",
     "url": "https://hashcat.net/hashcat/",
     "logo": "https://hashcat.net/misc/example_hashes/hashcat.png"},
    {"id": "wireshark", "name": "Wireshark", "category": "network", "bin": "wireshark", "pkg": "wireshark",
     "desc": "Analizador de tráfico de red. Inspecciona paquetes al detalle.",
     "url": "https://www.wireshark.org/download.html",
     "logo": "https://www.wireshark.org/assets/icons/wireshark-fin@2x.png"},
    {"id": "tcpdump", "name": "tcpdump", "category": "network", "bin": "tcpdump", "pkg": "tcpdump",
     "desc": "Captura de paquetes por línea de comandos, ligero y potente.",
     "url": "https://www.tcpdump.org/",
     "logo": "https://www.tcpdump.org/tcpdump-power.gif"},
    {"id": "netcat", "name": "Netcat", "category": "network", "bin": "nc", "pkg": "netcat-traditional",
     "desc": "La navaja suiza de las redes: conexiones, listeners y transferencias.",
     "url": "https://nmap.org/ncat/",
     "logo": ""},
    {"id": "responder", "name": "Responder", "category": "network", "bin": "responder", "pkg": "responder",
     "desc": "Envenenamiento LLMNR/NBT-NS para capturar credenciales en red local.",
     "url": "https://github.com/lgandx/Responder/releases",
     "logo": ""},
    {"id": "enum4linux", "name": "enum4linux", "category": "recon", "bin": "enum4linux", "pkg": "enum4linux",
     "desc": "Enumeración de información de sistemas Windows/Samba (SMB).",
     "url": "https://github.com/CiscoCXSecurity/enum4linux",
     "logo": ""},
    {"id": "dnsenum", "name": "dnsenum", "category": "recon", "bin": "dnsenum", "pkg": "dnsenum",
     "desc": "Enumeración de DNS: registros, subdominios y transferencias de zona.",
     "url": "https://github.com/SparrowOchon/dnsenum2",
     "logo": ""},
    {"id": "aircrack", "name": "Aircrack-ng", "category": "wireless", "bin": "aircrack-ng", "pkg": "aircrack-ng",
     "desc": "Suite para auditoría de redes WiFi: captura y crackeo de claves.",
     "url": "https://www.aircrack-ng.org/downloads.html",
     "logo": "https://www.aircrack-ng.org/resources/aircrack-ng-logo.png"},
    {"id": "burpsuite", "name": "Burp Suite", "category": "web", "bin": "burpsuite", "pkg": "burpsuite",
     "desc": "Proxy de interceptación y suite para auditoría de aplicaciones web.",
     "url": "https://portswigger.net/burp/communitydownload",
     "logo": ""},
    {"id": "wpscan", "name": "WPScan", "category": "web", "bin": "wpscan", "pkg": "wpscan",
     "desc": "Escáner de vulnerabilidades específico para sitios WordPress.",
     "url": "https://github.com/wpscanteam/wpscan/releases",
     "logo": ""},
    {"id": "crackmapexec", "name": "CrackMapExec", "category": "exploitation", "bin": "crackmapexec", "pkg": "crackmapexec",
     "desc": "Post-explotación y movimiento lateral en redes Active Directory.",
     "url": "https://github.com/Porchetta-Industries/CrackMapExec/releases",
     "logo": ""},
    {"id": "impacket", "name": "Impacket", "category": "exploitation", "bin": "impacket-smbserver", "pkg": "impacket-scripts",
     "desc": "Colección de scripts para protocolos de red (SMB, Kerberos, etc.).",
     "url": "https://github.com/fortra/impacket/releases",
     "logo": ""},
    {"id": "bettercap", "name": "Bettercap", "category": "network", "bin": "bettercap", "pkg": "bettercap",
     "desc": "Framework para ataques MITM y reconocimiento de redes.",
     "url": "https://github.com/bettercap/bettercap/releases",
     "logo": ""},
    {"id": "feroxbuster", "name": "Feroxbuster", "category": "web", "bin": "feroxbuster", "pkg": "feroxbuster",
     "desc": "Fuerza bruta de contenido web recursivo, escrito en Rust (rápido).",
     "url": "https://github.com/epi052/feroxbuster/releases",
     "logo": ""},
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
                        else f"No se pudo instalar {tool['name']} vía apt. "
                             f"Descárgala de la fuente oficial: {tool['url']}"),
            "installed": is_installed(tool["bin"]),
            "url": tool["url"],
            "output": (proc.stdout + proc.stderr)[-1500:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "La instalación tardó demasiado y se canceló."}
    except Exception as e:
        return {"ok": False, "error": str(e), "url": tool["url"]}
