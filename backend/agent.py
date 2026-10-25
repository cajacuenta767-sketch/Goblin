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
import intent
import router
import approvals
import cancel
import engagement
import preview
import progress
import scope
import state
from tools import scan_tool
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
    "ALCANCE: haz SOLO lo que el usuario pide en su último mensaje. Nunca escanees, "
    "enumeres ni ataques nada por iniciativa propia. La metodología de pentest (reconocimiento, "
    "enumeración, explotación, reporte) solo se aplica cuando el usuario pide un trabajo de "
    "pentest sobre un objetivo fijado. Para programar, editar archivos o responder preguntas, "
    "no uses herramientas de seguridad. Si durante un pentest encuentras algo relevante "
    "(puerto abierto con servicio vulnerable, mala configuración, credencial), REGÍSTRALO con "
    "add_finding indicando la severidad (critical/high/medium/low/info).\n\n"
    "REGLAS: antes de acciones destructivas (borrar, sobrescribir, comandos peligrosos), "
    "explica en una frase qué harás y por qué. Usa herramientas SOLO cuando el usuario "
    "pida una acción concreta sobre el sistema; ante saludos o preguntas generales, "
    "responde en texto y no llames ninguna herramienta. Si la petición no está clara, "
    "pregunta antes de actuar. Responde en español. "
    "Opera SOLO sobre objetivos con autorización explícita; si no está claro, pregúntalo."
)

# sesiones[session_id] = {"messages": [...], "queue": [tool_calls pendientes], "model": str}
sessions: dict[str, dict] = {}


