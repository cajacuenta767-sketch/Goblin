"""
Generador de informe de pentest en Markdown a partir de los hallazgos de una sesión.
"""
import time
from pathlib import Path

import config
import db

SEV_LABEL = {
    "critical": "Crítica", "high": "Alta", "medium": "Media",
    "low": "Baja", "info": "Informativa",
}
SEV_ORDER = ["critical", "high", "medium", "low", "info"]


def generate(sid: str) -> str:
    """Devuelve el informe en Markdown y lo guarda en workspace/reports/."""
    findings = db.list_findings(sid)
    sessions = {s["id"]: s for s in db.list_sessions()}
    sess = sessions.get(sid, {})
    target = sess.get("target") or "(sin target definido)"
    title = sess.get("title") or "Pentest"
    fecha = time.strftime("%Y-%m-%d %H:%M")

    # Conteo por severidad
    counts = {s: 0 for s in SEV_ORDER}
    for f in findings:
        counts[f.get("severity", "info")] = counts.get(f.get("severity", "info"), 0) + 1

    md = []
    md.append(f"# Informe de Pentest — {title}\n")
    md.append(f"**Objetivo:** {target}  ")
    md.append(f"**Fecha:** {fecha}  ")
    md.append(f"**Generado por:** GOBLIN\n")

    md.append("## Resumen ejecutivo\n")
    total = len(findings)
    md.append(f"Se identificaron **{total} hallazgos** durante la evaluación:\n")
    md.append("| Severidad | Cantidad |")
    md.append("|-----------|----------|")
    for s in SEV_ORDER:
        if counts[s]:
            md.append(f"| {SEV_LABEL[s]} | {counts[s]} |")
    md.append("")

    if findings:
        md.append("## Tabla de hallazgos\n")
        md.append("| # | Severidad | Hallazgo | Host | Puerto |")
        md.append("|---|-----------|----------|------|--------|")
        for i, f in enumerate(findings, 1):
            md.append(f"| {i} | {SEV_LABEL.get(f['severity'], f['severity'])} | "
                      f"{f['title']} | {f.get('host','')} | {f.get('port','')} |")
        md.append("")

        md.append("## Detalle de hallazgos\n")
        for i, f in enumerate(findings, 1):
            md.append(f"### {i}. {f['title']}  [{SEV_LABEL.get(f['severity'], f['severity'])}]\n")
            if f.get("host"):
                md.append(f"- **Host:** {f['host']}" + (f":{f['port']}" if f.get("port") else ""))
            if f.get("description"):
                md.append(f"\n**Descripción:**\n\n{f['description']}\n")
            if f.get("evidence"):
                md.append(f"**Evidencia:**\n\n```\n{f['evidence']}\n```\n")
            md.append("")
    else:
        md.append("_No se registraron hallazgos en esta sesión._\n")

    # Anexo: log de acciones (auditoría)
    audit = db.get_audit(sid)
    if audit:
        md.append("## Anexo — Registro de acciones\n")
        md.append("| Hora | Herramienta | Aprobada |")
        md.append("|------|-------------|----------|")
        for a in audit:
            hora = time.strftime("%H:%M:%S", time.localtime(a["created_at"]))
            md.append(f"| {hora} | {a['tool']} | {'sí' if a['approved'] else 'no'} |")
        md.append("")

    report = "\n".join(md)

    # Guardar en workspace/reports/
    out_dir = config.WORKSPACE / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"informe_{time.strftime('%Y%m%d_%H%M%S')}.md"
    (out_dir / fname).write_text(report, encoding="utf-8")

    return report
