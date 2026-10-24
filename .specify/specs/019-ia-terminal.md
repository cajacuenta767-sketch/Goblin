# Spec 019 — La IA escribe en la terminal y ve su salida

**Estado:** 🟨 En progreso · **Depende de:** 004 (terminal pty)

## Qué
Que la IA pueda enviar comandos a la terminal pty viva (la misma que ve el usuario) y leer
su salida. Así puede dejar listeners, mantener el directorio entre comandos y usar la shell
con estado, en vez de solo run_shell (que ejecuta y muere).

## Por qué
run_shell no mantiene estado. Para pentest real la IA necesita una shell viva: cd que
persista, procesos en segundo plano, herramientas interactivas.

## Diseño
Una terminal pty compartida y persistente por sesión, gestionada en el backend:
- El usuario interactúa vía WebSocket (ya existe).
- La IA interactúa vía herramientas: term_run (envía comando, espera, devuelve salida),
  term_read (lee la salida reciente sin enviar nada).
- La IA ve lo que el usuario escribió y viceversa (misma shell).

## Requisitos funcionales
- RF1: Terminal pty persistente por sesión, accesible por IA y usuario.
- RF2: Herramienta term_run(command): envía el comando, espera un momento, devuelve salida.
- RF3: Herramienta term_read(): devuelve la salida acumulada reciente.
- RF4: La terminal mantiene estado (cd, variables, procesos en segundo plano).
- RF5: term_run requiere aprobación (ejecuta comandos reales).

## Criterios de validación
- [ ] term_run ejecuta un comando y devuelve su salida.
- [ ] El estado persiste entre term_run (cd, variables).
- [ ] term_run bloquea comandos de la lista negra.

## Archivos
- `backend/term_session.py` — terminal pty compartida por sesión
- `backend/tools/terminal_tool.py` — term_run, term_read
- `backend/terminal.py` — usar la terminal compartida
- `backend/tests/test_term.py`
