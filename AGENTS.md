# AGENTS.md — Instrucciones para agentes de IA

> Si eres una IA (Claude Code, un asistente, o GOBLIN mismo) trabajando en este proyecto,
> LEE ESTO PRIMERO. Define cómo contribuir sin romper nada. Complementa la constitución
> (`.specify/constitution.md`), que es la autoridad máxima.

## Antes de tocar código

1. Lee `.specify/constitution.md` (reglas inviolables).
2. Lee la spec correspondiente en `.specify/specs/`. Si no existe, créala antes de programar.
3. Consulta `ARQUITECTURA.md` para el stack y las capas.
4. Consulta `PLAN.md` para saber en qué fase estamos.

## Flujo de trabajo (SDD)

```
constitución → spec → clarificar dudas → plan → tareas → implementar → validar → iterar
```

- **Nunca** programes "a ojo". Toda funcionalidad nace de una spec.
- Si una spec es ambigua, pregunta antes de asumir.
- Al terminar, valida contra la spec y marca las tareas como hechas.

## Reglas de oro

- **Respeta las capas:** Frontend → API → Core → Tools → Datos. No saltes capas.
- **Un modelo primero:** no metas Gemini/híbrido hasta que la base con DeepHat sea estable.
- **Seguridad:** acciones destructivas piden aprobación; la lista negra se respeta siempre.
- **Local:** servidor solo en 127.0.0.1; secretos solo en `.env`.
- **Hardware:** todo debe correr en CPU con 16 GB RAM.

## Convenciones de código

- Python 3.11+, type hints, funciones cortas, docstrings en lo público.
- Nombres en inglés en el código; mensajes al usuario en español.
- Sin `except: pass`. Maneja errores con mensajes claros.
- Frontend: vanilla JS, sin frameworks ni build.

## Git

- Commits atómicos, en español, imperativo: "Agrega X", "Corrige Y".
- Nunca subas `.env`, `workspace/`, `data/` ni el modelo.
- Rama principal: `main`.

## Estructura del proyecto

```
.specify/
  constitution.md     ← reglas inviolables
  specs/              ← una spec por funcionalidad (numeradas)
  tasks.md            ← tareas concretas derivadas de las specs
AGENTS.md             ← este archivo
PLAN.md               ← roadmap/visión
ARQUITECTURA.md       ← stack y decisiones técnicas
backend/              ← Python (api/core/tools/db)
frontend/             ← HTML/CSS/JS
scripts/              ← install.sh, run.sh
```

## Qué NO hacer

- No inventes capacidades, modelos o enlaces: verifica antes de afirmar.
- No añadas dependencias sin justificarlas.
- No ejecutes acciones destructivas sin aprobación.
- No expongas el servidor a la red.
- No improvises cambios de alcance: vuelve a la spec.
