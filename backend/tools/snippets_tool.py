"""Herramienta para que la IA acceda a la biblioteca de snippets de pentest."""
import snippets


def get_snippet(category: str = "") -> str:
    return snippets.get_snippet(category)
