# Spec 042 — Dictado con Whisper local

**Estado:** 🟨 Implementado · validado con transcriptor simulado y micrófono falso en Chromium · ⬜ PC: transcripción real con el modelo `base`
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

- [x] Sin `faster-whisper` instalado, el botón 🎤 está oculto y el estado lo dice (E2E).
- [x] Con audio de prueba (WAV de 2 s), el endpoint devuelve texto (prueba con transcriptor simulado).
- [x] Grabaciones de más de 60 s se rechazan (antes de transcribir, y el botón para tras 60 s).
- [x] Pruebas en `backend/tests/test_voz.py` con transcriptor simulado (13).
- [ ] ⬜ PC: transcripción real con el modelo `base` en el i7-10700.

## Límites

- Sin GPU, `small` tarda varios segundos por frase. Por defecto se usa `base`.
- El acceso al micrófono en WebKitGTK depende de la versión instalada; se valida en la PC.

## Decisiones de implementación

- **Solo Whisper local.** Se quita la Web Speech API como respaldo: en Chromium envía el audio a
  servicios de Google, y RF4 lo prohíbe. Sin Whisper listo no hay dictado y el botón 🎤 queda oculto.
- **Módulo `backend/voice_stt.py`.** `status()` (RF5) explica qué falta: la librería o el modelo.
  `transcribe_bytes()` valida tipo (webm, ogg, mp4, wav, mp3), tamaño (12 MB) y duración (60 s).
  La duración se comprueba con `info.duration` antes de leer los segmentos. El archivo temporal se
  crea con permisos 0600 y se borra siempre.
- **Endpoints.** `GET /api/voice/status` y `POST /api/transcribe` (cuerpo binario, sin multipart para
  no añadir dependencias). `transcribe` responde 403 si la petición no viene de este equipo, 413 si la
  cabecera anuncia más de 12 MB y 400 con el motivo si el audio no sirve.
- **Modelo.** `scripts/fetch-whisper.sh` descarga `base` en `data/models/` (ignorado por git) y
  necesita internet una vez. La librería no va en `requirements.txt` porque arrastra ctranslate2 y
  av; `install.sh` muestra el comando.
- **Interfaz.** El botón 🎤 nace oculto en el HTML y aparece solo si el estado está listo. Usa
  MediaRecorder y para solo a los 60 s. El texto se añade al campo y no se envía. La barra de estado
  muestra «Dictado: listo (base)» o «Dictado: no disponible», con el motivo en el tooltip.
- **Validación.** faster-whisper 1.2.1 instalado: la firma de `WhisperModel` y de `transcribe` coincide
  con el código. La descarga del modelo queda bloqueada desde el entorno de desarrollo, así que la
  transcripción real no se ha ejecutado aquí; se valida en la PC.

## Límites

- Con `base` y CPU, una frase tarda unos segundos. `GOBLIN_WHISPER_THREADS` fija los hilos (4 por defecto).
- MediaRecorder en WebKitGTK depende de la versión instalada: si no hay grabación, el botón no aparece.
  Se valida en la PC.
