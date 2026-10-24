// === GOBLIN — Marketplace de herramientas de ciberseguridad (Spec 016 / 026 / 027) ===
// Instalar / desinstalar: GOBLIN ejecuta el comando con sudo. Si hace falta, pide la
// contraseña en un diálogo propio; se usa una sola vez y no se guarda (Spec 027).
// Alternativa: escribir el comando en la terminal integrada (Spec 026).
// Descargar / web oficial: el backend abre la URL del catálogo. No usa target="_blank",
// porque no abre nada en la ventana nativa de Tauri.

const ToolStore = {
  el: { panel: null, grid: null, filters: null, close: null, btn: null, refresh: null, jobs: null },
  tools: [],
  categories: [],
  activeCategory: "all",
  watching: false,   // seguimos un trabajo en curso

  FINISHED: ["ok", "error", "cancelled"],
  JOB_LABEL: {
    checking: "Comprobando permisos…", needs_password: "Esperando tu contraseña",
    running: "En curso…", ok: "Terminado", error: "Error", cancelled: "Cancelado",
  },

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

    // Panel de instalaciones: entre los filtros y la rejilla (Spec 027 RF5)
    this.el.jobs = document.createElement("div");
    this.el.jobs.className = "ts-jobs";
    this.el.jobs.hidden = true;
    this.el.grid.parentNode.insertBefore(this.el.jobs, this.el.grid);

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
    await this.resumeJobs();
  },

  // Muestra el último trabajo y retoma el seguimiento si sigue activo (Spec 027 RF11)
  async resumeJobs() {
    try {
      const r = await API.toolJobs();
      const last = (r.jobs || [])[0];
      if (!last) { this.el.jobs.hidden = true; return; }
      this.renderJob(last);
      if (!this.watching && !this.FINISHED.includes(last.status)) this.watch(last.id);
    } catch (e) {
      this.el.jobs.hidden = true;
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
    const busy = this.watching;   // mientras hay un trabajo, no se lanza otro
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
    const actions = card.querySelector(".ts-actions");
    const msg = card.querySelector(".ts-msg");
    if (t.installed) {
      installBtn.textContent = "✓ Instalada";
      installBtn.classList.add("installed");
      installBtn.disabled = true;
      if (t.pkg) {
        const un = document.createElement("button");
        un.className = "ts-dl ts-uninstall";
        un.textContent = "🗑 Desinstalar";
        un.title = "Quitar esta herramienta con apt-get remove";
        un.disabled = busy;
        un.addEventListener("click", () => this.showConfirm(t, card, "remove"));
        actions.appendChild(un);
      }
    } else if (t.command) {
      installBtn.textContent = "Instalar";
      installBtn.disabled = busy;
      installBtn.addEventListener("click", () => this.showConfirm(t, card, "install"));
    } else {
      installBtn.remove();
      const manual = document.createElement("div");
      manual.className = "ts-manual";
      manual.textContent = "Solo descarga manual (no está en apt)";
      actions.prepend(manual);
    }

    card.querySelector(".ts-source").addEventListener("click", (e) => {
      e.preventDefault();
      this.openUrl(t, msg);
    });
    card.querySelector(".ts-dl").addEventListener("click", () => this.openUrl(t, msg));
    return card;
  },

  // Confirmación dentro de la tarjeta, con el comando exacto (Spec 027 RF1)
  showConfirm(t, card, action) {
    const box = card.querySelector(".ts-confirm");
    if (!box.hidden) { box.hidden = true; return; }   // segundo clic: cierra
    const remove = action === "remove";
    box.innerHTML = "";

    const intro = document.createElement("div");
    intro.textContent = remove
      ? `Se desinstalará ${t.name} con este comando:`
      : `Se instalará ${t.name} con este comando:`;
    const code = document.createElement("code");
    code.textContent = remove ? t.remove_command : t.command;
    const note = document.createElement("div");
    note.textContent = "Te pediré tu contraseña de administrador en un diálogo de GOBLIN. Se usa una sola vez y no se guarda.";

    const row = document.createElement("div");
    row.className = "ts-confirm-row";
    const ok = document.createElement("button");
    ok.className = "ts-btn" + (remove ? " danger" : "");
    ok.textContent = remove ? "Desinstalar" : "Instalar";
    const no = document.createElement("button");
    no.className = "ts-btn ghost";
    no.textContent = "Cancelar";
    row.append(ok, no);
    if (!remove) {
      const term = document.createElement("button");
      term.className = "ts-btn ghost";
      term.textContent = "En la terminal";
      term.title = "Escribir el comando en la terminal de GOBLIN en vez de ejecutarlo aquí";
      term.addEventListener("click", () => { box.hidden = true; this.viaTerminal(t, card); });
      row.append(term);
    }
    box.append(intro, code, note, row);
    box.hidden = false;

    no.addEventListener("click", () => { box.hidden = true; });
    ok.addEventListener("click", () => { box.hidden = true; this.runJob(t, card, action); });
  },

  // Inicia el trabajo en el backend y sigue su progreso (Spec 027)
  async runJob(t, card, action) {
    const msg = card.querySelector(".ts-msg");
    this.setMsg(msg, "", "");
    try {
      const r = await API.startToolJob(t.id, action);
      if (!r.ok) { this.setMsg(msg, r.error || "No se pudo iniciar.", "err"); return; }
      this.renderJob(r.job);
      await this.watch(r.job.id);
    } catch (e) {
      this.setMsg(msg, "Error al iniciar: " + e.message, "err");
    }
  },

  // Sigue un trabajo hasta que termina. Si espera contraseña, abre el diálogo (Spec 027 RF2, RF4)
  async watch(jobId) {
    if (this.watching) return;
    this.watching = true;
    try {
      while (true) {
        const r = await API.toolJob(jobId);
        if (!r.ok || !r.job) { this.renderError(r.error || "No se encontró el trabajo."); break; }
        const j = r.job;
        this.renderJob(j);
        if (j.status === "needs_password") {
          const pw = await this.askPassword(j);
          if (pw === null) await API.cancelToolJob(jobId);
          else await API.submitToolJobPassword(jobId, pw);
          continue;
        }
        if (this.FINISHED.includes(j.status)) break;
        await new Promise((res) => setTimeout(res, 700));
      }
    } catch (e) {
      this.renderError("Se perdió la conexión con GOBLIN: " + e.message);
    } finally {
      this.watching = false;
    }
    await this.load();
  },

  // Diálogo propio para la contraseña (no es nativo). Resuelve con la contraseña o null.
  askPassword(j) {
    return new Promise((resolve) => {
      const overlay = document.createElement("div");
      overlay.className = "ts-modal show";
      overlay.innerHTML = `
        <div class="ts-dialog" role="dialog" aria-modal="true" aria-label="Contraseña de administrador">
          <div class="ts-dialog-title">Contraseña de administrador</div>
          <div class="ts-dialog-text"></div>
          <input class="ts-pass" type="password" autocomplete="off" spellcheck="false" placeholder="Tu contraseña de sudo">
          <div class="ts-dialog-err"></div>
          <div class="ts-confirm-row">
            <button class="ts-btn ok">Continuar</button>
            <button class="ts-btn ghost cancel">Cancelar</button>
          </div>
          <div class="ts-dialog-note">Se usa solo para este comando. No se guarda ni se registra.</div>
        </div>`;
      overlay.querySelector(".ts-dialog-text").textContent =
        `${j.action === "remove" ? "Desinstalar" : "Instalar"} ${j.name} necesita permisos de administrador.`;
      const err = overlay.querySelector(".ts-dialog-err");
      if (/incorrecta/i.test(j.message || "")) err.textContent = j.message;
      const input = overlay.querySelector(".ts-pass");
      const okBtn = overlay.querySelector(".ok");
      const done = (value) => { input.value = ""; overlay.remove(); resolve(value); };
      okBtn.addEventListener("click", () => {
        if (!input.value) { err.textContent = "Escribe tu contraseña."; return; }
        done(input.value);
      });
      overlay.querySelector(".cancel").addEventListener("click", () => done(null));
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") okBtn.click();
        if (e.key === "Escape") done(null);
      });
      document.body.appendChild(overlay);
      input.focus();
    });
  },

  // Panel de instalaciones: estado y salida en vivo del trabajo (Spec 027 RF5)
  renderJob(j) {
    const box = this.el.jobs;
    box.hidden = false;
    box.innerHTML = "";
    const head = document.createElement("div");
    head.className = "ts-jobs-head";
    const title = document.createElement("span");
    title.className = "ts-jobs-title";
    title.textContent = `${j.action === "remove" ? "Desinstalar" : "Instalar"} ${j.name}`;
    const status = document.createElement("span");
    status.className = "ts-jobs-status";
    const label = this.JOB_LABEL[j.status] || j.status;
    status.textContent = j.message ? `${label} · ${j.message}` : label;
    head.append(title, status);

    if (this.FINISHED.includes(j.status)) {
      const close = document.createElement("button");
      close.className = "ts-btn ghost";
      close.textContent = "Cerrar";
      close.addEventListener("click", () => { box.hidden = true; });
      head.appendChild(close);
    } else {
      const cancel = document.createElement("button");
      cancel.className = "ts-btn ghost ts-jobs-cancel";
      cancel.textContent = "Cancelar";
      cancel.addEventListener("click", () => API.cancelToolJob(j.id).catch(() => {}));
      head.appendChild(cancel);
    }

    const log = document.createElement("pre");
    log.className = "ts-jobs-log";
    log.textContent = (j.log || []).join("\n");
    box.append(head, log);
    log.scrollTop = log.scrollHeight;
  },

  renderError(text) {
    const box = this.el.jobs;
    box.hidden = false;
    box.innerHTML = "";
    const d = document.createElement("div");
    d.className = "ts-msg err";
    d.textContent = text;
    box.appendChild(d);
  },

  // Alternativa de Spec 026: escribe el comando en la terminal integrada
  async viaTerminal(t, card) {
    const msg = card.querySelector(".ts-msg");
    this.setMsg(msg, "Preparando el comando…", "");
    try {
      const r = await API.installTool(t.id);
      if (r.installed) { this.setMsg(msg, r.message || "Ya está instalada.", "ok"); return; }
      if (!r.ok) { this.setMsg(msg, r.error || "No se pudo preparar la instalación.", "err"); return; }
      const sent = (typeof Terminal_ !== "undefined") && (await Terminal_.runCommand(r.command));
      if (sent) { this.hide(); return; }   // la terminal queda visible sin el marketplace encima
      this.setMsg(msg, "No se pudo abrir la terminal. Copia y ejecuta: " + r.command, "err");
    } catch (e) {
      this.setMsg(msg, "Error al preparar la instalación: " + e.message, "err");
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
