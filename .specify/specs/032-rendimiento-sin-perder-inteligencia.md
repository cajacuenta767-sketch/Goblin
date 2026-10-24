# Spec 032 — Rendimiento sin perder inteligencia

**Estado:** 🟨 Implementada, validación en PC pendiente · **Tipo:** rendimiento · **Depende de:** 008, 018, 022, 024, 025
**Numeración:** 028–031 ya están reservadas en el backlog (editor, PDF, sudo, pty).

## Problema

En CPU (i7-10700, sin GPU) la velocidad del modelo local es el cuello de botella. Revisando el código
se encontraron estas causas, por orden de peso:

1. **Doble generación en cada respuesta de texto.** `stream_message` hacía primero un sondeo
   sin stream (generación completa que se descartaba) y después otra generación en stream.
   Cada respuesta de texto costaba el doble de tiempo de cómputo.
2. **Salidas de herramientas enormes en el contexto.** `shell.py` deja hasta 20 000 caracteres y
   `filesystem.py` hasta 30 000. Cada token del contexto se vuelve a procesar en cada paso del agente.
3. **System prompt con comandos que no existen.** `/target`, `/recon`, `/scan` y `/report` no los
   procesa ningún código (backlog B-01). Son tokens fijos en cada turno sin utilidad.
4. **Híbrido con doble llamada.** Si Gemini se niega, DeepHat repite la consulta completa. Hay
   temas de pentest que siempre van a rechazarse en Gemini, así que la espera es segura de perder.
5. **Saludos generados por el modelo grande.** Un "hola" ocupa al 7B completo.

## Qué NO se toca (para no perder inteligencia)

- El modelo por defecto sigue siendo DeepHat-V1-7B Q4_K_M. No se baja a 3B ni a Q3.
- El contexto `num_ctx` sigue en 4096.
- Las tareas de pentest, herramientas y análisis siempre van a DeepHat 7B.
- Las guardas de privacidad (spec 025) y la lista negra no cambian.

## Requisitos funcionales

- **RF1.** Una respuesta de texto se genera UNA sola vez, en stream. Si el modelo pide una herramienta,
  el texto ya mostrado se descarta y se sigue por el flujo normal con aprobaciones.
- **RF2.** Detener (spec 024) corta la generación en stream en menos de 1 s, aunque el modelo aún no
  haya emitido el primer token.
- **RF3.** Cada resultado de herramienta que llega al modelo se recorta a `GOBLIN_TOOL_OUTPUT_CHARS`
  (por defecto 6000) conservando el inicio y el final. La salida completa sigue guardada en la auditoría.
- **RF4.** El system prompt no lista comandos que no existen.
- **RF5.** Un saludo corto y sin pregunta (hola, gracias, buenas…) se responde con
  `GOBLIN_FAST_MODEL` si está configurado. Si no lo está, se usa DeepHat como siempre.
- **RF6.** En modo híbrido, si el mensaje o el historial tratan de pentest (nmap, sqlmap, exploit,
  escaneo, CVE…), la respuesta va directa a DeepHat local, sin intentar Gemini ni reintentar.
- **RF7.** `options.num_thread` se toma de `GOBLIN_NUM_THREAD` (por defecto 8, los núcleos físicos).
- **RF8.** `run.sh` activa `OLLAMA_FLASH_ATTENTION=1`. Solo tiene efecto si GOBLIN arranca Ollama.

## Requisitos no funcionales

- **RNF1.** Ninguna función nueva cambia el texto que devuelve DeepHat, solo cuándo y cuánto se procesa.
- **RNF2.** Sin dependencias nuevas.

## Criterios de aceptación

- [x] Una respuesta de texto en modo local hace UNA sola llamada al modelo (test con cliente simulado).
- [x] Si el modelo pide herramienta en el stream, se envía `discard` y `fallback` y el mensaje del
      usuario no queda duplicado.
- [x] `_fit_tool_output` recorta con inicio y final y avisa de lo omitido; no toca salidas cortas.
- [x] El system prompt no contiene `/target`, `/recon`, `/scan` ni `/report`.
- [x] `is_greeting` acepta saludos cortos y rechaza preguntas.
- [x] `needs_local_intent` detecta temas de pentest y no detecta charla normal.
- [x] Detener sigue funcionando en el flujo de stream (test de cancelación).
- [ ] Medido en la PC con DeepHat real: tiempo al primer token y tokens/s antes y después (pendiente del usuario).

## Límites

- Sin Ollama en este entorno, las mejoras de velocidad no se midieron con el modelo real. Solo se
  verificó la lógica con pruebas. La ganancia real se mide en la PC.
- `GOBLIN_FAST_MODEL` requiere descargar el modelo pequeño (por ejemplo `qwen2.5-coder:1.5b`). Por
  defecto está apagado.
- `OLLAMA_FLASH_ATTENTION` solo aplica si GOBLIN arranca el servidor de Ollama. Si Ollama ya corre
  como servicio, hay que ponerlo en su entorno.
- El cache de KV en `q8_0` no se activa: su efecto en calidad no se pudo comprobar aquí.
