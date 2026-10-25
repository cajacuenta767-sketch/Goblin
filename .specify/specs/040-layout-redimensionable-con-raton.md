# Spec 040 — Layout redimensionable y paneles acoplables (solo ratón)

**Estado:** ✅ Hecho y validado en Chromium con ratón · ⬜ PC: ventana Tauri · **Tipo:** interfaz · **Depende de:** 002, 023
**Motivo:** el usuario quiere que la ventana se comporte como Word o un IDE: cambiar el tamaño de cada zona
arrastrando, mover paneles (sobre todo la terminal) dentro de la ventana y recuperar el diseño guardado.
Todo con ratón.

## Requisitos funcionales

- **RF1 · Divisores.** Entre columnas (izquierda | centro | derecha) y entre paneles apilados dentro de una
  columna hay un divisor. Arrastrarlo cambia el tamaño de los dos paneles vecinos. Mínimo 120 px por panel.
- **RF2 · Acoplar.** Cada panel (barra lateral, chat, explorador/editor, terminal, hallazgos/hosts) tiene una
  cabecera con agarre. Al arrastrarla se muestran zonas de destino (izquierda, derecha, abajo del centro,
  arriba/abajo de cada columna). Soltar en una zona mueve el panel allí.
- **RF3 · Terminal dentro de la ventana.** La terminal puede acoplarse en cualquier zona, incluida la derecha.
  Siempre queda dentro de la ventana; no flota fuera.
- **RF4 · Colapsar.** Doble clic en una cabecera de panel lo colapsa a su cabecera; otro doble clic lo abre.
- **RF5 · Guardar.** La disposición (zona, orden y tamaños) se guarda en `localStorage`. Si falla, la app
  arranca con la disposición por defecto. Botón "Restablecer disposición" en el menú **View**.
- **RF6 · Solo ratón.** No se requieren atajos de teclado para mover ni redimensionar.
- **RF7 · Sin pérdida de estado.** Mover un panel no reinicia el chat, la terminal ni el editor (los nodos
  se mueven, no se recrean).

## Criterios de aceptación

- [ ] Arrastrar el divisor entre chat y explorador cambia el ancho sin saltos.
- [ ] Arrastrar la cabecera de la terminal a la zona derecha la coloca allí y el chat sigue escribible.
- [ ] Tras recargar, el panel conserva zona y tamaño.
- [ ] "Restablecer disposición" vuelve al diseño inicial.
- [ ] Un panel no puede quedar con ancho o alto menor de 120 px.
- [ ] Prueba E2E con Playwright y eventos de ratón en `scratchpad` (no en el repo).

## Límites

- No se implementan ventanas flotantes ni pestañas arrastrables entre zonas (fuera de alcance v1).
- En pantallas de menos de 900 px de ancho, la columna derecha se apila debajo del chat.
