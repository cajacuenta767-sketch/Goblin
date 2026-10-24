# Spec 027 — Marketplace: instalar con contraseña en la app y registro en vivo

**Estado:** 🟨 En progreso · **Tipo:** funcionalidad · **Depende de:** 026
**Reemplaza:** Spec 026, RF2 ("GOBLIN no recibe la contraseña"). La terminal sigue como alternativa.

## Problema

La Spec 026 dejaba la contraseña de sudo en la terminal y no mostraba qué pasaba durante la
instalación. El usuario pidió dos cosas: ver la salida de la instalación dentro de GOBLIN y que,
si hace falta, aparezca un diálogo donde escribir la contraseña de administrador.

## Requisitos funcionales

- **RF1.** Instalar y Desinstalar piden confirmación dentro de la tarjeta, con el comando exacto (igual que en 026).
- **RF2.** Si sudo necesita contraseña (`sudo -n true` falla), aparece un diálogo de GOBLIN con un campo de contraseña. Si no la necesita, el trabajo se ejecuta directamente.
- **RF3.** La contraseña viaja por stdin a `sudo -S`, una sola vez, y se descarta. Nunca va en argumentos (no aparece en `ps`), nunca se guarda en el trabajo, nunca se escribe en el registro y nunca vuelve a la UI.
- **RF4.** Si la contraseña es incorrecta, el trabajo vuelve a "esperando contraseña" con el mensaje "Contraseña incorrecta" y el diálogo se reabre.
- **RF5.** La salida de apt se muestra en vivo en el panel "Instalaciones" (últimas 400 líneas). Las líneas de autenticación de sudo se ocultan.
- **RF6.** Cancelar detiene el trabajo: SIGTERM a sudo, que lo reenvía al comando. Si no termina en 8 s, SIGKILL.
- **RF7.** Solo un trabajo a la vez, porque apt usa un bloqueo. Un trabajo que espera contraseña también cuenta como activo.
- **RF8.** Tiempo máximo: 30 minutos. Pasado ese tiempo, el trabajo se detiene con un mensaje.
- **RF9.** Al terminar, el catálogo se vuelve a leer y la tarjeta muestra el estado real.
- **RF10.** Desinstalar (`apt-get remove -y`) usa la misma mecánica y la misma confirmación.
- **RF11.** Al reabrir el marketplace se retoma el último trabajo. Si espera contraseña, vuelve a pedirla.
- **RF12.** "En la terminal" sigue disponible como alternativa (Spec 026).

## Límites (se dicen claro)

- Python no puede borrar de memoria una cadena. La contraseña queda en memoria hasta que el
  recolector la libera. Se minimiza: la referencia se borra en cuanto se escribe a sudo.
- La contraseña viaja por HTTP solo en 127.0.0.1, hacia el backend local. No sale de la máquina.
- Si se cancela con SIGKILL, apt puede dejar un bloqueo. Hay que ejecutar
  `sudo dpkg --configure -a` a mano.
- Si se reinicia el backend, el registro de trabajos se pierde (solo vive en memoria).
- Las pruebas usan un `sudo` y un `apt-get` simulados. No se instaló nada real.
- No se probó en la app nativa de Tauri ni en Parrot.

## Criterios de aceptación

- [x] Con sudo que pide contraseña, aparece el diálogo; con contraseña correcta la herramienta se instala.
- [x] Con contraseña incorrecta, el diálogo vuelve a pedirla con el aviso "Contraseña incorrecta".
- [x] Sin contraseña requerida, la instalación corre sin diálogo.
- [x] La contraseña no aparece en el estado del trabajo, en el registro de instalación ni en los argumentos de sudo.
- [x] Solo se acepta un trabajo a la vez.
- [x] Cancelar detiene el trabajo en menos de 10 s.
- [x] Desinstalar usa `apt-get remove` y pide contraseña.
- [x] Probado en el navegador con el backend real (flujo completo, sudo y apt simulados).
- [ ] Probado en el PC con la app nativa y el sudo real (pendiente del usuario).

## Fuera de alcance

- Guardar la contraseña (sudo timestamp, keyring). Se descarta: no se guarda nada.
- Actualizar todas las herramientas de una vez.
- Cola de varias instalaciones.
