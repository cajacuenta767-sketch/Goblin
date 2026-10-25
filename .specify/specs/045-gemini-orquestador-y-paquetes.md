# Spec 045 — Gemini como orquestador con relevo local e instalación de paquetes

**Estado:** 🟨 Implementado · pruebas ✅ (36, con clientes simulados; suite 248) · ⬜ PC: Gemini real con tu clave e instalación real con pip · **Tipo:** funcionalidad + correcciones · **Depende de:** 008, 025, 033, 035, 038, 044 · **Sustituye a:** 032 RF6

**Motivo:**
1. En la captura, DeepHat respondió con un plan de texto y no ejecutó nada. La causa es el plan visible
   (Spec 035): "instala todo y luego lees…" tiene dos verbos y "luego", así que se pide un plan sin herramientas.
   Además no existía ninguna herramienta para instalar paquetes.
2. Quieres a Gemini como cabeza: responde y ejecuta herramientas. Cuando se niega (censura, bloqueo o respuesta
   vacía), DeepHat sigue la misma petición sin que el flujo se detenga.
3. Al revisar el código aparecieron dos fallos que harían fallar el relevo:
   - Los mensajes de Gemini son objetos propios. Ollama no los acepta (`dict(message)`), así que el relevo a
     mitad de bucle rompería el historial.
   - `sensitive_reason` leía `str(m)`. En un objeto de Gemini eso no incluye el texto: una IP escrita por Gemini
     no se detectaba.
   - El historial de herramientas se mandaba a Gemini como texto plano, no como llamadas y respuestas de función.

## Decisiones

- **D1 · La privacidad prevalece (Constitución II).** Si el historial contiene IP, rango, IPv6, objetivo activo o
  término del engagement, DeepHat responde aunque el modo sea híbrido. Gemini nunca recibe esos datos.
- **D2 · Pentest sin datos sensibles: Gemini primero.** Cambia Spec 032 RF6, que mandaba esos temas directo a DeepHat.
  Es una petición explícita del usuario. Queda superado el principio "Un modelo primero" de AGENTS.md para este cambio.
- **D3 · Instalación solo con pip**, en el `python3` del PATH (el mismo que usan los scripts lanzados desde la
  terminal). No se usa `--break-system-packages` ni sudo. apt y npm global quedan fuera hasta decidir B-05.
- **D4 · Instalar siempre pide aprobación**, en todos los niveles (también en "confianza").
- **D5 · El plan visible (Spec 035) también pasa por el router**: Gemini primero, relevo local. La ejecución no cambia.

## Requisitos funcionales

- **RF1 · Gemini como cabeza en modo híbrido.** Cada paso del bucle (texto y herramientas) va primero a Gemini si
  no hay datos sensibles y hay clave API. Pentest incluido.
- **RF2 · Relevo sin bloqueo.** Si Gemini lanza error, bloquea (block_reason o finish_reason de seguridad),
  devuelve vacío o se niega (heurística de texto), el MISMO paso se repite con DeepHat y el mismo historial.
  La respuesta negada no entra en el historial. La nota indica el motivo.
- **RF3 · Historial compatible.** En Gemini, las llamadas van como `function_call` y los resultados como
  `function_response` con el nombre de la herramienta. Las llamadas que Gemini generó conservan su firma
  (`thought_signature`). Al pasar a DeepHat, los mensajes se convierten al formato de Ollama.
- **RF4 · Guarda de privacidad completa.** El escaneo lee el texto y los argumentos de las llamadas de cualquier
  mensaje, también de los objetos de Gemini.
- **RF5 · Instalación con aprobación.** Herramienta `install_package(manager, name)`. `manager` ∈ {pip}. `name` debe
  cumplir `^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$` (sin URLs, rutas ni versiones). Ejecuta
  `python3 -m pip install --no-input --disable-pip-version-check <name>` sin shell, con tope de 300 s.
  Pide aprobación siempre y queda en la auditoría.
- **RF6 · Pista al fallar.** Si la salida de `run_shell` o `term_run` contiene `No module named 'x'` o
  `command not found`, lo que ve el modelo incluye una pista: instalar con pip (el nombre del paquete puede no
  coincidir con el módulo, p. ej. yaml → PyYAML) o pedir al usuario el comando del sistema.
- **RF7 · Plan visible con el router.** El plan de Spec 035 usa el mismo router que el resto de respuestas.

## Criterios de aceptación

- [x] Híbrido sin datos sensibles: la respuesta sale de Gemini (cliente simulado).
- [x] Pentest sin datos sensibles: Gemini primero.
- [x] Con una IP en el historial: Gemini no se llama y la nota lo dice.
- [x] Gemini lanza error o se niega: DeepHat responde con el mismo historial.
- [x] Relevo a mitad de bucle: una herramienta de Gemini, luego una negativa, y el bucle termina con DeepHat.
- [x] Historial de Gemini con `function_call` y `function_response`, y firma conservada.
- [x] `finish_reason` de seguridad lanza error.
- [x] `install_package` rechaza gestores y nombres no válidos, y llama a pip sin shell (subprocess simulado).
- [x] `install_package` pide aprobación en nivel "confianza".
- [x] La pista de módulo faltante aparece en la salida de la herramienta.
- [x] Plan visible de un mensaje de varios pasos: lo genera Gemini (sin herramientas).
- [x] Pruebas en `backend/tests/test_orquestador.py` y `backend/tests/test_paquetes.py`.

## Límites

- No validado contra la API real de Gemini ni con clave desde este entorno. El nombre `gemini-3.8-flash` sigue sin
  confirmarse contra la API en vivo.
- La firma de pensamiento de Gemini 3 solo se conserva para llamadas generadas por Gemini. Si la API la exige en
  otro caso, el error cae a DeepHat y se registra.
- La instalación va al Python del PATH. Un entorno virtual del proyecto no se detecta.
- pip ejecuta código al instalar un paquete. La aprobación explícita mitiga el riesgo, no lo elimina.
- La detección de rechazo sigue siendo heurística por texto. Un rechazo que no use esas frases no activa el relevo.
- Sin commit ni push en esta entrega.
