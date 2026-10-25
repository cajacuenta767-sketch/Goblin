"""Alcance del engagement, memoria del resumen y nmap estructurado (Spec 036)."""
from types import SimpleNamespace

import pytest

import agent
import db
import engagement
import scope
import state
from tools import scan_tool


@pytest.fixture
def base(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    db.init()
    return "sess-036"


class _Fake:
    def __init__(self, texto="Listo."):
        self.texto = texto
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(message=SimpleNamespace(content=self.texto, tool_calls=None))


class _Fn:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _Call:
    def __init__(self, name, arguments):
        self.function = _Fn(name, arguments)


XML_NMAP = """<?xml version="1.0"?>
<!DOCTYPE nmaprun>
<nmaprun>
<host><status state="up"/><address addr="10.10.10.5" addrtype="ipv4"/>
<ports>
<port protocol="tcp" portid="22"><state state="open"/><service name="ssh" product="OpenSSH" version="8.2p1"/></port>
<port protocol="tcp" portid="23"><state state="closed"/><service name="telnet"/></port>
<port protocol="tcp" portid="80"><state state="open"/><service name="http" product="Apache httpd" version="2.4.41"/></port>
</ports></host>
<host><status state="up"/><address addr="10.10.10.6" addrtype="ipv4"/>
<ports><port protocol="tcp" portid="443"><state state="open"/><service name="https"/></port></ports></host>
</nmaprun>
"""

NMAP_TEXTO = """Starting Nmap 7.94
Nmap scan report for 10.10.11.42
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1
80/tcp open  http    nginx 1.18
"""


# --- RF1 · normalización y pertenencia al alcance ---

def test_normalizar_entradas():
    assert scope.normalize_entry("https://Ejemplo.com/x") == "ejemplo.com"
    assert scope.normalize_entry("10.0.0.0/24") == "10.0.0.0/24"
    assert scope.normalize_entry("10.0.0.5:8080") == "10.0.0.5"
    assert scope.normalize_entry("localhost") is None
    assert scope.normalize_entry("notas.txt") is None
    assert scope.normalize_entry("no es un host") is None


def test_pertenencia_ip_rango_dominio():
    entradas = ["10.10.10.0/24", "ejemplo.com"]
    assert scope.in_scope("10.10.10.7", entradas)
    assert not scope.in_scope("10.10.11.1", entradas)
    assert scope.in_scope("sub.ejemplo.com", entradas)
    assert not scope.in_scope("otroejemplo.com", entradas)
    assert not scope.in_scope("evil-ejemplo.com", entradas)


def test_loopback_siempre_permitido():
    assert scope.in_scope("127.0.0.1", [])
    assert scope.in_scope("localhost", [])


# --- RF2–RF4 · bloqueo de comandos ---

def test_nmap_fuera_de_alcance_se_bloquea():
    msg = scope.check_command("nmap -sV 10.10.11.9", ["10.10.10.5"])
    assert msg and msg.startswith("BLOQUEADO")


def test_nmap_dentro_de_alcance_no_se_bloquea():
    assert scope.check_command("nmap -sV 10.10.10.5", ["10.10.10.5"]) is None


def test_sin_alcance_definido_se_bloquea():
    msg = scope.check_command("nmap 10.0.0.1", [])
    assert msg and "no hay alcance definido" in msg


def test_destinos_no_verificables_se_bloquean():
    assert scope.check_command("nmap $IP", ["10.0.0.1"]).startswith("BLOQUEADO")
    assert scope.check_command("nmap -iL objetivos.txt", ["10.0.0.1"]).startswith("BLOQUEADO")


def test_comandos_sin_red_no_se_miran():
    assert scope.check_command("ls -la /tmp", []) is None
    assert scope.check_command("searchsploit apache 2.4", ["10.0.0.1"]) is None


def test_subdominio_permitido_en_curl():
    assert scope.check_command("curl https://sub.ejemplo.com/a", ["ejemplo.com"]) is None


def test_http_get_fuera_de_alcance():
    assert scope.check_url("http://10.0.0.9/", ["10.0.0.0/24"]) is None
    assert scope.check_url("http://8.8.8.8/", ["10.0.0.0/24"]).startswith("BLOQUEADO")


# --- RF5 · memoria del engagement ---

def test_resumen_con_objetivo_alcance_hosts_y_hallazgos(base, monkeypatch):
    monkeypatch.setattr(state, "get_target", lambda: "10.10.10.5")
    db.add_scope(base, "scope", "10.10.10.0/24")
    scan_tool.record_nmap(base, XML_NMAP)
    db.add_finding(base, "high", "SQLi en login", "10.10.10.5", "80", "", "")
    texto = engagement.summary(base)
    assert "Objetivo: 10.10.10.5" in texto
    assert "10.10.10.0/24" in texto
    assert "10.10.10.5: 22/tcp ssh" in texto
    assert "SQLi en login" in texto


def test_resumen_vacio_si_no_hay_datos(base, monkeypatch):
    monkeypatch.setattr(state, "get_target", lambda: "")
    assert engagement.summary(base) == ""


def test_contexto_conserva_resumen_tras_muchos_turnos(base, monkeypatch):
    monkeypatch.setattr(state, "get_target", lambda: "10.10.10.5")
    db.add_finding(base, "critical", "RCE conocida", "10.10.10.5", "8080", "", "")
    s = agent.get_session(base)
    for i in range(30):
        s["messages"].append({"role": "user", "content": f"mensaje {i}"})
        s["messages"].append({"role": "assistant", "content": f"respuesta {i}"})
    ctx = agent._context(s)
    assert any("RESUMEN DEL ENGAGEMENT" in agent._content(m) for m in ctx)
    assert len(ctx) <= 2 * 10 + 3   # sistema + resumen + últimos turnos


# --- RF2 y RF7 con el agente real ---

def test_agente_bloquea_nmap_fuera_sin_pedir_aprobacion(base, monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(agent, "client", fake)
    db.add_scope(base, "scope", "10.10.10.5")
    s = agent.get_session(base)
    s["queue"] = [_Call("run_shell", {"command": "nmap -sV 10.10.11.9"})]
    out = agent._step(s, base)
    assert out["type"] == "text"
    bloqueos = [m for m in s["messages"] if agent._role(m) == "tool"]
    assert any("BLOQUEADO" in agent._content(m) for m in bloqueos)
    assert any(a["approved"] == 0 and "BLOQUEADO" in a["result"] for a in db.get_audit(base))


def test_agente_pide_aprobacion_dentro_de_alcance(base, monkeypatch):
    monkeypatch.setattr(agent, "client", _Fake())
    db.add_scope(base, "scope", "10.10.10.5")
    s = agent.get_session(base)
    s["queue"] = [_Call("run_shell", {"command": "nmap -sV 10.10.10.5"})]
    out = agent._step(s, base)
    assert out["type"] == "approval"
    assert out["tool"] == "run_shell"


def test_nmap_texto_guarda_puertos(base):
    assert scan_tool.record_nmap(base, NMAP_TEXTO) == 2
    hosts = db.list_hosts(base)
    assert {(h["host"], h["port"]) for h in hosts} == {("10.10.11.42", "22"), ("10.10.11.42", "80")}


def test_nmap_xml_guarda_solo_puertos_abiertos(base):
    assert scan_tool.record_nmap(base, XML_NMAP) == 3
    hosts = db.list_hosts(base)
    assert ("10.10.10.5", "23") not in {(h["host"], h["port"]) for h in hosts}
    versiones = {h["port"]: h["version"] for h in hosts}
    assert versiones["22"] == "OpenSSH 8.2p1"


def test_xml_con_entidades_se_rechaza(base):
    malicioso = XML_NMAP.replace("<!DOCTYPE nmaprun>", '<!DOCTYPE nmaprun [<!ENTITY x "y">]>')
    assert scan_tool.record_nmap(base, malicioso) == 0
