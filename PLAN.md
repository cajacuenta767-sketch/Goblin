# PLAN — GOBLIN 🟢 (IA IDE Local estilo Antigravity)

> 🔵 **Nombre de la app: GOBLIN.** App de escritorio local para Parrot OS. Backend en
> **Python (FastAPI)**, arquitectura híbrida (Gemini + DeepHat local sin censura) vía
> **Ollama**, interfaz tipo IDE con chat agéntico, explorador de archivos, editor de
> código y terminal. La IA tiene control del sistema (crear, mover, borrar archivos y
> carpetas, ejecutar comandos) con aprobaciones para acciones peligrosas.
> 🔵 **Tema visual: negro estilo Antigravity** (fondo casi negro, acentos sutiles) → ver §9

- **SO objetivo:** Parrot OS (Linux Debian)
- **Backend:** Python 3.11+ · FastAPI · Ollama
- **Frontend:** HTML/CSS/JS (luego migrable a React + Vite)
- 🔵 **Arquitectura de modelos: HÍBRIDA.** Gemini (nube) orquesta y responde rápido; **DeepHat-V1-7B** (local) entra cuando Gemini se niega por censura o cuando hay datos sensibles del objetivo.
- **Estado del documento:** v1.1 — vivo, se va actualizando por fases
- 🔵 **Perfil del usuario:** ingeniero de ciberseguridad → proyecto enfocado 100% en pentesting
- 🔵 **Hardware objetivo real:** i7-10700 (8C/16H) · 16 GB RAM · **sin GPU dedicada** (solo CPU) → ver §8

---

## 0. Leyenda de estado

- ⬜ Pendiente
- 🟨 En progreso
- ✅ Hecho
- 🔵 = texto/cambios que agregamos en revisiones (equivale a "ver en azul")

---

## 1. Arquitectura general

```
┌──────────────────────────────────────────────┐
│ Frontend (navegador, localhost)              │
│  Sidebar izq: chats, proyectos, explorador   │
│  Centro: editor de código (Monaco)           │
│  Panel chat: conversación agéntica           │
│  Panel inferior: terminal (xterm.js)         │
│  Topbar: selector de modelo, botones, modo   │
└───────────────┬──────────────────────────────┘
                │ HTTP + WebSocket (127.0.0.1)
┌───────────────▼──────────────────────────────┐
│ Backend FastAPI                              │
│  - Orquestador del agente (bucle tools)      │
│  - 🔵 ROUTER híbrido (Gemini ↔ DeepHat)       │
│  - Registro de herramientas                  │
│  - Sistema de aprobaciones                   │
│  - Gestión de sesiones y proyectos           │
│  - WebSocket para streaming y terminal       │
└──────┬──────────────────────────┬─────────────┘
       │ 🔵 nube (rápido)          │ local (sin censura)
┌──────▼───────────────┐   ┌──────▼──────────────────┐
│ 🔵 Gemini API        │   │ Ollama (127.0.0.1:11434)│
│ (orquesta, razona,   │   │ DeepHat-V1-7B           │
│  escribe, planea)    │   │ (payloads, exploits)    │
└──────────────────────┘   └─────────────────────────┘
```

---

## 2. Fases de desarrollo

### Fase 1 — MVP funcional ✅ (base ya creada)
- ✅ Chat con el modelo vía Ollama
- ✅ Herramientas: listar, leer, escribir, crear carpeta, mover, borrar, shell
- ✅ Sistema de aprobaciones para acciones destructivas
- ✅ Explorador de archivos básico
- ✅ Instalador `install.sh` y `run.sh`
- ✅ Adjuntar archivos de texto

### Fase 2 — Interfaz tipo IDE 🟨
- ⬜ Layout de 4 paneles redimensionables (sidebar / editor / chat / terminal)
- ⬜ Editor de código **Monaco** (el de VS Code) con resaltado de sintaxis
- ⬜ Pestañas de archivos abiertos
- ⬜ Guardar archivo con Ctrl+S
- ⬜ Árbol de archivos expandible (no solo una carpeta a la vez)
- ⬜ Tema claro / oscuro

### 🔵 Fase 2.5 — Router híbrido (Gemini + DeepHat) ⬜
- ⬜ Integrar la API de Gemini (requiere API key, se guarda en `.env`, NO en el repo)
- ⬜ Lógica de router en el backend que decide qué modelo usa cada mensaje
- ⬜ Detección automática de negativa de Gemini (safety block) → reintento con DeepHat
- ⬜ Selector de **3 modos** en la interfaz:
  - 🟢 **Híbrido:** Gemini primero, DeepHat si se niega (máxima velocidad, para labs)
  - 🟡 **Local puro:** solo DeepHat (privacidad total, para engagements reales con cliente/NDA)
  - 🔵 **Manual:** el usuario elige modelo por mensaje
