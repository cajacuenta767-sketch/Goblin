# Tareas de GOBLIN (SDD)

> Estado real al **2026-10-24**. Cada tarea apunta a su spec. Se marca ✅ solo si se probó.
> "⬜ PC" = requiere la PC del usuario (Parrot). Lo nuevo se añade aquí antes de programarse.

**Leyenda:** ⬜ pendiente · 🟨 implementado, validación pendiente · ✅ hecho y validado

---

## Núcleo (specs 001–007) — ✅ salvo validaciones en PC

- ✅ 001 Backend core (agente, herramientas, API, tests). ⬜ PC: chat real con DeepHat (T001.10).
- ✅ 002 Frontend IDE (chat, explorador, aprobaciones). ⬜ PC: chat real (T002.10).
- 🟨 003 App nativa Tauri. Config lista; ⬜ PC: compilar el paquete y validar la ventana (T003.10).
- ✅ 004 Terminal integrada (pty real, WebSocket).
- ✅ 005 Persistencia SQLite (sesiones, mensajes, auditoría).
- ✅ 006 Hallazgos e informe Markdown.
- 🟨 007 Editor Monaco. Funciona, pero carga Monaco desde CDN (necesita internet). **Falta el archivo de spec 007** (ver backlog B-07).

## Specs 008–019 — 🟨 código y tests listos; checklists de la spec sin marcar

Cada spec tiene su checklist sin marcar. No se marca hasta validarla en la PC.

- 🟨 008 Router híbrido (Gemini + DeepHat). ⬜ PC: probar Gemini con API key real (T008.8).
- 🟨 009 Autoaprobación por niveles (cauto / normal / confianza). Validado: `delete_path` siempre pide.
- 🟨 010 Dictado por voz (Web Speech API).
- 🟨 011 UI de sesiones, hallazgos e informe.
- 🟨 012 Targets y engagements.
- 🟨 013 Tests automáticos (suite actual: 46 pruebas, pasan).
- 🟨 014 CI, snippets y metadatos del repo. Snippets solo accesibles por la IA (ver B-02).
- 🟨 015 Robustez y diagnóstico (`/api/diagnostics`). Corregido 500 por modelo sin nombre (2026-10-24).
- 🟨 016 Marketplace de herramientas (instalar nmap, sqlmap, etc. desde la app).
- 🟨 017 Parsers de escaneos (nmap / nikto).
- 🟨 018 Streaming de respuestas. Validado: el streaming se corta con Detener (spec 024).
- 🟨 019 La IA escribe en la terminal y ve su salida.

## Spec 021 — Fix app nativa: backend ✅

- ✅ Arranque del backend desde la app nativa (`find_project_dir`, espera a 127.0.0.1:8800).
- ⬜ PC: confirmar que la app abre sin terminal.

## Spec 022 — Tool-calling para DeepHat + respaldo por texto — 🟨

- ✅ Parser `text_toolcall.py` y su integración con aprobaciones (tests).
- ⬜ PC: `hola` no imprime JSON; "crea la carpeta …" dispara la caja de aprobación; el log muestra `Tool call recuperada por texto`.

## Spec 023 — Botones funcionales — 🟨

- ✅ Probado en Chromium contra el backend: todos los controles visibles responden.
- ✅ Riel de barra colapsada (corregido: antes no se podía reabrir).
- ✅ Explorador lista, entra y sube carpetas (corregido error por `#wsView`).
- ⬜ PC: controles de ventana (cerrar, minimizar, maximizar) con la app compilada.

## Spec 024 — Botón Detener — ✅

- ✅ Botón ⏹ mientras responde; el aviso aparece en ~250 ms con un modelo que tarda 25 s.
- ✅ Streaming detenido entre trozos (873 ms; el texto queda congelado).
- ✅ `run_shell` interrumpido termina con `CANCELADO` en menos de 5 s (grupo de procesos).
- ✅ La cola de herramientas y la cola de aprobación se vacían.
- ⬜ Pendiente (spec 031): procesos de la terminal pty.

## Spec 025 — Guardas de privacidad y autorización — 🟨

