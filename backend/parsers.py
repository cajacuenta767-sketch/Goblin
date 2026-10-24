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


def parse_nmap(output_or_path: str) -> str:
    text = _read(output_or_path)
    host = ""
    hm = re.search(r"Nmap scan report for\s+(\S+)", text)
    if hm:
        host = hm.group(1)
    ports = []
    for line in text.splitlines():
        m = _PORT_RE.match(line.strip())
        if m:
            port, proto, _state, service, version = m.groups()
            ports.append({"port": port, "proto": proto, "service": service,
                          "version": version.strip()})
    if not ports:
        return "No se encontraron puertos abiertos en la salida de nmap."
    lines = [f"Escaneo nmap de {host or '(host desconocido)'} — {len(ports)} puertos abiertos:"]
    for p in ports:
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
