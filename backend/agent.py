"""
Agente GOBLIN: mantiene la conversación, llama al modelo (DeepHat vía Ollama),
ejecuta herramientas y gestiona las aprobaciones.

Diseño del bucle:
- El modelo responde texto o pide herramientas (tool_calls).
- Las herramientas sin aprobación se ejecutan solas.
- Las que requieren aprobación PAUSAN el bucle y devuelven {"type": "approval"}.
  El frontend muestra la caja de aprobación; al responder, se llama a approve().
- Hay un tope de pasos (MAX_STEPS) para evitar bucles infinitos de un modelo 7B.
- Detener (Spec 024): stop() marca la sesión; el bucle se corta en el siguiente
  punto de control y la llamada al modelo se abandona sin esperarla.
- Guarda de privacidad (Spec 025): en modo híbrido, si la conversación contiene datos
  sensibles (IP, rango de red u objetivo activo), la respuesta la genera DeepHat local.
"""
import json
import queue
import sys
import os
import threading

import config
import db
import router
import approvals
import cancel
import state
from ollama import Client
from tools import SCHEMAS, NEEDS_APPROVAL, run_tool
from text_toolcall import parse_text_toolcall

# Permite importar el cliente de Gemini desde core/llm/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core", "llm"))

client = Client(host=config.OLLAMA_HOST)


class _FakeCall:
    """Imita una tool_call de Ollama para el respaldo por texto (Spec 022)."""
    def __init__(self, name, args):
        self.function = type("F", (), {"name": name, "arguments": args})()

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
    "REGLAS: antes de acciones destructivas (borrar, sobrescribir, comandos peligrosos), "
    "explica en una frase qué harás y por qué. Usa herramientas SOLO cuando el usuario "
    "pida una acción concreta sobre el sistema; ante saludos o preguntas generales, "
    "responde en texto y no llames ninguna herramienta. Responde en español. "
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


def _opts() -> dict:
    """Opciones de Ollama para cada llamada (Spec 032, RF7)."""
    return {"num_ctx": config.NUM_CTX, "num_thread": config.NUM_THREAD}


def _fit_tool_output(text: str, limit: int | None = None) -> str:
    """Recorta una salida de herramienta para el modelo, conservando inicio y final (RF3).

    La salida completa ya está en la auditoría; aquí solo se limita lo que procesa la CPU.
    """
    limit = config.TOOL_OUTPUT_CHARS if limit is None else limit
    if not text or len(text) <= limit:
        return text
    head = (limit * 2) // 3
    tail = limit - head
    omitted = len(text) - head - tail
    return (f"{text[:head]}\n[... {omitted} caracteres omitidos para ahorrar contexto ...]\n"
            f"{text[-tail:]}")


def _role(m) -> str | None:
    return m.get("role") if isinstance(m, dict) else getattr(m, "role", None)


def _content(m) -> str:
    return (m.get("content") if isinstance(m, dict) else getattr(m, "content", "")) or ""


def _last_user_text(messages) -> str:
    for m in reversed(messages):
        if _role(m) == "user":
            return _content(m)
    return ""


def _call_deephat(s: dict):
    """Llama al modelo local (DeepHat) vía Ollama."""
    resp = client.chat(
        model=s["model"],
        messages=s["messages"],
        tools=SCHEMAS,
        options=_opts(),
        keep_alive=config.KEEP_ALIVE,
    )
    resp._goblin_model = "DeepHat"
    return resp


def _current_target() -> str:
    try:
        return state.get_target() or ""
    except Exception:  # noqa: BLE001 - sin objetivo o estado no disponible
        return ""


