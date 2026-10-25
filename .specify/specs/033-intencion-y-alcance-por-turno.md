# Spec 033 — Intención y alcance de herramientas por turno

**Estado:** 🟨 Implementada, validación en PC pendiente · **Tipo:** comportamiento · **Depende de:** 009, 022, 025, 032
**Motivo:** al pedir "analiza X", GOBLIN ejecutaba herramientas sobre la computadora (listados,
disco, comandos) sin que se lo pidieran.

## Problema

El modelo recibe siempre todas las herramientas y decide solo cuándo usarlas. Una petición de
análisis o de pregunta se interpreta como acción y dispara listados, escaneos o comandos. El
prompt pide "usar herramientas solo cuando se pida una acción", pero un modelo de 7B no siempre lo
respeta, así que la regla tiene que estar en código.

## Requisitos funcionales

- **RF1.** Cada turno se clasifica por intención:
  - `action`: pide hacer algo (crear, escribir, borrar, mover, copiar, ejecutar, instalar, escanear…).
    Recibe todas las herramientas; las que requieren aprobación siguen pidiéndola.
  - `analysis`: pide analizar, explicar, resumir o revisar. Recibe solo herramientas de lectura
    (`read_file`, `list_dir`, `search_files`) y **solo si el mensaje nombra una ruta o un archivo**.
    Sin ruta, no recibe herramientas: responde en texto y pregunta qué ruta analizar.
  - `chat`: saludos, preguntas generales y cualquier otro caso. Sin herramientas.
- **RF2.** La clasificación es por palabras clave en código (no la decide el modelo).
- **RF3.** Si el modelo intenta llamar una herramienta que el turno no permite, el agente no la
  ejecuta y devuelve al modelo el aviso "no permitida en esta petición; pide la acción explícitamente".
- **RF4.** Las herramientas permitidas se fijan al empezar el turno y valen para todos sus pasos.
- **RF5.** Los controles de aprobación (spec 009), de escaneos (alcance) y de privacidad (spec 025)
  siguen igual. Esta spec solo añade un filtro previo.

## Requisitos no funcionales

- **RNF1.** Sin dependencias nuevas.
- **RNF2.** Clasificar un mensaje no hace llamadas al modelo ni a herramientas.

## Criterios de aceptación

- [x] "analiza mi computadora" → turno `analysis` sin ruta → ninguna herramienta.
- [x] "analiza ~/proyecto/app.py" → solo herramientas de lectura.
- [x] "crea la carpeta pruebas" → turno `action` con todas las herramientas.
- [x] "hola" y "explica qué es nmap" → sin herramientas.
- [x] Una llamada a herramienta fuera de las permitidas no se ejecuta.
- [x] El filtro se aplica en modo local y en streaming.
- [x] Pruebas en `backend/tests/test_intencion.py`.
- [ ] Probado en la PC con DeepHat real (pendiente del usuario).

## Límites

- La clasificación por palabras clave falla en casos ambiguos. Ante la duda, el sistema prefiere
  no ejecutar: pide la ruta o la acción explícita.
- Esta spec no cambia el modelo ni mejora su razonamiento; solo evita acciones no pedidas.
- Las mejoras de la Etapa 1 (perfiles de herramientas, resultados estructurados, memoria del
  engagement, plan con confirmación) quedan para specs posteriores.
