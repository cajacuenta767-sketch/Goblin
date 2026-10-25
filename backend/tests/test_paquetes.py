"""Spec 045 RF5 y RF6: instalación de paquetes con validación y aprobación. pip simulado."""
from types import SimpleNamespace

import pytest

import approvals
from tools import packages, registry


def _pip_simulado(monkeypatch, returncode=0, salida="Successfully installed requests"):
    llamadas = []

    def fake_run(cmd, **kw):
        llamadas.append((cmd, kw))
        return SimpleNamespace(returncode=returncode, stdout=salida, stderr="")

    monkeypatch.setattr(packages.subprocess, "run", fake_run)
    return llamadas


def test_nombre_valido_se_instala_con_argumentos_en_lista(monkeypatch):
    llamadas = _pip_simulado(monkeypatch)

    out = packages.install_package("pip", "requests")

    cmd, kw = llamadas[0]
    assert cmd[1:3] == ["-m", "pip"]
    assert cmd[-1] == "requests"
    assert kw.get("shell", False) is False
    assert "--break-system-packages" not in cmd
    assert "Instalado 'requests'" in out


@pytest.mark.parametrize("nombre", [
    "requests; rm -rf /", "../x", "git+https://evil.example/x", "pkg==1.0",
    "-r/etc/passwd", "", "a b", "https://x/y.whl", "/ruta/local",
])
def test_nombres_no_validos_no_ejecutan_nada(monkeypatch, nombre):
    monkeypatch.setattr(packages.subprocess, "run",
                        lambda *a, **k: pytest.fail("no debe ejecutar pip con un nombre no válido"))
    assert "no válido" in packages.install_package("pip", nombre)


@pytest.mark.parametrize("gestor", ["apt", "npm", "pip; rm -rf /", ""])
def test_gestores_fuera_de_la_lista_no_ejecutan_nada(monkeypatch, gestor):
    monkeypatch.setattr(packages.subprocess, "run",
                        lambda *a, **k: pytest.fail("no debe ejecutar un gestor no permitido"))
    assert "no permitido" in packages.install_package(gestor, "requests")


def test_proteccion_pep668_no_se_salta(monkeypatch):
    llamadas = _pip_simulado(
        monkeypatch, returncode=1,
        salida="error: externally-managed-environment",
    )

    out = packages.install_package("pip", "requests")

    assert "PEP 668" in out
    assert all("--break-system-packages" not in cmd for cmd, _ in llamadas)


def test_instalar_siempre_pide_aprobacion_en_todos_los_niveles():
    assert "install_package" in registry.NEEDS_APPROVAL
    for nivel in ("cauto", "normal", "confianza"):
        approvals.set_level("sid-instalar", nivel)
        assert approvals.needs_approval("sid-instalar", "install_package", True,
                                        {"manager": "pip", "name": "x"}) is True


def test_esquema_de_install_package_exige_gestor_y_nombre():
    esquema = next(s for s in registry.SCHEMAS if s["function"]["name"] == "install_package")
    assert set(esquema["function"]["parameters"]["required"]) == {"manager", "name"}


def test_pista_por_modulo_que_falta():
    texto = packages.sugerencia("ModuleNotFoundError: No module named 'yaml'")
    assert "yaml" in texto and "install_package" in texto


def test_pista_por_comando_que_falta_no_propone_instalar_con_pip():
    texto = packages.sugerencia("bash: nmapx: command not found")
    assert "comando del sistema" in texto


def test_sin_error_no_hay_pista():
    assert packages.sugerencia("todo bien") == ""
