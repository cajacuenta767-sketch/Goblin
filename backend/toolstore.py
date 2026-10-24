"""
Marketplace de herramientas de ciberseguridad (Spec 016 / 020 / 026).

Catálogo de herramientas de pentest con:
  - enlace a su fuente oficial (web o GitHub releases) para la última versión,
  - logo oficial cargado en vivo desde su web (no incrustado, para no infringir marcas),
  - instalación vía apt, ejecutada en la TERMINAL del usuario (Spec 026): sudo le pide su
    contraseña allí. GOBLIN nunca recibe ni guarda la contraseña.

Seguridad: el comando y las URLs salen SOLO del catálogo estático. Los IDs que llegan de la
UI se validan contra el catálogo; los nombres de paquete se validan con una expresión regular
antes de formar cualquier comando.
"""
import os
import re
import shutil
import subprocess

_PKG_RE = re.compile(r"^[a-z0-9][a-z0-9.+-]*$")
_BIN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")


def _command(pkg: str) -> str:
    """Comando que se escribe en la terminal. Refresca la lista de paquetes y luego instala."""
    return f"sudo apt-get update && sudo apt-get install -y {pkg}"


def _tool(tid, name, category, binary, pkg, desc, url, logo="", verified=True, path=None):
    """Construye una entrada del catálogo validando sus campos."""
    if pkg is not None and not _PKG_RE.match(pkg):
        raise ValueError(f"Nombre de paquete no válido: {pkg!r}")
    if binary is not None and not _BIN_RE.match(binary):
        raise ValueError(f"Nombre de binario no válido: {binary!r}")
    if not url.startswith("https://"):
        raise ValueError(f"La URL de {tid} debe ser https: {url!r}")
    return {
        "id": tid, "name": name, "category": category,
        "bin": binary, "path": path, "pkg": pkg,
        "desc": desc, "url": url, "logo": logo,
        # verified: el nombre del paquete se comprobó descargando el .deb en Ubuntu 24.04.
        "verified": verified,
        # command: lo que se escribe en la terminal; None si no hay paquete apt.
        "command": _command(pkg) if pkg else None,
        # remove_command: lo que se muestra al desinstalar (Spec 027).
        "remove_command": f"sudo apt-get remove -y {pkg}" if pkg else None,
    }


CATEGORIES = ["recon", "osint", "web", "passwords", "exploitation",
              "post", "network", "wireless", "forensics", "reverse"]

