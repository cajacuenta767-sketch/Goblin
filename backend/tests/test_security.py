"""Tests de seguridad: lista negra de comandos y aprobaciones."""
from tools import registry
import approvals


def test_blocked_rm_rf_root():
    out = registry.run_tool("run_shell", {"command": "rm -rf /"})
    assert "BLOQUEADO" in out


def test_blocked_fork_bomb():
    out = registry.run_tool("run_shell", {"command": ":(){ :|:& };:"})
    assert "BLOQUEADO" in out


def test_blocked_mkfs():
    out = registry.run_tool("run_shell", {"command": "mkfs.ext4 /dev/sda1"})
    assert "BLOQUEADO" in out


def test_normal_command_runs():
    out = registry.run_tool("run_shell", {"command": "echo hola"})
    assert "hola" in out and "BLOQUEADO" not in out


def test_delete_always_asks():
    # delete_path pide aprobación en TODOS los niveles, incluso confianza
    for level in ["cauto", "normal", "confianza"]:
        approvals.set_level("sec", level)
        assert approvals.needs_approval("sec", "delete_path", True) is True


def test_readonly_never_asks():
    approvals.set_level("sec", "cauto")
    assert approvals.needs_approval("sec", "list_dir", False) is False


def test_trust_level_auto_approves_shell():
    approvals.set_level("sec", "confianza")
    assert approvals.needs_approval("sec", "run_shell", True) is False
