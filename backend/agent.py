"""
Agente GOBLIN: mantiene la conversación, llama al modelo (DeepHat vía Ollama),
ejecuta herramientas y gestiona las aprobaciones.

Diseño del bucle:
- El modelo responde texto o pide herramientas (tool_calls).
- Las herramientas sin aprobación se ejecutan solas.
- Las que requieren aprobación PAUSAN el bucle y devuelven {"type": "approval"}.
  El frontend muestra la caja de aprobación; al responder, se llama a approve().
- Hay un tope de pasos (MAX_STEPS) para evitar bucles infinitos de un modelo 7B.
"""
import config
from ollama import Client
from tools import SCHEMAS, NEEDS_APPROVAL, run_tool

client = Client(host=config.OLLAMA_HOST)

SYSTEM_PROMPT = (
    "Eres GOBLIN, un asistente de ciberseguridad y pentesting que trabaja dentro de la "
    "PC del usuario (Parrot OS). Tienes herramientas para crear, leer, mover, copiar y "
    "borrar archivos y carpetas, buscar texto, ver el disco y ejecutar comandos de shell. "
    "Trabajas con metodología: reconocimiento, enumeración, explotación, post-explotación "
    "y reporte. Antes de acciones destructivas (borrar, sobrescribir, comandos peligrosos), "
    "explica en una frase qué vas a hacer y por qué. Usa SIEMPRE las herramientas para "
    "actuar sobre el sistema en lugar de solo describir los comandos. Responde en el idioma "
    "del usuario (español). Recuerda operar solo sobre objetivos con autorización."
)

# sesiones[session_id] = {"messages": [...], "queue": [tool_calls pendientes], "model": str}
sessions: dict[str, dict] = {}


def get_session(sid: str, model: str | None = None) -> dict:
    if sid not in sessions:
        sessions[sid] = {
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
            "queue": [],
            "steps": 0,
        }
    if model:
        sessions[sid]["model"] = model
    sessions[sid].setdefault("model", config.DEFAULT_MODEL)
    return sessions[sid]


def _call_model(s: dict):
    return client.chat(
        model=s["model"],
        messages=s["messages"],
        tools=SCHEMAS,
        options={"num_ctx": config.NUM_CTX},
        keep_alive=config.KEEP_ALIVE,
    )


def _exec(call) -> dict:
    name = call.function.name
    args = dict(call.function.arguments or {})
    result = run_tool(name, args)
    return {"name": name, "args": args, "result": result}


def _step(s: dict) -> dict:
    """Avanza el agente hasta texto final, una aprobación pendiente, o el tope de pasos."""
    while True:
        # 1) ¿Hay herramientas en cola por ejecutar?
        if s["queue"]:
            call = s["queue"][0]
            name = call.function.name
            if name in NEEDS_APPROVAL:
                return {
                    "type": "approval",
                    "tool": name,
                    "args": dict(call.function.arguments or {}),
                    "model": s["model"],
                }
            # Herramienta segura: ejecutar sin preguntar
            s["queue"].pop(0)
            done = _exec(call)
            s["messages"].append({"role": "tool", "content": done["result"], "tool_name": name})
            continue

        # 2) Tope de pasos (anti-bucle)
        s["steps"] += 1
        if s["steps"] > config.MAX_STEPS:
            s["steps"] = 0
            return {"type": "text", "content": "[GOBLIN se detuvo: se alcanzó el tope de pasos. "
                                               "Pídeme que continúe si hace falta.]",
                    "model": s["model"]}

        # 3) Preguntar al modelo
        try:
            resp = _call_model(s)
        except Exception as e:
            return {"type": "error", "content": f"Error al contactar el modelo ({s['model']}): {e}. "
                                               f"¿Está Ollama corriendo y el modelo descargado?"}
        msg = resp.message
        s["messages"].append(msg)

        if not msg.tool_calls:
            s["steps"] = 0
            return {"type": "text", "content": msg.content or "", "model": s["model"]}
        s["queue"] = list(msg.tool_calls)


def user_message(sid: str, text: str, model: str | None = None) -> dict:
    s = get_session(sid, model)
    s["messages"].append({"role": "user", "content": text})
    s["steps"] = 0
    return _step(s)


def approve(sid: str, approved: bool) -> dict:
    s = get_session(sid)
    if not s["queue"]:
        return {"type": "text", "content": "No hay acciones pendientes de aprobación.",
                "model": s["model"]}
    call = s["queue"].pop(0)
    name = call.function.name
    if approved:
        done = _exec(call)
        result = done["result"]
    else:
        result = "El usuario DENEGÓ esta acción. No la ejecutes; propón una alternativa si aplica."
    s["messages"].append({"role": "tool", "content": result, "tool_name": name})
    return _step(s)


def reset_session(sid: str) -> None:
    sessions.pop(sid, None)
