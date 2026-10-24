# Spec 015 — Robustez y diagnóstico

**Estado:** 🟨 En progreso

## Qué
Que GOBLIN detecte y explique con claridad los problemas comunes de primer uso:
Ollama no corre, el modelo no está descargado, el backend no responde.

## Por qué
Un buen programa no falla en silencio. El usuario debe saber qué pasa y cómo arreglarlo.

## Requisitos funcionales
- RF1: Endpoint /api/diagnostics que comprueba: Ollama vivo, modelo por defecto descargado,
  espacio en disco, RAM disponible.
- RF2: El frontend muestra un aviso claro si algo falta (ej. "Descarga el modelo con...").
- RF3: Si el modelo por defecto no está, el aviso da el comando exacto para descargarlo.

## Criterios de validación
- [ ] /api/diagnostics reporta el estado de cada componente.
- [ ] Con Ollama caído, el aviso lo explica.

## Archivos
- `backend/main.py` — endpoint /api/diagnostics
- `frontend/js/main.js` — mostrar avisos
