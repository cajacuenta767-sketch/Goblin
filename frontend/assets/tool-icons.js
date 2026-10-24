// === GOBLIN — Iconos SVG propios para el marketplace (sin logos con copyright) ===
// Cada icono representa la categoría/función de la herramienta.

const TOOL_ICONS = {
  nmap: `<svg viewBox="0 0 24 24" fill="none" stroke="#3ddc84" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M5 5l3 3M16 16l3 3M19 5l-3 3M8 16l-3 3"/></svg>`,
  web: `<svg viewBox="0 0 24 24" fill="none" stroke="#3ddc84" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/></svg>`,
  db: `<svg viewBox="0 0 24 24" fill="none" stroke="#3ddc84" stroke-width="2"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></svg>`,
  key: `<svg viewBox="0 0 24 24" fill="none" stroke="#3ddc84" stroke-width="2"><circle cx="8" cy="8" r="5"/><path d="M11.5 11.5L21 21M17 17l2-2M14 14l2-2"/></svg>`,
  exploit: `<svg viewBox="0 0 24 24" fill="none" stroke="#3ddc84" stroke-width="2"><path d="M13 2L3 14h7l-1 8 10-12h-7z"/></svg>`,
  net: `<svg viewBox="0 0 24 24" fill="none" stroke="#3ddc84" stroke-width="2"><rect x="2" y="3" width="8" height="6" rx="1"/><rect x="14" y="15" width="8" height="6" rx="1"/><path d="M6 9v3a3 3 0 003 3h6"/></svg>`,
  search: `<svg viewBox="0 0 24 24" fill="none" stroke="#3ddc84" stroke-width="2"><circle cx="10" cy="10" r="7"/><path d="M15 15l6 6"/></svg>`,
  wifi: `<svg viewBox="0 0 24 24" fill="none" stroke="#3ddc84" stroke-width="2"><path d="M2 8c6-5 14-5 20 0M5 12c4.5-3.5 9.5-3.5 14 0M8.5 15.5c2-1.5 5-1.5 7 0"/><circle cx="12" cy="19" r="1" fill="#3ddc84"/></svg>`,
};

function toolIcon(name) {
  return TOOL_ICONS[name] || TOOL_ICONS.search;
}
