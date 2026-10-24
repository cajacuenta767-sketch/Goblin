# Spec 018 — Streaming de respuestas

**Estado:** 🟨 En progreso · **Depende de:** 001

## Qué
Que la respuesta de texto de la IA aparezca token a token (como escribiendo), no de golpe.
Importante en CPU lenta: muestra que trabaja y no parece colgada.

## Decisión técnica (honesta)
El agente hace un bucle con herramientas; hacer streaming de TODO el bucle es complejo.
Esta spec hace lo valioso y robusto: streaming del texto final de la IA cuando responde
sin pedir herramientas. Las fases con herramientas siguen con el indicador de "trabajando".
Se entrega como endpoint opcional; el chat normal (sin streaming) sigue funcionando.

## Requisitos funcionales
- RF1: Endpoint SSE /api/chat/stream que transmite la respuesta token a token.
- RF2: El frontend muestra el texto creciendo en vivo.
- RF3: Si la respuesta requiere herramientas/aprobación, cae al flujo normal (no streaming).
- RF4: Funciona con DeepHat (Ollama soporta stream=True).

## Criterios de validación
- [ ] El endpoint transmite chunks.
- [ ] El frontend muestra el texto apareciendo poco a poco.

## Archivos
- `backend/main.py` — endpoint SSE
- `backend/agent.py` — función de streaming
- `frontend/js/chat.js` — consumir el stream
