"""Tests de Spec 024 (Detener) y Spec 025 (guardas de privacidad y autorización)."""
import threading
import time

import agent
import approvals
import cancel
import router
from tools import registry
from tools.registry import NEEDS_APPROVAL


# ---------- Spec 024: Detener ----------

def test_detener_mata_shell_en_curso():
    sid = "t-shell-stop"
    cancel.clear(sid)
    cancel.set_session(sid)
    out = {}

    def run():
        out["r"] = registry.run_tool("run_shell", {"command": "sleep 30"})

    t = threading.Thread(target=run)
    t.start()
    time.sleep(0.7)
    matados = cancel.request(sid)
    t.join(timeout=5)
    cancel.set_session(None)
    cancel.clear(sid)
    assert not t.is_alive(), "run_shell no terminó tras Detener"
    assert matados >= 1
    assert "CANCELADO" in out["r"]


def test_detener_evita_ejecutar_herramientas_pendientes(monkeypatch):
    sid = "t-cola-stop"
    cancel.clear(sid)
    s = agent.get_session(sid)
    llamadas = []
    monkeypatch.setattr(agent, "_call_model", lambda s, sid=None: llamadas.append(1))
    s["queue"] = [agent._FakeCall("list_dir", {"path": "."})]
    cancel.request(sid)
    res = agent._step(s, sid)
    cancel.clear(sid)
    agent.reset_session(sid)
    assert res["type"] == "stopped"
    assert llamadas == []
    assert s["queue"] == []


def test_detener_corta_llamada_al_modelo_en_curso(monkeypatch):
    sid = "t-modelo-stop"
    cancel.clear(sid)
    s = agent.get_session(sid)

    def modelo_lento(s, sid=None):
        time.sleep(3)
        return None

    monkeypatch.setattr(agent, "_call_model", modelo_lento)
    threading.Timer(0.3, lambda: cancel.request(sid)).start()
    t0 = time.time()
    res = agent._step(s, sid)
    dt = time.time() - t0
    cancel.clear(sid)
    agent.reset_session(sid)
    assert res["type"] == "stopped"
    assert dt < 2.0, f"tardó {dt:.1f}s en responder a Detener"


# ---------- Spec 025: guardas ----------

def test_detecta_ip_en_historial():
    msgs = [{"role": "system", "content": "Eres GOBLIN"},
            {"role": "user", "content": "escanea 10.10.10.5"}]
    assert router.sensitive_reason(msgs, "") == "una dirección IP"


def test_detecta_rango_cidr_en_salida_de_herramienta():
    msgs = [{"role": "tool", "content": "red 192.168.0.0/24 activa"}]
    assert router.sensitive_reason(msgs, "") == "un rango de red"


def test_detecta_objetivo_activo_por_nombre():
    msgs = [{"role": "user", "content": "revisa example-corp.local"}]
    assert router.sensitive_reason(msgs, "example-corp.local") == "el objetivo activo"


def test_sin_datos_sensibles_no_bloquea():
    msgs = [{"role": "system", "content": "Eres GOBLIN, versión dos"},
            {"role": "user", "content": "hola, ¿qué puedes hacer?"}]
    assert router.sensitive_reason(msgs, "") is None


def test_set_target_pide_aprobacion_en_todos_los_niveles():
    assert "set_target" in NEEDS_APPROVAL
    for nivel in ("cauto", "normal", "confianza"):
        approvals.set_level("t-auth", nivel)
        assert approvals.needs_approval("t-auth", "set_target", True) is True
    approvals.set_level("t-auth", "cauto")


def test_hibrido_con_ip_responde_deephat_sin_llamar_gemini(monkeypatch):
    """Spec 025: con API key y modo híbrido, un dato sensible fuerza DeepHat y deja nota."""
    import config
    from types import SimpleNamespace
    sid = "t-hibrido"
    monkeypatch.setattr(config, "GEMINI_API_KEY", "clave-falsa")
    monkeypatch.setattr(router, "gemini_available", lambda: True)
    router.set_mode(sid, "hybrid")
    s = agent.get_session(sid)
    s["messages"].append({"role": "user", "content": "escanea 10.0.0.7"})

    def fake_deephat(sess):
        return SimpleNamespace(message=SimpleNamespace(content="ok", tool_calls=None))

    monkeypatch.setattr(agent, "_call_deephat", fake_deephat)
    resp = agent._call_model(s, sid)
    router.set_mode(sid, "local")
    agent.reset_session(sid)
    assert getattr(resp, "_goblin_note", "").startswith("🔒")
    assert "Gemini no recibió nada" in resp._goblin_note


def test_detener_vacia_cola_de_aprobacion():
    sid = "t-aprob-stop"
    cancel.clear(sid)
    s = agent.get_session(sid)
    s["queue"] = [agent._FakeCall("write_file", {"path": "x", "content": "y"})]
    res = agent.stop(sid)
    cancel.clear(sid)
    agent.reset_session(sid)
    assert res["ok"] is True
    assert s["queue"] == []
