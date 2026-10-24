# Spec 011 — UI de sesiones, hallazgos e informe

**Estado:** 🟨 En progreso · **Depende de:** 005, 006

## Qué
Cablear en el frontend lo que ya existe en el backend: la sidebar lista sesiones reales,
se puede abrir una conversación anterior, ver los hallazgos y generar el informe.

## Requisitos funcionales
- RF1: La sidebar lista las sesiones reales desde /api/sessions.
- RF2: Clic en una sesión carga sus mensajes en el chat.
- RF3: "New Conversation" crea una sesión nueva (id único).
- RF4: Panel de hallazgos que lista los findings de la sesión con color por severidad.
- RF5: Botón "Generar informe" que muestra el informe en el chat.
- RF6: Borrar una sesión desde la sidebar.

## Criterios de validación
- [ ] Las sesiones reales aparecen en la sidebar.
- [ ] Abrir una sesión carga su conversación.
- [ ] Los hallazgos se ven con su color de severidad.

## Archivos
- `frontend/js/sessions.js` — sidebar de sesiones
- `frontend/js/findings.js` — panel de hallazgos + informe
- `frontend/index.html`, `css/layout.css`
