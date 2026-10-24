# Spec 014 — CI, snippets de pentest y metadatos del repo

**Estado:** 🟨 En progreso

## Qué
Integración continua (los tests corren solos en GitHub), biblioteca de snippets de pentest,
y metadatos del repositorio (LICENSE, CONTRIBUTING).

## Requisitos funcionales
- RF1: GitHub Actions que corre pytest en cada push.
- RF2: Biblioteca de snippets de pentest (reverse shells, transferencia, enumeración).
- RF3: Herramienta `get_snippet(category)` para que la IA sugiera one-liners.
- RF4: LICENSE (MIT) y CONTRIBUTING.md (explica el flujo SDD).

## Criterios de validación
- [ ] El workflow de CI es válido (YAML correcto).
- [ ] get_snippet devuelve snippets por categoría.

## Archivos
- `.github/workflows/tests.yml`
- `backend/snippets.py` + `backend/tools/` (herramienta get_snippet)
- `LICENSE`, `CONTRIBUTING.md`
