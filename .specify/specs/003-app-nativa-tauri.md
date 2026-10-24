# Spec 003 — App nativa de escritorio (Tauri) para Parrot OS

**Estado:** 🟨 En progreso · **Fase:** 7 (adelantada) · **Depende de:** 001, 002

## Qué (objetivo)

Convertir GOBLIN en una **aplicación de escritorio nativa** para Parrot OS: una ventana
propia (no el navegador), con icono, lanzable desde el menú de aplicaciones, y un instalador
`.deb`. El usuario pidió explícitamente una app para Linux, NO un formato web.

## Por qué

El usuario nunca pidió que GOBLIN se abriera en el navegador. Pidió una app nativa de Parrot.
Tauri envuelve el frontend+backend existentes en una ventana nativa sin reescribir nada.

## Decisión de arquitectura

- **Tauri v2** como envoltorio nativo (ligero, usa el webkit del sistema, genera `.deb`).
- El **backend Python (FastAPI) se mantiene igual**: la app Tauri lo arranca como proceso
  hijo al abrir, y la ventana nativa carga `http://127.0.0.1:8800`.
- **No se reescribe** ni el frontend ni el backend. Tauri es solo la cáscara nativa.
- Al cerrar la ventana, la app detiene el backend Python.

```
┌─────────────────────────────────────────┐
│  App nativa GOBLIN (Tauri, ventana GTK) │
│  ┌───────────────────────────────────┐  │
│  │ WebView → http://127.0.0.1:8800   │  │  ← el frontend que ya existe
│  └───────────────────────────────────┘  │
│  Al abrir: lanza el backend Python      │
│  Al cerrar: detiene el backend          │
└─────────────────────────────────────────┘
          │ (proceso hijo)
   ┌──────▼──────────────┐
   │ backend Python      │  ← sin cambios
   │ (FastAPI + Ollama)  │
   └─────────────────────┘
```

## Requisitos funcionales

- RF1: Al abrir la app, arranca el backend Python automáticamente.
- RF2: La ventana nativa muestra la interfaz de GOBLIN (carga el servidor local).
- RF3: Al cerrar la ventana, el backend Python se detiene (no quedan procesos zombi).
- RF4: Icono propio de GOBLIN y entrada en el menú de aplicaciones de Parrot.
- RF5: Instalador `.deb` instalable con `sudo dpkg -i` / `apt install`.
- RF6: Ventana redimensionable, tamaño inicial razonable (ej. 1400x900).

## Requisitos no funcionales

- RNF1: Ligero (Tauri usa webkit del sistema, no empaqueta Chromium). Importante por los 16 GB.
- RNF2: El build se hace en la PC del usuario (Parrot tiene las deps). Aquí solo se prepara.
- RNF3: No romper el modo navegador: seguir pudiendo correr con `run.sh` para desarrollo.

## Dependencias del sistema (para compilar en Parrot)

- Rust + Cargo (rustup)
- `libwebkit2gtk-4.1-dev`, `libgtk-3-0`, `build-essential`, `libssl-dev`, `libayatana-appindicator3-dev`, `librsvg2-dev`
- Node.js (para la CLI de Tauri)

## Criterios de validación

- [ ] `./scripts/build.sh` compila la app sin errores en Parrot.
- [ ] Se genera un `.deb` en `src-tauri/target/release/bundle/deb/`.
- [ ] Instalar el `.deb` crea la entrada en el menú y el icono.
- [ ] Abrir GOBLIN desde el menú muestra la ventana nativa con la interfaz.
- [ ] Cerrar la ventana detiene el backend (verificar con `ps aux | grep uvicorn`).
- [ ] El modo navegador (`run.sh`) sigue funcionando para desarrollo.

## Archivos a crear

```
src-tauri/
├── Cargo.toml
├── tauri.conf.json
├── build.rs
├── src/main.rs          # arranca backend Python + abre ventana
└── icons/               # iconos de la app
scripts/build.sh         # compila la app nativa + .deb
scripts/dev-nativo.sh    # modo desarrollo con ventana nativa
```

## Fuera de alcance

- Compilar el binario en este entorno de nube (no tiene Rust/webkit). Se compila en Parrot.
- Auto-actualización desde GitHub Releases (iteración futura).
