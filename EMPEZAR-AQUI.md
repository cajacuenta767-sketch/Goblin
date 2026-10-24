# 👋 EMPEZAR AQUÍ — Lee esto primero

> **Si eres una IA (Antigravity, Claude Code, Cursor, etc.) o un desarrollador** que acaba
> de abrir este proyecto: este documento te orienta en 2 minutos. Léelo completo antes de
> tocar nada.

---

## ¿Qué es esto?

**GOBLIN** es un IDE de escritorio local con IA agéntica para **ciberseguridad y pentesting**,
pensado para correr en **Parrot OS**. Un chat de IA que puede crear/mover/borrar archivos y
ejecutar comandos en la PC, usando un modelo local sin censura (**DeepHat-V1-7B**) vía Ollama.

El proyecto se construye con **SDD (Spec-Driven Development)**: todo nace de una especificación.

---

## 📂 Mapa de documentos (en qué orden leerlos)

| Orden | Archivo | Qué contiene |
|-------|---------|--------------|
| 1 | `EMPEZAR-AQUI.md` | Este archivo. Orientación rápida. |
| 2 | `.specify/constitution.md` | **Reglas inviolables** del proyecto. La autoridad máxima. |
| 3 | `AGENTS.md` | Instrucciones para ti (la IA): cómo contribuir sin romper nada. |
| 4 | `ESTADO.md` | Qué está hecho, qué falta, dónde está cada cosa. |
| 5 | `ARQUITECTURA.md` | Stack, capas, estructura de carpetas, base de datos. |
| 6 | `PLAN.md` | Roadmap completo por fases (la visión). |
| 7 | `.specify/specs/*.md` | Las especificaciones por funcionalidad. |
| 8 | `.specify/tasks.md` | Tareas concretas (✅/⬜) derivadas de las specs. |

---

## 🧭 Reglas de oro (resumen de la constitución)

1. **Local-first:** todo corre en la máquina. Nada sale a la nube salvo Gemini (opt-in).
2. **Seguridad:** acciones destructivas piden aprobación; hay lista negra de comandos.
3. **Capas:** Frontend → API → Core → Tools → Datos. No se saltan.
4. **Un modelo primero:** DeepHat solo. Gemini/híbrido llega después.
5. **Hardware:** debe correr en CPU con 16 GB RAM (i7-10700, sin GPU dedicada).
6. **SDD:** nada se programa sin spec. Lo nuevo se añade primero como tarea.

---

## ▶️ Cómo instalar y correr (en Parrot OS)

```bash
# 1. Instalar todo (Ollama + dependencias + modelo DeepHat ~4.5 GB)
chmod +x scripts/*.sh
./scripts/install.sh

# 2. Arrancar
./scripts/run.sh

# 3. Abrir en el navegador
#    http://127.0.0.1:8800
```

**Requisitos:** Linux (Parrot OS), Python 3.11+, 16 GB RAM, ~6 GB de disco libre.

---

## 📊 Estado actual (resumen)

- ✅ **Backend** completo y probado: agente, herramientas de archivos/shell, API, aprobaciones.
- ✅ **Frontend** funcional: chat, explorador, aprobaciones, barra de estado (sin Monaco aún).
- ✅ **Scripts** de instalación y arranque para Parrot.
- ⬜ **Falta probar** el chat con DeepHat real (requiere Ollama + modelo en la PC).
- ⬜ **Próximas specs:** terminal pty, persistencia, hallazgos/informe, router Gemini, voz.

Ver `ESTADO.md` para el detalle completo.

---

## 🛠️ Si vas a seguir desarrollando (IA o humano)

1. Lee la constitución y AGENTS.md.
2. Mira `ESTADO.md` y `.specify/tasks.md` para ver qué sigue.
3. La próxima tarea pendiente es: **validar el chat con DeepHat** y luego **Spec 003 (terminal pty)**.
4. Toda funcionalidad nueva: primero una spec en `.specify/specs/`, luego tareas, luego código.
5. Respeta las capas y las convenciones de `ARQUITECTURA.md`.

---

## 🔗 Subir a GitHub

El repo destino es: `https://github.com/cajacuenta767-sketch/Goblin`

```bash
./scripts/subir-github.sh
```

O manualmente, ver `ESTADO.md` sección "Subir a GitHub".
