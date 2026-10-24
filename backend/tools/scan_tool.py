"""Herramientas para parsear salidas de escaneos (Spec 017)."""
import parsers


def parse_nmap(output: str) -> str:
    return parsers.parse_nmap(output)


def parse_nikto(output: str) -> str:
    return parsers.parse_nikto(output)
