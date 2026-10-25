"""
GOBLIN — Servidor principal (FastAPI).
Sirve el frontend y expone la API del agente + estado + archivos.
Escucha solo en 127.0.0.1 (nadie externo puede acceder).
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ollama import Client

import config
import agent
import scope
import state
import terminal
import db
from tools import list_dir

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
ollama_client = Client(host=config.OLLAMA_HOST)

app = FastAPI(title="GOBLIN")
db.init()   # crea las tablas de SQLite si no existen


# ---------- Modelos de petición ----------
class ChatIn(BaseModel):
    session_id: str = "main"
    message: str
    model: str | None = None


class ApproveIn(BaseModel):
    session_id: str = "main"
    approved: bool


class ScopeIn(BaseModel):
    kind: str = "scope"     # 'scope' = objetivo autorizado · 'term' = término sensible
    entry: str = ""


class TargetIn(BaseModel):
    target: str = ""


class StopIn(BaseModel):
    session_id: str = "main"


# ---------- API ----------
@app.post("/api/chat")
def chat(body: ChatIn):
    return agent.user_message(body.session_id, body.message, body.model)


@app.post("/api/approve")
def approve(body: ApproveIn):
    return agent.approve(body.session_id, body.approved)


@app.post("/api/stop")
def stop(body: StopIn):
    """Detener (Spec 024): cancela la respuesta en curso y mata los procesos de shell."""
    return agent.stop(body.session_id)


@app.post("/api/chat/stream")
def chat_stream(body: ChatIn):
    """Chat en streaming (Spec 018): transmite la respuesta token a token (SSE)."""
    import json as _json
    from fastapi.responses import StreamingResponse

    def gen():
        for ev in agent.stream_message(body.session_id, body.message, body.model):
            yield f"data: {_json.dumps(ev, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/files")
def files(path: str = "."):
    try:
        return {"ok": True, "listing": list_dir(path)}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


class FileContentIn(BaseModel):
    path: str
    content: str


@app.get("/api/file")
def file_read(path: str):
    """Lee el contenido de un archivo para el editor (Spec 007)."""
    from tools import read_file
    try:
        return {"ok": True, "content": read_file(path)}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.post("/api/file")
def file_write(body: FileContentIn):
    """Guarda el contenido editado en el archivo (Spec 007). Es una escritura directa
    del usuario desde el editor, por eso no pasa por la aprobación del agente."""
    from tools import write_file
    try:
        return {"ok": True, "result": write_file(body.path, body.content)}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.get("/api/models")
def models():
    """Lista los modelos instalados en Ollama (para el selector)."""
    try:
        return {"ok": True, "models": [m.model for m in ollama_client.list().models]}
    except Exception as e:
        return {"ok": False, "models": [], "error": str(e)}


# ---------- Sesiones (Spec 005) ----------
@app.get("/api/sessions")
def sessions_list():
    return {"sessions": db.list_sessions()}


@app.get("/api/sessions/{sid}")
def session_get(sid: str):
    return {"messages": db.get_messages(sid)}


@app.delete("/api/sessions/{sid}")
def session_delete(sid: str):
    db.delete_session(sid)
    agent.reset_session(sid)
    return {"ok": True}


# ---------- Hallazgos e informe (Spec 006) ----------
@app.get("/api/findings/{sid}")
def findings_list(sid: str):
    return {"findings": db.list_findings(sid)}


@app.get("/api/report/{sid}")
def report_get(sid: str):
    import report
    return {"report": report.generate(sid)}


# ---------- Router híbrido / modo (Spec 008) ----------
class ModeIn(BaseModel):
    session_id: str = "main"
    mode: str  # local / hybrid / manual


@app.get("/api/mode")
def mode_get(session_id: str = "main"):
    import router
    return {"mode": router.get_mode(session_id), "gemini_available": router.gemini_available()}


@app.post("/api/mode")
def mode_set(body: ModeIn):
    import router
    m = router.set_mode(body.session_id, body.mode)
    # Aviso: híbrido sin API key cae a local.
    warn = None
    if m == "hybrid" and not router.gemini_available():
        warn = "No hay API key de Gemini configurada. El modo híbrido usará solo DeepHat (local)."
    return {"mode": m, "gemini_available": router.gemini_available(), "warning": warn}


# ---------- Nivel de autoaprobación (Spec 009) ----------
class LevelIn(BaseModel):
    session_id: str = "main"
    level: str  # cauto / normal / confianza


@app.get("/api/approval-level")
def level_get(session_id: str = "main"):
    import approvals
    return {"level": approvals.get_level(session_id)}


@app.post("/api/approval-level")
def level_set(body: LevelIn):
    import approvals
    return {"level": approvals.set_level(body.session_id, body.level)}


# ---------- Marketplace de herramientas (Spec 016) ----------
class ToolIn(BaseModel):
    tool_id: str


@app.get("/api/toolstore")
def toolstore_list():
    import toolstore
    return {"tools": toolstore.catalog(), "categories": toolstore.CATEGORIES}


@app.post("/api/toolstore/install")
def toolstore_install(body: ToolIn):
    """Prepara la instalación (Spec 026): devuelve el comando; la UI lo escribe en la terminal."""
    import toolstore
    return toolstore.install(body.tool_id)


@app.post("/api/toolstore/open")
def toolstore_open(body: ToolIn):
    """Abre la web oficial de una herramienta del catálogo en el navegador (Spec 026)."""
    import toolstore
    return toolstore.open_url(body.tool_id)


# ---------- Instalación con contraseña en la app y registro en vivo (Spec 027) ----------
class JobIn(BaseModel):
    tool_id: str
    action: str = "install"   # install / remove


class PasswordIn(BaseModel):
    password: str             # se usa UNA vez en sudo -S y se descarta; nunca se registra


@app.post("/api/toolstore/jobs")
def toolstore_job_start(body: JobIn):
    """Inicia instalar o desinstalar. Si sudo pide contraseña, el trabajo queda esperándola."""
    import toolstore_jobs
    return toolstore_jobs.start_job(body.tool_id, body.action)


@app.get("/api/toolstore/jobs")
def toolstore_jobs_list():
    import toolstore_jobs
    return {"ok": True, "jobs": toolstore_jobs.list_jobs()}


@app.get("/api/toolstore/jobs/{job_id}")
def toolstore_job_get(job_id: str):
    import toolstore_jobs
    job = toolstore_jobs.get_job(job_id)
    if job is None:
        return {"ok": False, "error": "Trabajo no encontrado."}
    return {"ok": True, "job": job}


@app.post("/api/toolstore/jobs/{job_id}/password")
def toolstore_job_password(job_id: str, body: PasswordIn):
    """Entrega la contraseña a sudo una vez. La respuesta nunca la incluye."""
    import toolstore_jobs
    return toolstore_jobs.submit_password(job_id, body.password)


@app.post("/api/toolstore/jobs/{job_id}/cancel")
def toolstore_job_cancel(job_id: str):
    import toolstore_jobs
    return toolstore_jobs.cancel_job(job_id)


@app.get("/api/chat/status/{sid}")
def chat_status(sid: str):
    """Herramienta en curso y contexto estimado para la barra de estado (Spec 037)."""
    return agent.session_status(sid)


def _alcance_json(sid: str) -> dict:
    return {"scope": db.list_scope(sid, "scope"), "terms": db.list_scope(sid, "term")}


@app.get("/api/scope/{sid}")
def get_scope(sid: str):
    """Alcance del engagement y términos sensibles de la sesión (Spec 036, 038)."""
    return _alcance_json(sid)


@app.post("/api/scope/{sid}")
def add_scope(sid: str, body: ScopeIn):
    """Añade un objetivo al alcance (IP, rango o dominio) o un término sensible.
    Solo lo edita el usuario desde la interfaz: la IA no puede ampliar el alcance."""
    texto = (body.entry or "").strip()
    if body.kind == "scope":
        entrada = scope.normalize_entry(texto)
        if not entrada:
            raise HTTPException(status_code=400, detail="Escribe una IP, un rango (10.0.0.0/24) o un dominio válido.")
        db.add_scope(sid, "scope", entrada)
    elif body.kind == "term":
        if not texto or len(texto) > 100 or "\n" in texto:
            raise HTTPException(status_code=400, detail="El término debe tener entre 1 y 100 caracteres, en una línea.")
        db.add_scope(sid, "term", texto)
    else:
        raise HTTPException(status_code=400, detail="Tipo no válido: usa 'scope' o 'term'.")
    return _alcance_json(sid)


@app.post("/api/scope/{sid}/remove")
def remove_scope(sid: str, body: ScopeIn):
    if body.kind not in ("scope", "term"):
        raise HTTPException(status_code=400, detail="Tipo no válido.")
    db.remove_scope(sid, body.kind, body.entry)
    return _alcance_json(sid)


@app.get("/api/snippets")
def get_snippets():
    """Snippets de pentest por categoría, para el panel de engagement (Spec 041, RF4)."""
    import snippets
    return {"categories": {
        cat: [{"name": nombre, "code": codigo} for nombre, codigo in items]
        for cat, items in snippets.SNIPPETS.items()
    }}


@app.get("/api/hosts/{sid}")
def get_hosts(sid: str):
    """Hosts y puertos abiertos guardados por nmap en la sesión (Spec 036, RF7)."""
    return {"hosts": db.list_hosts(sid)}


@app.get("/api/target")
def get_target():
    return {"target": state.get_target()}


@app.post("/api/target")
def set_target(body: TargetIn):
    """Fija el target y lo publica a la Polybar (Fase 9)."""
    t = state.set_target(body.target)
    return {"target": t}


@app.get("/api/info")
def info():
    return {
        "app": "GOBLIN",
        "workspace": str(config.WORKSPACE),
        "full_access": config.FULL_ACCESS,
        "default_model": config.DEFAULT_MODEL,
        "num_ctx": config.NUM_CTX,
        "target": state.get_target(),
    }


@app.get("/api/health")
def health():
    """Comprueba que Ollama responde."""
    try:
        ollama_client.list()
        return {"ollama": "ok"}
    except Exception as e:
        return {"ollama": "down", "error": str(e)}


@app.get("/api/system")
def system():
    """Uso de RAM y CPU para la barra de estado (RF8 de la spec 002)."""
    try:
        import psutil
        vm = psutil.virtual_memory()
        return {
            "ok": True,
            "ram_percent": vm.percent,
            "ram_used_gb": round(vm.used / (1024 ** 3), 1),
            "ram_total_gb": round(vm.total / (1024 ** 3), 1),
            "cpu_percent": psutil.cpu_percent(interval=None),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/diagnostics")
def diagnostics():
    """Diagnóstico de primer uso (Spec 015): Ollama, modelo, disco, RAM."""
    import shutil
    result = {"problems": []}

    # Ollama vivo
    models = []
    try:
        models = [(m.model or "") for m in ollama_client.list().models]
        result["ollama"] = "ok"
    except Exception:
        result["ollama"] = "down"
        result["problems"].append({
            "what": "Ollama no está corriendo",
            "fix": "Arráncalo con: ollama serve  (o usa ./scripts/run.sh)",
        })

    # Modelo por defecto descargado
    short = config.DEFAULT_MODEL
    model_ok = any(short.split("/")[-1].split(":")[0].lower() in m.lower() for m in models)
    result["model_downloaded"] = model_ok
    if result["ollama"] == "ok" and not model_ok:
        result["problems"].append({
            "what": "El modelo por defecto no está descargado",
            "fix": f"Descárgalo con: ollama pull {config.DEFAULT_MODEL}",
        })

    # Disco
    try:
        _t, _u, free = shutil.disk_usage(config.WORKSPACE)
        free_gb = round(free / (1024 ** 3), 1)
        result["disk_free_gb"] = free_gb
        if free_gb < 10:
            result["problems"].append({
                "what": f"Poco espacio en disco ({free_gb} GB libres)",
                "fix": "Libera espacio; el modelo necesita ~5 GB.",
            })
    except Exception:
        pass

    # RAM
    try:
        import psutil
        avail = round(psutil.virtual_memory().available / (1024 ** 3), 1)
        result["ram_available_gb"] = avail
        if avail < 2:
            result["problems"].append({
                "what": f"Poca RAM disponible ({avail} GB)",
                "fix": "Cierra apps pesadas; el modelo 7B necesita ~6 GB.",
            })
    except Exception:
        pass

    result["ok"] = len(result["problems"]) == 0
    return result


@app.websocket("/ws/terminal")
async def ws_terminal(websocket: WebSocket):
    """Terminal pty real (Spec 004). Arranca en el workspace o en la carpeta del target."""
    await websocket.accept()
    # Si hay un target fijado, arranca la terminal en su carpeta de engagement.
    cwd = str(config.WORKSPACE)
    try:
        await terminal.run_terminal(websocket, cwd)
    except WebSocketDisconnect:
        pass


# Sirve el frontend (debe ir al final para no tapar las rutas /api)
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
