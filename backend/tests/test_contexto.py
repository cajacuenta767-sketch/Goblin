"""Tests de respuestas de capacidad y contexto acotado (Spec 034)."""
from types import SimpleNamespace

import agent
import config
import intent


class _Fake:
    def __init__(self):
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return iter([SimpleNamespace(message=SimpleNamespace(content="x", tool_calls=None))])


# --- RF1: preguntas de capacidad ---

def test_pregunta_de_capacidad_se_detecta():
    assert intent.is_capability("¿puedes analizar algo?")
    assert intent.is_capability("¿qué puedes hacer?")
    assert intent.is_capability("quién eres")


def test_peticion_con_accion_no_es_capacidad():
    assert not intent.is_capability("¿puedes crear la carpeta pruebas?")
    assert not intent.is_capability("crea la carpeta pruebas")


def test_capacidad_no_llama_al_modelo_en_streaming(monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(agent, "client", fake)
    eventos = list(agent.stream_message("sess-034-a", "¿puedes analizar algo?", None))
    assert fake.calls == []
    texto = "".join(e["content"] for e in eventos if e["type"] == "token")
    assert texto == intent.CAPABILITY_REPLY
    assert eventos[-1]["type"] == "done"


def test_capacidad_no_llama_al_modelo_sin_streaming(monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(agent, "client", fake)
    out = agent.user_message("sess-034-b", "¿puedes analizar algo?", None)
    assert fake.calls == []
    assert out["content"] == intent.CAPABILITY_REPLY


# --- RF2: contexto acotado ---

def _sesion_larga(turnos):
    msgs = [{"role": "system", "content": "SYS"}]
    for i in range(turnos):
        msgs.append({"role": "user", "content": f"u{i}"})
        msgs.append({"role": "assistant", "content": f"a{i}"})
    return {"messages": msgs}


def test_contexto_envia_solo_los_ultimos_turnos(monkeypatch):
    monkeypatch.setattr(config, "HISTORY_TURNS", 3)
    s = _sesion_larga(8)
    ctx = agent._context(s)
    usuarios = [m["content"] for m in ctx if m["role"] == "user"]
    assert usuarios == ["u5", "u6", "u7"]
    assert ctx[0]["role"] == "system"


def test_contexto_completo_si_cabe(monkeypatch):
    monkeypatch.setattr(config, "HISTORY_TURNS", 10)
    s = _sesion_larga(3)
    assert agent._context(s) == s["messages"]


def test_historial_completo_se_conserva(monkeypatch):
    monkeypatch.setattr(config, "HISTORY_TURNS", 2)
    s = _sesion_larga(6)
    agent._context(s)
    assert len([m for m in s["messages"] if m["role"] == "user"]) == 6
