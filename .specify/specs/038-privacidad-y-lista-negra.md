# Spec 038 — Privacidad ampliada y lista negra normalizada

**Estado:** 🟨 Implementado · pruebas unitarias ✅ · ⬜ PC: DeepHat real · **Tipo:** seguridad · **Depende de:** 025, 036
**Motivo:** la guarda de privacidad solo veía IPv4 y el objetivo exacto. La lista negra comparaba texto literal
y se esquivaba cambiando espacios o mayúsculas.

## Problema

1. La guarda de privacidad (Spec 025) no detecta IPv6 ni nombres de cliente o términos del engagement.
2. `config.BLOCKED_PATTERNS` compara subcadenas exactas: `rm  -rf /` (dos espacios) o `rm -fr /` no se bloquean.
3. El modo "local puro" no indica en la interfaz que nada sale a la red (ver Spec 041).

## Requisitos funcionales

- **RF1 · IPv6.** Se detectan direcciones IPv6 válidas (validadas con `ipaddress`, no con una regex suelta
  para no marcar horas como "12:30:45").
- **RF2 · Términos sensibles.** Cada sesión tiene una lista de términos (nombre de cliente, dominios
  secundarios). Un término presente en el historial o en el resumen del engagement fuerza DeepHat. La lista
  se edita en la interfaz y **nunca** se envía a Gemini.
- **RF3 · Lista negra.** Antes de comparar, el comando se normaliza: minúsculas, espacios colapsados,
  comillas eliminadas. Además se bloquean patrones con expresiones regulares: `rm` recursivo y forzado sobre
  `/`, `~` o `*`, `mkfs`, `dd` contra `/dev/`, fork bomb, `shutdown`/`reboot`/`halt`/`poweroff`.
- **RF4 · Sin cambios en la aprobación.** La lista negra bloquea aunque el usuario apruebe (Constitución III.2).

## Criterios de aceptación

- [ ] `2001:db8::1` en el historial fuerza DeepHat en modo híbrido.
- [ ] `12:30:45` no se marca como IPv6.
- [ ] Un término de cliente añadido en la interfaz fuerza DeepHat.
- [ ] `rm  -rf   /` y `RM -FR /` se bloquean.
- [ ] `rm -rf ./carpeta` no se bloquea.
- [ ] Pruebas en `backend/tests/test_privacidad_blacklist.py`.

## Límites

- Una lista negra no es un sandbox. La protección principal sigue siendo la aprobación del usuario.
- Los términos solo se detectan si aparecen literalmente (sin acentos o variantes no se encuentran).