- ✅ Híbrido: IP, rango de red u objetivo activo en el historial fuerzan DeepHat local, con nota en el chat.
- ✅ `set_target` pide aprobación en todos los niveles; la caja muestra la advertencia de autorización por escrito.
- ✅ Denegar `set_target` deja el objetivo intacto.
- ⬜ PC: híbrido sin datos sigue usando Gemini (requiere API key real).
- ⚠️ Límite: IPv6, nombres de cliente y hostnames arbitrarios no se detectan (ver B-10).

---

## Spec 026 — Marketplace: instalación por terminal y catálogo ampliado — 🟨

- ✅ "Instalar" muestra el comando exacto en una confirmación dentro de la tarjeta (sin `confirm()`).
- ✅ Confirmar escribe el comando en la terminal integrada; GOBLIN no recibe la contraseña de sudo.
- ✅ "Descargar" y "↗" abren la web oficial desde el backend (`xdg-open`); IDs y URLs fuera del catálogo se rechazan.
- ✅ Burp Suite (solo descarga) no muestra "Instalar"; los paquetes no comprobados llevan la etiqueta.
- ✅ "↻ Actualizar" y catálogo de 67 herramientas en 10 categorías.
- ✅ Pruebas: 61 de backend pasan (15 nuevas del marketplace); E2E en Chromium 21/21.
- ⬜ PC: instalar una herramienta desde la app nativa y comprobar que "Descargar" abre la web oficial.
- ⬜ Verificar en Parrot los paquetes marcados "pkg sin verificar" (ver Spec 026, Límites).

---

## Spec 027 — Instalar con contraseña en la app y registro en vivo — 🟨

- ✅ Diálogo propio para la contraseña de sudo: se usa una vez con `sudo -S` y no se guarda ni se registra.
- ✅ Contraseña incorrecta: el diálogo vuelve a pedirla con el aviso.
- ✅ Registro de apt en vivo, cancelar (menos de 10 s) y un solo trabajo a la vez.
- ✅ Desinstalar con `apt-get remove` y la misma confirmación.
- ✅ Pruebas: 8 del backend de trabajos (sudo y apt simulados) y E2E de navegador 18/18.
- ⬜ PC: instalar y desinstalar con el sudo real desde la app nativa.
- ⚠️ Límite: si se reinicia el backend se pierde el registro de trabajos; cancelar con SIGKILL puede dejar un bloqueo de apt.

---

## Spec 032 — Rendimiento sin perder inteligencia — 🟨

- ✅ Una sola generación por respuesta de texto (antes había un sondeo que se descartaba).
- ✅ Detener corta el stream en menos de 2 s aunque el modelo no haya dado el primer token (test).
- ✅ Salidas de herramientas recortadas a `GOBLIN_TOOL_OUTPUT_CHARS` (inicio + final).
- ✅ System prompt sin comandos que no existen (`/target`, `/recon`, `/scan`, `/report`).
- ✅ Saludos cortos con `GOBLIN_FAST_MODEL` (apagado por defecto) y sin herramientas.
- ✅ Temas de pentest en híbrido van directo a DeepHat (sin reintento tras rechazo de Gemini).
- ✅ `num_thread` desde `GOBLIN_NUM_THREAD`; `OLLAMA_FLASH_ATTENTION=1` en `run.sh`.
- ✅ Pruebas: 82 pasan (`backend/tests/test_rendimiento.py`, 12 nuevas).
- ⬜ PC: medir tiempo al primer token y tokens/s antes y después con DeepHat real.
- ⬜ PC: decidir si se descarga `qwen2.5-coder:1.5b` para `GOBLIN_FAST_MODEL`.

## Spec 033 — Intención y alcance por turno — 🟨

- ✅ `backend/intent.py` clasifica cada petición en acción, análisis o charla (código, sin modelo).
- ✅ "Analiza X" sin ruta no recibe herramientas; con ruta, solo lectura.
- ✅ Una herramienta fuera de la intención del turno no se ejecuta.
- ✅ Pruebas: 95 pasan (`test_intencion.py`, 8 nuevas).
- ⬜ PC: probar "analiza mi computadora" con DeepHat real y confirmar que no se ejecuta nada.

## Spec 034 — Respuestas de capacidad y contexto acotado — 🟨

- ✅ "¿puedes analizar algo?" recibe respuesta fija, sin modelo (verificado en navegador).
- ✅ El modelo recibe el system prompt y los últimos `GOBLIN_HISTORY_TURNS` turnos (10).
- ✅ Pruebas: `test_contexto.py` (7).
- ⬜ PC: probar "¿puedes analizar algo?" con DeepHat real.