- ⬜ Indicador visible de qué modelo respondió cada mensaje (etiqueta "Gemini" / "DeepHat")
- ⬜ 🔵 Regla de seguridad: en modo híbrido, detectar datos sensibles (IPs, dominios del
  objetivo, nombres) y forzar DeepHat local aunque Gemini pudiera responder
- ⬜ Aviso claro al usuario cuando un mensaje va a salir a la nube (Gemini)

### Fase 3 — Terminal integrada ⬜
- ⬜ Terminal real con **xterm.js** conectada por WebSocket a una shell (pty)
- ⬜ La IA puede escribir en esa misma terminal
- ⬜ Historial de comandos

### Fase 4 — Chat agéntico avanzado ⬜
- ⬜ Streaming de respuestas token a token
- ⬜ Mostrar en vivo qué herramienta está usando la IA ("ejecutando nmap...")
- ⬜ Botón de "aprobar todo" por sesión (modo confianza)
- ⬜ Renderizado de Markdown y bloques de código con botón "copiar"
- ⬜ Historial de chats guardado en disco
- ⬜ Múltiples sesiones / proyectos en la sidebar

### Fase 5 — Multimedia (como Antigravity) ⬜
- ⬜ Subir imágenes (preview en el chat)
- ⬜ Subir video → extraer fotogramas con `ffmpeg`
- ⬜ Transcribir audio/video con `whisper` local
- ⬜ Arrastrar y soltar archivos al chat
- ⬜ (Opcional) Modelo de visión local para describir imágenes (ej. `llava`, `qwen2.5-vl`)

### Fase 6 — Especialización en ciberseguridad ⬜
- ✅ 🔵 Modelo `DeepHat-V1-7B` verificado y disponible como GGUF para Ollama
- ⬜ Integrarlo como modelo de ciberseguridad por defecto en la interfaz
- ⬜ Herramientas dedicadas: nmap, sqlmap, metasploit, análisis de logs
- ⬜ Plantillas de prompts (recon, análisis de vulnerabilidades, informe)
- ⬜ Carpeta de proyectos de pentest con estructura automática (/recon, /loot, /reports)

### Fase 7 — Empaquetado y distribución ⬜
- ⬜ App de escritorio con **Tauri** (ventana nativa, icono, no navegador)
- ⬜ Instalador `.deb` para Parrot/Debian
- ⬜ Publicar en GitHub Releases
- ⬜ Auto-actualización desde el repo

### 🔵 Fase 8 — Funciones PRO de pentest (lo que agrega valor real)
- ⬜ **Barra de Target** dentro de GOBLIN: campo para fijar IP/dominio y alcance del
  engagement. La IA siempre tiene el target en contexto. Aviso de autorización la 1ª vez.
- ⬜ **Panel de Hallazgos (findings) en vivo** ⭐: la IA registra vulnerabilidades encontradas
  (severidad, host, puerto, descripción, evidencia) en una tabla lateral/inferior.
- ⬜ **Generador de informe automático** ⭐: botón que arma el reporte de pentest en
  Markdown/PDF a partir de los hallazgos de la sesión. (La parte más tediosa, automatizada.)
- ⬜ **Log de auditoría** ⭐: cada comando/acción que ejecuta la IA queda registrado con
  timestamp (qué, cuándo, resultado). Trazabilidad total, exportable, alimenta el informe.
- ⬜ **Botón de Pánico / Stop** ⭐: mata cualquier proceso que la IA tenga corriendo
  (escaneo desbocado, bucle del agente). Grande y siempre visible.
- ⬜ **Snippets / comandos rápidos**: biblioteca de one-liners del usuario (reverse shells,
  LinPEAS, transferencia de archivos, pivoting). Clic → se insertan.
- ⬜ **Visor estructurado de resultados**: parsear salida de nmap/nikto/etc. y mostrarla
  como tabla (puertos, servicios, versiones) en vez de solo texto crudo.

### 🔵 Fase 8.1 — Ideas PRO para más adelante (anotadas, no ahora)
- ⬜ Integración con Metasploit RPC (controlar msfconsole desde GOBLIN)
- ⬜ Gestión de wordlists (rockyou, SecLists) con acceso rápido
- ⬜ Notas por host (tipo CherryTree/Obsidian integrado)
- ⬜ Multi-máquina: cambiar entre varios targets de un mismo engagement

### 🔵 Fase 9 — Integración con la Polybar existente de Parrot (idea del usuario)
> 🔵 **ACLARACIÓN (corregida):** el usuario NO quiere meter GOBLIN dentro de la Polybar.
> Su Polybar YA tiene un espacio que muestra "No target". Lo que quiere es que GOBLIN
> ESCRIBA el target HACIA AFUERA, a ESE espacio de la Polybar: cuando el usuario fije/conecte
> un objetivo en GOBLIN, el "No target" de la Polybar cambie a la IP/dominio del target.
> La interfaz de GOBLIN NO muestra el target en su propia ventana; lo publica a la Polybar.

