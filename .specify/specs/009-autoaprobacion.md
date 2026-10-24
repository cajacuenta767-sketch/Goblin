# Spec 009 — Autoaprobación configurable por niveles

**Estado:** 🟨 En progreso · **Depende de:** 001

## Qué
Niveles de aprobación configurables para no tener que aprobar cada acción manualmente.

## Por qué
El usuario pidió "control total sin fricción", pero aprobar cada acción cansa. La solución
son niveles: auto para lo seguro, preguntar solo para lo destructivo.

## Niveles
- "cauto" (por defecto): pide aprobación para todo lo que modifica/ejecuta (write, move,
  copy, delete, shell). Es el comportamiento actual.
- "normal": auto-aprueba crear/escribir/mover/copiar; pide solo para borrar y shell.
- "confianza": auto-aprueba todo salvo borrar (delete siempre pide, por seguridad).

La lista negra de comandos SIEMPRE se respeta, en cualquier nivel (constitución art. III).
delete_path SIEMPRE pide confirmación, en todos los niveles.

## Criterios de validación
- [ ] En nivel "normal", make_dir se ejecuta sin preguntar; delete_path sí pregunta.
- [ ] En nivel "confianza", run_shell se ejecuta solo; delete_path aún pregunta.
- [ ] La lista negra bloquea en todos los niveles.

## Archivos
- `backend/approvals.py` — lógica de niveles
- `backend/agent.py` — consultar el nivel antes de pedir aprobación
- `backend/main.py` — endpoint para cambiar nivel
