"""
Cliente de Gemini para el router híbrido (Spec 008).
Traduce las herramientas de GOBLIN al formato de function-calling de Gemini.
Si la librería no está instalada o no hay API key, lanza una excepción clara para que
el router caiga a DeepHat (local).

Devuelve un objeto con la misma forma mínima que usa el agente:
  .message.content        -> texto de la respuesta
  .message.tool_calls     -> lista de llamadas a herramientas (o None)
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
        import google.generativeai  # noqa
        return True
    except ImportError:
        return False


def _to_gemini_tools(schemas):
    """Convierte los schemas (formato Ollama) al formato de Gemini."""
    decls = []
    for s in schemas:
        fn = s["function"]
        decls.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "parameters": fn.get("parameters", {"type": "object", "properties": {}}),
        })
    return [{"function_declarations": decls}]


def chat(messages, schemas):
    """Envía la conversación a Gemini y devuelve una respuesta con la forma del agente."""
    if not available():
        raise RuntimeError("Gemini no disponible (falta API key o la librería google-generativeai).")

    import google.generativeai as genai
    genai.configure(api_key=config.GEMINI_API_KEY)

    # Separar system prompt y traducir el historial.
    system = ""
    history = []
    for m in messages:
        role = m.get("role") if isinstance(m, dict) else getattr(m, "role", "user")
        content = m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
        if role == "system":
            system += (content or "") + "\n"
        elif role == "user":
            history.append({"role": "user", "parts": [content or ""]})
        elif role in ("assistant", "tool"):
            history.append({"role": "model", "parts": [content or ""]})

    model = genai.GenerativeModel(
        config.GEMINI_MODEL,
        system_instruction=system or None,
        tools=_to_gemini_tools(schemas),
    )

    resp = model.generate_content(history)

    # Extraer texto y/o tool calls.
    text = ""
    tool_calls = []
    try:
        for part in resp.candidates[0].content.parts:
            if getattr(part, "text", None):
                text += part.text
            fc = getattr(part, "function_call", None)
            if fc and fc.name:
                args = dict(fc.args) if fc.args else {}
                tool_calls.append(_ToolCall(fc.name, args))
    except (IndexError, AttributeError):
        text = getattr(resp, "text", "") or ""

    return _Response(_Message(text, tool_calls or None))
