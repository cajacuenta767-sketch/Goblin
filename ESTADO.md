# ESTADO del proyecto GOBLIN

> Foto del proyecto: qué está hecho, qué falta, dónde está cada cosa. Se actualiza en cada
> avance. **Última actualización:** 2026-10-24.

## 🔵 Resumen de specs completadas (15 specs)

| Spec | Qué | Estado |
|------|-----|--------|
| 001 | Backend core (agente, herramientas, API) | ✅ probado |
| 002 | Frontend IDE (chat, explorador, aprobaciones) | ✅ probado |
| 003 | App nativa Tauri (.deb) | ✅ config lista (compila en Parrot) |
| 004 | Terminal integrada (pty real) | ✅ probado |
| 005 | Persistencia (SQLite) | ✅ probado |
| 006 | Hallazgos + informe de pentest | ✅ probado |
| 007 | Editor Monaco | ✅ probado |
| 008 | Router híbrido Gemini + DeepHat | ✅ probado (sin key) |
| 009 | Autoaprobación por niveles | ✅ probado |
| 010 | Dictado por voz | ✅ probado |
| 011 | UI sesiones/hallazgos/informe | ✅ probado |
| 012 | Targets y engagements | ✅ probado |
| 013 | Tests automáticos (24 tests) | ✅ 24 pasan |
| 014 | CI + snippets de pentest + LICENSE | ✅ probado |
| 015 | Robustez y diagnóstico | ✅ probado |

**Herramientas de la IA (15):** list_dir, read_file, write_file, make_dir, move_path,
copy_path, delete_path, search_files, disk_usage, run_shell, add_finding, generate_report,
set_target, clear_target, get_target, get_snippet.

**Tests:** 24 automáticos (`./scripts/test.sh`), corren solos en GitHub (CI).

## ⬜ Pendiente real (solo requiere la PC del usuario)
- Compilar el `.deb` en Parrot (`./scripts/build.sh`)
- Probar el chat con DeepHat real (Ollama + modelo descargado)
- Probar Gemini con API key real (modo híbrido)

---

## ✅ Hecho y probado (detalle histórico)

### Backend (Spec 001) — completo
| Archivo | Qué hace | Probado |
|---------|----------|---------|
| `backend/config.py` | Lee `.env`, ajustes de hardware (DeepHat, num_ctx 4096) | ✅ |
| `backend/tools/filesystem.py` | 9 operaciones: listar, leer, escribir, crear carpeta, mover, copiar, borrar, buscar, uso de disco | ✅ |
| `backend/tools/shell.py` | Ejecuta comandos con timeout + bloqueo de peligrosos | ✅ (bloqueo de `rm -rf /` verificado) |
| `backend/tools/registry.py` | Catálogo de herramientas, schemas para el LLM, aprobaciones | ✅ |
| `backend/agent.py` | Bucle agéntico, aprobaciones, tope anti-bucle, system prompt pentest | ✅ (compila, lógica probada) |
| `backend/state.py` | Publica el target a la Polybar | ✅ |
| `backend/main.py` | API FastAPI (chat, files, models, target, info, health, system) | ✅ (endpoints responden) |

