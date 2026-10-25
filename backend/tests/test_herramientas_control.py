"""Herramientas de control: editar líneas, permisos, HTTP sin redirecciones y Git (Spec 039)."""
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import approvals
import tools.editing as ed
import tools.git_ops as go
import tools.web as wb


class _Servidor(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redir":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:1/otro")
            self.end_headers()
            return
        cuerpo = b"hola desde el servidor"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *args):
        pass


@pytest.fixture
def servidor():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Servidor)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def test_chmod_rechaza_modos_no_octales(tmp_path):
    f = tmp_path / "x.sh"
    f.write_text("echo\n")
    for modo in ("u+x", "999", "7555555"):
        with pytest.raises(ValueError):
            ed.chmod(str(f), modo)


def test_chmod_aplica_el_modo(tmp_path):
    f = tmp_path / "x.sh"
    f.write_text("echo\n")
    ed.chmod(str(f), "600")
    assert oct(f.stat().st_mode & 0o777) == "0o600"


def test_chmod_no_toca_la_raiz():
    with pytest.raises(PermissionError):
        ed.chmod("/", "755")


def test_edit_lines_fuera_de_rango(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("a\nb\n")
    with pytest.raises(ValueError):
        ed.edit_lines(str(f), 1, 9, "x")
    assert f.read_text() == "a\nb\n"


def test_http_get_responde(servidor):
    out = wb.http_get(servidor + "/")
    assert out.startswith("[HTTP 200]")
    assert "hola desde el servidor" in out


def test_http_get_no_sigue_redirecciones(servidor):
    out = wb.http_get(servidor + "/redir")
    assert "[HTTP 302]" in out
    assert "no se sigue" in out


def test_http_get_solo_http_y_https():
    with pytest.raises(ValueError):
        wb.http_get("file:///etc/passwd")


def test_git_rechaza_acciones_destructivas(tmp_path):
    for accion in ("reset", "clean", "checkout", "push --force"):
        with pytest.raises(ValueError):
            go.git_ops(accion, str(tmp_path))
    with pytest.raises(ValueError):
        go.git_ops("commit", str(tmp_path), "")


@pytest.mark.skipif(shutil.which("git") is None, reason="git no instalado")
def test_git_status_en_un_repositorio(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    out = go.git_ops("status", str(tmp_path))
    assert out.startswith("[exit 0]")


def test_aprobacion_de_git_status_no_pide_pero_push_si():
    assert not approvals.needs_approval("t-039", "git_ops", True, {"action": "status"})
    assert not approvals.needs_approval("t-039", "git_ops", True, {"action": "log"})
    assert approvals.needs_approval("t-039", "git_ops", True, {"action": "push"})


def test_http_y_chmod_siempre_piden_aprobacion():
    assert approvals.needs_approval("t-039", "http_get", True, {"url": "http://x"})
    assert approvals.needs_approval("t-039", "chmod", True, {"path": "a", "mode": "755"})
