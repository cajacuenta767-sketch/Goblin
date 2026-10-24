"""
Terminal pty real para GOBLIN.
Arranca una shell bash persistente por cada sesión de terminal y la conecta con el
frontend (xterm.js) vía WebSocket. Mantiene directorio, variables y procesos en segundo
plano mientras la shell siga viva.
"""
import asyncio
import os
import signal
import struct

import config

try:
    import pty
    import fcntl
    import termios
    PTY_AVAILABLE = True
except ImportError:  # pragma: no cover (Windows)
    PTY_AVAILABLE = False


class PtyTerminal:
    """Una shell bash corriendo sobre un pseudo-terminal (pty)."""

    def __init__(self, cwd: str | None = None):
        self.pid: int | None = None
        self.fd: int | None = None
        self.cwd = cwd or str(config.WORKSPACE)

    def start(self) -> None:
        """Lanza bash en un pty. El hijo hereda un entorno de pentest razonable."""
        pid, fd = pty.fork()
        if pid == 0:
            # Proceso hijo: reemplaza la imagen por bash.
            try:
                os.chdir(self.cwd)
            except OSError:
                pass
            env = os.environ.copy()
            env["TERM"] = "xterm-256color"
            env["GOBLIN"] = "1"
            os.execvpe("/bin/bash", ["/bin/bash", "--login"], env)
        else:
            # Proceso padre: guarda el fd para leer/escribir.
            self.pid = pid
            self.fd = fd

    def write(self, data: str) -> None:
        if self.fd is not None:
            os.write(self.fd, data.encode("utf-8", errors="ignore"))

    def resize(self, rows: int, cols: int) -> None:
        """Ajusta el tamaño del pty (para que vim/nmap se vean bien)."""
        if self.fd is not None:
            size = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, size)

    def read(self, max_bytes: int = 65536) -> bytes:
        if self.fd is None:
            return b""
        return os.read(self.fd, max_bytes)

    def close(self) -> None:
        """Mata la shell y cierra el fd (sin dejar procesos huérfanos)."""
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


async def run_terminal(websocket, cwd: str | None = None) -> None:
    """
    Puente entre el WebSocket (xterm.js) y la shell pty.
    Mensajes del cliente:
      - texto normal   → se escribe en la shell
      - {"resize":[rows,cols]} → redimensiona el pty
    La salida de la shell se envía como texto al cliente.
    """
    if not PTY_AVAILABLE:
        await websocket.send_text("La terminal pty no está disponible en este sistema.\r\n")
        return

    term = PtyTerminal(cwd)
    term.start()
    loop = asyncio.get_event_loop()
    stop = asyncio.Event()

    async def pump_output():
        """Lee de la shell y lo manda al cliente."""
        while not stop.is_set():
            try:
                data = await loop.run_in_executor(None, term.read)
            except OSError:
                break
            if not data:
                break
            try:
                await websocket.send_text(data.decode("utf-8", errors="replace"))
            except Exception:
                break
        stop.set()

    out_task = asyncio.create_task(pump_output())

    try:
        while not stop.is_set():
            msg = await websocket.receive_text()
            # ¿Es un comando de control (resize)?
            if msg.startswith('{"resize"'):
                import json
                try:
                    rows, cols = json.loads(msg)["resize"]
                    term.resize(int(rows), int(cols))
                    continue
                except Exception:
                    pass
            term.write(msg)
    except Exception:
        pass
    finally:
        stop.set()
        term.close()
        out_task.cancel()
