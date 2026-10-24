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

## Spec 003 — App nativa con Tauri ✅ (config lista, compila en Parrot)

- ✅ T003.1 — src-tauri/Cargo.toml (dependencias Rust/Tauri v2)
- ✅ T003.2 — src-tauri/src/main.rs (arranca backend Python, abre ventana, lo detiene al cerrar)
- ✅ T003.3 — src-tauri/tauri.conf.json (ventana, bundle deb/appimage, deps del .deb)
- ✅ T003.4 — src-tauri/build.rs
- ✅ T003.5 — Iconos de GOBLIN (hexágono verde, 32/128/256/512 px)
- ✅ T003.6 — scripts/install-nativo.sh (Rust + Node + CLI Tauri + libs GTK/WebKit)
- ✅ T003.7 — scripts/build.sh (compila la app + genera .deb)
- ✅ T003.8 — install.sh actualizado (ofrece instalar la app nativa)
- ✅ T003.9 — Validar config (JSON/TOML/estructura main.rs) — hecho en el entorno
- ⬜ T003.10 — Compilar el .deb en Parrot y validar la ventana nativa (en la PC del usuario)

## Infraestructura (transversal)

- ✅ TI.1 — scripts/install.sh (instalador Parrot, instala Ollama + deps + modelo)
- ✅ TI.2 — scripts/run.sh (modo navegador para desarrollo)
- ✅ TI.3 — Subir a GitHub (repo cajacuenta767-sketch/Goblin) — CONECTADO y subido
- ✅ TI.4 — scripts/subir-github.sh

---

## Spec 004 — Terminal integrada (pty real) ✅

- ✅ T004.1 — backend/terminal.py (shell bash persistente sobre pty)
- ✅ T004.2 — backend/main.py: WebSocket /ws/terminal
- ✅ T004.3 — frontend: xterm.js por CDN + panel de terminal
- ✅ T004.4 — frontend/js/terminal.js (cliente xterm ↔ WebSocket)
- ✅ T004.5 — CSS del panel de terminal + botón "Terminal" en el input
- ✅ T004.6 — Validado end-to-end: cd y variables persisten (shell real viva)

## Próximas specs (aún sin escribir)

- 005 — Persistencia (SQLite: sesiones, mensajes)
- 006 — Hallazgos e informe de pentest (Fase 8)
- 007 — Editor Monaco (ver/editar archivos)
- 008 — Router híbrido Gemini + DeepHat (Fase 2.5)
- 009 — Dictado por voz (Whisper local, Fase 5)
- 010 — Autoaprobación configurable por niveles
