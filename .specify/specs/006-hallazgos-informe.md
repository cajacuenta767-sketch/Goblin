# Spec 006 — Hallazgos e informe de pentest

**Estado:** 🟨 En progreso · **Fase:** 8 · **Depende de:** 005 (persistencia)

## Qué
La IA registra vulnerabilidades encontradas (hallazgos) durante el pentest, y GOBLIN genera
un informe en Markdown a partir de ellos.

## Por qué
El reporte es la parte más tediosa del trabajo de pentest. Automatizarlo ahorra horas.

## Requisitos funcionales
- RF1: Nueva herramienta del agente `add_finding` (severidad, título, host, puerto, desc, evidencia).
  La IA la usa cuando encuentra algo durante el trabajo.
- RF2: Herramienta `generate_report` que arma el informe en Markdown de los hallazgos de la sesión.
- RF3: El informe incluye: resumen por severidad, tabla de hallazgos, detalle de cada uno, y
  el log de acciones (auditoría) como anexo.
- RF4: Endpoints: listar hallazgos de una sesión, generar/descargar informe.
- RF5: El informe se guarda en workspace/reports/.

## Requisitos no funcionales
- RNF1: Severidades estándar: critical, high, medium, low, info.
- RNF2: El informe es un .md limpio, listo para entregar o convertir a PDF.

## Criterios de validación
- [ ] La IA puede registrar un hallazgo con add_finding.
- [ ] generate_report produce un Markdown con resumen + tabla + detalle.
- [ ] Los hallazgos persisten (ya validado en spec 005).

## Archivos
- `backend/report.py` — genera el informe Markdown
- `backend/tools/pentest.py` — herramientas add_finding y generate_report
- `backend/tools/registry.py` — registrar las nuevas herramientas
- `backend/main.py` — endpoints /api/findings, /api/report
