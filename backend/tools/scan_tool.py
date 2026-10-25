"""Herramientas para parsear salidas de escaneos (Spec 017, Spec 036 RF7)."""
import db
import parsers
from . import pentest as pt


def record_nmap(sid: str, output: str) -> int:
    """Guarda en la base los puertos abiertos de una salida de nmap. Devuelve cuántos guardó."""
    if not sid:
        return 0
    records = [r for r in parsers.nmap_records(output) if r.get("host")]
    if not records:
        return 0
    return db.upsert_hosts(sid, records)


def parse_nmap(output: str) -> str:
    texto = parsers.parse_nmap(output)
    try:
        record_nmap(pt.current_sid(), output)
    except Exception:
        pass   # el parseo sigue funcionando aunque la base falle
    return texto


def parse_nikto(output: str) -> str:
    return parsers.parse_nikto(output)
