"""
Memoria del engagement (Spec 036, RF5): resumen del objetivo, alcance, hosts y hallazgos que
se añade al contexto del modelo en cada turno. Sale de SQLite, no del historial de chat, así que
no se pierde al recortar los últimos turnos (Spec 034).
"""
import db
import state

MAX_HOST_LINES = 30
MAX_FINDING_TITLES = 5


def summary(sid: str, target: str | None = None) -> str:
    """Texto del resumen, o cadena vacía si el engagement aún no tiene datos."""
    try:
        objetivo = target if target is not None else state.get_target()
        alcance = db.list_scope(sid, "scope")
        hosts = db.list_hosts(sid)
        hallazgos = db.list_findings(sid)
    except Exception:
        return ""
    if not (objetivo or alcance or hosts or hallazgos):
        return ""
    partes = ["RESUMEN DEL ENGAGEMENT (datos guardados; no los inventes ni los repitas sin necesidad)."]
    if objetivo:
        partes.append(f"Objetivo: {objetivo}")
    if alcance:
        partes.append("Alcance autorizado: " + ", ".join(alcance))
    if hosts:
        partes.append("Hosts y puertos abiertos (de escaneos anteriores):")
        for h in hosts[:MAX_HOST_LINES]:
            ver = f" · {h['version']}" if h.get("version") else ""
            partes.append(f"- {h['host']}: {h['port']}/{h['proto']} {h.get('service', '')}{ver}")
        if len(hosts) > MAX_HOST_LINES:
            partes.append(f"… y {len(hosts) - MAX_HOST_LINES} más")
    if hallazgos:
        conteo: dict[str, int] = {}
        for f in hallazgos:
            conteo[f["severity"]] = conteo.get(f["severity"], 0) + 1
        orden = ["critical", "high", "medium", "low", "info"]
        resumen = ", ".join(f"{conteo[s]} {s}" for s in orden if s in conteo)
        partes.append(f"Hallazgos registrados: {len(hallazgos)} ({resumen}).")
        titulos = [f["title"] for f in hallazgos[:MAX_FINDING_TITLES]]
        partes.append("Principales: " + "; ".join(titulos))
    return "\n".join(partes)
