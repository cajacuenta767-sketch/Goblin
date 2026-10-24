"""Tests del router híbrido."""
import router


def test_default_mode_is_local():
    assert router.get_mode("new-session") == "local"


def test_set_mode():
    assert router.set_mode("r", "hybrid") == "hybrid"
    assert router.set_mode("r", "manual") == "manual"
    assert router.set_mode("r", "invalido") == "local"  # cae a local


def test_gemini_unavailable_without_key():
    # Sin GEMINI_API_KEY, Gemini no está disponible (no revienta)
    import config
    config.GEMINI_API_KEY = ""
    assert router.gemini_available() is False


def test_refusal_detection():
    assert router.looks_like_refusal("I can't help with that")
    assert router.looks_like_refusal("Lo siento, no puedo ayudar con eso")
    assert not router.looks_like_refusal("Aquí está el script que pediste")
    assert not router.looks_like_refusal("")
