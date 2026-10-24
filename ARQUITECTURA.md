# ARQUITECTURA — GOBLIN

> Documento técnico de decisiones de arquitectura (ADR). Define el stack, la estructura,
> la base de datos y las convenciones ANTES de escribir código. Nada se construye hasta
> que esto esté aprobado. 🔵 = decisiones nuevas de esta propuesta.

---

## 1. Principios de diseño (las reglas que seguiremos)

1. **Local-first:** todo corre en la PC del usuario. Nada sale a la nube salvo Gemini (opt-in).
2. **Separación de capas:** frontend ↔ API ↔ lógica ↔ herramientas. Cada capa aislada.
3. **Seguridad por defecto:** acciones peligrosas piden aprobación; servidor solo en localhost.
4. **Un modelo primero:** arrancamos con DeepHat solo. Gemini/híbrido llega cuando sea estable.
5. **Código legible > código listo:** nombres claros, funciones cortas, comentado donde importa.
6. **Sin dependencias innecesarias:** cada librería debe justificarse. Menos = más mantenible.
7. **Todo versionado en git:** commits pequeños y descriptivos desde el primer día.

---

## 2. Stack tecnológico propuesto

### 2.1. Backend
| Pieza            | Elección              | Por qué                                              |
|------------------|-----------------------|------------------------------------------------------|
| Lenguaje         | **Python 3.11+**      | Ideal para IA/Ollama, pentesting, y lo pidió el user |
| Framework web    | **FastAPI**           | Async, rápido, WebSocket nativo, auto-docs           |
| Servidor ASGI    | **Uvicorn**           | El estándar para FastAPI                              |
| Cliente LLM      | **ollama** (pip)      | Cliente oficial de Ollama                            |
| Validación       | **Pydantic v2**       | Viene con FastAPI, valida datos de entrada/salida    |
| Base de datos    | **SQLite** (stdlib)   | Cero config, un archivo, perfecto para app local     |
| ORM / acceso DB  | **SQLModel**          | Pydantic + SQLAlchemy, encaja con FastAPI            |
| Terminal (pty)   | **ptyprocess**        | Shell real persistente (Fase 3)                      |
| Variables config | **python-dotenv**     | Carga `.env` (API keys, ajustes)                     |

### 2.2. Frontend
| Pieza            | Elección                       | Por qué                                     |
|------------------|--------------------------------|---------------------------------------------|
| Base             | **HTML + CSS + JS vanilla**    | 🔵 Empezamos simple, sin build. Rápido en tu PC |
| Editor de código | **Monaco** (CDN)               | El editor de VS Code, sin instalar nada     |
| Terminal UI      | **xterm.js** (CDN)             | Terminal en el navegador (Fase 3)           |
| Markdown         | **marked.js** (CDN)            | Renderiza las respuestas de la IA           |
| Resaltado código | **highlight.js** (CDN)         | Colorea bloques de código en el chat        |
| Comunicación     | **WebSocket + fetch**          | WS para streaming, fetch para acciones puntuales |

> 🔵 **Nota sobre React:** el plan menciona "migrable a React + Vite". Decisión: NO usar React
> ahora. Vanilla JS es suficiente, no necesita compilación (build), carga más rápido en tu
> CPU y es más fácil de depurar. Si el proyecto crece mucho, migramos después. Regla #6.

### 2.3. Modelo / IA
| Pieza            | Elección              | Por qué                                              |
|------------------|-----------------------|------------------------------------------------------|
| Runtime          | **Ollama**            | Gestiona el modelo local, API HTTP simple            |
| Modelo principal | **DeepHat-V1-7B** Q4  | Ya decidido (pentesting, sin censura, cabe en 16 GB) |
| Modelo nube      | Gemini (Fase 2.5)     | Opcional, más adelante                               |
| Transcripción    | **faster-whisper**    | Dictado por voz local (Fase 5)                       |

### 2.4. App nativa de escritorio (Spec 003) 🔵
| Pieza            | Elección              | Por qué                                              |
|------------------|-----------------------|------------------------------------------------------|
| App de escritorio| **Tauri v2**          | El usuario pidió app NATIVA para Parrot, no web      |
| Formato ventana  | GTK + WebKit (sistema)| Ligero: no empaqueta Chromium (importa por 16 GB)    |
| Instalador       | `.deb` + AppImage     | Instalable en Parrot con dpkg/apt                    |

> 🔵 **Decisión:** GOBLIN es una app nativa. Tauri abre una ventana propia que arranca el
> backend Python como proceso hijo y carga el frontend desde 127.0.0.1:8800. El modo
> navegador (`run.sh`) se mantiene solo para desarrollo. Ver `.specify/specs/003-app-nativa-tauri.md`.

---

## 3. Arquitectura en capas

