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

## Spec 005 — Persistencia (SQLite) ✅

- ✅ T005.1 — backend/db.py (SQLite stdlib: sesiones, mensajes, findings, auditoría)
- ✅ T005.2 — agent.py guarda mensajes + log de auditoría de cada acción
- ✅ T005.3 — main.py: endpoints /api/sessions (listar/abrir/borrar)
- ✅ T005.4 — Resuelto conflicto: eliminada carpeta db/ vacía que tapaba db.py
- ✅ T005.5 — Validado: mensajes/sesiones/auditoría persisten y se borran

## Spec 006 — Hallazgos e informe de pentest ✅

- ✅ T006.1 — backend/report.py (informe Markdown: resumen, tabla, detalle, anexo auditoría)
- ✅ T006.2 — backend/tools/pentest.py (herramientas add_finding, generate_report)
- ✅ T006.3 — registry.py: registradas las 2 herramientas nuevas + schemas
- ✅ T006.4 — main.py: endpoints /api/findings, /api/report
- ✅ T006.5 — Validado: la IA registra hallazgos y genera informe profesional

## Spec 007 — Editor Monaco ✅

- ✅ T007.1 — main.py: endpoints /api/file (leer y escribir contenido)
- ✅ T007.2 — Monaco por CDN + panel de editor en el panel derecho
- ✅ T007.3 — frontend/js/editor.js (abrir, editar, guardar con Ctrl+S, resaltado por lenguaje)
- ✅ T007.4 — explorer.js: clic en archivo lo abre en el editor
- ✅ T007.5 — Validado: leer/escribir archivos vía API funciona

## Spec 008 — Router híbrido (Gemini + DeepHat) ✅

- ✅ T008.1 — backend/router.py (modos local/hybrid/manual, detección de negativa)
- ✅ T008.2 — backend/core/llm/gemini_client.py (cliente Gemini con tools, falla limpio)
- ✅ T008.3 — agent.py: _call_model aplica el router (Gemini → fallback DeepHat)
- ✅ T008.4 — config.py: GEMINI_API_KEY, GEMINI_MODEL
- ✅ T008.5 — main.py: endpoints /api/mode (get/set)
- ✅ T008.6 — frontend: chip de modo (Local/Híbrido/Manual) + aviso sin API key
- ✅ T008.7 — Validado: modo por defecto local, híbrido sin key avisa y usa DeepHat
- ⬜ T008.8 — Probar Gemini real con API key (requiere key del usuario)

## Spec 009 — Autoaprobación por niveles ✅

- ✅ T009.1 — backend/approvals.py (niveles cauto/normal/confianza)
- ✅ T009.2 — agent.py consulta el nivel antes de pedir aprobación
- ✅ T009.3 — main.py: endpoint /api/approval-level
- ✅ T009.4 — Validado: delete SIEMPRE pide (incluso en confianza); lista negra siempre aplica

## Spec 010 — Dictado por voz ✅

- ✅ T010.1 — frontend/js/voice.js (Web Speech API, sin Whisper para ahorrar RAM)
- ✅ T010.2 — Micrófono con indicador "escuchando" (rojo pulsante)
- ✅ T010.3 — Reconocimiento en español, avisa si el navegador no soporta
- ✅ T010.4 — Validado: voice.js se sirve y se inicializa

## ✅ TODAS LAS SPECS PRINCIPALES COMPLETAS

Pendiente de cablear en la UI (backend listo, falta frontend):
- Sidebar de sesiones reales (endpoints /api/sessions ya existen)
- Panel de hallazgos visual (endpoints /api/findings ya existen)
- Botón de generar informe (endpoint /api/report ya existe)

Validaciones que requieren la PC del usuario:
- Compilar el .deb en Parrot
- Probar chat con DeepHat real
- Probar Gemini con API key real
