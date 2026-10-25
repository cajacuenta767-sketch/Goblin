# Spec 041 — Interfaz de apoyo: barra de estado, snippets, hosts, alcance y privacidad

**Estado:** ✅ Hecho y validado en Chromium con ratón · ⬜ PC: ventana Tauri · **Tipo:** interfaz · **Depende de:** 023, 036, 037, 038
**Motivo:** piezas del plan (§9.7 y B-02/B-14) que faltan y que el backend ya soporta o soportará.

## Requisitos funcionales

- **RF1 · Barra de estado.** Muestra: estado de Ollama, modelo, modo (Local/Híbrido/Manual con color: verde
  local, amarillo híbrido), RAM, CPU, contexto estimado (`~1.2k / 4k`) y el objetivo activo.
- **RF2 · Panel de alcance.** Lista de entradas de alcance y términos sensibles, con añadir y quitar. Quitar
  pide confirmación en línea (no `confirm()`).
- **RF3 · Panel de hosts.** Tabla de hosts y puertos abiertos de la sesión (Spec 036), con filtro por host.
- **RF4 · Snippets.** Lista de snippets por categoría; clic inserta el texto en el campo de entrada (no lo
  ejecuta). Reutiliza `backend/snippets.py`.
- **RF5 · Indicador de vista.** Los hallazgos y los hosts se ven en el mismo panel con pestañas.
- **RF6 · Sin datos nuevos al cloud.** Ninguna de estas vistas hace peticiones a servicios externos.

## Criterios de aceptación

- [ ] La barra muestra "Local" en verde y "Híbrido" en amarillo.
- [ ] Añadir un dominio al alcance aparece en el panel y en `GET /api/scope/{sid}`.
- [ ] Clic en un snippet deja su texto en el campo de entrada sin enviarlo.
- [ ] La tabla de hosts muestra los puertos guardados por nmap.
- [ ] Pruebas E2E en `scratchpad` con Playwright.

## Límites

- El contador de contexto es una estimación (Spec 037).
- Los snippets no se ejecutan desde la interfaz; ejecutar requiere que el usuario los pegue en la terminal.
