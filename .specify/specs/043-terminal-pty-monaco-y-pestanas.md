# Spec 043 — Terminal: Detener mata sus procesos · Monaco sin internet · Pestañas del editor

**Estado:** ⬜ Pendiente · **Tipo:** funcionalidad + interfaz · **Depende de:** 004, 019, 024, 007, 040
**Motivo:** pendientes del backlog B-12, B-08 y B-03.

## Requisitos funcionales

- **RF1 · Detener y pty (B-12).** Detener también termina los procesos que la IA lanzó en la terminal viva
  (`term_run`), agrupados por sesión (grupo de procesos). El shell del usuario no se cierra.
- **RF2 · Monaco sin internet (B-08).** El cargador y los archivos de Monaco se sirven desde `frontend/vendor/`
  en vez de cdnjs. Se incluyen solo los archivos necesarios (`min/vs`). Licencia MIT incluida.
- **RF3 · Pestañas del editor (B-03).** Varios archivos abiertos en pestañas; cerrar una pregunta si tiene
  cambios sin guardar (aviso en línea, no `confirm()`). Ctrl+S guarda la pestaña activa.

## Criterios de aceptación

- [ ] `term_run "sleep 999 &"` seguido de Detener deja el proceso terminado.
- [ ] La terminal del usuario sigue viva tras Detener.
- [ ] Sin conexión a internet, el editor carga.
- [ ] Abrir dos archivos muestra dos pestañas; cambiar entre ellas conserva el contenido no guardado.
- [ ] Pruebas en `backend/tests/test_terminal_detener.py` y E2E en `scratchpad`.

## Límites

- El tamaño de Monaco (min/vs) es de decenas de MB; se decide en la implementación si entra al repo o se
  descarga con un script.
