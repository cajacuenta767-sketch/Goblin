# Spec 012 — Targets y engagements

**Estado:** 🟨 En progreso · **Depende de:** 001, 005

## Qué
Gestión del objetivo del pentest: fijar un target, crear su estructura de carpetas
automática, y que la IA y la terminal trabajen en ese contexto.

## Requisitos funcionales
- RF1: Herramienta `set_target(target)` que fija el objetivo, lo guarda en la sesión y lo
  publica a la Polybar (reusa state.py).
- RF2: Al fijar un target, crear la estructura: engagements/<target>/{recon,loot,reports,notes}.
- RF3: Herramienta `clear_target()` que limpia el target (Polybar vuelve a "No target").
- RF4: Comandos rápidos en el system prompt: /recon, /scan, /report con flujos sugeridos.
- RF5: Endpoint para que el frontend muestre el target actual.

## Criterios de validación
- [ ] set_target crea la estructura de carpetas y actualiza la Polybar.
- [ ] clear_target limpia el target.

## Archivos
- `backend/tools/targets.py` — herramientas de target
- `backend/tools/registry.py` — registrar
- `backend/agent.py` — system prompt con comandos rápidos
