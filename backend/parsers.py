"""
Parsers de salida de herramientas de pentest (Spec 017).
Convierten la salida cruda de nmap/nikto en datos estructurados que la IA usa para
registrar hallazgos. Aceptan texto pegado o una ruta a un archivo (-oN).
"""
import re
from pathlib import Path

import config


def _read(output_or_path: str) -> str:
    """Si parece una ruta a un archivo existente, lee su contenido; si no, usa el texto."""
    s = output_or_path.strip()
    if "\n" not in s and len(s) < 300:
        p = Path(s).expanduser()
        if not p.is_absolute():
            p = config.WORKSPACE / s
        if p.is_file():
            return p.read_text(encoding="utf-8", errors="replace")
    return output_or_path


# Línea de puerto de nmap:  22/tcp   open  ssh     OpenSSH 8.2p1
_PORT_RE = re.compile(r"^(\d+)/(tcp|udp)\s+(open|open\|filtered)\s+(\S+)\s*(.*)$")
_XML_START = ("<?xml", "<nmaprun")


def _nmap_xml(text: str) -> list[dict]:
    """Puertos de un XML de nmap (-oX). Rechaza entidades para no abrir ataques de expansión."""
    import xml.etree.ElementTree as ET
    if "<!ENTITY" in text:
        return []
    ini = min((text.find(m) for m in _XML_START if m in text), default=-1)
    fin = text.rfind("</nmaprun>")
    if ini < 0 or fin < 0:
        return []
    try:
        root = ET.fromstring(text[ini:fin + len("</nmaprun>")])
    except ET.ParseError:
        return []
    records = []
    for host in root.iter("host"):
        addr = host.find("address[@addrtype='ipv4']")
        if addr is None:
            addr = host.find("address")
        if addr is None:
            continue
        ip = addr.get("addr", "")
        for port in host.iter("port"):
            st = port.find("state")
            if st is None or st.get("state") != "open":
                continue
            svc = port.find("service")
            version = ""
            if svc is not None:
                version = " ".join(x for x in (svc.get("product"), svc.get("version"), svc.get("extrainfo")) if x)
            records.append({
                "host": ip, "port": port.get("portid", ""), "proto": port.get("protocol", "tcp"),
                "state": "open", "service": svc.get("name", "") if svc is not None else "",
                "version": version,
            })
    return records


def _nmap_text(text: str) -> list[dict]:
    """Puertos de la salida de texto de nmap (-oN o consola)."""
    host = ""
    hm = re.search(r"Nmap scan report for\s+(?:.*\()?([\w.:-]+)\)?", text)
    if hm:
        host = hm.group(1)
    records = []
    for line in text.splitlines():
        m = _PORT_RE.match(line.strip())
        if m:
            port, proto, _state, service, version = m.groups()
            records.append({"host": host, "port": port, "proto": proto, "state": "open",
                            "service": service, "version": version.strip()})
    return records


def nmap_records(output_or_path: str) -> list[dict]:
    """Puertos abiertos de nmap como registros {host, port, proto, service, version} (Spec 036, RF7)."""
    text = _read(output_or_path)
    if any(m in text for m in _XML_START):
        return _nmap_xml(text)
    return _nmap_text(text)


def parse_nmap(output_or_path: str) -> str:
    records = nmap_records(output_or_path)
    if not records:
        return "No se encontraron puertos abiertos en la salida de nmap."
    host = records[0]["host"] or "(host desconocido)"
    lines = [f"Escaneo nmap de {host} — {len(records)} puertos abiertos:"]
    for p in records:
        v = f" · {p['version']}" if p["version"] else ""
        lines.append(f"  {p['port']}/{p['proto']}  {p['service']}{v}")
    lines.append("\nRevisa cada servicio/versión y registra con add_finding lo que sea relevante.")
    return "\n".join(lines)


def parse_nikto(output_or_path: str) -> str:
    text = _read(output_or_path)
    # Nikto marca hallazgos con '+ '
    findings = [ln.strip()[2:].strip() for ln in text.splitlines()
                if ln.strip().startswith("+ ") and ":" in ln]
    # filtrar líneas de cabecera típicas
    findings = [f for f in findings if not f.lower().startswith(("target", "start time",
                "server:", "end time", "host(s) tested"))]
    if not findings:
        return "No se encontraron hallazgos en la salida de nikto."
    lines = [f"Escaneo nikto — {len(findings)} observaciones:"]
    for f in findings[:50]:
        lines.append(f"  • {f[:200]}")
    lines.append("\nRegistra con add_finding las que sean vulnerabilidades reales.")
    return "\n".join(lines)
