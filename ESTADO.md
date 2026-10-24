# ESTADO del proyecto GOBLIN

> Foto del proyecto: qué está hecho, qué falta, dónde está cada cosa. Se actualiza en cada
> avance. **Última actualización:** 2026-10-23.

---

## ✅ Hecho y probado

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

### Infraestructura
- ✅ `scripts/install.sh` — instala Ollama + deps + modelo
- ✅ `scripts/run.sh` — arranca con flags de RAM/CPU
- ✅ Git inicializado con 3 commits
- ✅ SDD: constitución, AGENTS.md, specs, tasks

---

## ⬜ Pendiente

### Validación (requiere la PC del usuario)
- ⬜ Probar el chat con **DeepHat real** (necesita Ollama corriendo + modelo descargado).
  Aquí solo se probó la infraestructura web; el modelo no estaba disponible en el entorno.

### Próximas specs (sin escribir aún)
- ⬜ **003** — Terminal pty integrada (xterm.js + shell persistente) — Fase 3
- ⬜ **004** — Persistencia (SQLite: sesiones, mensajes) — Fase 4
- ⬜ **005** — Hallazgos e informe de pentest — Fase 8
- ⬜ **006** — Router híbrido Gemini + DeepHat — Fase 2.5
- ⬜ **007** — Dictado por voz (Whisper local) — Fase 5
- ⬜ **008** — Autoaprobación configurable por niveles
- ⬜ **Editor Monaco** — se dejó fuera de la v1 del frontend a propósito

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
