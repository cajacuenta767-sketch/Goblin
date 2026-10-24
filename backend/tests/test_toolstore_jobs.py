"""Tests de Spec 027 (instalar con contraseña y registro en vivo).

Usan un `sudo` y un `apt-get` FALSOS en el PATH: los procesos y las tuberías son reales,
pero no se instala nada. El `sudo` falso exige la contraseña por stdin, igual que el real.
"""
import json
import os
import time

import pytest

import toolstore
import toolstore_jobs

SUDO_FALSO = r'''#!/bin/bash
# sudo falso: anota sus argumentos en un registro y exige la contraseña por stdin (-S).
echo "ARGV: $*" >> "${FAKE_SUDO_LOG:-/dev/null}"
if [ "$1" = "-n" ]; then
  if [ -n "$FAKE_SUDO_NOPASS" ]; then shift; exec "$@"; fi
  echo "sudo: a password is required" >&2
  exit 1
fi
if [ "$1" = "-S" ]; then
  if [ -n "$FAKE_SUDO_NOPASS" ]; then shift 3; exec "$@"; fi
  read -r pw
  if [ "$pw" != "${FAKE_SUDO_PASS:-secreto-test}" ]; then
    echo "Sorry, try again." >&2
    echo "sudo: 1 incorrect password attempt" >&2
    exit 1
  fi
  shift 3
  exec "$@"
fi
exit 1
'''

APT_FALSO = r'''#!/bin/bash
# apt-get falso: crea o borra un "binario" en FAKE_BIN_DIR. No instala nada real.
echo "fake apt-get $*"
pkg="${@: -1}"
case "$1" in
  update) echo "Obteniendo listas de paquetes (falso)"; exit 0 ;;
  install)
    if [ "$pkg" = "dirb" ]; then echo "Instalando dirb (lento)…"; sleep 30; fi
    echo "Configurando $pkg (falso)"
    printf '#!/bin/sh\necho falso\n' > "$FAKE_BIN_DIR/$pkg"; chmod +x "$FAKE_BIN_DIR/$pkg"
    echo "Instalación de $pkg completada"; exit 0 ;;
  remove) rm -f "$FAKE_BIN_DIR/$pkg"; echo "Eliminado $pkg (falso)"; exit 0 ;;
esac
exit 1
'''


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    bindir = tmp_path / "bin"
    fakes = tmp_path / "fakes"          # aquí aparecen los "binarios" instalados
    bindir.mkdir()
    fakes.mkdir()
    for nombre, cuerpo in (("sudo", SUDO_FALSO), ("apt-get", APT_FALSO)):
        ruta = bindir / nombre
        ruta.write_text(cuerpo)
        os.chmod(ruta, 0o755)
    registro = tmp_path / "argv.log"
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{fakes}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_BIN_DIR", str(fakes))
    monkeypatch.setenv("FAKE_SUDO_LOG", str(registro))
    monkeypatch.setenv("FAKE_SUDO_PASS", "secreto-test")
    monkeypatch.delenv("FAKE_SUDO_NOPASS", raising=False)
    # "Instalada" = existe el binario falso en la carpeta de pruebas
    monkeypatch.setattr(toolstore, "is_installed", lambda t: (fakes / (t["pkg"] or "_")).exists())
    toolstore_jobs._JOBS.clear()
    yield {"fakes": fakes, "argv_log": registro}
    toolstore_jobs._JOBS.clear()


def _esperar(job_id, estados, limite=20):
    fin = time.time() + limite
    while time.time() < fin:
        j = toolstore_jobs.get_job(job_id)
        if j["status"] in estados:
            return j
        time.sleep(0.05)
    actual = toolstore_jobs.get_job(job_id)["status"]
    raise AssertionError(f"el trabajo no llegó a {estados}; estado actual: {actual}")