**Cómo funciona (GOBLIN → Polybar, en una dirección):**
- ⬜ GOBLIN escribe el target actual en un archivo de estado, ej. `~/.cache/goblin/target`
  (contenido: la IP/dominio, o vacío = "No target").
- ⬜ El módulo existente de la Polybar (el del "No target") se cambia a tipo `custom/script`
  que lee ese archivo cada 1-2 s y muestra su contenido. Si el archivo está vacío → "No target".
  ```ini
  ; ~/.config/polybar/config.ini  (módulo existente adaptado)
  [module/target]
  type = custom/script
  exec = cat ~/.cache/goblin/target 2>/dev/null || echo "No target"
  interval = 2
  format-prefix = "🎯 "
  ```
- ⬜ Al fijar un target en GOBLIN (o conectarse a él) → el backend escribe el archivo.
  Al cerrar GOBLIN o quitar el target → escribe vacío (vuelve a "No target").
- ⬜ (Opcional) Mismo mecanismo para publicar OTROS estados a la Polybar: si la IA está
  trabajando (`working`), el modo activo (híbrido/local), nº de hallazgos. Cada uno su archivo.

**Lo que NO se hace (confirmado):**
- 🔵 NO meter el IDE (editor/chat/terminal) dentro de la Polybar — no cabe y no es lo pedido.
- 🔵 GOBLIN sigue siendo su propia ventana normal. Solo "avisa" su estado a la Polybar.

---

## 3. Herramientas del agente (actuales y planeadas)

| Herramienta    | Estado | Aprobación | Descripción                         |
|----------------|--------|------------|-------------------------------------|
| `list_dir`     | ✅     | No         | Lista contenido de carpeta          |
| `read_file`    | ✅     | No         | Lee archivo de texto                |
| `write_file`   | ✅     | Sí         | Crea/sobrescribe archivo            |
| `make_dir`     | ✅     | No         | Crea carpeta                        |
| `move_path`    | ✅     | Sí         | Mueve/renombra                      |
| `delete_path`  | ✅     | Sí         | Elimina archivo/carpeta             |
| `run_shell`    | ✅     | Sí         | Ejecuta comando                     |
| `search_files` | ⬜     | No         | Buscar texto en archivos (grep)     |
| `edit_lines`   | ⬜     | Sí         | Editar rango de líneas de un archivo|
| `http_get`     | ⬜     | No         | Descargar/consultar una URL         |
| `git_ops`      | ⬜     | Sí         | init, add, commit, push             |

---

## 4. Seguridad y control

- 🔵 `FULL_ACCESS=true` → la IA toca cualquier ruta del usuario. `false` → solo `workspace/`.
- Acciones destructivas (escribir, mover, borrar, shell) siempre piden aprobación.
- Servidor solo en `127.0.0.1` (nadie externo accede).
- Recomendado: no ejecutar como `root`; probar primero en una carpeta de pruebas.
- ⬜ Pendiente: lista negra de comandos (`rm -rf /`, `mkfs`, `dd`, etc.) con bloqueo duro.
- ⬜ Pendiente: log de todas las acciones ejecutadas (auditoría).

### 🔵 4.1. Privacidad del modo híbrido (CRÍTICO para pentesting)

- 🔵 **Gemini = nube.** Todo lo que se le envíe viaja a servidores de Google. Esto es
  delicado en un pentest real: IPs del objetivo, hallazgos, nombres de cliente, datos
  bajo NDA **no deben salir de la máquina**.
- 🔵 **Regla de oro:** en engagements reales con cliente → usar **modo local puro** (solo
  DeepHat). Gemini solo para labs, práctica, CVEs genéricos y utilidades sin datos reales.
- 🔵 La API key de Gemini va en un archivo `.env` que **NUNCA** se sube a GitHub
  (añadir `.env` al `.gitignore`).
- ⬜ Pendiente: filtro que detecte IPs/dominios/datos sensibles antes de mandar a Gemini
  y avise o fuerce DeepHat.
- ⬜ Pendiente: indicador permanente en la interfaz del modo activo, con color
  (verde=híbrido, amarillo=local puro) para no equivocarse en un engagement.

---

## 5. Estructura de archivos (objetivo final)

```
ia-ide/
├── backend/
│   ├── main.py
│   ├── agent.py
│   ├── tools.py
│   ├── terminal.py        # (Fase 3) pty por WebSocket
│   ├── media.py           # (Fase 5) ffmpeg + whisper
│   ├── sessions.py        # (Fase 4) historial en disco
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
│       ├── editor.js      # Monaco
│       ├── terminal.js    # xterm.js
│       ├── chat.js
│       └── explorer.js
├── workspace/
├── install.sh
├── run.sh
├── PLAN.md                # este archivo
└── README.md
```

