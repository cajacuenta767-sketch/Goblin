"""Spec 045: Gemini como orquestador, relevo local sin bloquear y guarda de privacidad completa.

Todo con clientes simulados: no hay clave de Gemini ni Ollama en estas pruebas.
"""
from types import SimpleNamespace

import pytest
from google.genai import types
from ollama import Message

import agent
import config
import gemini_client          # el mismo módulo que usa agent (agent añade core/llm al path)
import router


class _DB:
    def add_message(self, *a, **k):
        pass

    def log_action(self, *a, **k):
        pass


class _Gemini:
    """Sustituye gemini_client.chat: devuelve o lanza, en orden, lo que se le indique."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []

    def __call__(self, mensajes, herramientas):
        self.llamadas.append((list(mensajes), herramientas))
        r = self.respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


class _DeepHat:
    """Sustituye agent.client (Ollama): responde texto fijo y guarda lo que recibió."""

    def __init__(self, texto="respuesta local"):
        self.texto = texto
        self.llamadas = []

    def chat(self, **kw):
        self.llamadas.append(kw)
        return SimpleNamespace(message=SimpleNamespace(content=self.texto, tool_calls=None))


def _resp(texto="", llamadas=None):
    return gemini_client._Response(gemini_client._Message(texto, llamadas))


def _sesion(sid, texto):
    return {
        "sid": sid, "model": "deephat-test",
        "messages": [{"role": "system", "content": "sistema"}, {"role": "user", "content": texto}],
        "queue": [], "steps": 0, "allowed": None,
    }


@pytest.fixture
def entorno(monkeypatch):
    sid = "t-orquestador"
    monkeypatch.setattr(config, "GEMINI_API_KEY", "clave-falsa")
    monkeypatch.setattr(agent, "db", _DB())
    monkeypatch.setattr(agent, "_log", lambda *a, **k: None)
    monkeypatch.setattr(agent, "_scope_block", lambda *a, **k: None)
    monkeypatch.setattr(agent, "_current_target", lambda: "")
    monkeypatch.setattr(agent, "_sensitive_terms", lambda sid: [])
    monkeypatch.setattr(agent.engagement, "summary", lambda sid: "")
    router.set_mode(sid, "hybrid")
    yield sid
    router.set_mode(sid, "local")


def test_gemini_responde_primero(entorno, monkeypatch):
    s = _sesion(entorno, "explícame qué es un proxy")
    gem = _Gemini(_resp("Un proxy es un intermediario."))
    dh = _DeepHat()
    monkeypatch.setattr(gemini_client, "chat", gem)
    monkeypatch.setattr(agent, "client", dh)

    resp = agent._call_model(s, entorno)

    assert resp.message.content == "Un proxy es un intermediario."
    assert resp._goblin_model == "Gemini"
    assert dh.llamadas == []


def test_pentest_sin_datos_sensibles_va_primero_a_gemini(entorno, monkeypatch):
    """Spec 045 D2: el antiguo atajo de pentest (Spec 032 RF6) ya no manda a DeepHat."""
    s = _sesion(entorno, "qué es una vulnerabilidad de inyección SQL")
    gem = _Gemini(_resp("Es una falla en la que la entrada se interpreta como SQL."))
    dh = _DeepHat()
    monkeypatch.setattr(gemini_client, "chat", gem)
    monkeypatch.setattr(agent, "client", dh)

    resp = agent._call_model(s, entorno)

    assert len(gem.llamadas) == 1
    assert resp._goblin_model == "Gemini"
    assert dh.llamadas == []


def test_datos_sensibles_no_llegan_a_gemini(entorno, monkeypatch):
    s = _sesion(entorno, "escanea 10.0.0.7")
    gem = _Gemini()                      # si se llamara, fallaría por falta de respuestas
    dh = _DeepHat("ok")
    monkeypatch.setattr(gemini_client, "chat", gem)
    monkeypatch.setattr(agent, "client", dh)

    resp = agent._call_model(s, entorno)

    assert gem.llamadas == []
    assert resp._goblin_model == "DeepHat"
    assert resp._goblin_note.startswith("🔒")


def test_modo_local_no_llama_a_gemini(entorno, monkeypatch):
    router.set_mode(entorno, "local")
    s = _sesion(entorno, "hola")
    gem = _Gemini()
    dh = _DeepHat("hola")
    monkeypatch.setattr(gemini_client, "chat", gem)
    monkeypatch.setattr(agent, "client", dh)

    agent._call_model(s, entorno)

    assert gem.llamadas == []
    assert len(dh.llamadas) == 1


def test_error_de_gemini_repite_el_paso_con_deephat(entorno, monkeypatch):
    s = _sesion(entorno, "dime algo")
    gem = _Gemini(RuntimeError("Gemini bloqueó la petición: SAFETY"))
    dh = _DeepHat("respuesta local")
    monkeypatch.setattr(gemini_client, "chat", gem)
    monkeypatch.setattr(agent, "client", dh)

    resp = agent._call_model(s, entorno)

    assert resp._goblin_model == "DeepHat"
    assert "no respondió" in resp._goblin_note
    assert dh.llamadas[0]["messages"] == agent._context(s)   # mismo historial


def test_negativa_de_gemini_no_entra_en_el_historial(entorno, monkeypatch):
    s = _sesion(entorno, "dime algo")
    antes = len(s["messages"])
    gem = _Gemini(_resp("Lo siento, pero no puedo ayudar con eso."))
    dh = _DeepHat("respuesta local")
    monkeypatch.setattr(gemini_client, "chat", gem)
    monkeypatch.setattr(agent, "client", dh)

    resp = agent._call_model(s, entorno)

    assert resp._goblin_model == "DeepHat"
    assert "se negó" in resp._goblin_note
    assert len(s["messages"]) == antes


def test_relevo_a_mitad_de_bucle_no_se_detiene(entorno, monkeypatch):
    """Gemini pide una herramienta, la herramienta se ejecuta, y en el paso siguiente Gemini se niega.
    DeepHat debe continuar con el historial real (mensajes de herramienta incluidos)."""
    s = _sesion(entorno, "lista la carpeta actual")
    gem = _Gemini(
        _resp("", [gemini_client._ToolCall("list_dir", {"path": "."})]),
        _resp("Lo siento, pero no puedo ayudar con eso."),
    )
    dh = _DeepHat("Aquí tienes el contenido de la carpeta.")
    monkeypatch.setattr(gemini_client, "chat", gem)
    monkeypatch.setattr(agent, "client", dh)

    out = agent._step(s, entorno)

    assert out["type"] == "text"
    assert out["model"] == "DeepHat"
    assert out["content"] == "Aquí tienes el contenido de la carpeta."
    recibidos = dh.llamadas[0]["messages"]
    assert all(isinstance(m, (dict, Message)) for m in recibidos)     # convertidos a formato Ollama
    assert any(isinstance(m, dict) and m.get("tool_name") == "list_dir" for m in recibidos)
    assert any(isinstance(m, dict) and m.get("tool_calls") for m in recibidos)


def test_guarda_lee_el_texto_de_objetos_de_gemini():
    """Spec 045 RF4: antes, str() de un objeto de Gemini no incluía su texto."""
    msg = gemini_client._Message("el servidor está en 192.168.1.20")
    assert router.sensitive_reason([msg]) == "una dirección IP"


def test_guarda_lee_los_argumentos_de_las_llamadas():
    llam = gemini_client._ToolCall("run_shell", {"command": "ping 10.1.2.3"})
    msg = gemini_client._Message("", [llam])
    assert router.sensitive_reason([msg]) == "una dirección IP"


def test_historial_de_gemini_usa_llamadas_y_respuestas_de_funcion():
    firma = types.Part(function_call=types.FunctionCall(name="read_file", args={"path": "a.txt"}),
                       thought_signature=b"firma-123")
    llam = gemini_client._ToolCall("read_file", {"path": "a.txt"}, part=firma)
    msgs = [
        {"role": "system", "content": "sistema"},
        {"role": "user", "content": "lee a.txt"},
        gemini_client._Message("", [llam]),
        {"role": "tool", "content": "hola", "tool_name": "read_file"},
    ]

    sistema, contenidos = gemini_client._convertir(msgs)

    assert sistema == "sistema"
    assert [c.role for c in contenidos] == ["user", "model", "user"]
    llamada = contenidos[1].parts[0]
    assert llamada.function_call.name == "read_file"
    assert llamada.thought_signature == b"firma-123"          # firma original conservada
    respuesta = contenidos[2].parts[0].function_response
    assert respuesta.name == "read_file"
    assert respuesta.response == {"result": "hola"}


def test_llamada_sin_firma_se_convierte_con_sus_argumentos():
    msgs = [
        {"role": "user", "content": "lista"},
        {"role": "assistant", "content": "", "tool_calls": [
            {"function": {"name": "list_dir", "arguments": {"path": "."}}}]},
        {"role": "tool", "content": "a.txt", "tool_name": "list_dir"},
    ]

    _, contenidos = gemini_client._convertir(msgs)

    fc = contenidos[1].parts[0].function_call
    assert fc.name == "list_dir" and fc.args == {"path": "."}


def test_varias_respuestas_de_herramienta_van_en_el_mismo_turno():
    msgs = [
        {"role": "user", "content": "compara"},
        {"role": "assistant", "content": "", "tool_calls": [
            {"function": {"name": "read_file", "arguments": {"path": "a"}}},
            {"function": {"name": "read_file", "arguments": {"path": "b"}}}]},
        {"role": "tool", "content": "A", "tool_name": "read_file"},
        {"role": "tool", "content": "B", "tool_name": "read_file"},
    ]

    _, contenidos = gemini_client._convertir(msgs)

    assert len(contenidos) == 3
    assert len(contenidos[2].parts) == 2


def test_finish_reason_de_seguridad_lanza_error(monkeypatch):
    respuesta = types.GenerateContentResponse(candidates=[types.Candidate(
        finish_reason=types.FinishReason.SAFETY,
        content=types.Content(role="model", parts=[types.Part(text="parcial")]),
    )])
    cliente = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kw: respuesta))
    monkeypatch.setattr(gemini_client, "_client", lambda: cliente)
    monkeypatch.setattr(config, "GEMINI_API_KEY", "clave-falsa")

    with pytest.raises(RuntimeError, match="SAFETY"):
        gemini_client.chat([{"role": "user", "content": "hola"}], [])


def test_plan_visible_lo_genera_gemini_sin_herramientas(entorno, monkeypatch):
    """Spec 045 RF7: el plan de Spec 035 también pasa por el router."""
    s = _sesion(entorno, "instala requests y luego lee el txt")
    gem = _Gemini(_resp("1. Instalar requests. ¿Lo ejecuto?"))
    dh = _DeepHat()
    monkeypatch.setattr(gemini_client, "chat", gem)
    monkeypatch.setattr(agent, "client", dh)

    texto, modelo = agent._plan_nonstream(s)

    assert modelo == "Gemini"
    assert "¿Lo ejecuto?" in texto
    assert gem.llamadas[0][1] == []          # sin herramientas
    assert dh.llamadas == []


def test_para_ollama_respeta_mensajes_ya_validos():
    m = Message(role="assistant", content="x")
    assert agent._para_ollama([m])[0] is m


def test_pista_de_modulo_llega_al_resultado_de_la_herramienta(monkeypatch):
    monkeypatch.setattr(agent, "run_tool", lambda name, args: "ModuleNotFoundError: No module named 'yaml'")
    call = gemini_client._ToolCall("term_run", {"command": "python3 script.py"})

    hecho = agent._exec(call, sid=None, approved=True)

    assert "yaml" in hecho["result"] and "install_package" in hecho["result"]