CATALOG = [
    # ---------- Recon ----------
    _tool("nmap", "Nmap", "recon", "nmap", "nmap",
          "Escáner de puertos y servicios. La base de todo reconocimiento de red.",
          "https://nmap.org/download.html", "https://nmap.org/images/nmap-logo-256x256.png"),
    _tool("masscan", "Masscan", "recon", "masscan", "masscan",
          "Escaneo de puertos masivo, muy rápido, para rangos de Internet o redes grandes.",
          "https://github.com/robertdavidgraham/masscan/releases"),
    _tool("dnsenum", "dnsenum", "recon", "dnsenum", "dnsenum",
          "Enumeración de DNS: registros, subdominios y transferencias de zona.",
          "https://github.com/fwaeytens/dnsenum"),
    _tool("dnsrecon", "dnsrecon", "recon", "dnsrecon", "dnsrecon",
          "Reconocimiento DNS: registros, transferencias de zona y fuerza bruta de subdominios.",
          "https://github.com/darkoperator/dnsrecon/releases"),
    _tool("fierce", "Fierce", "recon", "fierce", "fierce",
          "Localiza dominios y rangos IP cercanos a un objetivo mediante consultas DNS.",
          "https://github.com/mschwager/fierce/releases"),
    _tool("enum4linux", "enum4linux", "recon", "enum4linux", "enum4linux",
          "Enumeración de información de sistemas Windows/Samba (SMB).",
          "https://github.com/CiscoCXSecurity/enum4linux", verified=False),
    _tool("netdiscover", "Netdiscover", "recon", "netdiscover", "netdiscover",
          "Descubre hosts activos en la red local mediante ARP.",
          "https://github.com/alexxy/netdiscover/releases"),
    _tool("arp-scan", "arp-scan", "recon", "arp-scan", "arp-scan",
          "Escaneo ARP de la red local: lista hosts y su fabricante.",
          "https://github.com/royhills/arp-scan/releases"),
    _tool("nbtscan", "nbtscan", "recon", "nbtscan", "nbtscan",
          "Escaneo de nombres NetBIOS en redes Windows.",
          "https://sourceforge.net/projects/nbtscan/"),

    # ---------- OSINT ----------
    _tool("theharvester", "theHarvester", "osint", "theHarvester", "theharvester",
          "Recopila correos, subdominios y hosts de fuentes públicas sobre un dominio.",
          "https://github.com/laramies/theHarvester/releases", verified=False),
    _tool("recon-ng", "Recon-ng", "osint", "recon-ng", "recon-ng",
          "Framework de reconocimiento OSINT con módulos por fuente.",
          "https://github.com/lanmaster53/recon-ng/releases", verified=False),
    _tool("amass", "Amass", "osint", "amass", "amass",
          "Descubrimiento y mapeo de la superficie de ataque (subdominios, ASN, rangos).",
          "https://github.com/owasp-amass/amass/releases", verified=False),

    # ---------- Web ----------
    _tool("sqlmap", "SQLMap", "web", "sqlmap", "sqlmap",
          "Detección y explotación automática de inyecciones SQL.",
          "https://github.com/sqlmapproject/sqlmap/releases",
          "https://raw.githubusercontent.com/sqlmapproject/sqlmap/master/doc/logo.png"),
    _tool("gobuster", "Gobuster", "web", "gobuster", "gobuster",
          "Fuerza bruta de directorios, DNS y subdominios en servidores web.",
          "https://github.com/OJ/gobuster/releases"),
    _tool("ffuf", "ffuf", "web", "ffuf", "ffuf",
          "Fuzzer web rapidísimo para rutas, parámetros y subdominios.",
          "https://github.com/ffuf/ffuf/releases",
          "https://raw.githubusercontent.com/ffuf/ffuf/master/_img/ffuf_run_logo_600.png"),
    _tool("dirb", "DIRB", "web", "dirb", "dirb",
          "Búsqueda de directorios y archivos ocultos en un servidor web.",
          "https://sourceforge.net/projects/dirb/"),
    _tool("dirsearch", "dirsearch", "web", "dirsearch", "dirsearch",
          "Fuerza bruta de rutas web con soporte de extensiones y recursión.",
          "https://github.com/maurosoria/dirsearch/releases"),
    _tool("whatweb", "WhatWeb", "web", "whatweb", "whatweb",
          "Identifica tecnologías, versiones y plugins de una web.",
          "https://github.com/urbanadventurer/WhatWeb/releases"),
    _tool("nikto", "Nikto", "web", "nikto", "nikto",
          "Escáner de vulnerabilidades web: configuraciones y archivos peligrosos.",
          "https://github.com/sullo/nikto/releases"),
    _tool("wfuzz", "Wfuzz", "web", "wfuzz", "wfuzz",
          "Fuzzing de aplicaciones web para encontrar recursos ocultos.",
          "https://github.com/xmendez/wfuzz/releases"),
    _tool("burpsuite", "Burp Suite", "web", "burpsuite", None,
          "Proxy de interceptación y suite para auditoría de aplicaciones web.",
          "https://portswigger.net/burp/communitydownload", verified=False),
    _tool("wpscan", "WPScan", "web", "wpscan", "wpscan",
          "Escáner de vulnerabilidades específico para sitios WordPress.",
          "https://github.com/wpscanteam/wpscan/releases", verified=False),
    _tool("feroxbuster", "Feroxbuster", "web", "feroxbuster", "feroxbuster",
          "Fuerza bruta de contenido web recursivo, escrito en Rust (rápido).",
          "https://github.com/epi052/feroxbuster/releases", verified=False),
    _tool("commix", "Commix", "web", "commix", "commix",
          "Detección y explotación de inyección de comandos en aplicaciones web.",
          "https://github.com/commixproject/commix/releases", verified=False),
    _tool("zaproxy", "OWASP ZAP", "web", "zaproxy", "zaproxy",
          "Proxy de análisis de seguridad web de código abierto (alternativa a Burp).",
          "https://www.zaproxy.org/download/", verified=False),
    _tool("seclists", "SecLists", "web", None, "seclists",
          "Colección de listas de palabras: usuarios, contraseñas, rutas y payloads.",
          "https://github.com/danielmiessler/SecLists/releases",
          verified=False, path="/usr/share/seclists"),

    # ---------- Contraseñas ----------
    _tool("hydra", "THC-Hydra", "passwords", "hydra", "hydra",
          "Fuerza bruta de credenciales en SSH, FTP, HTTP y decenas de protocolos.",
          "https://github.com/vanhauser-thc/thc-hydra/releases"),
    _tool("john", "John the Ripper", "passwords", "john", "john",
          "Cracking de hashes de contraseñas, rápido y flexible.",
          "https://www.openwall.com/john/",
          "https://www.openwall.com/john/pics/john-the-ripper.png"),
    _tool("hashcat", "Hashcat", "passwords", "hashcat", "hashcat",
          "Cracking de hashes acelerado. El estándar para romper contraseñas.",
          "https://hashcat.net/hashcat/",
          "https://hashcat.net/misc/example_hashes/hashcat.png"),
    _tool("hashid", "hashID", "passwords", "hashid", "hashid",
          "Identifica el tipo de hash a partir de su formato.",
          "https://github.com/psypanda/hashID/releases"),
    _tool("crunch", "Crunch", "passwords", "crunch", "crunch",
          "Genera listas de palabras por patrón y longitud.",
          "https://sourceforge.net/projects/crunch-wordlist/"),
    _tool("cewl", "CeWL", "passwords", "cewl", "cewl",
          "Crea listas de palabras a partir del contenido de un sitio web.",
          "https://github.com/digininja/CeWL/releases"),
    _tool("medusa", "Medusa", "passwords", "medusa", "medusa",
          "Fuerza bruta paralela de credenciales en servicios de red.",
          "https://github.com/jmk-foofus/medusa/releases"),
    _tool("patator", "Patator", "passwords", "patator", "patator",
          "Fuerza bruta modular: un módulo por protocolo o aplicación.",
          "https://github.com/lanjelot/patator/releases"),

    # ---------- Explotación ----------
    _tool("metasploit", "Metasploit Framework", "exploitation", "msfconsole", "metasploit-framework",
          "Framework de explotación: exploits, payloads y post-explotación.",
          "https://github.com/rapid7/metasploit-framework/releases",
          "https://www.metasploit.com/includes/snippets/metasploit/images/metasploit-logo.svg",
          verified=False),
    _tool("impacket", "Impacket", "exploitation", "impacket-smbserver", "impacket-scripts",
          "Colección de scripts para protocolos de red (SMB, Kerberos, etc.).",
          "https://github.com/fortra/impacket/releases", verified=False),
    _tool("beef", "BeEF", "exploitation", "beef-xss", "beef-xss",
          "Framework de explotación de navegadores (XSS) para pruebas controladas.",
          "https://github.com/beefproject/beef/releases", verified=False),
    _tool("set", "SET (Social-Engineer Toolkit)", "exploitation", "setoolkit", "set",
          "Kit de ingeniería social para pruebas de phishing autorizadas.",
          "https://github.com/trustedsec/social-engineer-toolkit/releases", verified=False),
    _tool("exploitdb", "Exploit-DB (searchsploit)", "exploitation", "searchsploit", "exploitdb",
          "Búsqueda offline en la base de datos de exploits públicos.",
          "https://www.exploit-db.com/", verified=False),

    # ---------- Post-explotación ----------
    _tool("crackmapexec", "CrackMapExec", "post", "crackmapexec", "crackmapexec",
          "Post-explotación y movimiento lateral en redes Active Directory.",
          "https://github.com/Porchetta-Industries/CrackMapExec/releases", verified=False),
    _tool("bloodhound", "BloodHound", "post", "bloodhound", "bloodhound",
          "Mapea rutas de ataque en Active Directory a partir de sus relaciones.",
          "https://github.com/SpecterOps/BloodHound/releases", verified=False),
    _tool("smbmap", "smbmap", "post", "smbmap", "smbmap",
          "Enumera permisos y recursos compartidos SMB en una red.",
          "https://github.com/ShawnDEvans/smbmap/releases"),
    _tool("proxychains4", "proxychains-ng", "post", "proxychains4", "proxychains4",
          "Hace que cualquier programa pase por proxies SOCKS/HTTP (pivoting).",
          "https://github.com/rofl0r/proxychains-ng/releases"),
    _tool("tor", "Tor", "post", "tor", "tor",
          "Red de anonimato. Útil para enrutar tráfico de pruebas por Tor.",
          "https://www.torproject.org/download/tor/"),
    _tool("socat", "Socat", "post", "socat", "socat",
          "Relés y túneles bidireccionales entre cualquier par de canales.",
          "https://www.dest-unreach.org/socat/"),

    # ---------- Red ----------
    _tool("wireshark", "Wireshark", "network", "wireshark", "wireshark",
          "Analizador de tráfico de red. Inspecciona paquetes al detalle.",
          "https://www.wireshark.org/download.html",
          "https://www.wireshark.org/assets/icons/wireshark-fin@2x.png"),
    _tool("tcpdump", "tcpdump", "network", "tcpdump", "tcpdump",
          "Captura de paquetes por línea de comandos, ligero y potente.",
          "https://www.tcpdump.org/", "https://www.tcpdump.org/tcpdump-power.gif"),
    _tool("netcat", "Netcat", "network", "nc", "netcat-traditional",
          "La navaja suiza de las redes: conexiones, listeners y transferencias.",
          "https://nmap.org/ncat/"),
    _tool("bettercap", "Bettercap", "network", "bettercap", "bettercap",
          "Framework para ataques MITM y reconocimiento de redes.",
          "https://github.com/bettercap/bettercap/releases"),
    _tool("ettercap", "Ettercap", "network", "ettercap", "ettercap-text-only",
          "Ataques MITM en redes locales (ARP poisoning) en modo texto.",
          "https://github.com/Ettercap/ettercap/releases"),
    _tool("hping3", "hping3", "network", "hping3", "hping3",
          "Genera y analiza paquetes TCP/IP a medida. Pruebas de firewall.",
          "https://github.com/antirez/hping"),
    _tool("responder", "Responder", "network", "responder", "responder",
          "Envenenamiento LLMNR/NBT-NS para capturar credenciales en red local.",
          "https://github.com/lgandx/Responder/releases", verified=False),
    _tool("sslscan", "SSLScan", "network", "sslscan", "sslscan",
          "Analiza la configuración TLS/SSL de un servicio: cifrados y certificados.",
          "https://github.com/rbsec/sslscan/releases"),
    _tool("ssh-audit", "ssh-audit", "network", "ssh-audit", "ssh-audit",
          "Audita la configuración de servidores SSH: algoritmos y versiones débiles.",
          "https://github.com/jtesta/ssh-audit/releases"),
    _tool("smbclient", "smbclient", "network", "smbclient", "smbclient",
          "Cliente de línea de comandos para recursos compartidos SMB/Windows.",
          "https://www.samba.org/samba/download/"),
    _tool("onesixtyone", "onesixtyone", "network", "onesixtyone", "onesixtyone",
          "Fuerza bruta rápida de community strings SNMP.",
          "https://github.com/trailofbits/onesixtyone/releases"),
    _tool("snmp", "Net-SNMP (snmpwalk)", "network", "snmpwalk", "snmp",
          "Consulta y recorre árboles MIB de dispositivos SNMP.",
          "https://www.net-snmp.org/download.html"),
    _tool("ldap-utils", "LDAP utils", "network", "ldapsearch", "ldap-utils",
          "Consultas LDAP desde la terminal (ldapsearch, ldapwhoami, etc.).",
          "https://www.openldap.org/software/download/"),

    # ---------- WiFi ----------
    _tool("aircrack", "Aircrack-ng", "wireless", "aircrack-ng", "aircrack-ng",
          "Suite para auditoría de redes WiFi: captura y crackeo de claves.",
          "https://www.aircrack-ng.org/downloads.html",
          "https://www.aircrack-ng.org/resources/aircrack-ng-logo.png"),
    _tool("wifite", "Wifite", "wireless", "wifite", "wifite",
          "Automatiza ataques WiFi de auditoría contra redes cercanas.",
          "https://github.com/kimocoder/wifite2/releases"),
    _tool("reaver", "Reaver", "wireless", "reaver", "reaver",
          "Ataque de fuerza bruta contra el PIN WPS de routers.",
          "https://github.com/t6x/reaver-wps-fork-t6x/releases"),

    # ---------- Forense ----------
    _tool("binwalk", "Binwalk", "forensics", "binwalk", "binwalk",
          "Busca y extrae archivos embebidos en imágenes de firmware y binarios.",
          "https://github.com/ReFirmLabs/binwalk/releases"),
    _tool("foremost", "Foremost", "forensics", "foremost", "foremost",
          "Recuperación de archivos borrados por su cabecera en imágenes de disco.",
          "https://sourceforge.net/projects/foremost/"),
    _tool("steghide", "Steghide", "forensics", "steghide", "steghide",
          "Oculta y extrae datos en imágenes y audio (esteganografía).",
          "https://sourceforge.net/projects/steghide/"),
    _tool("exiftool", "ExifTool", "forensics", "exiftool", "libimage-exiftool-perl",
          "Lee y edita metadatos de imágenes, PDFs, audio y vídeo.",
          "https://exiftool.org/"),

    # ---------- Ingeniería inversa ----------
    _tool("radare2", "radare2", "reverse", "r2", "radare2",
          "Framework de análisis de binarios: desensamblado, depuración y parcheo.",
          "https://github.com/radareorg/radare2/releases"),
    _tool("gdb", "GDB", "reverse", "gdb", "gdb",
          "Depurador de GNU para inspeccionar programas en ejecución.",
          "https://www.sourceware.org/gdb/"),
]

