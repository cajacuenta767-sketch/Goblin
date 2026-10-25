# Spec 035 — Plan visible antes de ejecutar

**Estado:** 🟨 Implementada, validación en PC pendiente · **Tipo:** comportamiento · **Depende de:** 018, 033, 034
**Motivo:** en peticiones de varios pasos, GOBLIN actuaba sin mostrar qué iba a hacer. Ahora
propone el plan primero y ejecuta solo si el usuario lo confirma.

## Problema

Una petición como "crea la carpeta pruebas y luego escribe notas.txt" llevaba al modelo a ejecutar
en seguida, sin que el usuario viera el orden de los pasos. Si el modelo se desvía, el daño ya está
hecho cuando te enteras.

## Requisitos funcionales

- **RF1.** Una petición de acción de varios pasos (dos o más verbos de acción distintos, o palabras
  como "luego", "después", "primero") NO ejecuta herramientas. El modelo escribe un plan corto y
  numerado, sin llamar herramientas, y termina preguntando si lo ejecuta.
- **RF2.** Una petición de un solo paso sigue su flujo normal (con aprobaciones de siempre).
- **RF3.** Si la siguiente respuesta del usuario es una confirmación ("sí", "ok", "dale", "ejecuta"…),
  el turno de acción se ejecuta con el plan ya en el historial.
- **RF4.** Si la siguiente respuesta NO es una confirmación, el plan pendiente se descarta y el
  mensaje se trata como una petición nueva.
- **RF5.** El plan funciona en streaming y en el modo normal.

## Criterios de aceptación

- [x] "crea la carpeta pruebas y luego escribe notas.txt" → plan, sin herramientas.
- [x] "crea la carpeta pruebas" → un paso, sin plan.
- [x] "sí" después del plan → ejecuta.
- [x] Un mensaje distinto después del plan lo descarta.
- [x] Pruebas en `backend/tests/test_plan.py`.
- [ ] Probado en la PC con DeepHat real (pendiente del usuario).

## Límites

- Detectar "varios pasos" es por palabras clave. "crea la carpeta X y dentro un archivo Y" cuenta
  como un paso, porque solo hay un verbo.
- El plan lo escribe el mismo modelo que ejecuta. Un plan malo sigue siendo posible; por eso el
  usuario confirma antes.
- La confirmación es una palabra; no hay botón en la interfaz. Un botón es mejora posterior.
