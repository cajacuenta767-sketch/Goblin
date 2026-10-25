"""
Cliente de Gemini para el router híbrido (Specs 008, 044 y 045).

Usa el SDK oficial google-genai (google-generativeai está legado desde nov-2025).
Traduce las herramientas de GOBLIN a function declarations de Gemini y el historial a
llamadas y respuestas de función (Spec 045, RF3).
Si la librería no está instalada, no hay API key, Gemini bloquea la respuesta o no devuelve
texto ni herramientas, lanza RuntimeError y el agente repite el paso con DeepHat (local).

Devuelve un objeto con la misma forma mínima que usa el agente:
  .message.content     -> texto de la respuesta
  .message.tool_calls  -> lista de llamadas a herramientas (o None)
"""
import config
import historial

# Motivos de finish_reason que significan respuesta bloqueada (Spec 045, RF2).
_FIN_BLOQUEO = {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII"}


class _ToolCallFn:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _ToolCall:
    def __init__(self, name, arguments, part=None):
        self.function = _ToolCallFn(name, arguments)
        # Parte original de Gemini: lleva la firma de pensamiento que la API pide en la siguiente petición.
        self.part = part


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


def _nombre_enum(valor) -> str:
    """Nombre corto de un enum del SDK (FinishReason.SAFETY -> SAFETY)."""
    if valor is None:
        return ""
    return (getattr(valor, "name", None) or str(valor)).split(".")[-1]


def _convertir(messages):
    """Separa el system prompt y traduce el historial a contenidos de google-genai (Spec 045, RF3).

    - Texto del usuario y del modelo -> parts de texto.
    - Llamadas a herramientas del modelo -> function_call (o la parte original con su firma).
    - Resultados de herramientas -> function_response con el nombre de la herramienta.
    """
    from google.genai import types
    system = ""
    contents = []
    for m in messages:
        role = historial.rol(m)
        texto = historial.contenido(m)
        if role == "system":
            system += texto + "\n"
            continue
        if role == "tool":
            nombre = (m.get("tool_name") if isinstance(m, dict) else getattr(m, "tool_name", None)) \
                or "herramienta"
            parte = types.Part.from_function_response(name=nombre, response={"result": texto})
            ultimo = contents[-1] if contents else None
            if ultimo is not None and ultimo.role == "user" and ultimo.parts \
                    and ultimo.parts[0].function_response:
                ultimo.parts.append(parte)          # varias respuestas seguidas: mismo turno
            else:
                contents.append(types.Content(role="user", parts=[parte]))
            continue
        if role == "assistant":
            partes = []
            if texto.strip():
                partes.append(types.Part(text=texto))
            for nombre, args, original in historial.llamadas(m):
                if original is not None:
                    partes.append(original)         # conserva la firma de pensamiento
                else:
                    partes.append(types.Part(function_call=types.FunctionCall(
                        name=nombre, args=dict(args) if isinstance(args, dict) else {})))
            if partes:
                contents.append(types.Content(role="model", parts=partes))
            continue
        if role == "user" and texto.strip():            # Gemini rechaza partes vacías
            contents.append(types.Content(role="user", parts=[types.Part(text=texto)]))
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

    motivo = _nombre_enum(getattr(getattr(resp, "prompt_feedback", None), "block_reason", None))
    if motivo:
        raise RuntimeError(f"Gemini bloqueó la petición: {motivo}")

    candidatos = getattr(resp, "candidates", None) or []
    candidato = candidatos[0] if candidatos else None
    fin = _nombre_enum(getattr(candidato, "finish_reason", None))
    if fin in _FIN_BLOQUEO:
        raise RuntimeError(f"Gemini bloqueó la respuesta: {fin}")

    texto, llamadas = "", []
    partes = []
    if candidato is not None and getattr(candidato, "content", None):
        partes = candidato.content.parts or []
    for part in partes:
        if getattr(part, "thought", False):
            continue                      # razonamiento interno: no se muestra
        if getattr(part, "text", None):
            texto += part.text
        fc = getattr(part, "function_call", None)
        if fc and fc.name:
            llamadas.append(_ToolCall(fc.name, dict(fc.args) if fc.args else {}, part=part))

    if not texto and not llamadas:
        raise RuntimeError("Gemini no devolvió respuesta utilizable.")
    return _Response(_Message(texto, llamadas or None))