### Frontend (Spec 002) — v1 sin Monaco
| Archivo | Qué hace | Probado |
|---------|----------|---------|
| `frontend/index.html` | Estructura de paneles | ✅ (se sirve) |
| `frontend/css/theme.css` | Tokens de color (verde goblin #3ddc84) | ✅ |
| `frontend/css/layout.css` | Paneles, barra de estado, progreso | ✅ |
| `frontend/js/api.js` | Llamadas al backend | ✅ |
| `frontend/js/chat.js` | Enviar/recibir, markdown, etiqueta de modelo | ✅ |
| `frontend/js/approvals.js` | Caja de aprobación (borde rojo si peligrosa) | ✅ |
| `frontend/js/explorer.js` | Árbol de archivos navegable | ✅ |
| `frontend/js/main.js` | Arranque, estado, barra inferior RAM/CPU | ✅ |

### App nativa (Spec 003) — configuración lista, se compila en Parrot
| Archivo | Qué hace | Probado |
|---------|----------|---------|
| `src-tauri/Cargo.toml` | Dependencias Rust/Tauri v2 | ✅ TOML válido |
| `src-tauri/src/main.rs` | Arranca el backend Python, abre la ventana nativa, lo detiene al cerrar | ✅ estructura coherente |
| `src-tauri/tauri.conf.json` | Ventana (1400x900), bundle `.deb`/AppImage, deps del paquete | ✅ JSON válido |
| `src-tauri/icons/` | Icono GOBLIN (hexágono verde, varios tamaños) | ✅ generados |
| `scripts/install-nativo.sh` | Instala Rust + Node + CLI Tauri + libs GTK/WebKit | ✅ |
| `scripts/build.sh` | Compila la app y genera el `.deb` | ⬜ (se compila en Parrot) |

> ⚠️ La compilación final (`.deb`) se hace en TU Parrot: Tauri necesita Rust y libs de
> sistema que no están en el entorno de nube. Toda la config está lista y validada; en tu
> PC solo corres `./scripts/install-nativo.sh` y luego `./scripts/build.sh`.

### Infraestructura
- ✅ `scripts/install.sh` — instala Ollama + deps + modelo (y ofrece la app nativa)
- ✅ `scripts/run.sh` — modo navegador (desarrollo)
- ✅ `scripts/build.sh` — compila la app nativa
- ✅ Git conectado a GitHub (cajacuenta767-sketch/Goblin) y subido
- ✅ SDD: constitución, AGENTS.md, specs (001, 002, 003), tasks

---

## ⬜ Pendiente

### Validación (requiere la PC del usuario)
- ⬜ Probar el chat con **DeepHat real** (necesita Ollama corriendo + modelo descargado).
  Aquí solo se probó la infraestructura web; el modelo no estaba disponible en el entorno.

### Specs siguientes
La lista viva de tareas y el backlog priorizado están en `.specify/tasks.md`.
Resumen al 2026-10-24: 024 (Detener) y 025 (guardas de privacidad y autorización) implementadas
y validadas en el entorno; 022, 023 y 025 (Gemini real) esperan prueba en la PC del usuario.

---

## 📍 Dónde está cada cosa (referencia rápida)

```
goblin/
├── EMPEZAR-AQUI.md     ← punto de entrada (léelo primero)
├── ESTADO.md           ← este archivo
├── AGENTS.md           ← instrucciones para IAs
├── PLAN.md             ← roadmap por fases
├── ARQUITECTURA.md     ← stack y decisiones técnicas
├── README.md           ← descripción para GitHub
├── .specify/
│   ├── constitution.md ← reglas inviolables
│   ├── specs/          ← especificaciones (001, 002...)
│   └── tasks.md        ← tareas ✅/⬜
├── backend/            ← Python (api/core/tools/db)
├── frontend/           ← HTML/CSS/JS
├── scripts/            ← install.sh, run.sh, subir-github.sh
├── .env.example        ← plantilla de config (copiar a .env)
├── workspace/          ← área de trabajo de la IA (no en git)
└── data/               ← datos (no en git)
```

---

## 🔗 Subir a GitHub

**Repo destino:** `https://github.com/cajacuenta767-sketch/Goblin`

**Opción automática:**
```bash
./scripts/subir-github.sh
```

**Opción manual:**
```bash
git init                 # (si aún no es repo)
git add -A
git commit -m "GOBLIN"
git branch -M main
git remote add origin https://github.com/cajacuenta767-sketch/Goblin.git
git push -u origin main
```

> Si pide autenticación: usuario de GitHub + **token personal** (Settings → Developer
> settings → Personal access tokens → classic → permiso `repo`). GitHub ya no acepta
> la contraseña normal.

---

## 📝 Historial de commits

1. `Crea esqueleto de GOBLIN: backend (FastAPI + agente + herramientas), docs y configuración`
2. `Adopta Spec-Driven Development (SDD)`
3. `Implementa Spec 002: frontend IDE (v1 sin Monaco) + scripts`