```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND  (navegador en 127.0.0.1:8000)                │
│  - index.html + css/ + js/ (módulos por panel)          │
│  - Monaco (editor), xterm.js (terminal), marked (md)    │
└───────────────┬─────────────────────────────────────────┘
                │  WebSocket (chat/stream)  +  REST (acciones)
┌───────────────▼─────────────────────────────────────────┐
│  API LAYER  (FastAPI — backend/api/)                    │
│  - routes: chat, files, terminal, sessions, findings    │
│  - valida entrada/salida con Pydantic                   │
│  - NO tiene lógica de negocio: solo recibe y delega     │
└───────────────┬─────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────┐
│  CORE / LÓGICA  (backend/core/)                         │
│  - agent.py    → bucle del agente (piensa→actúa→observa)│
│  - router.py   → elige modelo (DeepHat/Gemini) [Fase2.5]│
│  - approvals.py→ gestiona aprobaciones                  │
│  - llm/        → clientes: ollama_client, gemini_client │
└───────────────┬─────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────┐
│  TOOLS  (backend/tools/) — lo que la IA puede HACER     │
│  - files.py (crear/mover/borrar/copiar/buscar)          │
│  - shell.py (ejecutar comandos)                         │
│  - registry.py (catálogo de herramientas + schemas)     │
│  - safety.py (lista negra, validación de rutas)         │
└───────────────┬─────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────┐
│  DATOS  (backend/db/) + SISTEMA DE ARCHIVOS             │
│  - SQLite (sesiones, mensajes, hallazgos, auditoría)    │
│  - workspace/ y rutas del sistema (control de la PC)    │
└─────────────────────────────────────────────────────────┘
```

**Regla de oro de las capas:** cada capa solo habla con la de abajo. El frontend nunca
toca las herramientas directamente; pasa por la API → core → tools. Esto hace el código
testeable y seguro.

---

## 4. Estructura de carpetas completa

```
goblin/
├── backend/
│   ├── main.py                 # arranque FastAPI, monta todo
│   ├── config.py               # lee .env, constantes globales
│   │
│   ├── api/                    # CAPA API (solo rutas)
│   │   ├── __init__.py
│   │   ├── chat.py             # WebSocket del chat + streaming
│   │   ├── files.py            # endpoints de explorador
│   │   ├── sessions.py         # listar/crear/borrar conversaciones
│   │   ├── findings.py         # hallazgos (Fase 8)
│   │   ├── terminal.py         # WebSocket terminal (Fase 3)
│   │   └── system.py           # info de modelo, RAM/CPU, target
│   │
│   ├── core/                   # CAPA LÓGICA
│   │   ├── __init__.py
│   │   ├── agent.py            # bucle del agente
│   │   ├── router.py           # selección de modelo (Fase 2.5)
│   │   ├── approvals.py        # cola de aprobaciones
│   │   └── llm/
│   │       ├── __init__.py
│   │       ├── ollama_client.py
│   │       └── gemini_client.py   # (Fase 2.5)
│   │
│   ├── tools/                  # CAPA HERRAMIENTAS
│   │   ├── __init__.py
│   │   ├── registry.py         # catálogo + schemas para el LLM
│   │   ├── files.py            # operaciones de archivos
│   │   ├── shell.py            # ejecución de comandos
│   │   └── safety.py           # lista negra, validación de rutas
│   │
│   ├── db/                     # CAPA DATOS
│   │   ├── __init__.py
│   │   ├── database.py         # conexión SQLite, init
│   │   └── models.py           # modelos SQLModel (tablas)
│   │
│   ├── system_prompts/         # prompts del sistema
│   │   └── pentest.md          # prompt especializado pentest
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── index.html              # estructura de la UI
│   ├── css/
│   │   ├── theme.css           # tokens de color (verde goblin)
│   │   └── layout.css          # los paneles
│   └── js/
│       ├── main.js             # arranque, estado global
│       ├── api.js              # llamadas al backend (fetch/WS)
│       ├── chat.js             # panel de chat
│       ├── editor.js           # Monaco
│       ├── explorer.js         # árbol de archivos
│       ├── terminal.js         # xterm.js (Fase 3)
│       └── approvals.js        # cajas de aprobación
│
├── workspace/                  # área de trabajo de la IA (git-ignored)
├── data/                       # SQLite vive aquí (git-ignored)
│   └── goblin.db
│
├── scripts/
│   ├── install.sh              # instalador Parrot
│   └── run.sh                  # arranque
│
├── .env.example                # plantilla de config (SÍ se sube)
├── .env                        # config real (git-ignored, NO se sube)
├── .gitignore
├── PLAN.md
├── ARQUITECTURA.md             # este archivo
└── README.md
```

---

## 5. Base de datos (SQLite) — esquema

> Un solo archivo `data/goblin.db`. Cuatro tablas para empezar.

### Tabla `sessions` (conversaciones)
| Campo        | Tipo      | Descripción                          |
|--------------|-----------|--------------------------------------|
| id           | TEXT PK   | UUID de la sesión                    |
| title        | TEXT      | Título de la conversación            |
| target       | TEXT      | IP/dominio del engagement (opcional) |
| model        | TEXT      | Modelo usado por defecto             |
| created_at   | DATETIME  | Fecha de creación                    |
| updated_at   | DATETIME  | Última actividad                     |

