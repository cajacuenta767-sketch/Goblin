# Spec 037 — Diff en la aprobación, progreso en vivo y contador de contexto

**Estado:** 🟨 Implementado · pruebas unitarias ✅ · ⬜ PC: DeepHat real · **Tipo:** interfaz + API · **Depende de:** 002, 018, 034
**Motivo:** la caja de aprobación no mostraba qué iba a cambiar, y "GOBLIN está trabajando…" no decía qué
herramienta corría ni cuánto llevaba.

## Problema

1. Al pedir aprobar `write_file` o `edit_lines` solo se ve la ruta y el contenido nuevo, no el cambio.
2. Mientras una herramienta corre no hay señal de cuál es ni cuánto lleva.
3. El usuario no ve cuánto contexto usa el modelo (Spec 034 lo recorta a 10 turnos, pero no se muestra).

## Requisitos funcionales

- **RF1 · Diff.** Para `write_file` y `edit_lines` la respuesta de aprobación incluye `diff`: diferencias
  unificadas entre el archivo actual y el resultado (archivo nuevo = todo añadido). Máximo 200 líneas;
  el resto se resume ("… N líneas más").
- **RF2 · Vista del diff.** La caja de aprobación muestra el diff con líneas añadidas en verde y quitadas
  en rojo, sin `innerHTML` con datos sin escapar.
- **RF3 · Progreso.** El backend registra la herramienta en curso por sesión (nombre y hora de inicio).
  `GET /api/chat/status/{sid}` devuelve `{busy, action, elapsed_s, context_tokens, context_limit}`.
- **RF4 · Indicador.** Mientras la sesión está ocupada, el indicador muestra
  "⚡ ejecutando run_shell… 12 s" o "GOBLIN está pensando…" si no hay herramienta en curso. Se actualiza
  cada segundo mientras dura la respuesta.
- **RF5 · Contexto.** `context_tokens` es una estimación (caracteres / 4) del contexto que se enviaría al
  modelo; `context_limit` es `GOBLIN_NUM_CTX`. La barra de estado lo muestra.

## Criterios de aceptación

- [ ] `write_file` sobre un archivo existente devuelve un diff con `-` y `+`.
- [ ] `write_file` sobre un archivo nuevo devuelve solo líneas `+`.
- [ ] El diff de más de 200 líneas se recorta con la nota de líneas restantes.
- [ ] Durante `run_shell` el estado devuelve `action = "run_shell"`; al terminar, `action = null`.
- [ ] La caja de aprobación escapa el contenido (sin inyección de HTML).
- [ ] Pruebas en `backend/tests/test_diff_progreso.py`.

## Límites

- El conteo de tokens es una estimación; el tokenizador real de DeepHat no se carga en GOBLIN.
- El progreso no muestra el avance dentro de un comando (solo nombre y tiempo).
