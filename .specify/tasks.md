# Tareas de GOBLIN (SDD)

> Tareas concretas derivadas de las specs. Se marcan al completarse. Cada tarea apunta a
> su spec. No se trabaja nada que no esté aquí; lo nuevo se añade primero como tarea.

**Leyenda:** ⬜ pendiente · 🟨 en progreso · ✅ hecho

---

## Spec 001 — Backend Core ✅

- ✅ T001.1 — Estructura de carpetas por capas
- ✅ T001.2 — config.py (lee .env, ajustes de hardware)
- ✅ T001.3 — tools/filesystem.py (9 operaciones de archivos)
- ✅ T001.4 — tools/shell.py (con bloqueo de comandos peligrosos)
- ✅ T001.5 — tools/registry.py (catálogo + schemas + aprobaciones)
- ✅ T001.6 — agent.py (bucle agéntico + aprobaciones + anti-bucle)
- ✅ T001.7 — state.py (publicar target a Polybar)
- ✅ T001.8 — main.py (API FastAPI)
- ✅ T001.9 — Probar herramientas end-to-end (sin Ollama)
- ⬜ T001.10 — Probar chat con DeepHat real (en la PC del usuario)

## Spec 002 — Frontend IDE ✅ (v1 sin Monaco)

- ✅ T002.1 — index.html (estructura de paneles)
- ✅ T002.2 — css/theme.css (tokens de color, verde goblin)
- ✅ T002.3 — css/layout.css (los 3 paneles + barra de estado + progreso)
- ✅ T002.4 — js/api.js (llamadas al backend)
- ✅ T002.5 — js/chat.js (enviar/recibir, etiqueta de modelo, markdown)
- ✅ T002.6 — js/approvals.js (caja de aprobación visual, borde rojo si peligrosa)
- ✅ T002.7 — js/explorer.js (árbol de archivos real, navegable)
- ✅ T002.8 — js/main.js (arranque, estado, barra inferior con RAM/CPU)
- ✅ T002.x — backend: endpoint /api/system (RAM/CPU) añadido
- ✅ T002.9 — Validar endpoints + servido del frontend (sin Ollama)
- ⬜ T002.10 — Validar chat real con DeepHat (en la PC del usuario)
- ⬜ T002.11 — Editor Monaco (iteración futura, se dejó fuera de v1 a propósito)

## Infraestructura (transversal)

- ✅ TI.1 — scripts/install.sh (instalador Parrot, instala Ollama + deps + modelo)
- ✅ TI.2 — scripts/run.sh (arranque con flags de RAM/CPU)
- ⬜ TI.3 — Subir a GitHub (repo público "goblin") — pendiente de reconectar GitHub

---

## Próximas specs (aún sin escribir)

- 003 — Terminal pty integrada (Fase 3)
- 004 — Persistencia (SQLite: sesiones, mensajes)
- 005 — Hallazgos e informe de pentest (Fase 8)
- 006 — Router híbrido Gemini + DeepHat (Fase 2.5)
- 007 — Dictado por voz (Whisper local, Fase 5)
- 008 — Autoaprobación configurable por niveles
