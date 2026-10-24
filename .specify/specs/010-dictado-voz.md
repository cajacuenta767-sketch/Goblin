# Spec 010 — Dictado por voz

**Estado:** 🟨 En progreso · **Fase:** 5 · **Depende de:** 002

## Qué
El usuario pulsa el micrófono, habla, y su voz se transcribe a texto en el input del chat.
Luego envía como cualquier mensaje.

## Por qué
El usuario lo pidió explícitamente: dictar un prompt a la IA en vez de teclearlo.

## Decisión técnica
Usar la Web Speech API del navegador (reconocimiento de voz integrado), NO Whisper local.
Motivo: Whisper consume RAM que en 16 GB no sobra (compite con el modelo). La Web Speech API
es gratis, no instala nada y no gasta RAM del modelo. En Parrot (basado en Chromium/WebKit)
funciona. Si en el futuro se quiere 100% offline, se puede añadir Whisper como opción.

## Requisitos funcionales
- RF1: Clic en el micrófono inicia la escucha; la voz aparece como texto en el input.
- RF2: El micrófono indica visualmente que está escuchando (color/animación).
- RF3: Reconocimiento en español por defecto.
- RF4: Si el navegador no soporta la API, avisar en vez de fallar en silencio.

## Criterios de validación
- [ ] Pulsar el micrófono y hablar llena el input con el texto.
- [ ] El micrófono muestra que está activo.
- [ ] Sin soporte, avisa claramente.

## Archivos
- `frontend/js/voice.js` — Web Speech API
- `frontend/index.html` — cargar voice.js, id en el botón de micrófono
