"""Tests de persistencia (SQLite)."""
import db


def test_session_lifecycle():
    db.init()
    sid = db.create_session("Test pentest")
    db.add_message(sid, "user", "hola")
    db.add_message(sid, "assistant", "respuesta", "DeepHat")
    msgs = db.get_messages(sid)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    # aparece en el listado
    assert any(s["id"] == sid for s in db.list_sessions())
    # borrar limpia
    db.delete_session(sid)
    assert not any(s["id"] == sid for s in db.list_sessions())


def test_findings():
    db.init()
    sid = db.create_session("Test findings")
    db.add_finding(sid, "critical", "RCE", "10.0.0.1", "80", "desc", "evidencia")
    db.add_finding(sid, "low", "Banner info", "10.0.0.1", "22")
    fs = db.list_findings(sid)
    assert len(fs) == 2
    # orden por severidad: critical primero
    assert fs[0]["severity"] == "critical"
    db.delete_session(sid)


def test_audit_log():
    db.init()
    sid = db.create_session("Test audit")
    db.log_action(sid, "run_shell", '{"command":"ls"}', "salida", True)
    audit = db.get_audit(sid)
    assert len(audit) == 1
    assert audit[0]["tool"] == "run_shell"
    db.delete_session(sid)