---

## 6. Decisiones abiertas (por definir juntos)

- ✅ 🔵 Nombre de la app → **GOBLIN**
- ✅ 🔵 Color/tema principal → **negro estilo Antigravity** (acento por definir: verde/cian)
- 🔵 ⬜ ¿Empezamos Fase 2 por el **editor Monaco** o por la **terminal**? → pendiente de decidir
- 🔵 ⬜ ¿Modelo de visión local para imágenes? → aplazado (consume RAM; por ahora solo texto)
- 🔵 ⬜ Tono exacto del color de acento (verde Goblin recomendado)

---

## 🔵 8. Hardware objetivo (PC real) y ajustes

### 8.1. Especificaciones detectadas

| Componente   | Detalle                                                            |
|--------------|--------------------------------------------------------------------|
| CPU          | Intel Core i7-10700 @ 2.90 GHz · 8 núcleos / 16 hilos · x86_64     |
| Placa base   | ASUS PRIME B560M-A · Chipset B560 · LGA1200 · BIOS 0811 (2021)     |
| RAM          | 16 GB (15.4 GiB) · Swap ZRAM 7.7 GB + 3.3 GB en disco              |
| GPU          | **Solo Intel UHD 630 integrada · SIN GPU dedicada**                |
| Disco        | SSD Kingston SA400S37240G 240 GB (SATA) · ~223 GB en raíz/home     |
| Red          | Ethernet Intel I219-V (Gigabit) · Wi-Fi Realtek RTL8192EE          |
| SO / Kernel  | Parrot Security OS 7.4 (echo) · Linux 7.1.13+parrot7-amd64         |

### 8.2. Implicaciones (lo que esto significa para el proyecto)

- 🔵 **Inferencia 100 % en CPU.** La UHD 630 no sirve para acelerar LLMs; Ollama correrá
  sobre los 16 hilos del i7. Es usable, pero no instantáneo.
- 🔵 **RAM es el cuello de botella.** Con 16 GB, el modelo + sistema + navegador + Monaco
  deben caber juntos. Un modelo de 8B en Q4 usa ~5-6 GB; queda margen, pero ajustado.
- 🔵 **Rendimiento esperado (CPU, 8B Q4):** ~4-8 tokens/segundo. Las respuestas largas
  tardan. Para fluidez, preferir modelos más pequeños o cuantización más agresiva.
- 🔵 **Disco:** 240 GB SSD. Cada modelo pesa 2-6 GB; no descargar muchos a la vez.
  Dejar al menos 20-30 GB libres para el SSD (los SSD sufren si se llenan).

### 8.3. 🔵 Modelos recomendados PARA ESTE equipo (orden de preferencia)

| Modelo               | Tamaño Q4 | RAM aprox | Velocidad CPU | Notas                                 |
|----------------------|-----------|-----------|---------------|---------------------------------------|
| 🔵 **DeepHat-V1-7B** ⭐| ~4.5 GB   | ~5-6 GB   | ~4-7 tok/s 🐢 | **MODELO POR DEFECTO.** Ciberseguridad/pentest, base Qwen2.5-Coder-7B, agéntico |
| `Dolphin3-Cyber-8B`  | ~4.9 GB   | ~6 GB     | Lento 🐢      | Respaldo cyber opcional (pentest, DFIR, malware) |
| `qwen2.5-coder:3b`   | ~2 GB     | ~3.5 GB   | Rápido ⚡     | Respaldo rápido SOLO si DeepHat desespera (menos capaz) |

- 🔵 **Decisión tomada: DeepHat-V1-7B es el ÚNICO modelo del proyecto, por defecto.**
  El usuario es ingeniero de ciberseguridad; el proyecto se enfoca en pentesting.
- 🔵 **Instalación directa** (sin Modelfile manual):
  ```bash
  ollama run hf.co/mradermacher/DeepHat-V1-7B-GGUF:Q4_K_M
  ```
  (repos alternativos equivalentes: `GGUF-A-Lot/`, `KikoCis/`, `liodon-ai/` en HuggingFace)
- 🔵 Cuantización por equipo: **16 GB RAM → Q4_K_M** · más ligero → Q3_K_M · 24 GB+ → Q6_K.
- 🔵 El menú de modelos de la interfaz se mantiene (por si a futuro se añade otro), pero
  arranca solo con DeepHat seleccionado.
- 🔵 Usar cuantización **Q4_K_M** (la que trae Ollama por defecto). No subir a Q8 en este equipo.
- 🔵 Config Ollama recomendada: `OLLAMA_NUM_PARALLEL=1`, `num_ctx=4096` (no 8192, para ahorrar RAM).

### 8.4. 🔵 Ajustes de instalación para este equipo

