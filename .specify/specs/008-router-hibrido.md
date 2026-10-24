# Spec 008 — Router híbrido (Gemini + DeepHat)

**Estado:** 🟨 En progreso · **Fase:** 2.5 · **Depende de:** 001, 005

## Qué
Un router que decide qué modelo responde cada mensaje: Gemini (nube, rápido) o DeepHat
(local, sin censura). Tres modos: híbrido, local puro, manual.

## Por qué
DeepHat va lento en CPU. Gemini es rápido y potente para el 90% del trabajo; DeepHat entra
cuando Gemini se niega por censura o cuando hay datos sensibles del objetivo.

## Requisitos funcionales
- RF1: Cliente de Gemini (API) que use las mismas herramientas que DeepHat.
- RF2: Modo HÍBRIDO: Gemini primero; si se niega (safety block) → reintenta con DeepHat.
- RF3: Modo LOCAL PURO: solo DeepHat (para engagements con NDA).
- RF4: Modo MANUAL: el usuario elige el modelo por mensaje.
- RF5: Cada respuesta indica qué modelo la generó (ya existe la etiqueta en el frontend).
- RF6: La API key de Gemini se lee de .env (GEMINI_API_KEY), nunca del repo.
- RF7: Si no hay API key, el modo híbrido cae a local puro con aviso claro.

## Requisitos no funcionales
- RNF1: Privacidad: en local puro, NADA sale a la nube (constitución art. II).
- RNF2: Detección de negativa robusta: error de safety O frases de rechazo típicas.
- RNF3: Un solo formato de herramientas traducido a cada modelo.

## Criterios de validación
- [ ] Sin API key, el modo híbrido avisa y usa DeepHat (no revienta).
- [ ] Con API key, modo híbrido usa Gemini y cae a DeepHat si se niega.
- [ ] Modo local puro nunca contacta Gemini.
- [ ] El modo se puede cambiar desde el frontend.

## Nota de honestidad
Este es el componente más complejo (lo advertí en PLAN §10). La detección de "Gemini se negó"
se calibra con pruebas reales. Se entrega funcional con DeepHat garantizado; Gemini requiere
API key del usuario para probarse de verdad.

## Archivos
- `backend/core/llm/gemini_client.py` — cliente de Gemini con tools
- `backend/router.py` — lógica de selección de modelo
- `backend/agent.py` — usar el router
- `backend/main.py` — endpoint para cambiar de modo
- `frontend/js/main.js` — selector de modo
