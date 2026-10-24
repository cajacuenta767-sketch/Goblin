"""
Estado de GOBLIN que se publica HACIA AFUERA, a la Polybar (Fase 9).
GOBLIN escribe el target en ~/.cache/goblin/target; el módulo de Polybar lo lee.
"""
import config


def set_target(target: str) -> str:
    """Fija el target actual. Vacío = 'No target' en la Polybar."""
    target = (target or "").strip()
    try:
        config.TARGET_FILE.write_text(target, encoding="utf-8")
    except OSError:
        pass
    return target


def get_target() -> str:
    try:
        return config.TARGET_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def clear_target() -> None:
    set_target("")
