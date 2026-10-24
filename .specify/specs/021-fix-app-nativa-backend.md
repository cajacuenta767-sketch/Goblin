# Spec 021 — Fix: la app nativa no arrancaba el backend

**Estado:** ✅ Corregido · **Tipo:** bugfix · **Depende de:** 003

## Problema (reportado por el usuario)
Al abrir la app nativa instalada, "parece un HTML nomás": se ve la interfaz pero ningún
botón funciona.

## Causa raíz
El `main.rs` usaba `std::env::current_dir()` para localizar el proyecto. En una app
instalada (abierta desde el menú), el directorio actual es `/` o la home, NO la carpeta del
proyecto. Por eso buscaba el backend en `/backend/main.py` (inexistente), el backend Python
nunca arrancaba, y la ventana cargaba 127.0.0.1:8800 sin nadie escuchando → UI muerta.

Además, esperaba 1.5s fijos antes de cargar la URL; en CPU lenta el backend puede tardar más.

## Solución
- `find_project_dir()`: busca el proyecto en varias rutas (GOBLIN_HOME, cwd, junto al
  ejecutable, ~/goblin) y usa la primera que tenga backend/main.py.
- `wait_for_backend()`: espera hasta ~30s a que el backend responda en el puerto, en vez de
  un sleep fijo.
- Aviso en build.sh y docs: el proyecto debe estar en ~/goblin o definir GOBLIN_HOME.

## Criterios de validación
- [x] El código compila (estructura verificada; cargo build en Parrot).
- [ ] Al abrir la app instalada con el proyecto en ~/goblin, los botones funcionan.
  (Validación final en la PC del usuario.)

## Archivos
- `src-tauri/src/main.rs`, `scripts/build.sh`, `README.md`
