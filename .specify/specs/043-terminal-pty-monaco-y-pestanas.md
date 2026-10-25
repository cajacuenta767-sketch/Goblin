# Spec 043 — Terminal: Detener mata sus procesos · Monaco sin internet · Pestañas del editor

**Estado:** ✅ Hecho y validado (pruebas de terminal y E2E en Chromium) · ⬜ PC: terminal pty en Parrot
**Motivo:** pendientes del backlog B-12, B-08 y B-03.

## Requisitos funcionales

- **RF1 · Detener y pty (B-12).** Detener también termina los procesos que la IA lanzó en la terminal viva
  (`term_run`), agrupados por sesión (grupo de procesos). El shell del usuario no se cierra.
- **RF2 · Monaco sin internet (B-08).** El cargador y los archivos de Monaco se sirven desde `frontend/vendor/`
  en vez de cdnjs. Se incluyen solo los archivos necesarios (`min/vs`). Licencia MIT incluida.
- **RF3 · Pestañas del editor (B-03).** Varios archivos abiertos en pestañas; cerrar una pregunta si tiene
  cambios sin guardar (aviso en línea, no `confirm()`). Ctrl+S guarda la pestaña activa.

## Criterios de aceptación

- [x] `term_run "sleep 999 &"` seguido de Detener deja el proceso terminado.
- [x] La terminal del usuario sigue viva tras Detener.
- [x] Sin conexión a internet, el editor carga.
- [x] Abrir dos archivos muestra dos pestañas; cambiar entre ellas conserva el contenido no guardado.
- [x] Pruebas en `backend/tests/test_terminal_detener.py` (7) y E2E de editor con ratón y red bloqueada (14).

## Límites

- El tamaño de Monaco (min/vs) es de decenas de MB; se decide en la implementación si entra al repo o se
  descarga con un script.

## Decisiones de implementación

- **RF1 (etiqueta de sesión).** `term_session` envuelve cada comando de la IA: exporta
  `GOBLIN_TERM_TAG=<sesión>`, ejecuta el comando y lo desexporta. Los procesos que el comando deja en
  segundo plano heredan la variable al nacer, aunque se desdoblen. Detener (`cancel.request`) busca los
  procesos con esa etiqueta en su entorno y mata también sus descendientes. La shell del usuario y
  sus procesos no llevan la etiqueta, así que no se tocan. Las líneas de la envoltura se quitan de la
  salida que ve la IA.
- **RF2 (Monaco).** Monaco 0.52.0 pesa 14 MB en `min/vs`, así que **no entra al repo**. Lo descarga
  `scripts/fetch-monaco.sh` (tarball oficial de npm, solo `min/vs` y LICENSE) en `frontend/vendor/monaco/`,
  ignorado por git. `install.sh` lo ejecuta. Sin esa carpeta, el editor avisa y dice qué ejecutar.
  El cargador ya no va por CDN.
- **RF3 (pestañas).** Cada archivo abierto es un modelo de Monaco con su pestaña. El punto ● marca los
  cambios sin guardar. Cerrar una pestaña sin guardar: primer clic avisa en línea, segundo clic cierra
  (expira en 8 s). Nunca se usa `confirm()`. Ctrl+S guarda la pestaña activa.

## Límites

- `GOBLIN_TERM_TAG` depende de que el proceso herede el entorno. Un proceso que la IA lance con
  `setsid` y limpie su entorno quedaría fuera; el caso normal (`&`, `nohup`, `disown`) sí se cubre.
- La terminal solo se puede validar con pty real en la PC (Parrot).

