"""Tests de Spec 026 (marketplace): catálogo, instalación por terminal y apertura de URLs."""
import pytest

import toolstore


def _no_subprocess(monkeypatch):
    """Falla si install() o open_url() intentan lanzar un proceso directamente."""
    def boom(*args, **kwargs):
        raise AssertionError("no debe lanzar procesos desde install()/open_url() de esta forma")
    monkeypatch.setattr(toolstore.subprocess, "run", boom)


# ---------- Forma del catálogo ----------

def test_catalog_ids_are_unique_and_complete():
    ids = [t["id"] for t in toolstore.CATALOG]
    assert len(ids) == len(set(ids))
    assert len(ids) >= 60
    for t in toolstore.CATALOG:
        assert t["name"] and t["desc"]
        assert t["category"] in toolstore.CATEGORIES
        assert t["url"].startswith("https://")
        assert t["bin"] or t["path"], f"{t['id']} necesita binario o ruta para detectarla"


def test_every_category_has_tools():
    used = {t["category"] for t in toolstore.CATALOG}
    assert used == set(toolstore.CATEGORIES)


def test_package_and_binary_names_are_safe():
    for t in toolstore.CATALOG:
        if t["pkg"]:
            assert toolstore._PKG_RE.match(t["pkg"]), t["id"]
        if t["bin"]:
            assert toolstore._BIN_RE.match(t["bin"]), t["id"]


def test_only_burpsuite_is_manual_download():
    manual = [t["id"] for t in toolstore.CATALOG if not t["pkg"]]
    assert manual == ["burpsuite"]


def test_command_is_built_from_package_only():
    t = toolstore._BY_ID["nmap"]
    assert t["command"] == "sudo apt-get update && sudo apt-get install -y nmap"
    assert toolstore._BY_ID["burpsuite"]["command"] is None


def test_tool_builder_rejects_unsafe_package_name():
    with pytest.raises(ValueError):
        toolstore._tool("x", "X", "recon", "x", "nmap; rm -rf /", "d", "https://example.com")


def test_tool_builder_rejects_non_https_url():
    with pytest.raises(ValueError):
        toolstore._tool("x", "X", "recon", "x", "nmap", "d", "http://example.com")


# ---------- Instalación: prepara el comando, no ejecuta apt ----------

def test_install_returns_command_without_running_apt(monkeypatch):
    _no_subprocess(monkeypatch)
    monkeypatch.setattr(toolstore, "is_installed", lambda t: False)
    r = toolstore.install("nmap")
    assert r["ok"] is True and r["installed"] is False
    assert r["command"] == "sudo apt-get update && sudo apt-get install -y nmap"


def test_install_rejects_unknown_id(monkeypatch):
    _no_subprocess(monkeypatch)
    r = toolstore.install("nmap; rm -rf /")
    assert r["ok"] is False
    assert "command" not in r


def test_install_manual_tool_has_no_command(monkeypatch):
    _no_subprocess(monkeypatch)
    monkeypatch.setattr(toolstore, "is_installed", lambda t: False)
    r = toolstore.install("burpsuite")
    assert r["ok"] is False
    assert "command" not in r
    assert r["url"].startswith("https://")


def test_install_already_installed_returns_no_command(monkeypatch):
    _no_subprocess(monkeypatch)
    monkeypatch.setattr(toolstore, "is_installed", lambda t: True)
    r = toolstore.install("nmap")
    assert r["ok"] is True and r["installed"] is True
    assert "command" not in r


# ---------- Apertura de la web oficial ----------

def test_open_url_rejects_unknown_id(monkeypatch):
    calls = []
    monkeypatch.setattr(toolstore.subprocess, "Popen", lambda *a, **k: calls.append(a))
    r = toolstore.open_url("../../etc/passwd")
    assert r["ok"] is False
    assert calls == []


def test_open_url_opens_only_the_catalog_url(monkeypatch):
    calls = []

    class FakePopen:
        def __init__(self, args, **kwargs):
            calls.append((args, kwargs))

    monkeypatch.setattr(toolstore.shutil, "which",
                        lambda name: "/usr/bin/xdg-open" if name == "xdg-open" else None)
    monkeypatch.setattr(toolstore.subprocess, "Popen", FakePopen)
    r = toolstore.open_url("nmap")
    assert r["ok"] is True
    args, kwargs = calls[0]
    assert args == ["/usr/bin/xdg-open", toolstore._BY_ID["nmap"]["url"]]
    assert kwargs.get("start_new_session") is True
    assert kwargs.get("shell", False) is False


def test_open_url_without_xdg_open_explains_and_gives_link(monkeypatch):
    monkeypatch.setattr(toolstore.shutil, "which", lambda name: None)
    r = toolstore.open_url("nmap")
    assert r["ok"] is False
    assert r["url"].startswith("https://")


# ---------- Detección por ruta ----------

def test_is_installed_by_path(tmp_path):
    assert toolstore.is_installed({"bin": None, "path": str(tmp_path)}) is True
    assert toolstore.is_installed({"bin": None, "path": str(tmp_path / "no-existe")}) is False
