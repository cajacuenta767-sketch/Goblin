"""Spec 043 RF1: Detener termina los procesos que la IA lanzó en la terminal viva.

Usa una shell pty real (bash). Los procesos de prueba se identifican por su nombre
(sleep con un número raro) para no tocar nada ajeno.
"""
import os
import subprocess
import time

import psutil
import pytest

import cancel
import term_session


def _vivo(pid: int) -> bool:
    try:
        p = psutil.Process(pid)
        return p.status() != psutil.STATUS_ZOMBIE
    except psutil.Error:
        return False


def _buscar_sleep(segundos: str) -> list[int]:
    """PIDs de los sleep con ese argumento."""
    out = []
    for p in psutil.process_iter(["name", "cmdline"]):
        try:
            cmd = p.info.get("cmdline") or []
            if p.info.get("name") == "sleep" and cmd[-1:] == [segundos]:
                out.append(p.pid)
        except psutil.Error:
            continue
    return out


@pytest.fixture
def term():
    if not term_session.PTY_AVAILABLE:
        pytest.skip("pty no disponible")
    sid = "detener-43"
    term_session.set_session(sid)
    t = term_session.get_terminal(sid)
    yield t
    cancel.kill_terminal_tree(sid)


def test_detener_mata_el_proceso_que_lanzo_la_ia(term):
    term.run("sleep 987654 &")
    time.sleep(0.5)
    pids = _buscar_sleep("987654")
    assert pids, "el sleep en segundo plano debería existir"
    assert cancel.kill_terminal_tree("detener-43") >= 1
    time.sleep(0.5)
    assert not any(_vivo(p) for p in pids), "Detener debe terminar el proceso de la IA"


def test_la_shell_del_usuario_sigue_viva_tras_detener(term):
    term.run("sleep 987655 &")
    time.sleep(0.5)
    cancel.kill_terminal_tree("detener-43")
    time.sleep(0.3)
    assert "vivo_43" in term.run("echo vivo_43")


def test_no_mata_procesos_sin_etiqueta(term):
    ajeno = subprocess.Popen(["sleep", "987656"])  # lanzado por el test, sin etiqueta
    try:
        time.sleep(0.3)
        cancel.kill_terminal_tree("detener-43")
        time.sleep(0.2)
        assert ajeno.poll() is None, "un proceso sin etiqueta no debe morir"
    finally:
        ajeno.kill()
        ajeno.wait()


def test_otra_sesion_no_mata_los_procesos_de_esta(term):
    term.run("sleep 987657 &")
    time.sleep(0.5)
    pids = _buscar_sleep("987657")
    try:
        cancel.kill_terminal_tree("otra-sesion")
        time.sleep(0.2)
        assert all(_vivo(p) for p in pids)
    finally:
        cancel.kill_terminal_tree("detener-43")


def test_salida_sin_marcas_de_la_envoltura(term):
    out = term.run("echo hola_43")
    assert "hola_43" in out
    assert cancel.TERM_TAG_VAR not in out
    assert cancel.TERM_TAG_VAR not in term.read_recent()


def test_etiqueta_saneada():
    assert cancel.safe_tag("a/b c;d") == "abcd"
    assert cancel.safe_tag("") == "main"
    assert cancel.safe_tag("sesion-01_x") == "sesion-01_x"


def test_request_incluye_procesos_de_terminal(term):
    term.run("sleep 987658 &")
    time.sleep(0.5)
    pids = _buscar_sleep("987658")
    n = cancel.request("detener-43")
    time.sleep(0.3)
    assert n >= 1
    assert not any(_vivo(p) for p in pids)
    cancel.clear("detener-43")
