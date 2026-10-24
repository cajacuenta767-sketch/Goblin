"""
GOBLIN — Servidor principal (FastAPI).
Sirve el frontend y expone la API del agente + estado + archivos.
Escucha solo en 127.0.0.1 (nadie externo puede acceder).
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ollama import Client

import config
import agent
import state
from tools import list_dir

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
ollama_client = Client(host=config.OLLAMA_HOST)

app = FastAPI(title="GOBLIN")


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


@app.get("/api/models")
def models():
    """Lista los modelos instalados en Ollama (para el selector)."""
    try:
        return {"ok": True, "models": [m.model for m in ollama_client.list().models]}
    except Exception as e:
        return {"ok": False, "models": [], "error": str(e)}


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


# Sirve el frontend (debe ir al final para no tapar las rutas /api)
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
