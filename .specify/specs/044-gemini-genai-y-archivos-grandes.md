# Spec 044 — Gemini con google-genai y archivos grandes visibles

**Estado:** 🟨 Implementado · pruebas ✅ y E2E en Chromium ✅ · ⬜ PC: Gemini real con tu clave · **Tipo:** funcionalidad + correcciones · **Depende de:** 008, 018, 037, 043
**Motivo:** (1) el cliente de Gemini usa `google-generativeai`, paquete legado: Google retiró su soporte el
30-nov-2025 y recomienda `google-genai`. El modelo por defecto `gemini-1.5-flash` ya no es el de referencia.
(2) El usuario no puede ver archivos grandes: el adjunto rechaza más de 200 KB y el editor abre los archivos
cortados a 30 000 caracteres. **Guardar un archivo abierto así lo sobrescribe y borra el resto.**

## Justificación de la dependencia (Constitución IV.4)

- `google-genai` (SDK oficial de Google). Sustituye a `google-generativeai`, que está legado. Sigue siendo
  opcional: sin API key o sin librería, el router cae a DeepHat.
- Modelo por defecto `gemini-3.8-flash`, según la guía oficial de migración y la lista de modelos
  (comprobado el 24-oct-2026). Se cambia con `GEMINI_MODEL`.

## Requisitos funcionales

- **RF1 · Gemini con google-genai.** `core/llm/gemini_client.py` usa `from google import genai` y
  `client.models.generate_content(model, contents, config)`. Las herramientas de GOBLIN se declaran como
  `FunctionDeclaration` con su esquema JSON. La respuesta mantiene la forma del agente (texto y `tool_calls`).
  Una respuesta vacía o bloqueada lanza error, y el router cae a DeepHat.
- **RF2 · El editor ve el archivo completo.** `/api/file` devuelve el contenido entero (hasta 5 MB). Más de 5 MB
  se rechaza con un mensaje claro en lugar de cortarlo. Guardar nunca escribe una versión recortada.
- **RF3 · Adjuntos grandes.** El botón + acepta textos de hasta 5 MB. Hasta 16 KB se pegan en el campo como hoy.
  Más grandes se guardan en `workspace/adjuntos/<nombre>`, se abren en una pestaña del editor y el campo recibe
  una línea con la ruta y el número de líneas. El modelo no recibe el archivo entero.
- **RF4 · Lectura por tramos para el modelo.** `read_file` acepta `desde` (línea inicial, base 1) y `lineas`
  (por defecto 150, máximo 400). Cada respuesta tiene como máximo 5 000 caracteres y, si queda más archivo,
  indica la línea siguiente. Un archivo pequeño (≤150 líneas y ≤5 000 caracteres) se devuelve completo, como hoy.

## Criterios de aceptación

- [x] Un archivo de 102 KB abierto en el editor muestra sus 3 000 líneas; guardar sin cambios deja el archivo igual (pruebas y E2E).
- [x] Un archivo de más de 5 MB no se abre y el editor dice por qué.
- [x] Un adjunto de 231 KB aparece en una pestaña del editor completo y el campo recibe la ruta, no el texto entero (E2E).
- [x] `read_file` con `desde=2001, lineas=150` devuelve esas líneas y la indicación de continuar.
- [x] El cliente de Gemini construye herramientas válidas con `google-genai` y lee texto y llamadas a herramientas
      (pruebas con respuesta simulada con la forma real del SDK).
- [x] Sin respuesta utilizable de Gemini, el cliente lanza error y el agente responde con DeepHat.
- [x] Pruebas en `backend/tests/test_archivos_grandes.py` (12) y `backend/tests/test_gemini_cliente.py` (8); E2E de adjunto
      y guardado en Chromium (9 comprobaciones).

## Límites

- Los nombres de modelo cambian. Si `GEMINI_MODEL` no existe en la cuenta, Gemini falla y el router usa DeepHat.
  No se valida contra la API real desde este entorno (sin clave de API).
- Un archivo binario adjuntado se lee como texto con caracteres de reemplazo; no se decodifica.
- Los adjuntos quedan en `workspace/adjuntos/` y el usuario los borra cuando quiera.
