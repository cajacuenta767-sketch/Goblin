# Spec 002 — Frontend IDE (interfaz GOBLIN)

**Estado:** ⬜ Pendiente · **Fase:** 2 · **Depende de:** 001 (backend core)

## Qué (objetivo)

La interfaz de GOBLIN: tema negro estilo Antigravity, con sidebar, chat agéntico, editor de
código y explorador de archivos, conectada al backend para que el chat funcione de verdad.

## Por qué

Es la cara de la app. Convierte el backend (ya funcional) en algo usable visualmente.
Ya existe una maqueta estática aprobada (`goblin-mockup.html`); esta spec la hace funcional.

## Requisitos funcionales

- RF1: Layout de paneles: sidebar (izq), chat (centro), editor + workspace (der).
- RF2: Chat conectado al backend: enviar mensaje → recibir respuesta de la IA.
- RF3: Mostrar etiqueta del modelo que respondió (DeepHat / Gemini) en cada mensaje.
- RF4: Caja de aprobación visual: cuando la IA pide una acción peligrosa, mostrar tarjeta
  con botones aprobar (verde) / denegar (rojo); borde rojo si es destructiva.
- RF5: Explorador de archivos: listar el contenido real del workspace/sistema (API /files).
- RF6: Selector de modelo (lee /api/models).
- RF7: Renderizar Markdown y bloques de código en las respuestas.
- RF8: Barra de estado inferior: modelo activo, modo, RAM/CPU, (git, línea:col del editor).
- RF9: Indicador de "IA trabajando" (spinner) mientras procesa.

## Requisitos no funcionales

- RNF1: Vanilla JS, sin frameworks ni build. Librerías por CDN (Monaco, marked, highlight).
- RNF2: Tema negro con acento verde goblin (#3ddc84). Tokens de color en theme.css.
- RNF3: Responsive mínimo (que no se rompa a ancho de pantalla normal).
- RNF4: Cada panel en su propio módulo JS (chat.js, editor.js, explorer.js...).

## Criterios de validación

- [ ] Abrir http://127.0.0.1:8800 muestra la interfaz GOBLIN completa.
- [ ] Escribir un mensaje y recibir respuesta de la IA.
- [ ] Una acción peligrosa muestra la caja de aprobación y respeta la decisión.
- [ ] El explorador lista archivos reales.
- [ ] El look coincide con la maqueta aprobada.

## Fuera de alcance

- Terminal integrada (spec 003)
- Editor Monaco con guardado (se puede empezar en modo lectura)
- Streaming token a token (mejora posterior)

## Archivos a crear

`frontend/index.html`, `frontend/css/{theme,layout}.css`,
`frontend/js/{main,api,chat,explorer,approvals}.js`
