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
import json
import sys
import os

import config
import db
import router
import approvals
from ollama import Client
from tools import SCHEMAS, NEEDS_APPROVAL, run_tool

# Permite importar el cliente de Gemini desde core/llm/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core", "llm"))

client = Client(host=config.OLLAMA_HOST)

SYSTEM_PROMPT = (
    "Eres GOBLIN, un asistente de ciberseguridad y pentesting que trabaja dentro de la "
    "PC del usuario (Parrot OS). Tienes herramientas para crear, leer, mover, copiar y "
    "borrar archivos y carpetas, buscar texto, ver el disco, ejecutar comandos de shell, "
    "fijar el objetivo (set_target), registrar hallazgos (add_finding) y generar el informe "
    "(generate_report).\n\n"
    "METODOLOGÍA: trabaja por fases — reconocimiento, enumeración, explotación, "
    "post-explotación y reporte. Cuando encuentres algo relevante (puerto abierto con "
    "servicio vulnerable, mala configuración, credencial), REGÍSTRALO con add_finding "
    "indicando la severidad (critical/high/medium/low/info).\n\n"
    "COMANDOS RÁPIDOS que el usuario puede usar:\n"
    "  /target <ip>  → fija el objetivo y crea su estructura de carpetas\n"
    "  /recon        → reconocimiento del objetivo actual (nmap, enumeración de servicios)\n"
    "  /scan         → escaneo de vulnerabilidades\n"
    "  /report       → genera el informe de pentest con los hallazgos\n\n"
    "REGLAS: antes de acciones destructivas (borrar, sobrescribir, comandos peligrosos), "
    "explica en una frase qué harás y por qué. Usa SIEMPRE las herramientas para actuar "
    "sobre el sistema, no solo describas los comandos. Responde en español. "
    "Opera SOLO sobre objetivos con autorización explícita; si no está claro, pregúntalo."
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


def _call_deephat(s: dict):
    """Llama al modelo local (DeepHat) vía Ollama."""
    resp = client.chat(
        model=s["model"],
        messages=s["messages"],
        tools=SCHEMAS,
        options={"num_ctx": config.NUM_CTX},
        keep_alive=config.KEEP_ALIVE,
    )
    resp._goblin_model = "DeepHat"
    return resp


def _call_model(s: dict, sid: str | None = None):
    """Aplica el router híbrido: elige modelo según el modo de la sesión.
    - local  -> DeepHat
    - hybrid -> Gemini primero; si se niega o falla, DeepHat
    - manual -> el modelo que el frontend ya fijó en s["model"] (DeepHat por defecto)
    """
    mode = router.get_mode(sid) if sid else "local"

    if mode == "hybrid" and router.gemini_available():
        try:
            import gemini_client
            resp = gemini_client.chat(s["messages"], SCHEMAS)
            # ¿Gemini se negó? Caer a DeepHat.
            if not resp.message.tool_calls and router.looks_like_refusal(resp.message.content):
                resp = _call_deephat(s)
            else:
                resp._goblin_model = "Gemini"
            return resp
        except Exception:
            # Cualquier fallo de Gemini → respaldo local, sin romper.
            return _call_deephat(s)

    # local, manual, o híbrido sin API key → DeepHat
    return _call_deephat(s)


def _exec(call, sid: str | None = None, approved: bool = True) -> dict:
    name = call.function.name
    args = dict(call.function.arguments or {})
    result = run_tool(name, args)
    # Log de auditoría (Fase 8): qué herramienta se ejecutó, cuándo, resultado.
    if sid:
        try:
            db.log_action(sid, name, json.dumps(args, ensure_ascii=False), result, approved)
        except Exception:
            pass
    return {"name": name, "args": args, "result": result}


def _step(s: dict, sid: str | None = None) -> dict:
    """Avanza el agente hasta texto final, una aprobación pendiente, o el tope de pasos."""
    while True:
        # 1) ¿Hay herramientas en cola por ejecutar?
        if s["queue"]:
            call = s["queue"][0]
            name = call.function.name
            base = name in NEEDS_APPROVAL
            if approvals.needs_approval(sid, name, base):
                return {
                    "type": "approval",
                    "tool": name,
                    "args": dict(call.function.arguments or {}),
                    "model": s["model"],
                }
            # Herramienta segura: ejecutar sin preguntar
            s["queue"].pop(0)
            done = _exec(call, sid, approved=True)
            s["messages"].append({"role": "tool", "content": done["result"], "tool_name": name})
            continue

        # 2) Tope de pasos (anti-bucle)
        s["steps"] += 1
        if s["steps"] > config.MAX_STEPS:
            s["steps"] = 0
            return {"type": "text", "content": "[GOBLIN se detuvo: se alcanzó el tope de pasos. "
                                               "Pídeme que continúe si hace falta.]",
                    "model": s["model"]}

        # 3) Preguntar al modelo (router híbrido decide cuál)
        try:
            resp = _call_model(s, sid)
        except Exception as e:
            return {"type": "error", "content": f"Error al contactar el modelo: {e}. "
                                               f"¿Está Ollama corriendo y el modelo descargado?"}
        msg = resp.message
        used_model = getattr(resp, "_goblin_model", "DeepHat")
        s["messages"].append(msg)

        if not msg.tool_calls:
            s["steps"] = 0
            # Guardar la respuesta final de la IA en la base de datos.
            if sid and (msg.content or ""):
                try:
                    db.add_message(sid, "assistant", msg.content or "", used_model)
                except Exception:
                    pass
            return {"type": "text", "content": msg.content or "", "model": used_model}
        s["queue"] = list(msg.tool_calls)


def user_message(sid: str, text: str, model: str | None = None) -> dict:
    s = get_session(sid, model)
    # Las herramientas de pentest y de terminal usan esta sesión.
    try:
        from tools import pentest
        pentest.set_session(sid)
        import term_session
        term_session.set_session(sid)
    except Exception:
        pass
    s["messages"].append({"role": "user", "content": text})
    s["steps"] = 0
    # Persistencia: asegurar sesión, guardar el mensaje, poner título si es el primero.
    try:
        db.ensure_session(sid, s["model"])
        existing = db.get_messages(sid)
        db.add_message(sid, "user", text, None)
        if not existing:
            db.set_title(sid, text[:60])
    except Exception:
        pass
    return _step(s, sid)


def approve(sid: str, approved: bool) -> dict:
    s = get_session(sid)
    if not s["queue"]:
        return {"type": "text", "content": "No hay acciones pendientes de aprobación.",
                "model": s["model"]}
    call = s["queue"].pop(0)
    name = call.function.name
    if approved:
        done = _exec(call, sid, approved=True)
        result = done["result"]
    else:
        result = "El usuario DENEGÓ esta acción. No la ejecutes; propón una alternativa si aplica."
        try:
            db.log_action(sid, name, json.dumps(dict(call.function.arguments or {}), ensure_ascii=False),
                          result, approved=False)
        except Exception:
            pass
    s["messages"].append({"role": "tool", "content": result, "tool_name": name})
    return _step(s, sid)


def reset_session(sid: str) -> None:
    sessions.pop(sid, None)


def stream_message(sid: str, text: str, model: str | None = None):
    """Versión en streaming (Spec 018). Devuelve un generador de trozos de texto.
    Si la IA pide herramientas, cambia al flujo normal (señala 'tool' y el cliente
    reenvía por /api/chat). Solo hace streaming real del texto final.
    """
    s = get_session(sid, model)
    try:
        from tools import pentest
        pentest.set_session(sid)
    except Exception:
        pass
    s["messages"].append({"role": "user", "content": text})
    s["steps"] = 0
    try:
        db.ensure_session(sid, s["model"])
        existing = db.get_messages(sid)
        db.add_message(sid, "user", text, None)
        if not existing:
            db.set_title(sid, text[:60])
    except Exception:
        pass

    # Solo hacemos streaming en modo local (DeepHat/Ollama). En híbrido/manual con otro
    # modelo, delegamos al flujo normal.
    mode = router.get_mode(sid)
    if mode != "local":
        yield {"type": "fallback"}
        return

    # Primer sondeo SIN stream para saber si pedirá herramientas.
    try:
        probe = client.chat(model=s["model"], messages=s["messages"], tools=SCHEMAS,
                            options={"num_ctx": config.NUM_CTX}, keep_alive=config.KEEP_ALIVE)
    except Exception as e:
        yield {"type": "error", "content": f"Error al contactar el modelo: {e}"}
        return

    if probe.message.tool_calls:
        # Necesita herramientas → el flujo normal lo maneja (con aprobaciones).
        s["messages"].pop()  # quitar el user que reañadirá user_message
        s["messages"].pop() if s["messages"] and s["messages"][-1].get("role") == "user" else None
        yield {"type": "fallback"}
        return

    # Respuesta de texto: re-pedimos en streaming para transmitir token a token.
    full = ""
    try:
        for chunk in client.chat(model=s["model"], messages=s["messages"],
                                 options={"num_ctx": config.NUM_CTX},
                                 keep_alive=config.KEEP_ALIVE, stream=True):
            piece = chunk.message.content or ""
            if piece:
                full += piece
                yield {"type": "token", "content": piece}
    except Exception as e:
        yield {"type": "error", "content": f"Error en streaming: {e}"}
        return

    s["messages"].append({"role": "assistant", "content": full})
    try:
        db.add_message(sid, "assistant", full, "DeepHat")
    except Exception:
        pass
    yield {"type": "done", "model": "DeepHat"}
