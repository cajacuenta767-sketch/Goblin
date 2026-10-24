"""
GOBLIN — Servidor principal (FastAPI).
Sirve el frontend y expone la API del agente + estado + archivos.
Escucha solo en 127.0.0.1 (nadie externo puede acceder).
"""
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ollama import Client

import config
import agent
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


class TargetIn(BaseModel):
    target: str = ""


# ---------- API ----------
@app.post("/api/chat")
def chat(body: ChatIn):
    return agent.user_message(body.session_id, body.message, body.model)


@app.post("/api/approve")
def approve(body: ApproveIn):
    return agent.approve(body.session_id, body.approved)


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
class InstallIn(BaseModel):
    tool_id: str


@app.get("/api/toolstore")
def toolstore_list():
    import toolstore
    return {"tools": toolstore.catalog(), "categories": toolstore.CATEGORIES}


@app.post("/api/toolstore/install")
def toolstore_install(body: InstallIn):
    import toolstore
    return toolstore.install(body.tool_id)


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
        models = [m.model for m in ollama_client.list().models]
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
