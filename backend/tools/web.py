"""
Petición HTTP GET de solo lectura (Spec 039, RF3). Sin seguir redirecciones: una redirección
se devuelve como texto, para que el alcance (Spec 036) no se salte en silencio.
"""
import re
import urllib.error
import urllib.request

MAX_CHARS = 20000
TIMEOUT_S = 15


class _SinRedirecciones(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None   # urllib lanza HTTPError con el código 3xx y su cabecera Location


def http_get(url: str) -> str:
    u = (url or "").strip()
    if not re.match(r"^https?://", u, re.IGNORECASE):
        raise ValueError("solo se admiten URLs http:// o https://")
    opener = urllib.request.build_opener(_SinRedirecciones)
    req = urllib.request.Request(u, headers={"User-Agent": "GOBLIN/1.0"})
    try:
        with opener.open(req, timeout=TIMEOUT_S) as r:
            estado = r.status
            cuerpo = r.read(MAX_CHARS + 1).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        estado = e.code
        cuerpo = e.read(MAX_CHARS + 1).decode("utf-8", errors="replace")
        loc = e.headers.get("Location") if e.headers else None
        if loc:
            cuerpo = f"(redirección a {loc}; no se sigue)\n" + cuerpo
    except (urllib.error.URLError, OSError) as e:
        return f"Error de red: {e}"
    recorte = "\n[... respuesta truncada ...]" if len(cuerpo) > MAX_CHARS else ""
    return f"[HTTP {estado}]\n{cuerpo[:MAX_CHARS]}{recorte}"
