"""Diff en la aprobación, progreso en vivo y contexto estimado (Spec 037)."""
from types import SimpleNamespace

import pytest

import agent
import config
import preview
import progress
from tools import editing


def _lineas_de_cambio(diff):
    return [ln for ln in diff.splitlines() if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]


def test_diff_write_file_sobre_archivo_existente(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("uno\ndos\ntres\n", encoding="utf-8")
    d = preview.diff_for("write_file", {"path": str(f), "content": "uno\nDOS\ntres\n"})
    assert "-dos" in d and "+DOS" in d


def test_diff_archivo_nuevo_solo_anade(tmp_path):
    d = preview.diff_for("write_file", {"path": str(tmp_path / "n.txt"), "content": "a\nb\n"})
    cambios = _lineas_de_cambio(d)
    assert cambios and all(ln.startswith("+") for ln in cambios)


def test_diff_se_recorta_a_200_lineas(tmp_path):
    contenido = "".join(f"linea {i}\n" for i in range(300))
    d = preview.diff_for("write_file", {"path": str(tmp_path / "big.txt"), "content": contenido})
    assert "líneas más" in d
    assert len(d.splitlines()) <= preview.MAX_DIFF_LINES + 1


def test_diff_de_edit_lines_y_aplicacion(tmp_path):
    f = tmp_path / "e.txt"
    f.write_text("l1\nl2\nl3\nl4\nl5\n", encoding="utf-8")
    d = preview.diff_for("edit_lines", {"path": str(f), "start_line": 2, "end_line": 2, "new_text": "NUEVA"})
    assert "-l2" in d and "+NUEVA" in d
    assert f.read_text(encoding="utf-8") == "l1\nl2\nl3\nl4\nl5\n"   # la vista previa no toca el disco
    editing.edit_lines(str(f), 2, 2, "NUEVA")
    assert f.read_text(encoding="utf-8") == "l1\nNUEVA\nl3\nl4\nl5\n"


def test_apply_edit_rango_invalido():
    with pytest.raises(ValueError):
        editing.apply_edit("a\nb\n", 1, 5, "x")


def test_apply_edit_borrar_lineas():
    assert editing.apply_edit("a\nb\nc\n", 2, 2, "") == "a\nc\n"


def test_progreso_inicio_y_fin():
    progress.start("prog-1", "run_shell")
    st = progress.status("prog-1")
    assert st["action"] == "run_shell"
    assert st["elapsed_s"] >= 0
    progress.finish("prog-1")
    assert progress.status("prog-1")["action"] is None


def test_estado_de_sesion_incluye_contexto(monkeypatch):
    agent.get_session("st-037")
    st = agent.session_status("st-037")
    assert st["action"] is None
    assert st["context_limit"] == config.NUM_CTX
    assert st["context_tokens"] > 0
