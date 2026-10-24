# Spec 016 — Marketplace de herramientas de ciberseguridad

**Estado:** 🟨 En progreso · **Depende de:** 001

## Qué
Un panel lateral tipo "extensiones de VS Code" con herramientas de pentest. Cada una muestra
logo, nombre, descripción breve, y un botón para instalar/comprobar. Enfocado en ciberseguridad.

## Por qué
El usuario quiere poder descargar/instalar herramientas de pentest desde GOBLIN, sin salir a
la terminal, con una experiencia visual tipo marketplace.

## Requisitos funcionales
- RF1: Catálogo de herramientas de pentest (nmap, nikto, gobuster, sqlmap, hydra, etc.),
  cada una con: id, nombre, categoría, descripción, paquete apt, icono.
- RF2: El backend detecta si cada herramienta está instalada (which).
- RF3: Botón "Instalar" que ejecuta la instalación vía apt (con aprobación, usa sudo).
- RF4: Panel lateral con tarjetas: logo, nombre, descripción, estado (instalada/no), botón.
- RF5: Filtro por categoría (recon, web, passwords, exploitation, etc.).
- RF6: La instalación muestra progreso/resultado.

## Requisitos no funcionales
- RNF1: Instalar requiere sudo; se hace con aprobación del usuario (seguridad).
- RNF2: Solo herramientas de repos oficiales de Parrot/Debian (apt), nada de fuentes random.
- RNF3: Los iconos son SVG simples propios (no descargar logos externos con copyright).

## Criterios de validación
- [ ] El catálogo lista las herramientas con su estado real (instalada o no).
- [ ] El panel muestra las tarjetas con logo y descripción.
- [ ] Instalar ejecuta apt (validable sin sudo real en el entorno).

## Archivos
- `backend/toolstore.py` — catálogo + detección + instalación
- `backend/main.py` — endpoints /api/toolstore
- `frontend/js/toolstore.js` — panel marketplace
- `frontend/index.html`, `css/layout.css`
- `frontend/assets/tools/*.svg` — iconos
