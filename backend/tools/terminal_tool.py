"""
Herramientas para que la IA use la terminal viva compartida (Spec 019).
A diferencia de run_shell (ejecuta y muere), estas mantienen estado: cd, variables y
procesos en segundo plano persisten entre llamadas, en la misma shell que ve el usuario.
"""
import term_session


def term_run(command: str) -> str:
    """Envía un comando a la terminal viva de la sesión y devuelve su salida."""
    sid = term_session._active["sid"]
    term = term_session.get_terminal(sid)
    return term.run(command)


def term_read() -> str:
    """Lee la salida reciente de la terminal viva (incluye lo que escribió el usuario)."""
    sid = term_session._active["sid"]
    term = term_session.get_terminal(sid)
    return term.read_recent()
