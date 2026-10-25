"""Acceso uniforme a los mensajes del historial (Spec 045).

El historial mezcla dicts (Ollama y herramientas), objetos de Ollama (DeepHat) y objetos propios
del cliente de Gemini. Estas funciones leen los tres formatos igual.
"""


def rol(m):
    return m.get("role") if isinstance(m, dict) else getattr(m, "role", None)


def contenido(m) -> str:
    valor = m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
    return valor or ""


def llamadas(m) -> list:
    """[(nombre, argumentos, parte_original_o_None)] de las llamadas a herramientas del mensaje.

    `parte_original` es el objeto Part de Gemini que trae la firma de pensamiento; solo existe
    en llamadas que generó Gemini (ver gemini_client._ToolCall).
    """
    crudas = (m.get("tool_calls") if isinstance(m, dict) else getattr(m, "tool_calls", None)) or []
    salida = []
    for c in crudas:
        fn = c.get("function") if isinstance(c, dict) else getattr(c, "function", None)
        if isinstance(fn, dict):
            nombre, args = fn.get("name", ""), fn.get("arguments")
        else:
            nombre, args = getattr(fn, "name", ""), getattr(fn, "arguments", None)
        parte = None if isinstance(c, dict) else getattr(c, "part", None)
        salida.append((nombre or "", args or {}, parte))
    return salida


def texto(m) -> str:
    """Todo el texto que cuenta para la guarda de privacidad: contenido y argumentos de las llamadas."""
    partes = [contenido(m)]
    partes += [str(args) for _, args, _ in llamadas(m)]
    return "\n".join(partes)
