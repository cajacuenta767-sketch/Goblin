# Spec 034 — Respuestas de capacidad y contexto acotado

**Estado:** 🟨 Implementada, validación en PC pendiente · **Tipo:** comportamiento · **Depende de:** 033
**Motivo:** ante "¿puedes analizar algo?", DeepHat respondió con un plan sobre "analizar el sonido",
algo que el usuario nunca pidió. Y el modelo recibe toda la conversación de la sesión, sin recortar.

## Problema

1. Una pregunta sobre lo que GOBLIN puede hacer pasa por el modelo, que puede improvisar. Esa
   respuesta es fija y no necesita al modelo.
2. El historial completo de la sesión entra en cada llamada. En sesiones largas, temas antiguos
   compiten con la petición actual. En CPU, además, cada token extra cuesta tiempo.

## Requisitos funcionales

- **RF1.** Una pregunta de capacidad ("¿puedes…?", "¿qué puedes hacer?", "¿quién eres?") se
  responde con un texto fijo que describe lo que GOBLIN hace y cómo pedir un análisis. No llama al
  modelo. Una petición con verbo de acción ("¿puedes crear la carpeta X?") no es pregunta de
  capacidad y sigue el flujo normal.
- **RF2.** Al modelo solo se le envían el system prompt y los últimos `GOBLIN_HISTORY_TURNS` turnos
  de usuario (por defecto 10) con sus respuestas y herramientas. El historial completo sigue
  guardado en la sesión y en la base de datos.
- **RF3.** La respuesta de capacidad se guarda en la conversación igual que cualquier otra.

## Criterios de aceptación

- [x] "¿puedes analizar algo?" → respuesta fija, sin llamada al modelo.
- [x] "¿puedes crear la carpeta pruebas?" → no es capacidad; pide aprobación como cualquier acción.
- [x] Con más de N turnos, el modelo recibe el system prompt y solo los últimos N turnos.
- [x] El historial completo se conserva en la sesión.
- [x] Pruebas en `backend/tests/test_contexto.py`.
- [ ] Probado en la PC con DeepHat real (pendiente del usuario).

## Límites

- La detección de "pregunta de capacidad" es por palabras clave; una pregunta rara puede ir al modelo.
- Recortar el contexto puede hacer olvidar algo de hace más de N turnos. Si lo necesitas, se sube
  `GOBLIN_HISTORY_TURNS`.
