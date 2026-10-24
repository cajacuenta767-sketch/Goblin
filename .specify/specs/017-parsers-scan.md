# Spec 017 — Parsers de escaneos (nmap/nikto)

**Estado:** 🟨 En progreso · **Depende de:** 006 (hallazgos)

## Qué
Parsear la salida de nmap y nikto para extraer puertos, servicios y vulnerabilidades de
forma estructurada, para que la IA registre hallazgos sin interpretarlo todo a mano.

## Requisitos funcionales
- RF1: Herramienta `parse_nmap(output o archivo)` → lista de puertos/servicios/versiones.
- RF2: Herramienta `parse_nikto(output o archivo)` → lista de hallazgos web.
- RF3: El resultado es texto estructurado que la IA usa para decidir qué registrar.
- RF4: Funciona con salida de nmap normal (-oN) y texto pegado.

## Criterios de validación
- [ ] parse_nmap extrae puertos abiertos con servicio y versión.
- [ ] parse_nikto extrae los hallazgos con su descripción.

## Archivos
- `backend/parsers.py`
- `backend/tools/scan_tool.py` + registry
- `backend/tests/test_parsers.py`
