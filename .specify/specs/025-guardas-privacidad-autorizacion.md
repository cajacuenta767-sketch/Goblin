# Spec 025 — Guardas de privacidad (híbrido) y autorización por objetivo

**Estado:** 🟨 En progreso · **Tipo:** seguridad · **Depende de:** 008, 009, 012
**Referencias:** constitución II.1, II.4, III.5 · PLAN §4.1 · PLAN Fase 8 ("Barra de Target")

## Problema

**A. Privacidad en modo híbrido.** Cuando el modo es `hybrid` y hay API key de Gemini,
el router envía **todo el historial** de la sesión a Gemini. Si ya apareció una IP o el
dominio del objetivo (en un mensaje, en una salida de nmap o en un comando), sale de la
máquina. La constitución (II.1) dice que nada sale salvo que el usuario active el modo
híbrido, y el PLAN §4.1 pide forzar DeepHat local cuando hay datos sensibles. Hoy ese
forzado no existe.

**B. Autorización por objetivo.** La herramienta `set_target` no pide aprobación: la IA
puede fijar un objetivo sin que el usuario confirme que tiene autorización. La
constitución (III.5) exige autorización explícita por escrito, y el PLAN (Fase 8) pide
un aviso antes de empezar un objetivo.

## Requisitos funcionales

- **RF1.** En modo híbrido, si **cualquier** mensaje de la sesión (usuario, IA o
  herramientas) contiene una IPv4, un rango CIDR o el objetivo activo, la respuesta la
  genera DeepHat en local. Gemini no recibe nada.
- **RF2.** La revisión recorre **todo** el historial en cada turno, no solo el último
  mensaje. Así, un dato sensible que ya salió antes no queda fuera de la revisión.
- **RF3.** Cuando se fuerza DeepHat por datos sensibles, la respuesta incluye una nota
  visible: qué dato lo activó (tipo, no el valor completo) y que Gemini no recibió nada.
- **RF4.** `set_target` requiere aprobación en **todos** los niveles de autoaprobación
  (como `delete_path`). La caja de aprobación lo marca como peligroso y muestra:
  "Confirma que tienes autorización POR ESCRITO para este objetivo".
- **RF5.** Si el usuario deniega `set_target`, el objetivo no cambia.

## Límites (se dicen claro)

- La detección es por patrones: IPv4, CIDR y el objetivo activo. **No** detecta IPv6,
  nombres de cliente, ni hostnames arbitrarios que no sean el objetivo. Eso requiere una
  lista de términos del engagement (mejora futura).
- Un falso positivo (una IP de ejemplo en el texto) fuerza DeepHat; es el lado seguro.

## Criterios de aceptación

- [x] Sesión híbrida con IP en el historial → la respuesta es de DeepHat y lleva nota.
- [ ] Sesión híbrida sin datos sensibles → sigue usando Gemini (comportamiento actual).
- [x] `set_target` produce una caja de aprobación en nivel `confianza` también.
- [x] Denegar `set_target` no cambia el objetivo.
- [x] Las pruebas automáticas cubren la detección y la aprobación obligatoria.

## Fuera de alcance

- Lista de términos del engagement (nombres de cliente, dominios secundarios).
- Cifrado o anonimización de datos antes de enviarlos a Gemini (no se envían en absoluto
  cuando hay datos sensibles; no hace falta anonimizar).
