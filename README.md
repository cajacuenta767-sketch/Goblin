<div align="center">

# ⬢ GOBLIN

**IDE local con IA sin censura para ciberseguridad y pentesting**

Un asistente agéntico que corre 100% en tu máquina, con control total del sistema,
pensado para ingenieros de ciberseguridad.

</div>

---

## ¿Qué es GOBLIN?

GOBLIN es una aplicación de escritorio local (estilo IDE) con un chat de IA agéntico que
puede crear, mover y borrar archivos, ejecutar comandos y automatizar tareas de pentesting
directamente en tu PC. Usa un modelo local sin censura (**DeepHat-V1-7B**) vía Ollama, así
que nada sale a la nube.

> ⚠️ **Uso responsable:** GOBLIN ejecuta comandos reales en tu sistema. Úsalo solo contra
> objetivos para los que tengas autorización explícita por escrito. Los autores no se hacen
> responsables del mal uso.

## Características

- 🤖 **Chat agéntico** con un modelo local sin censura (DeepHat-V1-7B)
- 📂 **Control del sistema**: crear, mover, copiar, borrar archivos y carpetas
- 💻 **Terminal integrada** para ejecutar herramientas de pentest
- ✏️ **Editor de código** (Monaco) con vista de diferencias
- 🛡️ **Aprobaciones** para acciones peligrosas (configurable)
- 🎯 **Integración con Polybar**: publica el target activo a tu barra de Parrot
- 📊 **Hallazgos e informes** de pentest (en desarrollo)
- 🔒 **100% local y privado** (modo híbrido con Gemini opcional)

## Requisitos

- **SO:** Linux (probado en Parrot OS)
- **Python:** 3.11 o superior
- **RAM:** 16 GB recomendado (para el modelo de 7B)
- **Ollama:** se instala automáticamente
- **Espacio:** ~6 GB para el modelo

## Instalación

```bash
git clone https://github.com/TU_USUARIO/goblin.git
cd goblin
cp .env.example .env
chmod +x scripts/*.sh
./scripts/install.sh
```

## Uso

```bash
./scripts/run.sh
```

Luego abre `http://127.0.0.1:8000` en tu navegador.

## Arquitectura

Backend en **Python (FastAPI)** + **SQLite**, frontend en **HTML/CSS/JS vanilla** con
**Monaco** y **xterm.js**. Ver [ARQUITECTURA.md](ARQUITECTURA.md) para el detalle técnico
y [PLAN.md](PLAN.md) para el roadmap.

## Estado del proyecto

🚧 En desarrollo activo. Ver [PLAN.md](PLAN.md) para las fases.

## Licencia

Uso personal. Pendiente de definir licencia.
