"""Tests de la terminal viva compartida (IA + usuario)."""
import term_session
from tools import terminal_tool as tt


def test_term_persists_state():
    term_session.set_session("term-test")
    # cd persiste entre llamadas
    tt.term_run("cd /tmp")
    out = tt.term_run("pwd")
    assert "/tmp" in out


def test_term_variables_persist():
    term_session.set_session("term-test2")
    tt.term_run("export GTEST=hola")
    out = tt.term_run("echo VAL=$GTEST")
    assert "VAL=hola" in out


def test_term_blocks_dangerous():
    term_session.set_session("term-test3")
    out = tt.term_run("rm -rf /")
    assert "BLOQUEADO" in out


def test_term_read():
    term_session.set_session("term-test4")
    tt.term_run("echo marcador_unico_123")
    out = tt.term_read()
    assert "marcador_unico_123" in out
