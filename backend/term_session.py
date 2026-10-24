"""
Terminal pty compartida y persistente por sesión (Spec 019).
Tanto el usuario (vía WebSocket) como la IA (vía herramientas) usan la misma shell,
que mantiene estado (cd, variables, procesos en segundo plano).
"""
import os
import select
import signal
import time

import config

try:
    import pty
    PTY_AVAILABLE = True
except ImportError:
    PTY_AVAILABLE = False

# Lista negra de comandos (reusa la de config).
BLOCKED = config.BLOCKED_PATTERNS

# Una terminal por sesión.
_terms: dict[str, "SharedTerminal"] = {}


class SharedTerminal:
    def __init__(self, cwd: str | None = None):
        self.pid = None
        self.fd = None
        self.buffer = ""        # salida acumulada (para que la IA la lea)
        self.cwd = cwd or str(config.WORKSPACE)

    def start(self):
        if not PTY_AVAILABLE:
            return
        pid, fd = pty.fork()
        if pid == 0:
            try:
                os.chdir(self.cwd)
            except OSError:
                pass
            env = os.environ.copy()
            env["TERM"] = "xterm-256color"
            env["GOBLIN"] = "1"
            os.execvpe("/bin/bash", ["/bin/bash", "--login"], env)
        else:
            self.pid = pid
            self.fd = fd
            time.sleep(0.3)
            self._drain()  # consumir el prompt inicial

    def _drain(self, timeout: float = 0.3) -> str:
        """Lee todo lo disponible del pty sin bloquear."""
        out = ""
        if self.fd is None:
            return out
        end = time.time() + timeout
        while time.time() < end:
            r, _, _ = select.select([self.fd], [], [], 0.1)
            if not r:
                continue
            try:
                data = os.read(self.fd, 65536)
            except OSError:
                break
            if not data:
                break
            chunk = data.decode("utf-8", errors="replace")
            out += chunk
            self.buffer += chunk
            end = time.time() + timeout  # extiende mientras llegue salida
        # recortar el buffer para no crecer sin fin
        if len(self.buffer) > 40000:
            self.buffer = self.buffer[-40000:]
        return out

    def run(self, command: str, wait: float = 2.0) -> str:
        """Envía un comando y devuelve la salida producida."""
        if self.fd is None:
            return "La terminal no está iniciada."
        cmd = command.strip()
        if any(b in cmd for b in BLOCKED):
            return f"BLOQUEADO: el comando contiene un patrón peligroso.\nComando: {command}"
        os.write(self.fd, (command + "\n").encode("utf-8", errors="ignore"))
        return self._drain(timeout=wait).strip() or "(sin salida inmediata; usa term_read para ver más)"

    def read_recent(self, chars: int = 4000) -> str:
        self._drain(timeout=0.3)
        return self.buffer[-chars:] if self.buffer else "(terminal vacía)"

    def write_raw(self, data: str):
        """Escritura directa desde el WebSocket del usuario."""
        if self.fd is not None:
            os.write(self.fd, data.encode("utf-8", errors="ignore"))

    def close(self):
        if self.pid is not None:
            try:
                os.kill(self.pid, signal.SIGKILL)
                os.waitpid(self.pid, 0)
            except (ProcessLookupError, ChildProcessError):
                pass
            self.pid = None
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None


def get_terminal(sid: str = "main") -> SharedTerminal:
    """Devuelve (o crea) la terminal compartida de una sesión."""
    t = _terms.get(sid)
    if t is None or t.fd is None:
        t = SharedTerminal()
        t.start()
        _terms[sid] = t
    return t


# La IA fija la sesión activa antes de usar las herramientas de terminal.
_active = {"sid": "main"}


def set_session(sid: str):
    _active["sid"] = sid
