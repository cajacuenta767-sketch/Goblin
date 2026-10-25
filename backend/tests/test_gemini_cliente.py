"""Spec 044 RF1: cliente de Gemini sobre google-genai. Usa tipos reales del SDK y un cliente simulado."""
import pytest
from google.genai import types

import config
from core.llm import gemini_client as g
from tools import registry


class _Models:
    def __init__(self, respuesta):
        self.respuesta = respuesta
        self.llamada = None

    def generate_content(self, **kwargs):
        self.llamada = kwargs
        return self.respuesta


class _Cliente:
    def __init__(self, respuesta):
        self.models = _Models(respuesta)


@pytest.fixture
def con_clave(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "clave-de-prueba")


def _respuesta(*partes):
    return types.GenerateContentResponse(candidates=[
        types.Candidate(content=types.Content(role="model", parts=list(partes)))
    ])


def _usar(monkeypatch, respuesta):
    cliente = _Cliente(respuesta)
    monkeypatch.setattr(g, "_client", lambda: cliente)
    return cliente


def test_herramientas_de_goblin_son_declaraciones_validas():
    tools = g._to_gemini_tools(registry.SCHEMAS)
    decls = tools[0].function_declarations
    assert len(decls) == len(registry.SCHEMAS)
    nombres = {d.name for d in decls}
    assert {"read_file", "run_shell", "edit_lines"} <= nombres


def test_sin_herramientas_no_se_declara_ninguna():
    assert g._to_gemini_tools([]) is None


def test_sin_clave_no_esta_disponible(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    assert g.available() is False
    with pytest.raises(RuntimeError):
        g.chat([{"role": "user", "content": "hola"}], [])


def test_respuesta_de_texto(con_clave, monkeypatch):
    cliente = _usar(monkeypatch, _respuesta(types.Part(text="Hola, soy GOBLIN.")))
    resp = g.chat([{"role": "user", "content": "hola"}], [])
    assert resp.message.content == "Hola, soy GOBLIN."
    assert resp.message.tool_calls is None
    assert cliente.models.llamada["model"] == config.GEMINI_MODEL


def test_llamada_a_herramienta(con_clave, monkeypatch):
    parte = types.Part(function_call=types.FunctionCall(name="read_file", args={"path": "a.txt"}))
    _usar(monkeypatch, _respuesta(parte))
    resp = g.chat([{"role": "user", "content": "lee a.txt"}], registry.SCHEMAS)
    llamada = resp.message.tool_calls[0].function
    assert llamada.name == "read_file"
    assert llamada.arguments == {"path": "a.txt"}


def test_razonamiento_interno_no_se_muestra(con_clave, monkeypatch):
    _usar(monkeypatch, _respuesta(
        types.Part(text="razonamiento interno", thought=True),
        types.Part(text="Respuesta final"),
    ))
    assert g.chat([{"role": "user", "content": "x"}], []).message.content == "Respuesta final"


def test_sin_respuesta_utilizable_lanza_para_caer_a_deephat(con_clave, monkeypatch):
    _usar(monkeypatch, types.GenerateContentResponse(candidates=[]))
    with pytest.raises(RuntimeError, match="respuesta"):
        g.chat([{"role": "user", "content": "x"}], [])


def test_peticion_bloqueada_lanza(con_clave, monkeypatch):
    _usar(monkeypatch, types.GenerateContentResponse(
        prompt_feedback=types.GenerateContentResponsePromptFeedback(block_reason="SAFETY")))
    with pytest.raises(RuntimeError, match="bloque"):
        g.chat([{"role": "user", "content": "x"}], [])


def test_system_va_a_instruccion_y_mensajes_vacios_se_omiten(con_clave, monkeypatch):
    cliente = _usar(monkeypatch, _respuesta(types.Part(text="ok")))
    g.chat([
        {"role": "system", "content": "Eres GOBLIN."},
        {"role": "user", "content": "hola"},
        {"role": "assistant", "content": "   "},
        {"role": "assistant", "content": "¡Hola!"},
    ], [])
    llamada = cliente.models.llamada
    assert llamada["config"].system_instruction == "Eres GOBLIN."
    roles = [c.role for c in llamada["contents"]]
    assert roles == ["user", "model"]
