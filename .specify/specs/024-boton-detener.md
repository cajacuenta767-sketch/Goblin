# Spec 024 — Botón Detener (cancelación de la IA)

**Estado:** 🟨 En progreso · **Tipo:** funcionalidad · **Depende de:** 001, 004, 018
**Referencias:** constitución III.3 · PLAN §10.3 (puntos 9 y 11) · PLAN Fase 8 ("Botón de Pánico / Stop")

## Problema

GOBLIN no tiene forma de parar al agente. Un comando de shell colgado puede tardar
hasta `SHELL_TIMEOUT` (180 s), un modelo lento en CPU puede tardar minutos, y el
único freno es el tope de pasos (`MAX_STEPS`). Mientras tanto, la app parece
congelada y el usuario no puede impedir que la IA siga ejecutando acciones.

## Requisitos funcionales

- **RF1.** Mientras GOBLIN responde, el botón de enviar se convierte en **⏹ Detener**.
- **RF2.** Al detener, la IA: (a) no ejecuta ninguna herramienta pendiente, (b) descarta
  la cola de aprobación, (c) mata el proceso de shell en curso con todo su grupo de
  procesos (p. ej. un `nmap` lanzado desde `run_shell`), (d) descarta la respuesta del
  modelo que todavía estaba generando.
- **RF3.** En modo streaming, la respuesta se corta entre trozos. El texto ya generado
  queda en el historial marcado como detenido.
- **RF4.** Se muestra el aviso "Detenido por el usuario" dentro del chat.
- **RF5.** Una acción de shell interrumpida queda en el log de auditoría con resultado
  `CANCELADO`.

## Límites (se dicen claro, no se ocultan)

- El modelo local no se puede interrumpir en mitad de un sondeo sin streaming. La app
  deja de esperar al instante, pero Ollama termina de generar en segundo plano y su
  resultado se descarta.
- Los procesos lanzados desde la **terminal pty** (spec 004/019) no los mata este botón.
  Son una sesión aparte; su gestión queda para una spec posterior.

## Criterios de aceptación

- [x] Con una respuesta en curso, el botón enviar muestra ⏹ y al pulsarlo la IA se detiene.
- [x] `run_shell("sleep 30")` interrumpido por Detener termina en menos de 5 s con `CANCELADO`.
- [x] Una herramienta encolada no se ejecuta después de Detener.
- [x] Una cola de aprobación pendiente se vacía al detener.
- [x] El streaming se corta entre trozos y deja el aviso en el chat.
- [x] Las pruebas automáticas cubren la cancelación de shell y la detención del bucle.

## Fuera de alcance

- Matar procesos de la terminal pty (queda para una spec de gestión de procesos).
- Cancelar la generación del modelo a mitad de token sin streaming.
