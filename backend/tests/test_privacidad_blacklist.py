"""Privacidad ampliada y lista negra normalizada (Spec 038)."""
import pytest

import router
import tools.shell as sh


def test_ipv6_se_detecta():
    assert router.sensitive_reason(["host fe80::1 abierto"]) == "una dirección IPv6"


def test_hora_no_es_ipv6():
    assert router.sensitive_reason(["son las 12:30:45 hoy"]) is None


def test_termino_del_engagement_se_detecta():
    motivo = router.sensitive_reason(["auditoría para Acme"], terms=["acme"])
    assert motivo == "un término sensible del engagement"


def test_termino_vacio_no_dispara():
    assert router.sensitive_reason(["hola"], terms=[""]) is None


@pytest.mark.parametrize("comando", [
    "rm -rf /", "rm  -rf   /", "RM -FR /", "rm -rf '/'", "rm -rf ~", "ls; rm -rf /*",
    "sudo reboot", "mkfs.ext4 /dev/sdb", "dd if=/dev/zero of=/dev/sda",
    ":(){ :|:& };:", "echo ok && shutdown -h now",
])
def test_lista_negra_bloquea_variantes(comando):
    assert sh._is_blocked(comando)


@pytest.mark.parametrize("comando", [
    "rm -rf ./build", "ls -la", "echo reboot", "rm archivo.txt", "cat /etc/hosts",
])
def test_lista_negra_no_bloquea_comandos_normales(comando):
    assert not sh._is_blocked(comando)
