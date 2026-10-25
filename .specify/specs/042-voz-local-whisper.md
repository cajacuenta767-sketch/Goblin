# Spec 042 — Dictado con Whisper local

**Estado:** ⬜ Pendiente · **Tipo:** funcionalidad · **Depende de:** 010, 009
**Motivo:** el dictado usa Web Speech API, que no existe en la ventana nativa de Parrot (WebKitGTK). El plan
pedía Whisper local (§9.3 #22). Hoy el botón se oculta; no hay reemplazo.

## Justificación de la dependencia (Constitución IV.4)

- `faster-whisper` (CTranslate2, CPU, int8). Motivo: transcripción local sin GPU, sin enviar audio a la nube.
- Modelo `base` (~140 MB) o `small` (~460 MB) en `data/models/`. Se descarga una vez; nunca se sube al repo.
- Si la librería o el modelo no existen, el botón queda oculto y se muestra cómo instalarlos.

## Requisitos funcionales

- **RF1 · Captura.** Con el botón 🎤 se graba audio del micrófono (`MediaRecorder`). Pulsar de nuevo lo detiene.
- **RF2 · Transcripción.** El audio se envía a `POST /api/transcribe` (solo `127.0.0.1`) y se transcribe en
  CPU con `faster-whisper`, idioma `es`. Máximo 60 s por grabación.
- **RF3 · Texto al campo.** El texto aparece en el campo de entrada; no se envía solo.
- **RF4 · Sin nube.** El audio nunca sale de la máquina.
- **RF5 · Disponibilidad.** `GET /api/voice/status` indica si la librería y el modelo están listos.

## Criterios de aceptación

- [ ] Sin `faster-whisper` instalado, el botón 🎤 está oculto y el estado lo dice.
- [ ] Con audio de prueba (WAV de 2 s), el endpoint devuelve texto (prueba con modelo fake).
- [ ] Grabaciones de más de 60 s se rechazan.
- [ ] Pruebas en `backend/tests/test_voz.py` con transcriptor simulado.
- [ ] ⬜ PC: transcripción real con el modelo `base` en el i7-10700.

## Límites

- Sin GPU, `small` tarda varios segundos por frase. Por defecto se usa `base`.
- El acceso al micrófono en WebKitGTK depende de la versión instalada; se valida en la PC.
