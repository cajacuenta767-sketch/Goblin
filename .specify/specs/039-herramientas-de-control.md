# Spec 039 — Herramientas de control: editar líneas, permisos, HTTP y Git

**Estado:** ⬜ Pendiente · **Tipo:** herramientas del agente · **Depende de:** 001, 009, 036, 037
**Motivo:** el plan pedía `edit_lines`, `chmod`, `http_get` y `git_ops`. Sin ellas, la IA reescribe archivos
enteros para cambiar una línea y no puede publicar cambios.

## Requisitos funcionales

- **RF1 · `edit_lines(path, start_line, end_line, new_text)`.** Reemplaza las líneas `start_line..end_line`
  (1-based, inclusivas) por `new_text`. Aprobación en nivel "normal" y "confianza" como `write_file`. Devuelve
  el diff (Spec 037). Error claro si el rango no existe.
- **RF2 · `chmod(path, mode)`.** `mode` es octal de 3 o 4 dígitos (`755`). Siempre pide aprobación. No acepta
  `/` ni `~` como ruta raíz (el resto de la ruta se resuelve dentro del área de trabajo del sistema de archivos).
- **RF3 · `http_get(url)`.** Solo GET, timeout 15 s, máximo 20 000 caracteres de respuesta, sin seguir
  redirecciones (una redirección se devuelve como texto). Siempre pide aprobación. El host debe estar en el
  alcance (Spec 036); si no, se bloquea.
- **RF4 · `git_ops(action, path, message)`.** Acciones permitidas: `status`, `log`, `init`, `add`, `commit`,
  `push`. Se ejecuta con lista de argumentos (sin shell). Nunca `--force`, `reset --hard`, `clean`, `checkout --`.
  `status` y `log` no piden aprobación; el resto sí.
- **RF5 · Auditoría.** Todas pasan por el log de auditoría existente (Spec 005).

## Criterios de aceptación

- [ ] `edit_lines` cambia solo el rango indicado; el resto del archivo queda igual.
- [ ] `edit_lines` con un rango fuera del archivo devuelve error y no toca el archivo.
- [ ] `chmod` rechaza modos no octales (`u+x`, `999`).
- [ ] `http_get` a un host fuera del alcance se bloquea antes de la aprobación.
- [ ] `http_get` no sigue redirecciones.
- [ ] `git_ops` rechaza `--force`, `reset` y `clean`.
- [ ] Pruebas en `backend/tests/test_herramientas_control.py`.

## Límites

- `git push` usa las credenciales que ya tenga el sistema; GOBLIN no las gestiona.
- `chmod` sobre rutas fuera de WORKSPACE requiere `GOBLIN_FULL_ACCESS=true`, igual que el resto de herramientas.