def _call_model(s: dict, sid: str | None = None):
    """Aplica el router híbrido: elige modelo según el modo de la sesión.
    - local  -> DeepHat
    - hybrid -> Gemini primero; si se niega o falla, DeepHat.
                Si hay datos sensibles en la conversación, DeepHat siempre (Spec 025).
    - manual -> el modelo que el frontend ya fijó en s["model"] (DeepHat por defecto)
    """
    mode = router.get_mode(sid) if sid else "local"

    if mode == "hybrid" and router.gemini_available():
        reason = router.sensitive_reason(s["messages"], _current_target())
        if reason:
            resp = _call_deephat(s)
            resp._goblin_note = (f"🔒 Hay {reason} en la conversación: esta respuesta la generó "
                                 "DeepHat en local. Gemini no recibió nada.")
            return resp
        # Tema de pentest: DeepHat directo, sin esperar a un rechazo de Gemini (Spec 032, RF6).
        if router.needs_local_intent(_last_user_text(s["messages"])):
            resp = _call_deephat(s)
            resp._goblin_note = "🛠️ Tema de pentest: respondió DeepHat en local directamente."
            return resp
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


def _call_interruptible(fn, sid: str | None):
    """Ejecuta fn() en un hilo y espera el resultado, pero sale en cuanto se pide Detener.

    Devuelve (resultado, cancelado). Si se cancela, el hilo termina solo y su resultado
    se descarta. Así el botón Detener responde al instante aunque el modelo siga generando.
    """
    box: dict = {}

    def worker():
        try:
            box["value"] = fn()
        except Exception as e:  # noqa: BLE001 - se vuelve a lanzar en el hilo principal
            box["error"] = e

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    while t.is_alive():
        t.join(0.2)
        if cancel.is_cancelled(sid):
            return None, True
    if "error" in box:
        raise box["error"]
    return box.get("value"), False


_END = object()


def _iter_chunks(open_stream, sid: str | None, halt: threading.Event):
    """Lee el stream de Ollama en un hilo y lo entrega al hilo principal (Spec 032, RF2).

    Así Detener responde al instante aunque Ollama tarde en dar el primer token.
    Si se cancela o se pide parar (`halt`), el hilo cierra el stream y Ollama deja de generar.
    Entrega ("chunk", pieza) y, si se cancela, ("cancelled", None).
    """
    q: queue.Queue = queue.Queue()

    def worker():
        gen = None
        try:
            gen = open_stream()
            for chunk in gen:
                if halt.is_set() or cancel.is_cancelled(sid):
                    break
                q.put(("chunk", chunk))
        except Exception as e:  # noqa: BLE001 - se vuelve a lanzar en el hilo principal
            q.put(("error", e))
        finally:
            close = getattr(gen, "close", None)
            if callable(close):
                close()   # corta la generación en Ollama
            q.put((_END, None))

    threading.Thread(target=worker, daemon=True).start()
    while True:
        try:
            kind, item = q.get(timeout=0.2)
        except queue.Empty:
            if cancel.is_cancelled(sid) or halt.is_set():
                yield "cancelled", None
                return
            continue
        if kind is _END:
            return
        if kind == "error":
            raise item
        yield kind, item


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


def _stopped(s: dict) -> dict:
    """Cierra el turno por Detener: vacía la cola y reinicia el contador de pasos."""
    s["queue"] = []
    s["steps"] = 0
    return {"type": "stopped", "content": "Detenido por el usuario. Pídeme lo que sigue cuando quieras.",
            "model": s.get("model")}


def _step(s: dict, sid: str | None = None) -> dict:
    """Avanza el agente hasta texto final, una aprobación pendiente, o el tope de pasos."""
    while True:
        # 0) ¿El usuario pidió Detener? No se ejecuta nada más.
        if cancel.is_cancelled(sid):
            return _stopped(s)

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
            s["messages"].append({"role": "tool", "content": _fit_tool_output(done["result"]),
                                  "tool_name": name})
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
            resp, cancelled = _call_interruptible(lambda: _call_model(s, sid), sid)
        except Exception as e:
            return {"type": "error", "content": f"Error al contactar el modelo: {e}. "
                                               f"¿Está Ollama corriendo y el modelo descargado?"}
        if cancelled:
            return _stopped(s)
        msg = resp.message
        used_model = getattr(resp, "_goblin_model", "DeepHat")
        note = getattr(resp, "_goblin_note", None)
        s["messages"].append(msg)

        if not msg.tool_calls:
            # Respaldo (Spec 022): DeepHat a veces escribe la tool call como
            # texto suelto en vez del formato <tool_call> nativo. La recuperamos.
            fallback = parse_text_toolcall(msg.content or "")
            if fallback is not None:
                print(f"[GOBLIN] Tool call recuperada por texto: {fallback['tool']}")
                s["queue"] = [_FakeCall(fallback["tool"], fallback["args"])]
                continue
            s["steps"] = 0
            # Guardar la respuesta final de la IA en la base de datos.
            if sid and (msg.content or ""):
                try:
                    db.add_message(sid, "assistant", msg.content or "", used_model)
                except Exception:
                    pass
            out = {"type": "text", "content": msg.content or "", "model": used_model}
            if note:
                out["note"] = note
            return out
        s["queue"] = list(msg.tool_calls)


