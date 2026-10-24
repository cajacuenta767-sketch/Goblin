# Spec 001 — Backend Core (agente + herramientas + API)

**Estado:** ✅ Implementado · **Fase:** 1-2 · **Depende de:** nada

## Qué (objetivo)

Un backend en Python que exponga un agente de IA capaz de conversar con DeepHat (vía Ollama),
ejecutar herramientas sobre el sistema de archivos y la shell, con aprobaciones para acciones
peligrosas, servido por una API local.

## Por qué

Es el núcleo de GOBLIN: sin esto no hay IA ni control del sistema. Todo lo demás se apoya aquí.

## Requisitos funcionales

- RF1: Conversar con el modelo por defecto (DeepHat-V1-7B) vía Ollama.
- RF2: Herramientas de archivos: listar, leer, escribir, crear carpeta, mover, copiar,
  borrar, buscar texto, ver uso de disco.
- RF3: Herramienta de shell con timeout y bloqueo de comandos peligrosos.
- RF4: Las acciones que modifican/ejecutan requieren aprobación del usuario.
- RF5: Tope de iteraciones del agente (anti-bucle).
- RF6: API REST: chat, approve, files, models, target, info, health.
- RF7: Publicar el target a un archivo para la Polybar.

## Requisitos no funcionales

- RNF1: El servidor escucha solo en 127.0.0.1.
- RNF2: Contexto del modelo = 4096 (ahorro de RAM).
- RNF3: El modelo se libera tras inactividad (keep_alive).
- RNF4: Respeta FULL_ACCESS (true = todo el sistema; false = solo workspace).

## Criterios de validación

- [x] Crear/mover/copiar/borrar/buscar archivos funciona.
- [x] `rm -rf /` y otros patrones peligrosos se bloquean.
- [x] Comandos normales se ejecutan y devuelven salida.
- [x] config.py carga valores desde .env.
- [x] Todos los archivos compilan sin errores.
- [ ] Chat end-to-end con DeepHat real (requiere Ollama + modelo en la PC del usuario).

## Fuera de alcance (va en otras specs)

- Frontend (spec 002)
- Terminal pty persistente (spec 003)
- Router híbrido con Gemini (spec futura)
- Persistencia en base de datos (spec futura)
- Hallazgos e informes (spec futura)

## Archivos

`backend/config.py`, `backend/agent.py`, `backend/state.py`, `backend/main.py`,
`backend/tools/{filesystem,shell,registry}.py`
