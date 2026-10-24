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

  render() {
    const list = this.activeCategory === "all"
      ? this.tools
      : this.tools.filter((t) => t.category === this.activeCategory);
    this.el.grid.innerHTML = "";
    for (const t of list) {
      const card = document.createElement("div");
      card.className = "ts-card";
      card.innerHTML = `
        <div class="ts-icon">${toolIcon(t.icon)}</div>
        <div class="ts-info">
          <div class="ts-name">${t.name}</div>
          <div class="ts-desc"></div>
        </div>
        <button class="ts-btn ${t.installed ? "installed" : ""}" ${t.installed ? "disabled" : ""}>
          ${t.installed ? "✓ Instalada" : "Instalar"}
        </button>`;
      card.querySelector(".ts-desc").textContent = t.desc;
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