def test_instalar_con_contrasena_correcta_y_sin_guardarla(entorno):
    r = toolstore_jobs.start_job("masscan", "install")
    assert r["ok"] and r["job"]["status"] == "needs_password"
    jid = r["job"]["id"]

    assert toolstore_jobs.submit_password(jid, "secreto-test")["ok"]
    j = _esperar(jid, {"ok", "error"})

    assert j["status"] == "ok"
    assert any("Instalación de masscan completada" in linea for linea in j["log"])
    assert (entorno["fakes"] / "masscan").exists()
    # La contraseña no aparece en el trabajo, en el listado, en memoria ni en los argumentos de sudo.
    assert "secreto-test" not in json.dumps(toolstore_jobs.list_jobs())
    assert "secreto-test" not in str(toolstore_jobs._JOBS)
    assert "secreto-test" not in entorno["argv_log"].read_text()


def test_contrasena_incorrecta_vuelve_a_pedirla(entorno):
    jid = toolstore_jobs.start_job("masscan", "install")["job"]["id"]
    toolstore_jobs.submit_password(jid, "mal")
    j = _esperar(jid, {"needs_password"})
    assert "incorrecta" in j["message"]
    assert not (entorno["fakes"] / "masscan").exists()
    assert not any("Sorry" in linea or "incorrect password" in linea for linea in j["log"])

    toolstore_jobs.submit_password(jid, "secreto-test")
    assert _esperar(jid, {"ok", "error"})["status"] == "ok"


def test_sin_contrasena_si_sudo_no_la_pide(entorno, monkeypatch):
    monkeypatch.setenv("FAKE_SUDO_NOPASS", "1")
    jid = toolstore_jobs.start_job("masscan", "install")["job"]["id"]
    assert _esperar(jid, {"ok", "error"})["status"] == "ok"
    assert (entorno["fakes"] / "masscan").exists()


def test_solo_un_trabajo_a_la_vez(entorno):
    primero = toolstore_jobs.start_job("masscan", "install")
    assert primero["ok"]
    segundo = toolstore_jobs.start_job("dirb", "install")
    assert segundo["ok"] is False
    assert "en curso" in segundo["error"]


def test_cancelar_detiene_el_trabajo(entorno, monkeypatch):
    monkeypatch.setenv("FAKE_SUDO_NOPASS", "1")
    jid = toolstore_jobs.start_job("dirb", "install")["job"]["id"]   # dirb tarda 30 s en el apt falso
    _esperar(jid, {"running"})
    time.sleep(0.5)
    inicio = time.time()
    toolstore_jobs.cancel_job(jid)
    j = _esperar(jid, {"cancelled", "ok", "error"}, limite=12)
    assert j["status"] == "cancelled"
    assert time.time() - inicio < 10


def test_desinstalar_usa_apt_remove(entorno):
    (entorno["fakes"] / "masscan").write_text("#!/bin/sh\n")   # está instalada
    r = toolstore_jobs.start_job("masscan", "remove")
    assert r["ok"] and r["job"]["status"] == "needs_password"
    jid = r["job"]["id"]
    toolstore_jobs.submit_password(jid, "secreto-test")
    j = _esperar(jid, {"ok", "error"})
    assert j["status"] == "ok"
    assert not (entorno["fakes"] / "masscan").exists()
    assert "apt-get remove -y masscan" in entorno["argv_log"].read_text()


def test_rechaza_herramientas_manuales_y_estados_invalidos(entorno):
    assert toolstore_jobs.start_job("burpsuite", "install")["ok"] is False
    assert toolstore_jobs.start_job("masscan", "remove")["ok"] is False   # no está instalada
    assert toolstore_jobs.start_job("no-existe", "install")["ok"] is False
    assert toolstore_jobs.start_job("masscan", "borrar-todo")["ok"] is False


def test_catalogo_incluye_comando_de_desinstalacion():
    t = toolstore._BY_ID["nmap"]
    assert t["remove_command"] == "sudo apt-get remove -y nmap"
    assert toolstore._BY_ID["burpsuite"]["remove_command"] is None
