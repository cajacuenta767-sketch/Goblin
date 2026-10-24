# Spec 004 — Terminal integrada (pty real)

**Estado:** 🟨 En progreso · **Fase:** 3 · **Depende de:** 001 (backend), 002 (frontend)

## Qué (objetivo)

Una terminal real integrada en GOBLIN: una shell persistente (pty) que mantiene directorio,
variables de entorno y procesos en segundo plano (ej. un listener de netcat), conectada por
WebSocket entre el frontend (xterm.js) y el backend (ptyprocess).

## Por qué

El `run_shell` actual ejecuta un comando y muere: no sirve para pentesting real (no puedes
dejar un listener corriendo, hacer `cd` que persista, ni usar herramientas interactivas).
Una terminal pty viva es la pieza más valiosa que falta para el trabajo del usuario.

## Requisitos funcionales

- RF1: Shell real persistente en el backend (bash vía pty).
- RF2: El frontend muestra una terminal (xterm.js) conectada por WebSocket.
- RF3: Lo que el usuario escribe va a la shell; la salida vuelve en tiempo real.
- RF4: El estado persiste: `cd`, variables, procesos en segundo plano siguen vivos.
- RF5: Redimensionar la terminal ajusta el tamaño del pty (filas/columnas).
- RF6: La terminal arranca en el workspace (o en la carpeta del target si hay uno).
- RF7: Panel de terminal en la parte inferior de la interfaz, con pestaña.

## Requisitos no funcionales

- RNF1: La shell corre con los permisos del usuario (no root salvo que el user lo decida).
- RNF2: Si el WebSocket se cae, la shell del backend se cierra limpiamente (sin zombis).
- RNF3: xterm.js por CDN (sin build).
- RNF4: Solo accesible desde localhost (como todo GOBLIN).

## Criterios de validación

- [ ] Abrir la terminal muestra un prompt de bash real.
- [ ] `cd /tmp && pwd` muestra /tmp (el estado persiste entre comandos).
- [ ] `export X=1 && echo $X` muestra 1.
- [ ] Un proceso en segundo plano (ej. `sleep 30 &`) sigue vivo.
- [ ] Redimensionar la ventana ajusta la terminal.
- [ ] Cerrar la terminal no deja procesos bash huérfanos.

## Fuera de alcance

- Que la IA escriba en esta misma terminal (iteración futura; por ahora la IA usa run_shell).
- Múltiples pestañas de terminal (v1: una sola).
- Historial persistente entre sesiones.

## Archivos a crear/modificar

- `backend/terminal.py` — gestión del pty
- `backend/main.py` — endpoint WebSocket `/ws/terminal`
- `backend/requirements.txt` — añadir `ptyprocess`
- `frontend/index.html` — panel de terminal + xterm.js por CDN
- `frontend/js/terminal.js` — cliente xterm.js ↔ WebSocket
- `frontend/css/layout.css` — estilos del panel de terminal
