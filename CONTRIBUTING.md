# Cómo contribuir a GOBLIN

GOBLIN se desarrolla con **Spec-Driven Development (SDD)**. Nada se programa sin una
especificación. Si vas a contribuir (humano o IA), sigue este flujo.

## Antes de empezar
1. Lee `.specify/constitution.md` — las reglas inviolables (son la autoridad máxima).
2. Lee `AGENTS.md` — cómo contribuir sin romper nada.
3. Mira `ESTADO.md` y `.specify/tasks.md` — qué está hecho y qué falta.

## Flujo SDD
```
constitución → spec → clarificar → plan → tareas → implementar → validar → iterar
```
1. **Spec:** crea `.specify/specs/NNN-nombre.md` describiendo QUÉ y por qué.
2. **Tareas:** añade las tareas a `.specify/tasks.md`.
3. **Implementa:** respetando las capas (Frontend → API → Core → Tools → Datos).
4. **Valida:** corre `./scripts/test.sh`. Añade tests para lo nuevo.
5. **Commit:** mensaje en español, imperativo ("Agrega X").

## Reglas rápidas
- Servidor solo en 127.0.0.1. Secretos solo en `.env` (nunca al repo).
- Acciones destructivas piden aprobación. La lista negra de comandos se respeta siempre.
- Un modelo primero (DeepHat); el router híbrido ya existe pero no es el centro.
- Todo debe correr en CPU con 16 GB RAM.
- Añade tests en `backend/tests/` para cualquier lógica nueva.

## Tests
```bash
./scripts/test.sh
```
Los tests también corren automáticamente en GitHub en cada push (ver `.github/workflows/`).