def _begin_turn(sid: str) -> None:
    """Un turno nuevo borra cualquier Detener anterior y fija la sesión de herramientas."""
    cancel.clear(sid)
    cancel.set_session(sid)


def user_message(sid: str, text: str, model: str | None = None) -> dict:
    _begin_turn(sid)
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
    _begin_turn(sid)
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
    s["messages"].append({"role": "tool", "content": _fit_tool_output(result), "tool_name": name})
    return _step(s, sid)


def stop(sid: str) -> dict:
    """Detener (Spec 024): marca la sesión, mata el shell en curso y vacía la cola."""
    procesos = cancel.request(sid)
    s = sessions.get(sid)
    if s:
        s["queue"] = []
    return {"ok": True, "procesos_detenidos": procesos}


def reset_session(sid: str) -> None:
    sessions.pop(sid, None)


def stream_message(sid: str, text: str, model: str | None = None):
    """Versión en streaming (Spec 018). Devuelve un generador de trozos de texto.
    Si la IA pide herramientas, cambia al flujo normal (señala 'fallback' y el cliente
    reenvía por /api/chat). Solo hace streaming real del texto final.
    """
    _begin_turn(sid)
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

    # Saludo corto y modelo rápido configurado: no hace falta el modelo grande (RF5).
    fast = config.FAST_MODEL if (config.FAST_MODEL and router.is_greeting(text)) else ""
    use_model = fast or s["model"]
    use_tools = None if fast else SCHEMAS
    label = f"DeepHat-rápido ({fast})" if fast else "DeepHat"

    def _open_stream():
        return client.chat(model=use_model, messages=s["messages"], tools=use_tools,
                           options=_opts(), keep_alive=config.KEEP_ALIVE, stream=True)

    # UNA sola generación (RF1): el texto se muestra en vivo; si aparece una herramienta,
    # el texto ya mostrado se descarta y se sigue por el flujo normal con aprobaciones.
    full = ""
    tool_seen = False
    halt = threading.Event()
    try:
        for kind, item in _iter_chunks(_open_stream, sid, halt):
            if kind == "cancelled":
                break
            if item.message.tool_calls:
                tool_seen = True
                halt.set()
                break
            piece = item.message.content or ""
            if piece:
                full += piece
                yield {"type": "token", "content": piece}
    except Exception as e:
        halt.set()
        yield {"type": "error", "content": f"Error en streaming: {e}"}
        return

    if tool_seen:
        # Quitar el user que reañadirá user_message y pasar al flujo normal.
        if s["messages"] and _role(s["messages"][-1]) == "user":
            s["messages"].pop()
        if full:
            yield {"type": "discard"}
        yield {"type": "fallback"}
        return

    if cancel.is_cancelled(sid):
        # Se guarda lo que alcanzó a generarse, marcado como detenido.
        s["messages"].append({"role": "assistant", "content": full})
        try:
            db.add_message(sid, "assistant", (full + "\n[detenido]").strip(), label)
        except Exception:
            pass
        yield {"type": "stopped", "content": "Detenido por el usuario.", "model": s["model"]}
        return

    s["messages"].append({"role": "assistant", "content": full})
    try:
        db.add_message(sid, "assistant", full, label)
    except Exception:
        pass
    yield {"type": "done", "model": label}
