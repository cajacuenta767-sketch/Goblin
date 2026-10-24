// === GOBLIN — Marketplace de herramientas de ciberseguridad ===

const ToolStore = {
  el: { panel: null, grid: null, filters: null, close: null, btn: null },
  tools: [],
  categories: [],
  activeCategory: "all",

  CAT_LABEL: {
    all: "Todas", recon: "Recon", web: "Web", passwords: "Contraseñas",
    exploitation: "Explotación", network: "Red", wireless: "WiFi",
  },

  init() {
    this.el.panel = document.getElementById("toolstore");
    this.el.grid = document.getElementById("tsGrid");
    this.el.filters = document.getElementById("tsFilters");
    this.el.close = document.getElementById("tsClose");
    this.el.btn = document.getElementById("toolstoreBtn");

    this.el.btn.addEventListener("click", () => this.open());
    this.el.close.addEventListener("click", () => this.hide());
    this.el.panel.addEventListener("click", (e) => { if (e.target === this.el.panel) this.hide(); });
  },

  async open() {
    this.el.panel.classList.add("show");
    await this.load();
  },

  hide() { this.el.panel.classList.remove("show"); },

  async load() {
    try {
      const r = await API.toolstore();
      this.tools = r.tools || [];
      this.categories = r.categories || [];
      this.renderFilters();
      this.render();
    } catch (e) {
      this.el.grid.innerHTML = `<div class="ts-empty">No se pudo cargar el catálogo: ${e.message}</div>`;
    }
  },

  renderFilters() {
    const cats = ["all", ...this.categories];
    this.el.filters.innerHTML = "";
    for (const c of cats) {
      const b = document.createElement("span");
      b.className = "ts-filter" + (c === this.activeCategory ? " active" : "");
      b.textContent = this.CAT_LABEL[c] || c;
      b.addEventListener("click", () => { this.activeCategory = c; this.renderFilters(); this.render(); });
      this.el.filters.appendChild(b);
    }
  },

  // Icono de respaldo según categoría (cuando no hay logo oficial o no carga)
  fallbackIcon(cat) {
    const map = { recon: "search", web: "web", passwords: "key",
      exploitation: "exploit", network: "net", wireless: "wifi" };
    return toolIcon(map[cat] || "search");
  },

  render() {
    const list = this.activeCategory === "all"
      ? this.tools
      : this.tools.filter((t) => t.category === this.activeCategory);
    this.el.grid.innerHTML = "";
    for (const t of list) {
      const card = document.createElement("div");
      card.className = "ts-card";
      // Logo oficial en vivo; si no hay o falla, icono propio de la categoría.
      const logoHtml = t.logo
        ? `<img class="ts-logo" src="${t.logo}" alt="${t.name}" loading="lazy">`
        : `<span class="ts-fallback">${this.fallbackIcon(t.category)}</span>`;
      card.innerHTML = `
        <div class="ts-icon">${logoHtml}</div>
        <div class="ts-info">
          <div class="ts-name">${t.name}</div>
          <div class="ts-desc"></div>
          <a class="ts-source" href="${t.url}" target="_blank" rel="noopener">↗ Última versión oficial</a>
        </div>
        <div class="ts-actions">
          <button class="ts-btn ${t.installed ? "installed" : ""}" ${t.installed ? "disabled" : ""}>
            ${t.installed ? "✓ Instalada" : "Instalar (apt)"}
          </button>
          <a class="ts-dl" href="${t.url}" target="_blank" rel="noopener" title="Descargar de la fuente oficial">⬇ Descargar</a>
        </div>`;
      card.querySelector(".ts-desc").textContent = t.desc;
      // Si el logo oficial no carga, usar el icono propio
      const img = card.querySelector(".ts-logo");
      if (img) img.addEventListener("error", () => {
        img.outerHTML = `<span class="ts-fallback">${this.fallbackIcon(t.category)}</span>`;
      });
      const btn = card.querySelector(".ts-btn");
      if (!t.installed) btn.addEventListener("click", () => this.install(t, btn));
      this.el.grid.appendChild(card);
    }
    if (!list.length) this.el.grid.innerHTML = '<div class="ts-empty">Nada en esta categoría.</div>';
  },

  async install(tool, btn) {
    if (!confirm(`Instalar ${tool.name}?\n\nSe ejecutará: sudo apt install ${tool.id}\n(puede pedir tu contraseña en la terminal donde corre GOBLIN)`)) return;
    btn.textContent = "Instalando…";
    btn.disabled = true;
    try {
      const r = await API.installTool(tool.id);
      if (r.ok || r.installed) {
        btn.textContent = "✓ Instalada";
        btn.classList.add("installed");
        tool.installed = true;
      } else {
        btn.textContent = "Reintentar";
        btn.disabled = false;
        alert("No se pudo instalar: " + (r.error || r.message || "error") +
              "\n\nPuede que necesites instalarla manualmente: sudo apt install " + tool.id);
      }
    } catch (e) {
      btn.textContent = "Reintentar";
      btn.disabled = false;
      alert("Error: " + e.message);
    }
  },
};
