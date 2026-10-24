# Spec 026 — Marketplace: instalación por terminal y catálogo ampliado

**Estado:** 🟨 En progreso · **Tipo:** funcionalidad · **Depende de:** 004, 016, 020
**Referencias:** constitución (acciones privilegiadas o destructivas requieren aprobación) · PLAN §10.2 #7 (estrategia de sudo, pendiente; esta spec no la decide)

## Problema

El botón **Instalar (apt)** del marketplace no funcionaba, por tres motivos:

1. `install()` ejecuta `sudo apt-get install` como subproceso del backend, sin terminal.
   `sudo` necesita pedir la contraseña y no tiene dónde hacerlo, así que falla siempre
   (salvo que el sistema tenga `NOPASSWD`). El usuario solo ve un `alert()` con el error.
2. Los enlaces **⬇ Descargar** y **↗ Última versión oficial** usan `target="_blank"`.
   Dentro de la ventana nativa de Tauri no abren el navegador.
3. `confirm()` y `alert()` son diálogos nativos del navegador. No hay garantía de que la
   webview de Tauri en Linux los muestre. (No verificado en el PC; se sustituyen por HTML
   para no depender de ellos.)

Además, 8 paquetes del catálogo no existen en los repositorios de Ubuntu
(`metasploit-framework`, `crackmapexec`, `impacket-scripts`, `responder`, `enum4linux`,
`wpscan`, `feroxbuster`, y `burpsuite`, que no está en apt y solo se descarga). Y tras
instalar no había forma de volver a leer qué estaba instalado.

## Requisitos funcionales

- **RF1.** "Instalar" muestra una confirmación dentro de la tarjeta con el comando exacto.
  No usa `confirm()`.
- **RF2.** Al confirmar, el backend devuelve el comando (tomado del catálogo y validado) y
  la UI lo escribe en la **terminal integrada** y la abre. El usuario escribe su contraseña
  de sudo en el prompt real. GOBLIN no la recibe, no la ve y no la guarda.
- **RF3.** "Descargar" y "↗" llaman a `POST /api/toolstore/open`. El backend abre la URL con
  `xdg-open`. Solo acepta IDs del catálogo y URLs `https://` del catálogo; nunca abre una
  URL arbitraria.
- **RF4.** Las herramientas sin paquete apt (Burp Suite) no muestran "Instalar": muestran
  "Solo descarga manual".
- **RF5.** Si el nombre de paquete no está comprobado (`verified: false`), la tarjeta muestra
  la etiqueta "pkg sin verificar".
- **RF6.** "↻ Actualizar" vuelve a leer qué está instalado.
- **RF7.** Los errores se muestran como texto dentro de la tarjeta, sin `alert()`.
- **RF8.** La detección de "instalada" usa el binario en el PATH o, si la herramienta tiene
  `path`, la existencia de esa ruta (SecLists no tiene binario).
- **RF9.** El catálogo pasa de 23 a 67 herramientas en 10 categorías (se añaden OSINT,
  Post-explotación, Forense e Ingeniería inversa). Los paquetes verificados se comprobaron
  descargando el `.deb` en Ubuntu 24.04 y listando sus binarios.

## Límites (se dicen claro)

- Las comprobaciones se hicieron en Ubuntu 24.04 (base Debian). Parrot OS puede usar nombres
  distintos; por eso las entradas no comprobadas llevan la etiqueta.
- GOBLIN no sigue la instalación: sabe que el comando se envió, no si terminó bien. El estado
  real se ve con "↻ Actualizar".
- `xdg-open` necesita un navegador configurado en el escritorio.
- La estrategia de sudo a largo plazo (PLAN §10.2 #7) no se decide aquí. Este flujo no la
  necesita, porque sudo pide la contraseña en la terminal.
- Las URLs de fuente de las herramientas nuevas se escribieron desde el conocimiento del
  proyecto y no se abrieron una a una. Hay que probarlas en el PC.
- No se probó en la app Tauri nativa. Las pruebas son con el backend real y Chromium
  (Playwright).

## Criterios de aceptación

- [x] "Instalar" muestra el comando exacto dentro de la tarjeta, sin diálogo nativo.
- [x] Confirmar escribe el comando en la terminal integrada (comprobado en el buffer de xterm).
- [x] "Descargar" llama a `/api/toolstore/open`; con un ID desconocido no abre nada.
- [x] Burp Suite no muestra "Instalar".
- [x] Una herramienta con `verified: false` muestra la etiqueta.
- [x] "↻ Actualizar" refresca el estado instalado.
- [x] Hay pruebas automáticas: forma del catálogo, `install()` no ejecuta `apt`, y rechazo de
      URLs e IDs fuera del catálogo.
- [ ] Probado en el PC con la app nativa (pendiente del usuario).

## Fuera de alcance

- Instalar sin terminal (pkexec/polkit o diálogo de contraseña propio): guardaría credenciales;
  se descarta.
- Seguir el progreso de apt dentro de la tarjeta.
- Desinstalar herramientas.
- Fuentes distintas de apt (pip, go, descargas automáticas de GitHub).