- Añadir a `run.sh`:
  ```bash
  export OLLAMA_NUM_PARALLEL=1      # un solo request a la vez (poca RAM)
  export OLLAMA_MAX_LOADED_MODELS=1 # no mantener 2 modelos en RAM
  export OLLAMA_NUM_THREADS=8       # usar los 8 núcleos físicos
  ```
- En el `Modelfile`, bajar el contexto: `PARAMETER num_ctx 4096`.
- 🔵 Vigilar la RAM: si el sistema empieza a usar mucho swap, el modelo se ralentiza
  muchísimo. Cerrar apps pesadas (Chrome con muchas pestañas) al usar el modelo 8B.
- ⬜ Pendiente: botón en la interfaz que muestre uso de RAM/CPU en vivo.

### 8.5. 🔵 Qué NO intentar en este equipo

- Modelos de 14B, 32B o mayores → no caben en 16 GB o van inusablemente lentos.
- Cuantización Q8 o FP16 de modelos 8B → consumen demasiada RAM.
- Modelos de visión grandes (`llava:13b`) → mejor `moondream` o `llava:7b` si se necesita visión.
- Correr varios modelos a la vez.

---

## 🔵 9. Interfaz GOBLIN — inventario de elementos (tema negro Antigravity)

> Referencia visual: captura del IDE Antigravity aportada por el usuario. Tema negro,
> fondo casi negro (#0d0d0f aprox), texto gris claro, acentos sutiles. Enumeramos CADA
> elemento para construirlo sin inventar nada. Estado de cada uno: ⬜ / 🟨 / ✅.
>
> 🔵 **NOTA IMPORTANTE:** la barra de arriba de la captura (IP, iconos Pac-Man, reloj,
> "No target", botón power) **NO es parte de la app** — es la **Polybar/bspwm de Parrot OS**
> del usuario. GOBLIN NO la incluye. GOBLIN es SOLO la ventana del IDE (desde `File / View /
> Window` hacia abajo). No construir ninguna barra de estado del sistema.

### 9.1. Barra de ventana (menú tipo app de escritorio) ⬜
1. ⬜ Botones de ventana: cerrar / maximizar / minimizar (izquierda)
2. ⬜ Menús: `File` · `View` · `Window`

### 9.2. Panel izquierdo — Sidebar de navegación ⬜
3. ⬜ Icono GOBLIN + botón colapsar sidebar + navegación (atrás/adelante) + buscar
4. ⬜ Botón **New Conversation** (nueva conversación)
5. ⬜ **Conversation History** (historial de conversaciones)
6. ⬜ **Automations** (tareas/automatizaciones programadas)
7. ⬜ **Customizations** (personalización: tema, prompts, etc.)
8. ⬜ Sección **Projects**: lista de proyectos (ej. carpetas de pentest por cliente)
9. ⬜ Sección **Conversations**: lista de chats con título + antigüedad (2m, 3h, 10h, 1d)
10. ⬜ Indicador de chat activo (resaltado) y punto azul en chats con novedad
11. ⬜ Botón **Settings** (ajustes, abajo del todo)

### 9.3. Panel central — Chat agéntico ⬜
12. ⬜ Título de la conversación actual (barra superior del panel)
13. ⬜ Botones de la conversación: menú (⋮) y cambiar vista
14. ⬜ Área de mensajes: usuario y asistente, con Markdown y bloques de código
15. ⬜ 🔵 Etiqueta por mensaje indicando qué modelo respondió (Gemini / DeepHat)
16. ⬜ Secciones "Lo omitido / Riesgo" u observaciones del asistente
17. ⬜ Pie de cada mensaje: hora, botón copiar, pulgar arriba/abajo
18. ⬜ **Barra de input** inferior: `Ask anything, @ to mention, / for actions`
19. ⬜ Botón adjuntar (+) para imágenes/archivos/video
20. ⬜ **Selector de modelo** en el input (muestra modelo activo, ej. "DeepHat" / "Gemini")
21. ⬜ Selector de modo/velocidad (ej. "Turbo") + 🔵 selector de modo híbrido/local/manual
22. ⬜ 🔵 Botón de micrófono (dictado por voz) ⭐ MANTENER: el usuario habla, se transcribe
    con Whisper local, el texto aparece en el input y desde ahí se envía como prompt a la IA
    (igual que dictar un audio y que salga el texto). Útil para dar instrucciones sin teclear.
    + botón enviar

### 9.4. Panel derecho — Editor de código + Workspace ⬜
23. ⬜ Pestañas superiores: terminales y archivos abiertos (ej. `echo ... | sudo`, `bspwmrc`)
24. ⬜ Botón nueva pestaña (+)
25. ⬜ Botones de panel: pantalla completa, abrir/cerrar panel derecho
26. ⬜ **Breadcrumb** de ruta del archivo (ej. `home › hide › .config › bspwm › bspwmrc`)
27. ⬜ Etiqueta de estado del archivo (ej. `single edit`) + copiar + menú
28. ⬜ **Editor de código** con números de línea y resaltado de sintaxis (Monaco)
29. ⬜ 🔵 **Vista de diff**: líneas añadidas (verde) y quitadas (rojo), estilo Antigravity
30. ⬜ Plegado de líneas (`+5 more lines`, `+8 more lines`)
31. ⬜ **Explorador Workspace** (árbol de carpetas/archivos del proyecto, con refrescar)
32. ⬜ Selección de archivo activo resaltada

### 9.5. Panel inferior — Terminal integrada (Fase 3) ⬜
33. ⬜ Terminal real (xterm.js) conectada a shell por WebSocket
34. ⬜ Pestañas de terminal + historial

### 9.6. 🔵 Tema visual (tokens de color) ⬜
35. ⬜ Fondo principal: negro/casi negro (~#0d0d0f)
36. ⬜ Paneles: gris muy oscuro (~#161618) con bordes sutiles (~#2a2a2e)
37. ⬜ Texto: gris claro (~#e6e6e6), texto tenue (~#888)
38. ⬜ Diff añadido: verde oscuro translúcido · Diff quitado: rojo oscuro translúcido
39. ✅ 🔵 Acento (resaltado, foco): **verde goblin #3ddc84** (aprobado por el usuario)

### 🔵 9.7. Mejoras visuales a agregar a la maqueta (aprobadas por el usuario)
> El usuario aprobó colores y diseño base. Estas mejoras elevan el look a "IDE pro de pentest".
> NOTA: el "badge de target en el chat" se DESCARTÓ — el target ya se ve en la Polybar (Fase 9),
> duplicarlo dentro de GOBLIN no tiene sentido.
40. ⬜ **Barra de estado inferior (status bar)** ⭐: franja fina abajo de todo (estilo VS Code)
    siempre visible: modelo activo, modo (híbrido/local), uso de RAM/CPU en vivo, rama de git,
    línea:columna del editor. Es lo que más eleva el look a "IDE profesional".
41. ⬜ **Indicador de acción en vivo**: cuando la IA ejecuta algo, renglón animado con spinner
    (`⚡ Ejecutando nmap... (3s)`). Clave en CPU lenta: muestra que trabaja, no que está colgada.
42. ⬜ **Caja de aprobación visual**: tarjeta destacada en vez de texto plano
    ("⚠️ La IA quiere ejecutar `rm archivo.txt`") con botones grandes verde/rojo. Borde ROJO
    para acciones peligrosas (rm, dd, sudo), borde verde/neutro para normales.
43. ⬜ **Severidad con colores (panel de hallazgos)**: Critical=rojo · High=naranja ·
    Medium=amarillo · Low=azul · Info=gris. Chips de color, se lee de un vistazo.
44. ⬜ **Barra de progreso sutil arriba**: línea fina verde que corre en el borde superior
    mientras la IA genera (estilo YouTube/GitHub). Elegante, confirma "está vivo".
45. ⬜ **Resaltar comandos peligrosos** en rojo dentro del código/terminal (`rm`, `dd`, `mkfs`).
46. ⬜ **Mini-mapa** del código a la derecha del editor (como VS Code).
47. ⬜ **Contador de tokens/contexto**: cuánta memoria le queda al modelo en la conversación.
48. ⬜ **Atajos visibles** (tooltip ⓘ) al pasar el mouse sobre botones.

### 🔵 9.8. Lo que NO se agrega al diseño (decisión consciente)
- 🔵 Badge de target dentro de GOBLIN → DESCARTADO (ya está en la Polybar).
- 🔵 Animaciones llamativas / efectos "gamer" (neón parpadeante) → se ve amateur, distrae.
- 🔵 Exceso de iconos de colores → el minimalismo negro es lo que lo hace ver pro.
- 🔵 Múltiples temas (claro/varios) → solo negro.

---

## 🔵 10. Revisión técnica — qué falta para que FUNCIONE en tu PC

> Revisión completa del plan. Lo que sigue es lo que detecté que falta o mejoraría para
> que GOBLIN funcione de verdad en tu equipo (i7-10700, 16 GB, sin GPU) con el control
> total que pediste. Ordenado por prioridad.

### 10.1. 🔴 CRÍTICO — sin esto no funciona

1. ⬜ **DeepHat y tool-calling.** DeepHat se basa en Qwen2.5-Coder, que SÍ soporta
   herramientas nativas. PERO hay que verificar que el GGUF concreto conserve la plantilla
   de tools. Si falla, plan B: **tool-calling por texto** (el modelo responde un bloque
   JSON y el backend lo interpreta). Hay que construir AMBOS caminos y detectar cuál usar.
2. ⬜ **El modo híbrido necesita UN SOLO formato de herramientas.** Gemini y DeepHat
   manejan tools distinto. El router debe traducir las mismas herramientas a cada modelo,
   o la IA no podrá crear/mover/borrar archivos cuando use Gemini. **Es la pieza más difícil.**
3. ⬜ **Streaming por WebSocket, no HTTP simple.** El MVP actual (Fase 1) responde de golpe.
   En CPU, con respuestas lentas, el usuario necesita ver el texto aparecer poco a poco o
   parecerá colgado. Hay que pasar el chat a WebSocket con streaming desde el inicio de Fase 2.
4. ⬜ **Gestión de RAM en tiempo real.** Con 16 GB y DeepHat ocupando ~6 GB, si abres el
   navegador + Monaco + terminal, puedes quedarte sin RAM y todo se congela. Necesario:
   liberar el modelo de Ollama cuando no se use (`keep_alive`), y avisar si la RAM baja.

### 10.2. 🟠 IMPORTANTE — control total de la PC (lo que pediste)

5. ⬜ **Herramientas de archivos ampliadas.** El MVP tiene crear/mover/borrar/leer. Faltan
   para "control total": `copy_path` (copiar), `rename` (ya cubierto por move), `chmod`
   (permisos), `search_files` (grep recursivo), `find_files` (buscar por nombre),
   `read_binary`/`download` (archivos no-texto), `disk_usage` (espacio libre).
6. ⬜ **Terminal persistente real (pty), no `subprocess` suelto.** `run_shell` actual ejecuta
   un comando y muere. Para control total necesitas una shell viva que mantenga directorio,
   variables, procesos en segundo plano (ej. un `nc` escuchando). Eso es la Fase 3 (pty) y
   debería subir de prioridad: es clave para pentesting.
7. ⬜ **Permisos sudo controlados.** Muchas herramientas de pentest (nmap SYN scan, tcpdump)
   necesitan root. Decidir: ¿GOBLIN pide sudo por comando? ¿Corre con capabilities? Definir
   cómo la IA ejecuta cosas privilegiadas SIN que corras toda la app como root (peligroso).
8. ⬜ **Autoaprobación configurable por tipo.** Pediste control total sin fricción, pero
   aprobar cada acción cansa. Solución: niveles — "auto" para crear/leer/listar, "preguntar"
   solo para borrar/sudo/comandos destructivos. Configurable en Settings.

### 10.3. 🟡 ROBUSTEZ — para que no se rompa

9. ⬜ **Límite de iteraciones del agente.** Un modelo 7B puede entrar en bucle (llamar la
   misma herramienta sin parar). Poner tope (ej. 15 pasos) y botón de "Detener".
10. ⬜ **Manejo de errores de Ollama/Gemini.** ¿Qué pasa si Ollama no está corriendo, el
    modelo no está descargado, o se cae la red (Gemini)? El backend debe dar mensajes claros,
    no reventar.
11. ⬜ **Timeouts.** Un comando shell que cuelga (ej. `nmap` a toda una red) no debe congelar
    la app. El MVP ya tiene timeout de 180s en shell; ajustar y hacerlo cancelable.
12. ⬜ **Persistencia de sesiones.** Ahora las conversaciones viven en RAM y se pierden al
    cerrar. Guardarlas en SQLite o JSON en disco (Fase 4).
13. ⬜ **Lista negra de comandos.** Bloqueo duro de `rm -rf /`, `mkfs`, `dd of=/dev/sda`,
    fork bombs, etc. aunque la IA los proponga por error. Ya está como pendiente en §4.

### 10.4. 🟢 MEJORAS que yo añadiría

14. ⬜ **System prompt especializado en pentest.** Darle a DeepHat un prompt que lo haga
    trabajar con metodología (recon → enum → explotación → post → reporte) y que SIEMPRE
    recuerde pedir confirmación de autorización del objetivo.
15. ⬜ **Gestión de "targets".** Un campo para fijar el objetivo del engagement (IP/dominio)
    y que la IA lo tenga de contexto. Carpeta automática por target (`/engagements/<target>/`).
16. ⬜ **Plantillas/comandos rápidos.** Botones o `/comandos`: "/recon", "/scan", "/report"
    que lancen flujos predefinidos. Acelera mucho el trabajo real.
17. ⬜ **Exportar informe.** Generar un informe de pentest (Markdown/PDF) a partir de los
    hallazgos de la sesión. Muy útil para tu trabajo.
18. ⬜ **Modo offline total verificable.** Un indicador que confirme que NADA salió a la red
    cuando estás en modo local puro (importante para engagements con NDA).

### 10.5. 🔵 Mi recomendación de orden de trabajo (ruta realista)

> No construir todo a la vez. Ruta sugerida para llegar a algo usable rápido:

1. **Fase 2 (interfaz)** — primero el look GOBLIN funcionando (sin Monaco todavía, solo
   layout + chat + explorador). Ver algo real motiva y permite probar.
2. **Streaming + manejo de errores** (puntos 3, 10, 11) — para que el chat se sienta vivo.
3. **Terminal pty (Fase 3)** — subida de prioridad: es core para pentesting (punto 6).
4. **Herramientas ampliadas + autoaprobación** (puntos 5, 8) — el "control total" real.
5. **Router híbrido (Fase 2.5)** — cuando lo demás ya funcione con DeepHat solo. Es lo más
   complejo (puntos 1, 2); mejor no empezar por aquí.
6. **System prompt pentest + targets + plantillas** (puntos 14, 15, 16) — la capa pro.
7. **Informe, persistencia, empaquetado** — pulido final.

- 🔵 **Consejo honesto:** empieza con **modo local puro (solo DeepHat)**. Haz que GOBLIN
  funcione completo con un solo modelo. El router híbrido añádelo después, cuando ya tengas
  una app estable. Meter Gemini desde el día 1 multiplica la complejidad y los puntos de fallo.

---

## 7. Changelog

- **v0.1** — Documento inicial del plan. Fase 1 (MVP) ya construida en el chat.
- 🔵 **v0.2** — Agregada §8 con hardware real (i7-10700, 16 GB, sin GPU). Ajustados
  modelos recomendados a CPU: `qwen3:4b` como principal, `dolphin3` para sin censura.
  Añadidos flags de Ollama y contexto reducido a 4096 para ahorrar RAM.
- 🔵 **v0.3** — Verificado que **DeepHat-V1-7B SÍ tiene GGUF para Ollama**. Adoptado como
  modelo de ciberseguridad oficial del proyecto. Estrategia de dos modelos: `qwen3:4b`
  para desarrollar, `DeepHat-V1-7B` para tareas reales. Comando de instalación directo añadido.
- 🔵 **v0.4** — Usuario confirma ser ingeniero de ciberseguridad. **DeepHat-V1-7B fijado como
  modelo ÚNICO y por defecto** del proyecto (se descarta la estrategia de dos modelos).
  Proyecto reenfocado 100% en pentesting. `DEFAULT_MODEL` del backend pasa a DeepHat.
- 🔵 **v0.5** — Adoptada **arquitectura híbrida**: Gemini (nube) orquesta y responde rápido,
  DeepHat (local) entra cuando Gemini se niega por censura. Añadida Fase 2.5 (router) con
  3 modos (híbrido / local puro / manual) y sección 4.1 de privacidad para pentesting.
- 🔵 **v0.6** — **Nombre definido: GOBLIN.** Tema negro estilo Antigravity. Añadida §9 con
  el inventario completo de la interfaz (elementos numerados, basados en la captura del
  usuario) para construir sin alucinar. Definidos tokens de color base.
- 🔵 **v0.7** — **Corrección:** la barra superior de la captura (IP, Pac-Man, reloj, "No
  target", power) NO es Antigravity, es la **Polybar/bspwm de Parrot** del usuario. Eliminada
  del inventario. GOBLIN es SOLO la ventana del IDE (desde `File/View/Window` hacia abajo).
  §9 renumerada a 39 elementos.
- 🔵 **v0.8** — Añadida §10 (revisión técnica completa): 18 puntos de lo que falta para que
  GOBLIN funcione en el PC real con control total, ordenados por prioridad (crítico/importante/
  robustez/mejoras) + ruta de trabajo recomendada. Cerradas decisiones de §6 (nombre y tema).
- 🔵 **v0.9** — Añadidas Fase 8 (funciones PRO de pentest: barra de Target, panel de Hallazgos,
  informe automático, log de auditoría, botón de Pánico, snippets, visor estructurado), Fase 8.1
  (ideas futuras) y Fase 9 (integración con Parrot/Polybar). Dictado por voz confirmado como
  función a MANTENER (Whisper local → texto en el input). Creada la maqueta `goblin-mockup.html`.
- 🔵 **v1.0** — **Corrección Fase 9:** el usuario NO quiere GOBLIN dentro de la Polybar. Su
  Polybar ya tiene el espacio "No target"; GOBLIN debe ESCRIBIR el target a ESE espacio
  (vía archivo de estado `~/.cache/goblin/target` + módulo `custom/script` en Polybar).
  GOBLIN publica su estado hacia afuera; el IDE sigue en su propia ventana.
- 🔵 **v1.1** — Colores y diseño base APROBADOS (verde goblin #3ddc84 fijado). Añadidas §9.7
  (mejoras visuales: barra de estado inferior, indicador de acción en vivo, caja de aprobación
  visual, severidad por colores, barra de progreso, resaltado de comandos peligrosos, mini-mapa,
  contador de tokens, tooltips) y §9.8 (lo que NO se agrega). Badge de target DESCARTADO
  (ya está en la Polybar).
