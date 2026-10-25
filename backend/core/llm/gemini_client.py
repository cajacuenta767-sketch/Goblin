"""
Cliente de Gemini para el router híbrido (Specs 008 y 044).

Usa el SDK oficial google-genai (google-generativeai está legado desde nov-2025).
Traduce las herramientas de GOBLIN a function declarations de Gemini.
Si la librería no está instalada, no hay API key o Gemini no devuelve texto ni
herramientas, lanza RuntimeError y el agente cae a DeepHat (local).

Devuelve un objeto con la misma forma mínima que usa el agente:
  .message.content     -> texto de la respuesta
  .message.tool_calls  -> lista de llamadas a herramientas (o None)
"""
import config


class _ToolCallFn:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _ToolCall:
    def __init__(self, name, arguments):
        self.function = _ToolCallFn(name, arguments)


class _Message:
    def __init__(self, content, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls
        self.role = "assistant"


class _Response:
    def __init__(self, message):
        self.message = message


def available() -> bool:
    if not config.GEMINI_API_KEY:
        return False
    try:
        import google.genai  # noqa: F401
        return True
    except ImportError:
        return False


def _client():
    """Cliente de google-genai. Las pruebas lo sustituyen por uno simulado."""
    from google import genai
    return genai.Client(api_key=config.GEMINI_API_KEY)


def _to_gemini_tools(schemas):
    """Convierte los schemas (formato Ollama) a Tool de google-genai."""
    from google.genai import types
    decls = []
    for s in schemas or []:
        fn = s["function"]
        decls.append(types.FunctionDeclaration(
            name=fn["name"],
            description=fn.get("description", ""),
            parameters_json_schema=fn.get("parameters") or {"type": "object", "properties": {}},
        ))
    # Sin herramientas permitidas en este turno (Spec 033): no se declara ninguna.
    return [types.Tool(function_declarations=decls)] if decls else None


def _convertir(messages):
    """Separa el system prompt y traduce el historial al formato de google-genai."""
    from google.genai import types
    system = ""
    contents = []
    for m in messages:
        role = m.get("role") if isinstance(m, dict) else getattr(m, "role", "user")
        content = (m.get("content") if isinstance(m, dict) else getattr(m, "content", "")) or ""
        if role == "system":
            system += content + "\n"
            continue
        if not content.strip():
            continue                      # Gemini rechaza partes vacías
        if role == "user":
            contents.append(types.Content(role="user", parts=[types.Part(text=content)]))
        elif role in ("assistant", "tool"):
            contents.append(types.Content(role="model", parts=[types.Part(text=content)]))
    return system.strip() or None, contents


def chat(messages, schemas):
    """Envía la conversación a Gemini y devuelve una respuesta con la forma del agente."""
    if not available():
        raise RuntimeError("Gemini no disponible (falta API key o la librería google-genai).")

    from google.genai import types
    system, contents = _convertir(messages)
    cfg = types.GenerateContentConfig(
        system_instruction=system,
        tools=_to_gemini_tools(schemas),
    )
    resp = _client().models.generate_content(
        model=config.GEMINI_MODEL, contents=contents, config=cfg,
    )

    motivo = getattr(getattr(resp, "prompt_feedback", None), "block_reason", None)
    if motivo:
        raise RuntimeError(f"Gemini bloqueó la petición: {motivo}")

    texto, llamadas = "", []
    candidatos = getattr(resp, "candidates", None) or []
    partes = []
    if candidatos and getattr(candidatos[0], "content", None):
        partes = candidatos[0].content.parts or []
    for part in partes:
        if getattr(part, "thought", False):
            continue                      # razonamiento interno: no se muestra
        if getattr(part, "text", None):
            texto += part.text
        fc = getattr(part, "function_call", None)
        if fc and fc.name:
            llamadas.append(_ToolCall(fc.name, dict(fc.args) if fc.args else {}))

    if not texto and not llamadas:
        raise RuntimeError("Gemini no devolvió respuesta utilizable.")
    return _Response(_Message(texto, llamadas or None))
