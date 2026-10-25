"""Spec 044 RF2–RF4: editor completo, adjuntos grandes y lectura por tramos."""
import pytest
from fastapi.testclient import TestClient

import config
import main
from tools import filesystem as fs

LOCAL = ("127.0.0.1", 50000)


@pytest.fixture
def ws(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "WORKSPACE", tmp_path)
    return tmp_path


def _archivo(ws, nombre, lineas):
    p = ws / nombre
    p.write_text("".join(f"linea {i:05d} " + "x" * 20 + "\n" for i in range(lineas)), encoding="utf-8")
    return p


def test_archivo_pequeno_se_devuelve_entero(ws):
    p = ws / "corto.txt"
    p.write_text("uno\ndos\n", encoding="utf-8")
    assert fs.read_file(str(p)) == "uno\ndos\n"


def test_tramo_con_cabecera_y_continuacion(ws):
    p = _archivo(ws, "grande.txt", 2000)
    out = fs.read_file(str(p), desde=2001 - 1000, lineas=100)
    assert out.startswith("[grande.txt: líneas 1001-")
    assert "linea 01000" in out
    assert "sigue en la línea" in out


def test_tramo_nunca_pasa_de_5000_caracteres(ws):
    p = _archivo(ws, "ancho.txt", 400)          # cada línea ~30 caracteres
    out = fs.read_file(str(p), desde=1, lineas=400)
    assert len(out) <= fs.MAX_READ_CHARS + 300   # cabecera y pie incluidos
    assert "usa read_file con desde=" in out


def test_desde_fuera_de_rango(ws):
    p = _archivo(ws, "corto2.txt", 200)
    assert "fuera del archivo" in fs.read_file(str(p), desde=5000)


def test_editor_recibe_el_archivo_completo(ws):
    p = _archivo(ws, "tres_mil.txt", 3000)     # ~102 KB, antes se cortaba a 30 000
    texto = fs.read_file_completo(str(p))
    assert texto == p.read_text(encoding="utf-8")
    assert texto.count("\n") == 3000


def test_editor_rechaza_mas_de_5_mb(ws):
    p = ws / "enorme.bin"
    p.write_bytes(b"a" * (fs.MAX_EDIT_BYTES + 10))
    with pytest.raises(ValueError, match="5 MB"):
        fs.read_file_completo(str(p))


def test_adjunto_se_guarda_en_workspace_con_nombre_seguro(ws):
    r = fs.guardar_adjunto("../../mi informe (final).txt", "hola\nmundo\n")
    assert r["relative"] == "adjuntos/mi_informe_final.txt"
    assert (ws / "adjuntos" / "mi_informe_final.txt").read_text(encoding="utf-8") == "hola\nmundo\n"
    assert r["lines"] == 2


def test_adjunto_repetido_no_sobrescribe(ws):
    a = fs.guardar_adjunto("datos.csv", "1\n")
    b = fs.guardar_adjunto("datos.csv", "2\n")
    assert a["relative"] == "adjuntos/datos.csv"
    assert b["relative"] == "adjuntos/datos-2.csv"
    assert (ws / "adjuntos" / "datos.csv").read_text(encoding="utf-8") == "1\n"


def test_adjunto_mayor_de_5_mb_se_rechaza(ws):
    with pytest.raises(ValueError, match="5 MB"):
        fs.guardar_adjunto("x.txt", "a" * (fs.MAX_EDIT_BYTES + 1))


def test_api_file_devuelve_contenido_completo(ws):
    p = _archivo(ws, "api.txt", 3000)
    c = TestClient(main.app, client=LOCAL)
    r = c.get("/api/file", params={"path": str(p)})
    assert r.status_code == 200
    assert r.json()["content"] == p.read_text(encoding="utf-8")


def test_api_file_informa_si_pesa_demasiado(ws):
    p = ws / "pesado.bin"
    p.write_bytes(b"a" * (fs.MAX_EDIT_BYTES + 10))
    c = TestClient(main.app, client=LOCAL)
    r = c.get("/api/file", params={"path": str(p)})
    assert r.status_code == 400
    assert "5 MB" in r.json()["error"]


def test_api_adjunto_responde_ruta_relativa(ws):
    c = TestClient(main.app, client=LOCAL)
    r = c.post("/api/adjunto", json={"name": "notas.md", "content": "# hola\n"})
    assert r.status_code == 200
    assert r.json()["relative"] == "adjuntos/notas.md"


def test_read_file_acepta_los_parametros_del_modelo(ws):
    from tools import registry
    schema = next(s for s in registry.SCHEMAS if s["function"]["name"] == "read_file")
    props = schema["function"]["parameters"]["properties"]
    assert {"path", "desde", "lineas"} <= set(props)
    assert props["desde"]["type"] == "integer"
