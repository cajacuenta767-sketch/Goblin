"""Tests de informe y targets."""
import db
import report
from tools import targets
import state


def test_report_generation():
    db.init()
    sid = db.create_session("Test reporte")
    db.add_finding(sid, "high", "SQLi", "10.0.0.5", "80", "Inyección en login", "' OR 1=1")
    md = report.generate(sid)
    assert "# Informe de Pentest" in md
    assert "SQLi" in md
    assert "Resumen ejecutivo" in md
    db.delete_session(sid)


def test_target_creates_structure():
    out = targets.set_target("192.168.1.100")
    assert "recon" in out and "loot" in out
    assert state.get_target() == "192.168.1.100"
    targets.clear_target()
    assert state.get_target() == ""


def test_empty_target_rejected():
    assert "vacío" in targets.set_target("   ")
