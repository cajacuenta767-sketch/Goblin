# Spec 023 — Botones funcionales en toda la interfaz

## Problema (reportado por el usuario)

Al abrir la app nativa, varios botones no hacían nada: la interfaz parecía una
maqueta de HTML. Ejemplo reportado: pulsar un botón y que no ocurra nada.

## Causa raíz

1. **Módulos `const` consultados como `window.X`.** Cada módulo del frontend se
   declara con `const X = {...}`, que no crea `window.X`. Las comprobaciones
   `if (window.Sessions)`, `if (window.Findings)`, `if (window.ToolStore)`,
   `if (window.Voice)` y `window.Module` eran siempre falsas. Esos módulos nunca
   se inicializaban y sus botones no tenían manejadores.
2. **Controles de la maqueta sin acción.** Menús `File / View / Window`,
   botones de ventana, `☰`, `←`, `→`, `⌕`, "Historial", "Personalización",
   "Automations", `⋮` del chat, `+ Adjuntar`, pestaña `● bash`, ajustes del
   pie de página: existían en el HTML pero no estaban conectados.
3. **Explorador roto.** `Explorer.load()` usaba `this.el.view`, que apuntaba a
   `#wsView`, un elemento que no existe en el HTML. El error (`Cannot read
   properties of null`) lo capturaba el `try/catch` y se mostraba como
   "No se pudo listar", así que el explorador nunca mostraba archivos.
4. **Dependencia de CDN.** `marked`, `highlight.js` y `xterm` se cargaban desde
   internet; sin red, el chat y la terminal no se iniciaban.
5. **Controles de ventana sin permisos de Tauri.** Minimizar, maximizar y cerrar
   necesitan `withGlobalTauri` y capabilities; sin eso no podían ejecutarse.

## Solución

1. **Comprobaciones con `typeof`.** Se sustituyen `window.X` por
   `typeof X !== "undefined" && X` (18 casos en `chat.js`, `explorer.js`,
   `sessions.js`, `main.js` y los nuevos).
2. **Arranque tolerante a fallos.** `App.init()` ejecuta cada módulo dentro de
   `safe(nombre, fn)`: si uno falla, se registra en consola y los demás siguen.
3. **`frontend/js/chrome.js` (nuevo).** Conecta cada control de la barra de
   título, la barra lateral, los menús, el ⋮ del chat, el adjuntar archivo, la
   pestaña de la terminal y los ajustes (nivel de aprobación y modo).
   - Los controles de ventana usan `window.__TAURI__` en la app nativa. En el
     navegador muestran un aviso en vez de fallar en silencio.
   - "Personalización" y "Ajustes" abren el modal de ajustes.
   - "Automations" se quita de la barra lateral: no hay backend de tareas
     programadas. Se propondrá como spec aparte si el usuario la quiere.
4. **Librerías vendorizadas.** `frontend/vendor/` contiene `marked`,
   `highlight.js` (+ tema), `xterm` y `xterm-addon-fit`. Ya no dependen de red.
5. **Tauri.** `withGlobalTauri: true` en `tauri.conf.json`, ventana `label: "main"`
   y `src-tauri/capabilities/default.json` con permisos `core:window` de
   cerrar, minimizar, maximizar y alternar maximizado.
6. **Barra lateral colapsable como riel.** Al colapsarla queda un riel de 44 px
   con el `☰` visible, para poder volver a abrirla. Antes `display:none` ocultaba
   también el `☰` y la barra no se podía reabrir.
7. **Pestaña `● bash`.** Solo existe con la terminal abierta; su clic enfoca la
   terminal y no la cierra (para cerrarla está `⌃`).
8. **Historial.** Recarga la lista de conversaciones y la resalta brevemente.
9. **Explorador.** Guarda `if (this.el.view)` antes de usar `#wsView`.

## Validación

- [x] Prueba automática en Chromium (Playwright) contra el backend en
      `127.0.0.1:8800`, cada control en carga limpia, sin errores de página:
      Nueva conversación, ☰ (colapsa, riel visible, vuelve a abrir), ⌕, Historial,
      File / View / Window, View → Ajustes (modal con nivel `cauto` y modo `local`),
      ⚙ del pie, ⋮ del chat, cerrar/minimizar/maximizar (aviso en navegador),
      `+` (abre selector de archivo), pestaña bash (con la terminal abierta),
      chip de modo (cicla Local → Híbrido), Herramientas, Hallazgos, Informe,
      micrófono (sin error), Enviar.
- [x] Explorador: lista el workspace, entra en carpetas, sube con `..`, refresca.
- [x] `tauri.conf.json` y `capabilities/default.json` son JSON válido.
- [ ] **Pendiente:** compilar la app nativa (`cargo tauri build`) y comprobar en
      el equipo que los controles de ventana cierran, minimizan y maximizan.
- [ ] **Pendiente:** el editor Monaco sigue cargándose desde CDN; necesita red.
      Si falla, el resto de la app funciona.

## Changelog sugerido (PLAN.md)

- 🔵 **v1.5** — Todos los botones de la interfaz conectados a acciones reales.
  Causa: módulos `const` consultados como `window.X` (nunca se inicializaban),
  explorador con elemento inexistente, librerías por CDN y controles de ventana
  sin permisos de Tauri. Librerías vendorizadas; riel de barra colapsada;
  "Automations" retirada hasta tener spec propia.
