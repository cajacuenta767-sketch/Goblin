# Constitución de GOBLIN

> Las reglas inviolables del proyecto. Todo —código, specs, tareas y decisiones— debe
> respetar esta constitución. Si una spec contradice la constitución, gana la constitución.
> Spec-Driven Development (SDD): la especificación guía la construcción, no al revés.

**Versión:** 1.0 · **Ratificada:** 2026-10-23

---

## Artículo I — Identidad del proyecto

1. GOBLIN es un IDE local con IA agéntica para **ciberseguridad y pentesting**.
2. Corre en la máquina del usuario (Parrot OS). El usuario es ingeniero de ciberseguridad.
3. El modelo por defecto es **DeepHat-V1-7B** (local, sin censura) vía Ollama.

## Artículo II — Privacidad y localidad (NO NEGOCIABLE)

1. Todo corre en local. Ningún dato sale de la máquina **salvo** que el usuario active
   explícitamente el modo híbrido con Gemini.
2. El servidor escucha **solo en 127.0.0.1**. Nunca se expone a la red.
3. Los secretos (API keys) viven solo en `.env`, jamás en el código ni en el repositorio.
4. En un engagement real con cliente/NDA, el modo local puro es obligatorio.

## Artículo III — Seguridad (NO NEGOCIABLE)

1. Las acciones destructivas o privilegiadas (borrar, sobrescribir, mover, ejecutar
   comandos, sudo) **requieren aprobación del usuario** antes de ejecutarse.
2. Existe una **lista negra de comandos** con bloqueo duro (ej. `rm -rf /`, `mkfs`,
   fork bombs) que se bloquean aunque la IA los proponga y aunque el usuario los apruebe.
3. El agente tiene un **tope de iteraciones** para no entrar en bucles infinitos.
4. Toda acción que ejecuta la IA queda en un **log de auditoría** (trazabilidad total).
5. GOBLIN solo se usa contra objetivos con **autorización explícita por escrito**.

## Artículo IV — Arquitectura

1. **Separación de capas estricta:** Frontend → API → Core → Tools → Datos.
   Cada capa solo habla con la de abajo. El frontend NUNCA toca las herramientas directo.
2. **Backend:** Python 3.11+ con FastAPI. **Frontend:** HTML/CSS/JS vanilla (sin build).
3. **Un modelo primero:** se construye y estabiliza con DeepHat solo. El router híbrido
   (Gemini) se añade después, nunca antes de tener una base estable.
4. Sin dependencias innecesarias. Cada librería debe justificarse.

## Artículo V — Hardware objetivo

1. Equipo real: i7-10700 (8C/16H), 16 GB RAM, **sin GPU dedicada** (inferencia en CPU).
2. Toda decisión técnica respeta este límite: contexto reducido (num_ctx 4096), un solo
   modelo cargado a la vez, liberar RAM cuando el modelo no se usa.
3. No se proponen modelos ni configuraciones que no quepan o no corran en este equipo.

## Artículo VI — Proceso (SDD)

1. **Nada se programa sin una spec.** El flujo es: constitución → spec → clarificación →
   plan → tareas → implementación → validación → iteración.
2. Las specs se escriben en **Markdown**, en `.specify/specs/`, numeradas.
3. Una spec define QUÉ y por qué; el plan y las tareas definen CÓMO.
4. Toda implementación se **valida** contra su spec antes de darse por terminada.
5. Los cambios de alcance vuelven a la spec; no se improvisan en el código.

## Artículo VII — Calidad de código

1. Nombres en inglés en el código, textos al usuario en español.
2. Funciones cortas (una responsabilidad). Type hints en Python. Docstrings en lo público.
3. Nada de `except: pass`. Errores controlados con mensajes útiles.
4. Commits atómicos, mensaje claro en imperativo. Se versiona desde el primer día.

## Artículo VIII — Transparencia con el usuario

1. Se le dice al usuario la verdad sobre limitaciones (ej. lentitud en CPU), aunque no
   sea lo que quiere oír.
2. No se inventan hechos (modelos, enlaces, capacidades); se verifican antes de afirmar.
3. Las decisiones técnicas se explican, no se imponen.

---

## Enmiendas

- Cualquier cambio a esta constitución se registra aquí con fecha y motivo.
- (ninguna todavía)
