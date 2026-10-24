# Spec 022 — Tool-calling real para DeepHat + respaldo por texto

> Copiar a `.specify/specs/022-tool-calling-fallback.md` en el repo.

## Problema (reportado por el usuario)

Al chatear con GOBLIN (app nativa, modo Local/DeepHat), un mensaje simple
("hola") produjo como respuesta el JSON crudo de una llamada a herramienta
en vez de texto o de una ejecución real:

```
{"command": "whoami", "cwd": "/home/user"}
```

## Causa raíz

DeepHat-V1-7B está basado en Qwen2.5-Coder-7B, que tiene un formato de
tool-calling entrenado (`<tool_call>{"name":...,"arguments":...}</tool_call>`).
El modelo se descargó con `ollama run hf.co/mradermacher/DeepHat-V1-7B-GGUF:...`,
sin un Modelfile propio — Ollama le aplicó una plantilla (`TEMPLATE`) genérica
que no sabe interpretar ese formato. Por eso `resp.message.tool_calls` siempre
llega vacío, y el bucle del agente (`agent.py`) trata el contenido como texto
normal y lo muestra tal cual en el chat.

Esto confirma el riesgo ya anotado en `PLAN.md` §10.1, punto 1: "verificar que
el GGUF concreto conserve la plantilla de tools... si falla, plan B: tool-calling
por texto". El riesgo se materializó.

## Solución (3 capas, en orden de prioridad)

1. **Modelfile propio para DeepHat** (`Modelfile.deephat-tools`) con el
   `TEMPLATE` real de Qwen2.5 (sacado y verificado con
   `ollama show qwen2.5-coder:1.5b-instruct --modelfile`), creado como
   `deephat-tools` vía `ollama create`. Esta es la solución real: hace que
   Ollama pueble `tool_calls` nativo, igual que con cualquier modelo oficial.
2. **Parser de respaldo** (`backend/core/text_toolcall.py`) que reconoce el
   formato `<tool_call>` de Qwen y JSON suelto, para los casos en que el
   modelo no siga el formato al pie de la letra. Se registra como advertencia
   cuando se usa — nunca en silencio — y pasa por las mismas reglas de
   aprobación/seguridad que una tool_call nativa.
3. **Ajuste del `SYSTEM_PROMPT`**: instrucción explícita de no usar
   herramientas ante un saludo o mensaje sin tarea concreta.

## Validación

- [ ] `ollama run deephat-tools "..."` no imprime JSON crudo en respuestas
      conversacionales.
- [ ] Una petición de acción real dispara la caja de aprobación (o ejecución
      directa si el nivel de aprobación lo permite), no texto plano.
- [ ] Los logs muestran advertencia cuando se usa la capa 2 (indica que la
      capa 1 falló para ese mensaje puntual — sirve para medir qué tan
      seguido pasa).
- [ ] Tests nuevos en `backend/tests/` para `parse_text_toolcall()`: caso
      `<tool_call>`, caso JSON suelto, caso texto normal sin tool (debe
      devolver `None`).

## Changelog (añadir a PLAN.md)

- 🔵 **v1.4** — Diagnosticado y resuelto el riesgo #1 de §10.1: DeepHat no
  usaba tool-calling nativo de Ollama por falta de `TEMPLATE` propio en el
  Modelfile. Creada Spec 022: Modelfile `deephat-tools` con plantilla de
  Qwen2.5 (solución raíz) + parser de respaldo por texto (red de seguridad)
  + ajuste de SYSTEM_PROMPT para no disparar herramientas ante saludos.
