# Spec 005 — Persistencia (SQLite)

**Estado:** 🟨 En progreso · **Fase:** 4 · **Depende de:** 001

## Qué
Guardar sesiones de chat y sus mensajes en SQLite para que no se pierdan al cerrar la app.

## Por qué
Ahora las conversaciones viven en RAM y desaparecen al cerrar. Un pentester necesita volver
a una conversación anterior de un engagement.

## Requisitos funcionales
- RF1: Al enviar/recibir un mensaje, se guarda en SQLite (tabla messages).
- RF2: Las sesiones se guardan (tabla sessions) con título y timestamps.
- RF3: Endpoints: listar sesiones, abrir una sesión (sus mensajes), borrar sesión.
- RF4: El título de la sesión se genera del primer mensaje del usuario.
- RF5: La sidebar lista las sesiones reales desde la base de datos.

## Requisitos no funcionales
- RNF1: SQLite en `data/goblin.db` (git-ignored). Un solo archivo.
- RNF2: Sin ORM pesado: `sqlite3` de la stdlib (sin dependencias extra).
- RNF3: Escrituras seguras (no corromper si se cierra a media escritura).

## Criterios de validación
- [ ] Enviar un mensaje lo guarda en la DB.
- [ ] Cerrar y reabrir: la conversación sigue ahí.
- [ ] Listar y borrar sesiones funciona.

## Archivos
- `backend/db.py` — conexión SQLite, tablas, funciones CRUD
- `backend/agent.py` — guardar mensajes al conversar
- `backend/main.py` — endpoints /api/sessions
- `frontend/js/sessions.js` — sidebar con sesiones reales
