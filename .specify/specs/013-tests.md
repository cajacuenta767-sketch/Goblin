# Spec 013 — Tests automáticos

**Estado:** 🟨 En progreso · **Depende de:** todo el backend

## Qué
Suite de tests automáticos (pytest) que valida las piezas críticas del backend, para poder
cambiar código sin romper lo que funciona.

## Por qué
Ningún proyecto serio va sin tests. Permiten validar en segundos que todo sigue bien tras
un cambio. Es parte de la calidad de código (constitución art. VII).

## Cobertura
- Herramientas de archivos (crear, leer, mover, copiar, borrar, buscar).
- Seguridad: la lista negra bloquea comandos peligrosos.
- Persistencia: guardar/leer sesiones, mensajes, hallazgos.
- Router: modos, detección de negativa, Gemini no disponible sin key.
- Aprobaciones: niveles, delete siempre pide.
- Informe: generación con hallazgos.
- Targets: estructura de engagement.

## Criterios de validación
- [ ] `pytest` corre y todos los tests pasan.

## Archivos
- `backend/tests/test_tools.py`
- `backend/tests/test_security.py`
- `backend/tests/test_db.py`
- `backend/tests/test_router.py`
- `scripts/test.sh`
