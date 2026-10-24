"""Tests de los parsers de escaneos."""
import parsers

NMAP_OUTPUT = """Starting Nmap 7.94
Nmap scan report for 10.10.11.42
Host is up (0.045s latency).
PORT      STATE SERVICE  VERSION
22/tcp    open  ssh      OpenSSH 8.2p1 Ubuntu
80/tcp    open  http     Apache httpd 2.4.41
443/tcp   open  ssl/http Apache httpd 2.4.41
3306/tcp  open  mysql    MySQL 5.7.33
"""

NIKTO_OUTPUT = """- Nikto v2.5.0
+ Target IP: 10.10.11.42
+ Server: Apache/2.4.41
+ /admin/: Admin login page found.
+ /backup.sql: Database backup found - sensitive!
+ End Time: ...
"""


def test_parse_nmap():
    out = parsers.parse_nmap(NMAP_OUTPUT)
    assert "10.10.11.42" in out
    assert "22/tcp" in out and "ssh" in out
    assert "OpenSSH 8.2p1" in out
    assert "4 puertos" in out


def test_parse_nmap_empty():
    assert "No se encontraron" in parsers.parse_nmap("sin puertos aqui")


def test_parse_nikto():
    out = parsers.parse_nikto(NIKTO_OUTPUT)
    assert "backup.sql" in out or "Admin login" in out
    # no debe incluir la cabecera Target IP
    assert "Target IP" not in out
