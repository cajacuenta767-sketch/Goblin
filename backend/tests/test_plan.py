"""Tests de plan visible antes de ejecutar (Spec 035)."""
from types import SimpleNamespace

import agent
import config
import intent


class _Fake:
    """Modelo simulado: cuenta llamadas y responde texto (sin herramientas)."""

    def __init__(self, texto="1. Crear carpeta\n2. Escribir archivo\n¿Lo ejecuto?"):
        self.texto = texto
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("stream"):
            return iter([SimpleNamespace(message=SimpleNamespace(content=self.texto, tool_calls=None))])
        return SimpleNamespace(message=SimpleNamespace(content=self.texto, tool_calls=None))


# --- RF1: detección ---

def test_varios_pasos_se_detectan():
    assert intent.is_multistep("crea la carpeta pruebas y luego escribe notas.txt")
    assert intent.is_multistep("lista la carpeta y borra el log")


def test_un_paso_no_se_detecta():
    assert not intent.is_multistep("crea la carpeta pruebas")
    assert not intent.is_multistep("hola")


# --- RF3 y RF4: confirmación ---

def test_confirmaciones_comunes():
    for texto in ["sí", "Si", "ok", "¡Dale!", "ejecuta", "adelante"]:
        assert intent.is_confirmation(texto), texto


def test_otro_mensaje_no_es_confirmacion():
    assert not intent.is_confirmation("mejor borra el log")
    assert not intent.is_confirmation("sí pero sin borrar nada")


# --- RF1: el plan no ejecuta herramientas ---

def test_plan_en_streaming_no_manda_herramientas(monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(agent, "client", fake)
    monkeypatch.setattr(config, "FAST_MODEL", "")
    eventos = list(agent.stream_message("sess-035-a", "crea la carpeta pruebas y luego escribe notas.txt", None))
    assert fake.calls[0]["tools"] is None
    assert eventos[-1]["type"] == "done"
    assert agent.sessions["sess-035-a"]["pending_plan"] is True


def test_plan_normal_no_manda_herramientas(monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(agent, "client", fake)
    out = agent.user_message("sess-035-b", "crea la carpeta pruebas y luego escribe notas.txt", None)
    assert fake.calls[0]["tools"] is None
    assert out["type"] == "text"
    assert out["content"] == fake.texto
    assert agent.sessions["sess-035-b"]["pending_plan"] is True


# --- RF3: "sí" ejecuta el plan ---

def test_confirmacion_pasa_a_ejecutar_con_herramientas(monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(agent, "client", fake)
    agent.user_message("sess-035-c", "crea la carpeta pruebas y luego escribe notas.txt", None)
    fake.calls.clear()
    agent.user_message("sess-035-c", "sí", None)
    assert fake.calls, "tras confirmar debe llamarse al modelo"
    assert fake.calls[0]["tools"] is not None
    assert agent.sessions["sess-035-c"]["pending_plan"] is False


def test_confirmacion_en_streaming_se_delega_al_flujo_normal(monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(agent, "client", fake)
    list(agent.stream_message("sess-035-d", "crea la carpeta pruebas y luego escribe notas.txt", None))
    fake.calls.clear()
    eventos = list(agent.stream_message("sess-035-d", "sí", None))
    assert [e["type"] for e in eventos] == ["fallback"]
    assert fake.calls == [], "la confirmación no llama al modelo en streaming"


# --- RF4: otro mensaje descarta el plan ---

def test_otro_mensaje_descarta_el_plan(monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(agent, "client", fake)
    agent.user_message("sess-035-e", "crea la carpeta pruebas y luego escribe notas.txt", None)
    assert agent.sessions["sess-035-e"]["pending_plan"] is True
    agent.user_message("sess-035-e", "explica qué es nmap", None)
    assert agent.sessions["sess-035-e"]["pending_plan"] is False
