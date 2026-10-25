"""Tests de rendimiento sin perder inteligencia (Spec 032)."""
from types import SimpleNamespace

import agent
import config
import router


def _chunk(text="", tool_calls=None):
    return SimpleNamespace(message=SimpleNamespace(content=text, tool_calls=tool_calls))


class _FakeClient:
    """Cliente de Ollama simulado: cuenta cada llamada al modelo."""

    def __init__(self, chunks):
        self.chunks = chunks
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return iter(self.chunks)


def _collect(gen):
    return list(gen)


# --- RF3: recorte de salidas de herramientas ---

def test_salida_corta_no_se_toca():
    assert agent._fit_tool_output("hola", limit=100) == "hola"


def test_salida_larga_conserva_inicio_y_final():
    texto = "A" * 500 + "MEDIO" + "Z" * 500
    out = agent._fit_tool_output(texto, limit=300)
    assert out.startswith("A")
    assert out.rstrip().endswith("Z")
    assert "omitidos" in out
    assert len(out) < len(texto)


# --- RF4: system prompt sin comandos inexistentes ---

def test_system_prompt_sin_comandos_inexistentes():
    for cmd in ("/target", "/recon", "/scan", "/report"):
        assert cmd not in agent.SYSTEM_PROMPT


# --- RF5 y RF6: saludos y temas de pentest ---

def test_saludo_corto_es_saludo():
    assert router.is_greeting("hola")
    assert router.is_greeting("¡Gracias!")
    assert router.is_greeting("buenas tardes")


def test_pregunta_no_es_saludo():
    assert not router.is_greeting("hola, ¿qué puedes hacer?")
    assert not router.is_greeting("crea una carpeta llamada pruebas")


def test_detecta_tema_pentest():
    assert router.needs_local_intent("escanea 10.0.0.5 con nmap")
    assert router.needs_local_intent("hay un exploit para este servicio")
    assert router.needs_local_intent("busca el CVE-2021-44228")


def test_charla_normal_no_es_pentest():
    assert not router.needs_local_intent("cómo hago una tortilla de patatas")


# --- RF1: una sola generación por respuesta de texto ---

def test_respuesta_de_texto_se_genera_una_sola_vez(monkeypatch):
    fake = _FakeClient([_chunk("Hola "), _chunk("de nuevo")])
    monkeypatch.setattr(agent, "client", fake)
    monkeypatch.setattr(config, "FAST_MODEL", "")
    eventos = _collect(agent.stream_message("sess-una-vez", "explícame los puertos", None))
    assert len(fake.calls) == 1, "el modelo debe llamarse UNA sola vez"
    tokens = "".join(e["content"] for e in eventos if e["type"] == "token")
    assert tokens == "Hola de nuevo"
    assert eventos[-1]["type"] == "done"


def test_herramienta_en_stream_descarta_texto_y_pasa_a_fallback(monkeypatch):
    llamada = SimpleNamespace(function=SimpleNamespace(name="list_dir", arguments={}))
    fake = _FakeClient([_chunk("Voy a listar"), _chunk("", tool_calls=[llamada])])
    monkeypatch.setattr(agent, "client", fake)
    monkeypatch.setattr(config, "FAST_MODEL", "")
    sid = "sess-herramienta"
    eventos = _collect(agent.stream_message(sid, "lista la carpeta actual", None))
    tipos = [e["type"] for e in eventos]
    assert "discard" in tipos and tipos[-1] == "fallback"
    # El mensaje del usuario se quita: user_message lo volverá a añadir.
    msgs = agent.sessions[sid]["messages"]
    assert msgs[-1]["role"] != "user" or msgs[-1]["content"] != "lista la carpeta actual"


# --- RF5: modelo rápido solo para saludos, sin herramientas ---

def test_saludo_usa_modelo_rapido_sin_herramientas(monkeypatch):
    fake = _FakeClient([_chunk("¡Hola!")])
    monkeypatch.setattr(agent, "client", fake)
    monkeypatch.setattr(config, "FAST_MODEL", "qwen-rapido:1.5b")
    _collect(agent.stream_message("sess-saludo", "hola", None))
    assert fake.calls[0]["model"] == "qwen-rapido:1.5b"
    assert fake.calls[0]["tools"] is None


def test_pregunta_sigue_con_modelo_principal(monkeypatch):
    fake = _FakeClient([_chunk("Respuesta")])
    monkeypatch.setattr(agent, "client", fake)
    monkeypatch.setattr(config, "FAST_MODEL", "qwen-rapido:1.5b")
    _collect(agent.stream_message("sess-pregunta", "explica qué es un SYN scan", None))
    assert fake.calls[0]["model"] == config.DEFAULT_MODEL
    # Una pregunta no lleva herramientas (Spec 033).
    assert fake.calls[0]["tools"] is None


# --- RF7: hilos de CPU en cada llamada ---

def test_opciones_incluyen_hilos_y_contexto():
    opts = agent._opts()
    assert opts["num_ctx"] == config.NUM_CTX
    assert opts["num_thread"] == config.NUM_THREAD


# --- RF2: Detener corta aunque el modelo tarde en dar el primer token ---

def test_detener_corta_antes_del_primer_token(monkeypatch):
    import time

    class _Lento:
        def chat(self, **kwargs):
            def gen():
                time.sleep(5)
                yield _chunk("tarde")
            return gen()

    monkeypatch.setattr(agent, "client", _Lento())
    monkeypatch.setattr(agent.cancel, "is_cancelled", lambda sid: True)
    t0 = time.time()
    eventos = _collect(agent.stream_message("sess-detener", "explica algo", None))
    assert time.time() - t0 < 2, "Detener debe responder en menos de 2 s"
    assert eventos[-1]["type"] == "stopped"