## Spec 035 — Plan visible antes de ejecutar — 🟨

- ✅ Peticiones de varios pasos muestran un plan sin ejecutar nada (sin herramientas).
- ✅ "sí" ejecuta el plan; cualquier otro mensaje lo descarta.
- ✅ La etiqueta de la burbuja muestra el modelo que respondió (`chat.js`).
- ✅ Pruebas: `test_plan.py` (8); flujo completo verificado en navegador con modelo simulado.
- ⬜ PC: probar "crea la carpeta pruebas y luego escribe notas.txt" con DeepHat real.

## Infraestructura (transversal) — ✅

- ✅ `scripts/install.sh`, `run.sh`, `build.sh`, `install-nativo.sh`, `subir-github.sh`.
- ✅ GitHub: `cajacuenta767-sketch/Goblin` (ver aviso de redirección en el push: usar la URL con mayúscula).
- ✅ CI en GitHub Actions corre los tests de backend.

---

## Backlog priorizado (análisis del 2026-10-24)

Orden según riesgo y valor. Cada ítem se convertirá en spec antes de programarse (constitución VI.1).

### Prioridad 1 — Lo que el plan exige y falta

- ⬜ **B-01 · Comandos rápidos reales** (`/target`, `/recon`, `/scan`, `/report`). Hoy solo aparecen en el prompt del sistema; ningún código los procesa. Plan §10.4 #16. → spec 026.
- ⬜ **B-02 · Snippets en la UI**: clic en un snippet lo inserta en el chat/terminal. Hoy solo la IA puede leerlos (`get_snippet`). Fase 8. → spec 027.
- ⬜ **B-03 · Editor IDE**: pestañas de archivos abiertos, paneles redimensionables, tema claro (Fase 2, todo pendiente). → spec 028.
- ⬜ **B-04 · Informe en PDF** (plan §10.4 #17). Hay que justificar la dependencia (constitución IV.4). → spec 029.

### Prioridad 2 — Decisiones que son del usuario

- ❓ **B-05 · Privilegios (sudo)**: decidir cómo ejecuta la IA comandos con root (plan §10.2 #7). Opciones: pedir sudo por comando con aprobación; capabilities de nmap; o no permitir root. → spec 030 tras decidir.
- ❓ **B-06 · "Automations"**: se quitó de la barra lateral. ¿Se quiere como spec (tareas programadas) o se descarta?

### Prioridad 3 — Calidad y documentación

- ⬜ **B-07 · Spec 007 (Monaco)**: falta el archivo; crearlo como documentación de lo construido. Además, el número 020 no existe: confirmar si se omitió a propósito.
- ⬜ **B-08 · Monaco sin internet**: vendorizar el loader, igual que se hizo con marked/xterm.
- ⬜ **B-09 · Pruebas de interfaz en el repo**: el E2E de navegador (Playwright) vive fuera del repo. Decidir si entra al CI.
- ⬜ **B-10 · Ampliar la guarda de privacidad (025)**: IPv6 y lista de términos del engagement (nombres de cliente, dominios secundarios).
- ⬜ **B-11 · Marcar checklists de 008–019** cuando se validen en la PC.

### Prioridad 4 — Fase 8 y 5 (más adelante)

- ⬜ **B-12 · Gestión de procesos de la terminal pty** en Detener (extiende spec 024 → spec 031).
- ⬜ **B-13 · Fase 5 multimedia**: imágenes, video (fotogramas con ffmpeg), audio. Baja prioridad frente a pentest.
- ⬜ **B-14 · Visor estructurado de resultados** (tabla de puertos desde nmap). Los parsers ya existen; falta la UI.

---

## Validaciones que solo puede hacer el usuario (PC)

- ⬜ T001.10 · Chat con DeepHat real.
- ⬜ T003.10 · Compilar el paquete en Parrot y validar la ventana nativa (incluye controles de ventana de spec 023).
- ⬜ T008.8 · Gemini con API key real (incluye híbrido sin datos sensibles, spec 025).
- ⬜ Spec 022 · Tool-calling de DeepHat (ver sección 022).
- ⬜ Spec 024 · Detener con el modelo real en la PC (el E2E se probó con un Ollama de prueba).