_BY_ID = {t["id"]: t for t in CATALOG}


def _find(tool_id: str) -> dict | None:
    """Busca una herramienta del catálogo por ID. Nunca acepta datos de fuera del catálogo."""
    return _BY_ID.get(tool_id)


def is_installed(tool: dict) -> bool:
    """Detecta si la herramienta está: por binario en el PATH o por ruta (Spec 026)."""
    if tool.get("path"):
        return os.path.exists(tool["path"])
    if tool.get("bin"):
        return shutil.which(tool["bin"]) is not None
    return False


def catalog() -> list[dict]:
    """Devuelve el catálogo con el estado de instalación de cada herramienta."""
    return [{**t, "installed": is_installed(t)} for t in CATALOG]


def install(tool_id: str) -> dict:
    """Prepara la instalación (Spec 026). NO ejecuta apt: devuelve el comando para la terminal.

    La UI lo escribe en la terminal integrada; sudo pide la contraseña allí, en el prompt real.
    """
    tool = _find(tool_id)
    if not tool:
        return {"ok": False, "error": f"Herramienta desconocida: {tool_id}"}
    if is_installed(tool):
        return {"ok": True, "installed": True, "message": f"{tool['name']} ya está instalada."}
    if not tool["command"]:
        return {"ok": False, "installed": False, "url": tool["url"],
                "error": f"{tool['name']} no se instala con apt. Descárgala de su web oficial: {tool['url']}"}
    return {"ok": True, "installed": False, "command": tool["command"], "name": tool["name"]}


def open_url(tool_id: str) -> dict:
    """Abre la web oficial de una herramienta en el navegador del sistema (Spec 026).

    Solo abre URLs del catálogo (https). Usa xdg-open sin shell y separado de este proceso.
    """
    tool = _find(tool_id)
    if not tool:
        return {"ok": False, "error": f"Herramienta desconocida: {tool_id}"}
    url = tool["url"]
    if not url.startswith("https://"):
        return {"ok": False, "error": "Solo se abren enlaces https del catálogo.", "url": url}
    opener = shutil.which("xdg-open")
    if not opener:
        return {"ok": False, "url": url,
                "error": f"No hay xdg-open en este equipo. Abre este enlace a mano: {url}"}
    try:
        subprocess.Popen([opener, url], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError as e:
        return {"ok": False, "url": url, "error": f"No se pudo abrir el navegador: {e}. Enlace: {url}"}
    return {"ok": True, "url": url}