### Tabla `messages` (mensajes del chat)
| Campo        | Tipo      | Descripción                          |
|--------------|-----------|--------------------------------------|
| id           | INTEGER PK| Autoincremental                      |
| session_id   | TEXT FK   | A qué sesión pertenece               |
| role         | TEXT      | user / assistant / tool              |
| content      | TEXT      | El texto del mensaje                 |
| model        | TEXT      | Qué modelo respondió (DeepHat/Gemini)|
| created_at   | DATETIME  | Timestamp                            |

### Tabla `findings` (hallazgos de pentest — Fase 8)
| Campo        | Tipo      | Descripción                          |
|--------------|-----------|--------------------------------------|
| id           | INTEGER PK| Autoincremental                      |
| session_id   | TEXT FK   | A qué engagement pertenece           |
| severity     | TEXT      | critical/high/medium/low/info        |
| title        | TEXT      | Nombre del hallazgo                  |
| host         | TEXT      | IP/host afectado                     |
| port         | TEXT      | Puerto/servicio                      |
| description  | TEXT      | Detalle                              |
| evidence     | TEXT      | Evidencia/salida                     |
| created_at   | DATETIME  | Timestamp                            |

### Tabla `audit_log` (auditoría — Fase 8)
| Campo        | Tipo      | Descripción                          |
|--------------|-----------|--------------------------------------|
| id           | INTEGER PK| Autoincremental                      |
| session_id   | TEXT FK   | Sesión                               |
| tool         | TEXT      | Herramienta usada (run_shell, etc.)  |
| arguments    | TEXT      | Argumentos (JSON)                    |
| result       | TEXT      | Resultado (truncado)                 |
| approved     | BOOLEAN   | Si requirió y recibió aprobación     |
| created_at   | DATETIME  | Timestamp                            |

---

## 6. Flujo de datos (ejemplo: "crea una carpeta y escanea")

```
1. Usuario escribe en el chat          → frontend/js/chat.js
2. Se envía por WebSocket              → backend/api/chat.py
3. API llama al agente                 → backend/core/agent.py
4. Agente pregunta al modelo           → core/llm/ollama_client.py → Ollama
5. Modelo responde "usa make_dir"      → agent.py interpreta
6. make_dir no necesita aprobación     → tools/files.py lo ejecuta
7. Modelo responde "usa run_shell nmap"→ requiere aprobación
8. API manda la aprobación al frontend → approvals.js muestra la caja
9. Usuario aprueba                     → vuelve al agente
10. shell.py ejecuta, guarda en audit  → db/
11. Resultado se transmite (stream)    → chat.js lo muestra
```

---

## 7. Convenciones de código (reglas de buen programador)

- **Nombres:** inglés en el código (`create_file`), español en los textos al usuario.
- **Funciones cortas:** una función hace una cosa. Si pasa de ~40 líneas, se divide.
- **Type hints** en todo Python (`def read_file(path: str) -> str:`).
- **Docstrings** en funciones públicas.
- **Sin secretos en el código:** API keys solo en `.env`.
- **Commits atómicos:** un commit = un cambio lógico, mensaje claro en imperativo.
- **Errores controlados:** nada de `except: pass`. Siempre mensaje útil.

---

## 8. Git — estrategia

- **Rama principal:** `main`
- **Flujo:** por ahora trabajo directo en `main` (proyecto de 1 persona). Ramas por feature
  cuando haga falta.
- **`.gitignore`** cubre: `.env`, `workspace/`, `data/`, `__pycache__/`, `.venv/`, `*.pyc`
- **Commits** en español, imperativo: "Agrega explorador de archivos", "Corrige bug de rutas".
- **El repo NO incluye:** el modelo (pesa GB, se descarga con Ollama), ni secretos, ni datos.

---

## 9. Orden de construcción (siguiendo el plan)

> Nada de saltos. Este es el orden, un paso cerrado antes del siguiente.

1. ✅ Definir arquitectura (este documento)
2. ⬜ Crear estructura de carpetas + git init + .gitignore + README
3. ⬜ Backend: config, db (modelos + init), requirements
4. ⬜ Backend: capa tools (files, shell, safety, registry)
5. ⬜ Backend: capa core (agent, ollama_client, approvals)
6. ⬜ Backend: capa api (chat WS, files, sessions, system)
7. ⬜ Frontend: HTML + CSS (la maqueta ya aprobada) conectado al backend
8. ⬜ Scripts: install.sh + run.sh ajustados a tu PC
9. ⬜ Probar end-to-end con DeepHat
10. ⬜ Subir a GitHub

Fases posteriores (terminal pty, router híbrido, hallazgos, informe) van después,
cada una como su propio bloque de commits.
