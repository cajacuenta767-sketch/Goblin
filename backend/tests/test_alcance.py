"""Tests de alcance: la IA no escanea ni ataca sin que el usuario lo pida y lo apruebe."""
import agent
import approvals


def test_nmap_siempre_pide_aprobacion_en_confianza():
    approvals.set_level("alcance-1", "confianza")
    assert approvals.needs_approval("alcance-1", "run_shell", True, {"command": "nmap -sS 10.0.0.5"})


def test_escaneo_con_sudo_y_ruta_completa_tambien_pide():
    assert approvals.is_security_command("sudo nmap -sS 10.0.0.5")
    assert approvals.is_security_command("/usr/bin/nmap -p- host")
    assert approvals.is_security_command("VAR=1 sqlmap -u http://x")


def test_comando_normal_en_confianza_no_pide():
    approvals.set_level("alcance-2", "confianza")
    assert not approvals.needs_approval("alcance-2", "run_shell", True, {"command": "ls -la"})
    assert not approvals.needs_approval("alcance-2", "run_shell", True, {"command": "python3 app.py"})


def test_escribir_archivo_en_confianza_no_pide():
    approvals.set_level("alcance-3", "confianza")
    assert not approvals.needs_approval("alcance-3", "write_file", True, {"path": "a.py"})


def test_prompt_no_empuja_a_escanear():
    assert "trabaja por fases" not in agent.SYSTEM_PROMPT
    assert "Nunca escanees" in agent.SYSTEM_PROMPT
