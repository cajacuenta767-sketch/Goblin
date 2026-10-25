# Spec 046 — Diagnóstico del equipo y velocidad del modelo local

**Estado:** 🟨 Implementado · validado sin Ollama y con API simulada ✅ · ⬜ PC: informe real y tokens/s en tu i7-10700 · **Tipo:** herramienta de diagnóstico · **Depende de:** 032, 044, 045 · **Constitución:** V (hardware objetivo)

**Motivo:** La constitución fija el equipo de referencia (i7-10700, 8 núcleos físicos, 16 GB RAM, sin GPU dedicada, Parrot 7.4), pero la velocidad del modelo local nunca se midió en él. Las decisiones de contexto, hilos y modelo deben basarse en mediciones de ese equipo y no en estimaciones.

## Requisitos funcionales

- **RF1 · Informe de solo lectura.** `scripts/diagnostico-pc.sh` informa procesador, memoria, disco, gráficos, versión de Ollama, modelos instalados, versión de google-genai y las variables de rendimiento de `.env`.
- **RF2 · Benchmark.** Mide tokens por segundo del modelo (por defecto DeepHat Q4_K_M) con el `num_ctx` configurado y con 4, 8 y 16 hilos. Cada prueba genera 96 tokens por la API local de Ollama.
- **RF3 · Salida.** Se muestra en pantalla y se guarda en `workspace/diagnostico-pc.txt`, carpeta que git ignora.
- **RF4 · Sin efectos colaterales.** No imprime claves (`GEMINI_API_KEY` nunca aparece), no usa sudo, no instala nada y no cambia configuración. Lo único que escribe es el informe.
- **RF5 · Tolerancia a fallos.** Si Ollama no responde o no está instalado, el informe de hardware se genera igual y el benchmark se marca como omitido.

## Criterios de aceptación

- [x] Sin Ollama en el entorno de desarrollo: genera el informe y omite el benchmark (ejecutado).
- [x] Con una API de Ollama simulada: calcula tokens por segundo correctamente (96 tokens en 20 s = 4,80 tokens/s) y no falla si falta `ollama ps`.
- [ ] En tu PC: informe completo y tokens/s para 4, 8 y 16 hilos.
- [ ] Con esos números se decide `num_ctx` e hilos (ver propuesta).

## Propuesta preliminar (a confirmar con el informe real)

- **Modelo.** Mantener DeepHat Q4_K_M, de unos 4–5 GB en RAM. Cabe en 16 GB junto con Parrot. No proponer modelos más grandes sin medirlos: en CPU pueden ser muy lentos (constitución V.3).
- **Contexto.** Mantener 4096. Subir a 8192 solo si, con el modelo cargado, quedan al menos 6 GB libres y una respuesta corta tarda menos de unos 30 s. Es una regla a validar, no un dato medido.
- **Hilos.** 8 (núcleos físicos) por defecto. Cambiar a 4 o 16 solo si el benchmark demuestra que es más rápido.
- **Ollama.** `run.sh` ya fija `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_MAX_LOADED_MODELS=1` y `OLLAMA_FLASH_ATTENTION=1`. Candidato a medir: `OLLAMA_KV_CACHE_TYPE=q8_0`, que reduce la memoria del contexto. Requiere atención rápida y hay que confirmar que lo soporta tu versión de Ollama.
- **GPU integrada (UHD 630).** Por defecto, Ollama en Linux no la usa para inferencia. Se asume CPU.
- **Calidad.** La mejora de razonamiento sin costo de hardware es Gemini como cabeza en modo híbrido (Spec 045). El modelo local queda para datos sensibles.

## Límites

- Mide velocidad, no calidad de respuesta.
- Los resultados dependen de la carga del sistema en el momento de la prueba. Conviene cerrar navegador y otras apps pesadas antes de ejecutarla.
- En el entorno de desarrollo no hay Ollama ni la GPU del equipo real. Las cifras de rendimiento solo las dará el PC.
