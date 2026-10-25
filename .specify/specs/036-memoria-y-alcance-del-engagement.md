# Spec 036 — Memoria del engagement, alcance aplicado y nmap estructurado

**Estado:** 🟨 Implementado · pruebas unitarias ✅ · ⬜ PC: DeepHat real · **Tipo:** funcionalidad + seguridad · **Depende de:** 012, 025, 033, 034
**Motivo:** GOBLIN olvidaba el objetivo y los hallazgos después de unos mensajes (solo veía los últimos
10 turnos), no comprobaba que los escaneos apuntaran dentro del alcance autorizado y parseaba nmap solo
como texto suelto.

## Problema

1. El modelo solo recibe `GOBLIN_HISTORY_TURNS` turnos. El objetivo, los hosts y los hallazgos viven en
   SQLite, pero no se inyectan en cada turno.
2. `set_target` fija el objetivo, pero ninguna herramienta comprueba que `nmap`, `sqlmap`, `curl`… apunten
   dentro de un alcance. Un error del modelo puede escanear una red ajena.
3. `parse_nmap` solo lee la salida de texto. No se guardan los puertos por host ni se usan los datos de XML.

## Requisitos funcionales

- **RF1 · Alcance.** Cada sesión tiene una lista de entradas de alcance: IP, rango CIDR o dominio. `set_target`
  añade el objetivo al alcance tras la aprobación del usuario. El usuario edita la lista desde la interfaz;
  **la IA no puede ampliar el alcance**. Lo ve en el resumen del engagement (RF5); no hay herramienta para editarlo.
- **RF2 · Bloqueo.** Antes de pedir aprobación, una llamada a `run_shell`, `term_run` o `http_get` cuyo destino
  no esté en el alcance se **bloquea** y la IA recibe el motivo. Un dominio incluye sus subdominios. Loopback
  (`127.0.0.1`, `localhost`, `::1`) siempre se permite.
- **RF3 · Destinos no verificables.** En herramientas de red, un destino con variables (`$X`), sustitución de
  comandos o listas de archivo (`-iL`, `-iR`) se bloquea: no se puede comprobar el alcance.
- **RF4 · Sin alcance.** Si la sesión no tiene alcance y la herramienta de red tiene destinos, se bloquea con
  el mensaje "No hay alcance definido".
- **RF5 · Memoria.** Antes de cada llamada al modelo se añade un mensaje de sistema con el resumen del
  engagement: objetivo, alcance, hosts con puertos abiertos (máx. 30 líneas) y hallazgos por severidad con
  sus 5 títulos principales. Se calcula desde SQLite.
- **RF6 · Privacidad.** El resumen cuenta como contenido de la conversación para el router híbrido: si contiene
  una IP, un rango o un término sensible, la respuesta va a DeepHat (Spec 025/038).
- **RF7 · nmap estructurado.** Cada salida de `nmap` (texto `-oN` o XML `-oX -`) se parsea y los puertos
  abiertos se guardan en la tabla `hosts`. `parse_nmap` acepta XML además de texto.
- **RF8 · Vista.** La interfaz muestra la tabla de hosts y puertos de la sesión (ver Spec 041).

## Criterios de aceptación

- [ ] Un `nmap 10.10.10.5` con el objetivo fuera del alcance no pide aprobación: se bloquea con el motivo.
- [ ] `nmap 10.10.10.5` con el objetivo dentro del alcance pide aprobación como antes.
- [ ] `nmap $IP` se bloquea como no verificable.
- [ ] `curl https://sub.ejemplo.com` con `ejemplo.com` en el alcance está permitido.
- [ ] Un XML de nmap con dos hosts guarda sus puertos abiertos en la base.
- [ ] Tras 15 mensajes, el modelo sigue recibiendo el objetivo y los hallazgos (resumen).
- [ ] Un resumen con IP fuerza DeepHat en modo híbrido.
- [ ] Pruebas en `backend/tests/test_alcance_engagement.py`.

## Límites

- La detección de destinos lee tokens del comando. Un destino dentro de un script externo no se ve.
- El bloqueo depende de la lista de herramientas de red (`scope.NETWORK_CMDS`). Una herramienta fuera de la
  lista no se comprueba; por eso la lista incluye todas las de Spec 017 y las de red comunes.
- DNS: un dominio dentro del alcance puede resolver a una IP fuera de él. No se resuelve nada; se confía en el
  nombre escrito.
