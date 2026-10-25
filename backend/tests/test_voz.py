"""Spec 042: dictado con Whisper local. Usa un transcriptor simulado: no descarga modelos."""
import io
import math
import os
import struct
import wave

import pytest
from fastapi.testclient import TestClient

import main
import voice_stt

LOCAL = ("127.0.0.1", 50000)


@pytest.fixture(autouse=True)
def sin_transcriptor_al_terminar():
    yield
    voice_stt.set_transcriber(None)


def _wav(segundos: float = 2.0) -> bytes:
    """WAV mono de 16 kHz con un tono (lo que produce el navegador tras convertir)."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"".join(
            struct.pack("<h", int(3000 * math.sin(2 * math.pi * 440 * i / 16000)))
            for i in range(int(16000 * segundos))))
    return buf.getvalue()


def test_sin_libreria_el_estado_lo_dice(monkeypatch):
    monkeypatch.setattr(voice_stt, "_hay_libreria", lambda: False)
    st = voice_stt.status()
    assert st["available"] is False
    assert "pip install faster-whisper" in st["reason"]


def test_sin_modelo_el_estado_lo_dice(monkeypatch):
    monkeypatch.setattr(voice_stt, "_hay_libreria", lambda: True)
    monkeypatch.setattr(voice_stt, "_hay_modelo", lambda: False)
    st = voice_stt.status()
    assert st["available"] is False
    assert "fetch-whisper" in st["reason"]


def test_wav_de_dos_segundos_llega_al_transcriptor_y_devuelve_texto():
    visto = {}

    def fake(ruta):
        visto["ruta"] = ruta
        with wave.open(ruta) as w:
            visto["segundos"] = w.getnframes() / w.getframerate()
        return ("hola mundo", 2.0)

    voice_stt.set_transcriber(fake)
    assert voice_stt.transcribe_bytes(_wav(2.0), "audio/wav") == "hola mundo"
    assert abs(visto["segundos"] - 2.0) < 0.01
    assert not os.path.exists(visto["ruta"]), "el audio temporal se borra siempre"


def test_mas_de_60_segundos_se_rechaza():
    voice_stt.set_transcriber(lambda ruta: ("no debería verse", 61.0))
    with pytest.raises(voice_stt.VoiceError, match="60 s"):
        voice_stt.transcribe_bytes(_wav(1.0), "audio/wav")


def test_formato_no_admitido_se_rechaza():
    voice_stt.set_transcriber(lambda ruta: ("x", 1.0))
    with pytest.raises(voice_stt.VoiceError, match="Formato"):
        voice_stt.transcribe_bytes(b"abc", "text/plain")


def test_grabacion_vacia_se_rechaza():
    voice_stt.set_transcriber(lambda ruta: ("x", 1.0))
    with pytest.raises(voice_stt.VoiceError, match="vacía"):
        voice_stt.transcribe_bytes(b"", "audio/webm")


def test_endpoint_devuelve_texto_desde_este_equipo():
    voice_stt.set_transcriber(lambda ruta: ("prueba de voz", 2.0))
    c = TestClient(main.app, client=LOCAL)
    r = c.post("/api/transcribe", content=_wav(2.0), headers={"Content-Type": "audio/wav"})
    assert r.status_code == 200
    assert r.json() == {"ok": True, "text": "prueba de voz"}


def test_endpoint_rechaza_peticiones_de_otros_equipos():
    voice_stt.set_transcriber(lambda ruta: ("x", 1.0))
    c = TestClient(main.app, client=("192.168.1.20", 50000))
    r = c.post("/api/transcribe", content=_wav(1.0), headers={"Content-Type": "audio/wav"})
    assert r.status_code == 403


def test_endpoint_rechaza_archivos_grandes_por_cabecera():
    voice_stt.set_transcriber(lambda ruta: ("x", 1.0))
    c = TestClient(main.app, client=LOCAL)
    grande = b"0" * (voice_stt.MAX_BYTES + 1)
    r = c.post("/api/transcribe", content=grande, headers={"Content-Type": "audio/wav"})
    assert r.status_code == 413


def test_endpoint_formato_invalido_es_400():
    voice_stt.set_transcriber(lambda ruta: ("x", 1.0))
    c = TestClient(main.app, client=LOCAL)
    r = c.post("/api/transcribe", content=b"abc", headers={"Content-Type": "text/plain"})
    assert r.status_code == 400


def test_api_de_estado_con_transcriptor_listo():
    voice_stt.set_transcriber(lambda ruta: ("", 0.0))
    c = TestClient(main.app, client=LOCAL)
    assert c.get("/api/voice/status").json()["available"] is True


class _Seg:
    def __init__(self, texto):
        self.text = texto


class _Info:
    def __init__(self, duracion):
        self.duration = duracion


class _ModeloFalso:
    """Imita WhisperModel.transcribe: devuelve (segmentos perezosos, info)."""
    def __init__(self, duracion, textos):
        self.duracion = duracion
        self.textos = textos
        self.consumido = False
        self.kwargs = {}

    def transcribe(self, ruta, **kwargs):
        self.kwargs = kwargs

        def gen():
            self.consumido = True
            for t in self.textos:
                yield _Seg(t)
        return gen(), _Info(self.duracion)


def test_ruta_real_une_segmentos_en_espanol(monkeypatch):
    modelo = _ModeloFalso(2.0, [" hola", "mundo "])
    monkeypatch.setattr(voice_stt, "_cargar", lambda: modelo)
    assert voice_stt._transcribir_real("/tmp/no-existe.wav") == ("hola mundo", 2.0)
    assert modelo.kwargs.get("language") == "es"


def test_ruta_real_rechaza_sin_consumir_segmentos(monkeypatch):
    modelo = _ModeloFalso(75.0, ["no debe leerse"])
    monkeypatch.setattr(voice_stt, "_cargar", lambda: modelo)
    with pytest.raises(voice_stt.VoiceError, match="60 s"):
        voice_stt._transcribir_real("/tmp/no-existe.wav")
    assert modelo.consumido is False
