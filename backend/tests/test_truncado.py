"""Aviso visible cuando la respuesta se corta por el tope de tokens (charla)."""
from types import SimpleNamespace

import agent
import config


def _chunk(text="", done_reason=None):
    return SimpleNamespace(message=SimpleNamespace(content=text, tool_calls=None), done_reason=done_reason)


class _FakeClient:
    def __init__(self, chunks):
        self.chunks = chunks
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return iter(self.chunks)


def test_respuesta_cortada_por_longitud_avisa(monkeypatch):
    fake = _FakeClient([_chunk("Hola, esto empieza"), _chunk(" y se corta", done_reason="length")])
    monkeypatch.setattr(agent, "client", fake)
    monkeypatch.setattr(config, "FAST_MODEL", "")
    eventos = list(agent.stream_message("sess-trunc-a", "explica qué es un puerto", None))
    texto = "".join(e["content"] for e in eventos if e["type"] == "token")
    assert "cortada por longitud" in texto
    assert eventos[-1]["type"] == "done"
    guardado = agent.sessions["sess-trunc-a"]["messages"][-1]["content"]
    assert "cortada por longitud" in guardado


def test_respuesta_completa_no_avisa(monkeypatch):
    fake = _FakeClient([_chunk("Un puerto es un número."), _chunk("", done_reason="stop")])
    monkeypatch.setattr(agent, "client", fake)
    monkeypatch.setattr(config, "FAST_MODEL", "")
    eventos = list(agent.stream_message("sess-trunc-b", "explica qué es un puerto", None))
    texto = "".join(e["content"] for e in eventos if e["type"] == "token")
    assert "cortada" not in texto
    assert eventos[-1]["type"] == "done"
