// === GOBLIN — Marketplace de herramientas de ciberseguridad (Spec 016 / 026) ===
// Instalar: GOBLIN escribe el comando en la terminal integrada. La contraseña de sudo
// la pide la propia terminal; GOBLIN no la recibe ni la guarda.
// Descargar / web oficial: el backend abre la URL del catálogo. No usa target="_blank",
// que no abre nada en la ventana nativa de Tauri.

const ToolStore = {
  el: { panel: null, grid: null, filters: null, close: null, btn: null, refresh: null },
  tools: [],
  categories: [],
  activeCategory: "all",

  CAT_LABEL: {
    all: "Todas", recon: "Recon", osint: "OSINT", web: "Web", passwords: "Contraseñas",
    exploitation: "Explotación", post: "Post-explotación", network: "Red", wireless: "WiFi",
    forensics: "Forense", reverse: "Ingeniería inversa",
  },

  init() {
    this.el.panel = document.getElementById("toolstore");
    this.el.grid = document.getElementById("tsGrid");
    this.el.filters = document.getElementById("tsFilters");
    this.el.close = document.getElementById("tsClose");
    this.el.btn = document.getElementById("toolstoreBtn");

    // ↻ Actualizar: vuelve a leer qué está instalado
    this.el.refresh = document.createElement("span");
    this.el.refresh.className = "ts-refresh";
    this.el.refresh.title = "Volver a comprobar qué está instalado";
    this.el.refresh.textContent = "↻ Actualizar";
    this.el.close.parentNode.insertBefore(this.el.refresh, this.el.close);

    this.el.btn.addEventListener("click", () => this.open());
    this.el.close.addEventListener("click", () => this.hide());
    this.el.refresh.addEventListener("click", () => this.load());
    this.el.panel.addEventListener("click", (e) => { if (e.target === this.el.panel) this.hide(); });
  },

  async open() {
    this.el.panel.classList.add("show");
    await this.load();
  },

  hide() { this.el.panel.classList.remove("show"); },

  _empty(text) {
    this.el.grid.innerHTML = "";
    const d = document.createElement("div");
    d.className = "ts-empty";
    d.textContent = text;
    this.el.grid.appendChild(d);
  },

  async load() {
    this._empty("Leyendo catálogo…");
    try {
      const r = await API.toolstore();
      this.tools = r.tools || [];
      this.categories = r.categories || [];
      this.renderFilters();
      this.render();
    } catch (e) {
      this._empty("No se pudo cargar el catálogo: " + e.message);
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
    const map = { recon: "search", osint: "search", web: "web", passwords: "key",
      exploitation: "exploit", post: "exploit", network: "net", wireless: "wifi",
      forensics: "search", reverse: "exploit" };
    return toolIcon(map[cat] || "search");
  },

  fallbackEl(cat) {
    const s = document.createElement("span");
    s.className = "ts-fallback";
    s.innerHTML = this.fallbackIcon(cat);   // SVG propio de GOBLIN, no viene del catálogo
    return s;
  },

  // Logo oficial en vivo; si no hay o falla, icono propio de la categoría
  iconEl(t) {
    if (!t.logo) return this.fallbackEl(t.category);
    const img = document.createElement("img");
    img.className = "ts-logo";
    img.alt = t.name;
    img.loading = "lazy";
    img.src = t.logo;
    img.addEventListener("error", () => img.replaceWith(this.fallbackEl(t.category)));
    return img;
  },

  render() {
    const list = this.activeCategory === "all"
      ? this.tools
      : this.tools.filter((t) => t.category === this.activeCategory);
    this.el.grid.innerHTML = "";
    if (!list.length) { this._empty("Nada en esta categoría."); return; }
    for (const t of list) this.el.grid.appendChild(this.card(t));
  },

  card(t) {
    const card = document.createElement("div");
    card.className = "ts-card";
    card.innerHTML = `
      <div class="ts-icon"></div>
      <div class="ts-info">
        <div class="ts-name"></div>
        <div class="ts-desc"></div>
        <a class="ts-source" href="#" title="Abrir la web oficial">↗ Última versión oficial</a>
      </div>
      <div class="ts-actions">
        <button class="ts-btn ts-install"></button>
        <button class="ts-dl" title="Abrir la fuente oficial en tu navegador">⬇ Descargar</button>
      </div>
      <div class="ts-confirm" hidden></div>
      <div class="ts-msg"></div>`;

    // Textos del catálogo con textContent (nunca innerHTML)
    card.querySelector(".ts-name").textContent = t.name;
    card.querySelector(".ts-desc").textContent = t.desc;
    card.querySelector(".ts-icon").appendChild(this.iconEl(t));

    // Etiqueta si el nombre de paquete no está comprobado
    if (t.pkg && !t.verified) {
      const badge = document.createElement("span");
      badge.className = "ts-badge";
      badge.title = "Nombre de paquete no comprobado en Ubuntu/Debian; puede fallar";
      badge.textContent = "pkg sin verificar";
      card.querySelector(".ts-name").appendChild(badge);
    }

    const installBtn = card.querySelector(".ts-install");
    const msg = card.querySelector(".ts-msg");
    if (t.installed) {
      installBtn.textContent = "✓ Instalada";
      installBtn.classList.add("installed");
      installBtn.disabled = true;
    } else if (t.command) {
      installBtn.textContent = "Instalar";
      installBtn.addEventListener("click", () => this.showConfirm(t, card));
    } else {
      installBtn.remove();
      const manual = document.createElement("div");
      manual.className = "ts-manual";
      manual.textContent = "Solo descarga manual (no está en apt)";
      card.querySelector(".ts-actions").prepend(manual);
    }

    card.querySelector(".ts-source").addEventListener("click", (e) => {
      e.preventDefault();
      this.openUrl(t, msg);
    });
    card.querySelector(".ts-dl").addEventListener("click", () => this.openUrl(t, msg));
    return card;
  },

  // Confirmación dentro de la tarjeta (sustituye al confirm() nativo, Spec 026 RF1)
  showConfirm(t, card) {
    const box = card.querySelector(".ts-confirm");
    if (!box.hidden) { box.hidden = true; return; }   // segundo clic: cierra
    box.innerHTML = "";

    const intro = document.createElement("div");
    intro.textContent = "Se enviará a la terminal de GOBLIN:";
    const code = document.createElement("code");
    code.textContent = t.command;
    const note = document.createElement("div");
    note.textContent = "Te pedirá tu contraseña de sudo allí. GOBLIN no la recibe ni la guarda.";

    const row = document.createElement("div");
    row.className = "ts-confirm-row";
    const ok = document.createElement("button");
    ok.className = "ts-btn";
    ok.textContent = "Confirmar";
    const no = document.createElement("button");
    no.className = "ts-btn ghost";
    no.textContent = "Cancelar";
    row.append(ok, no);
    box.append(intro, code, note, row);
    box.hidden = false;

    no.addEventListener("click", () => { box.hidden = true; });
    ok.addEventListener("click", () => { box.hidden = true; this.install(t, card); });
  },

  // Pide al backend el comando validado y lo escribe en la terminal (Spec 026 RF2)
  async install(t, card) {
    const msg = card.querySelector(".ts-msg");
    const btn = card.querySelector(".ts-install");
    this.setMsg(msg, "Preparando el comando…", "");
    btn.disabled = true;
    try {
      const r = await API.installTool(t.id);
      if (r.installed) {
        this.setMsg(msg, r.message || "Ya está instalada.", "ok");
        return;
      }
      if (!r.ok) {
        this.setMsg(msg, r.error || "No se pudo preparar la instalación.", "err");
        btn.disabled = false;
        return;
      }
      const sent = (typeof Terminal_ !== "undefined") && (await Terminal_.runCommand(r.command));
      if (sent) {
        // La terminal queda visible: se cierra el marketplace para no taparla.
        this.hide();
        btn.disabled = false;
        return;
      }
      this.setMsg(msg, "No se pudo abrir la terminal. Copia y ejecuta: " + r.command, "err");
      btn.disabled = false;
    } catch (e) {
      this.setMsg(msg, "Error al preparar la instalación: " + e.message, "err");
      btn.disabled = false;
    }
  },

  // Abre la web oficial en el navegador del sistema (Spec 026 RF3)
  async openUrl(t, msg) {
    this.setMsg(msg, "Abriendo en tu navegador…", "");
    try {
      const r = await API.openUrl(t.id);
      if (r.ok) this.setMsg(msg, "Se abrió la web oficial en tu navegador.", "ok");
      else this.setMsg(msg, r.error || "No se pudo abrir el enlace.", "err");
    } catch (e) {
      this.setMsg(msg, "No se pudo abrir: " + e.message + ". Enlace: " + t.url, "err");
    }
  },

  setMsg(el, text, kind) {
    el.textContent = text;
    el.className = "ts-msg" + (kind ? " " + kind : "");
  },
};
