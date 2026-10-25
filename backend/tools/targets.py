"""
Herramientas de gestión de target/engagement (Spec 012).
Fijar el objetivo del pentest crea su estructura de carpetas y lo publica a la Polybar.
"""
import re

import config
import state

# Subcarpetas estándar de un engagement de pentest.
ENGAGEMENT_DIRS = ["recon", "loot", "reports", "notes", "exploits"]


def _safe_name(target: str) -> str:
    """Convierte una IP/dominio en un nombre de carpeta seguro."""
    return re.sub(r"[^a-zA-Z0-9._-]", "_", target.strip())[:64]


def set_target(target: str) -> str:
    """Fija el target, crea su estructura de carpetas y lo publica a la Polybar."""
    target = target.strip()
    if not target:
        return "El target no puede estar vacío."
    state.set_target(target)
    # El objetivo que el usuario aprobó entra al alcance de la sesión (Spec 036, RF1).
    try:
        import db
        import scope
        import pentest as pt
        entrada = scope.normalize_entry(target)
        if entrada:
            db.add_scope(pt.current_sid(), "scope", entrada)
    except Exception:
        pass   # si la base falla, el objetivo queda fijado igual
    # Crear estructura del engagement
    base = config.WORKSPACE / "engagements" / _safe_name(target)
    created = []
    for d in ENGAGEMENT_DIRS:
        p = base / d
        p.mkdir(parents=True, exist_ok=True)
        created.append(d)
    return (f"Target fijado: {target} (visible en la Polybar).\n"
            f"Estructura creada en engagements/{_safe_name(target)}/: {', '.join(created)}")


def clear_target() -> str:
    """Limpia el target. La Polybar vuelve a 'No target'."""
    state.clear_target()
    return "Target limpiado. La Polybar muestra 'No target'."


def get_target() -> str:
    t = state.get_target()
    return f"Target actual: {t}" if t else "No hay target fijado."