def get_session(sid: str, model: str | None = None) -> dict:
    if sid not in sessions:
        sessions[sid] = {
            "sid": sid,
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


def _stream_opts(tools) -> dict:
    """Opciones para el stream. Sin herramientas (charla), la respuesta tiene tope de tokens:
    en CPU una respuesta larga a un saludo cuesta minutos (Spec 033, límite de respuesta)."""
    opts = _opts()
    if tools is None:
        opts["num_predict"] = config.CHAT_MAX_TOKENS
    return opts


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


def _context(s: dict) -> list:
    """Mensajes que recibe el modelo: el system prompt y los últimos HISTORY_TURNS turnos
    de usuario (Spec 034, RF2). El historial completo sigue guardado en la sesión."""
    msgs = s["messages"]
    users = [i for i, m in enumerate(msgs) if _role(m) == "user"]
    if len(users) <= config.HISTORY_TURNS or not msgs:
        base = msgs
    else:
        start = users[-config.HISTORY_TURNS]
        base = [msgs[0]] + msgs[start:]
    # Memoria del engagement (Spec 036, RF5): objetivo, alcance, hosts y hallazgos desde la base.
    resumen = engagement.summary(s["sid"]) if s.get("sid") else ""
    if resumen and base:
        return [base[0], {"role": "system", "content": resumen}] + list(base[1:])
    return base


def _tools_for(s: dict) -> list | None:
    """Esquemas de herramientas permitidos en el turno (Spec 033). None = sin herramientas."""
    allowed = s.get("allowed")
    if allowed is None:          # turno de acción: todas
        return SCHEMAS
    schemas = [sc for sc in SCHEMAS if sc["function"]["name"] in allowed]
    return schemas or None


def _set_turn_tools(s: dict, text: str) -> None:
    """Fija qué herramientas puede usar este turno, según la intención (Spec 033)."""
    s["allowed"] = intent.allowed_tools(text)


def _call_deephat(s: dict):
    """Llama al modelo local (DeepHat) vía Ollama."""
    resp = client.chat(
        model=s["model"],
        messages=_context(s),
        tools=_tools_for(s),
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
        sid_s = sid or s.get("sid") or ""
        contenido = list(s["messages"]) + [engagement.summary(sid_s)]
        reason = router.sensitive_reason(contenido, _current_target(), _sensitive_terms(sid_s))
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
            resp = gemini_client.chat(_context(s), _tools_for(s) or [])
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


def _sensitive_terms(sid: str) -> list[str]:
    """Términos sensibles del engagement (nombres de cliente…). Nunca salen a la nube (Spec 038)."""
    if not sid:
        return []
    try:
        return db.list_scope(sid, "term")
    except Exception:
        return []


def _scope_block(sid: str | None, name: str, args: dict) -> str | None:
    """Motivo por el que la herramienta sale del alcance del engagement, o None (Spec 036, RF2–RF4).
    Si no se puede leer el alcance, se bloquea: ante la duda, no se ejecuta."""
    if not sid or name not in ("run_shell", "term_run", "http_get"):
        return None
    try:
        entradas = db.list_scope(sid, "scope")
    except Exception:
        return "BLOQUEADO por alcance: no se pudo leer el alcance del engagement."
    if name == "http_get":
        return scope.check_url(str(args.get("url", "")), entradas)
    return scope.check_command(str(args.get("command", "")), entradas)


def _log(sid: str | None, name: str, args: dict, result: str, approved: bool) -> None:
    """Log de auditoría (Fase 8): qué herramienta se intentó, cuándo, resultado."""
    if not sid:
        return
    try:
        db.log_action(sid, name, json.dumps(args, ensure_ascii=False), result, approved)
    except Exception:
        pass


def _exec(call, sid: str | None = None, approved: bool = True) -> dict:
    name = call.function.name
    args = dict(call.function.arguments or {})
    bloqueo = _scope_block(sid, name, args)
    if bloqueo:
        result = bloqueo
    else:
        if sid:
            progress.start(sid, name)
        try:
            result = run_tool(name, args)
        finally:
            if sid:
                progress.finish(sid)
        # nmap que se ejecuta en la terminal o por shell: sus puertos van a la base (Spec 036, RF7).
        if sid and name in ("run_shell", "term_run") and \
                scope.command_name(str(args.get("command", ""))) == "nmap":
            try:
                scan_tool.record_nmap(sid, result)
            except Exception:
                pass
    _log(sid, name, args, result, approved)
    return {"name": name, "args": args, "result": result}


def session_status(sid: str) -> dict:
    """Estado para la interfaz: herramienta en curso y contexto estimado (Spec 037, RF3–RF5)."""
    st = progress.status(sid)
    s = sessions.get(sid)
    tokens = sum(len(_content(m)) for m in _context(s)) // 4 if s else 0
    return {**st, "context_tokens": tokens, "context_limit": config.NUM_CTX}


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
            # Spec 033: una herramienta fuera de la intención del turno no se ejecuta.
            if s.get("allowed") is not None and name not in s["allowed"]:
                s["queue"].pop(0)
                s["messages"].append({"role": "tool", "tool_name": name, "content": (
                    f"Herramienta '{name}' no permitida en esta petición. Responde en texto y "
                    "pide al usuario la acción o la ruta explícitas si las necesitas.")})
                continue
            args_call = dict(call.function.arguments or {})
            # Alcance (Spec 036): si sale del engagement, no se pide aprobación; se bloquea.
            bloqueo = _scope_block(sid, name, args_call)
            if bloqueo:
                s["queue"].pop(0)
                _log(sid, name, args_call, bloqueo, False)
                s["messages"].append({"role": "tool", "tool_name": name, "content": bloqueo})
                continue
            base = name in NEEDS_APPROVAL
            if approvals.needs_approval(sid, name, base, args_call):
                pendiente = {
                    "type": "approval",
                    "tool": name,
                    "args": args_call,
                    "model": s["model"],
                }
                diff = preview.diff_for(name, args_call)   # Spec 037, RF1
                if diff:
                    pendiente["diff"] = diff
                return pendiente
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


# Plan visible (Spec 035): el modelo propone pasos sin herramientas; "sí" los ejecuta.
PLAN_REQUEST = (
    "Escribe un plan corto y numerado (máximo 6 pasos) para cumplir la última petición del "
    "usuario, nombrando la herramienta de cada paso. No ejecutes nada ni llames herramientas. "
    "Termina con: «¿Lo ejecuto? Responde sí o dime qué cambiar.»"
)
EXECUTE_TEXT = "Ejecuta el plan que propusiste, paso a paso."


def _plan_messages(s: dict) -> list:
    """Historial acotado más la petición de plan (no se guarda en la conversación)."""
    return list(_context(s)) + [{"role": "user", "content": PLAN_REQUEST}]


def _plan_nonstream(s: dict) -> str:
    resp = client.chat(model=s["model"], messages=_plan_messages(s), tools=None,
                       options=_stream_opts(None), keep_alive=config.KEEP_ALIVE)
    return resp.message.content or ""


def user_message(sid: str, text: str, model: str | None = None) -> dict:
    _begin_turn(sid)
    s = get_session(sid, model)
    if s.get("pending_plan") and intent.is_confirmation(text):
        text = EXECUTE_TEXT                     # RF3: confirmación → ejecutar el plan
    s["pending_plan"] = False                   # RF4: cualquier otro mensaje descarta el plan
    _set_turn_tools(s, text)
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
    if intent.is_capability(text):
        s["messages"].append({"role": "assistant", "content": intent.CAPABILITY_REPLY})
        try:
            db.add_message(sid, "assistant", intent.CAPABILITY_REPLY, "GOBLIN")
        except Exception:
            pass
        return {"type": "text", "content": intent.CAPABILITY_REPLY, "model": "GOBLIN"}
    if intent.is_multistep(text):               # RF1: plan visible, sin ejecutar
        try:
            plan = _plan_nonstream(s)
        except Exception as e:
            return {"type": "error", "content": f"Error al preparar el plan: {e}"}
        s["messages"].append({"role": "assistant", "content": plan})
        s["pending_plan"] = True
        try:
            db.add_message(sid, "assistant", plan, "DeepHat")
        except Exception:
            pass
        return {"type": "text", "content": plan, "model": "DeepHat"}
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
    if s.get("pending_plan") and intent.is_confirmation(text):
        yield {"type": "fallback"}              # la confirmación la procesa user_message (Spec 035)
        return
    s["pending_plan"] = False                   # RF4: cualquier otro mensaje descarta el plan
    _set_turn_tools(s, text)
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

    # Pregunta de capacidad: respuesta fija, sin modelo (Spec 034, RF1).
    if intent.is_capability(text):
        s["messages"].append({"role": "assistant", "content": intent.CAPABILITY_REPLY})
        try:
            db.add_message(sid, "assistant", intent.CAPABILITY_REPLY, "GOBLIN")
        except Exception:
            pass
        yield {"type": "token", "content": intent.CAPABILITY_REPLY}
        yield {"type": "done", "model": "GOBLIN"}
        return

    # Solo hacemos streaming en modo local (DeepHat/Ollama). En híbrido/manual con otro
    # modelo, delegamos al flujo normal.
    mode = router.get_mode(sid)
    if mode != "local":
        yield {"type": "fallback"}
        return

    # Plan visible en streaming (Spec 035, RF1): sin herramientas, queda pendiente de confirmación.
    if intent.is_multistep(text):
        full = ""
        halt = threading.Event()

        def _open_plan():
            return client.chat(model=s["model"], messages=_plan_messages(s), tools=None,
                               options=_stream_opts(None), keep_alive=config.KEEP_ALIVE, stream=True)
        try:
            for kind, item in _iter_chunks(_open_plan, sid, halt):
                if kind == "cancelled":
                    break
                piece = item.message.content or ""
                if piece:
                    full += piece
                    yield {"type": "token", "content": piece}
        except Exception as e:
            halt.set()
            yield {"type": "error", "content": f"Error al preparar el plan: {e}"}
            return
        if cancel.is_cancelled(sid):
            yield {"type": "stopped", "content": "Detenido por el usuario.", "model": s["model"]}
            return
        s["messages"].append({"role": "assistant", "content": full})
        s["pending_plan"] = True
        try:
            db.add_message(sid, "assistant", full, "DeepHat")
        except Exception:
            pass
        yield {"type": "done", "model": "DeepHat"}
        return

    # Saludo corto y modelo rápido configurado: no hace falta el modelo grande (RF5).
    fast = config.FAST_MODEL if (config.FAST_MODEL and router.is_greeting(text)) else ""
    use_model = fast or s["model"]
    use_tools = None if fast else _tools_for(s)
    label = f"DeepHat-rápido ({fast})" if fast else "DeepHat"

    def _open_stream():
        return client.chat(model=use_model, messages=_context(s), tools=use_tools,
                           options=_stream_opts(use_tools), keep_alive=config.KEEP_ALIVE,
                           stream=True)

    # UNA sola generación (RF1): el texto se muestra en vivo; si aparece una herramienta,
    # el texto ya mostrado se descarta y se sigue por el flujo normal con aprobaciones.
    full = ""
    tool_seen = False
    reason = None   # motivo de fin de Ollama: "length" = cortada por el tope de tokens
    halt = threading.Event()
    try:
        for kind, item in _iter_chunks(_open_stream, sid, halt):
            if kind == "cancelled":
                break
            if item.message.tool_calls:
                tool_seen = True
                halt.set()
                break
            reason = getattr(item, "done_reason", None) or reason
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

    if reason == "length":
        # Que el usuario sepa que la respuesta no terminó, en vez de un corte sin explicación.
        aviso = "\n\n[Respuesta cortada por longitud. Escribe «continúa» para seguir.]"
        full += aviso
        yield {"type": "token", "content": aviso}
    s["messages"].append({"role": "assistant", "content": full})
    try:
        db.add_message(sid, "assistant", full, label)
    except Exception:
        pass
    yield {"type": "done", "model": label}
