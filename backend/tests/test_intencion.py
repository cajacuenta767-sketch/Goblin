"""Tests de intención y alcance por turno (Spec 033)."""
from types import SimpleNamespace

import agent
import config
import intent


def _chunk(text="", tool_calls=None):
    return SimpleNamespace(message=SimpleNamespace(content=text, tool_calls=tool_calls))


class _Fake:
    def __init__(self, chunks):
        self.chunks = chunks
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return iter(self.chunks)


# --- RF1 y RF2: clasificación ---

def test_analiza_sin_ruta_no_da_herramientas():
    assert intent.classify("analiza mi computadora") == "analysis"
    assert intent.allowed_tools("analiza mi computadora") == set()


def test_analiza_con_ruta_solo_lectura():
    texto = "analiza ~/proyecto/app.py"
    assert intent.classify(texto) == "analysis"
    assert intent.allowed_tools(texto) == intent.READ_ONLY_TOOLS


def test_accion_da_todas_las_herramientas():
    assert intent.classify("crea la carpeta pruebas") == "action"
    assert intent.allowed_tools("crea la carpeta pruebas") is None


def test_saludo_y_pregunta_sin_herramientas():
    assert intent.allowed_tools("hola") == set()
    assert intent.allowed_tools("explica qué es nmap") == set()


def test_accion_gana_sobre_analisis():
    assert intent.classify("analiza y borra el log") == "action"


# --- RF3: herramienta fuera de la intención no se ejecuta ---

def test_herramienta_no_permitida_no_se_ejecuta(monkeypatch):
    ejecutadas = []
    monkeypatch.setattr(agent, "run_tool", lambda name, args: ejecutadas.append(name) or "ok")
    llamada = SimpleNamespace(function=SimpleNamespace(name="disk_usage", arguments={}))
    s = {"model": "m", "messages": [], "queue": [llamada], "steps": 0, "allowed": set()}
    agent._step(s, None)
    assert "disk_usage" not in ejecutadas
    assert any("no permitida" in m.get("content", "") for m in s["messages"])


# --- RF4 y RF5: streaming y modelo sin herramientas en chat ---

def test_analisis_sin_ruta_no_envia_herramientas_al_modelo(monkeypatch):
    fake = _Fake([_chunk("¿Qué ruta quieres que analice?")])
    monkeypatch.setattr(agent, "client", fake)
    monkeypatch.setattr(config, "FAST_MODEL", "")
    list(agent.stream_message("sess-033-a", "analiza mi computadora", None))
    assert fake.calls[0]["tools"] is None


def test_accion_envia_herramientas_al_modelo(monkeypatch):
    fake = _Fake([_chunk("Listo")])
    monkeypatch.setattr(agent, "client", fake)
    monkeypatch.setattr(config, "FAST_MODEL", "")
    list(agent.stream_message("sess-033-b", "crea la carpeta pruebas", None))
    assert fake.calls[0]["tools"] is not None


# --- Límite de respuesta en charla (RF de respuesta corta) ---

def test_charla_tiene_tope_de_tokens(monkeypatch):
    fake = _Fake([_chunk("Hola")])
    monkeypatch.setattr(agent, "client", fake)
    monkeypatch.setattr(config, "FAST_MODEL", "")
    list(agent.stream_message("sess-033-c", "hola como estas", None))
    assert fake.calls[0]["options"]["num_predict"] == config.CHAT_MAX_TOKENS


def test_accion_no_tiene_tope_de_tokens(monkeypatch):
    fake = _Fake([_chunk("Listo")])
    monkeypatch.setattr(agent, "client", fake)
    monkeypatch.setattr(config, "FAST_MODEL", "")
    list(agent.stream_message("sess-033-d", "crea la carpeta pruebas", None))
    assert "num_predict" not in fake.calls[0]["options"]
