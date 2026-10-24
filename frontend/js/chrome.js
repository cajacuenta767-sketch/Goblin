// === GOBLIN — Botones de la ventana (barra de título, menús, barra lateral, ajustes) ===
// Cada control visible tiene una acción real. Si una función solo existe en la app
// nativa (controles de ventana de Tauri), en el navegador avisa en vez de fallar en silencio.

const Chrome = {
  el: {},

  init() {
    this.el.sidebar = document.getElementById("sidebar");
    this.el.drop = document.getElementById("menuDrop");
    this.el.chatDrop = null;

    this.wireWindowDots();
    this.wireMenuBar();
    this.wireSidebarIcons();
    this.wireSidebarNav();
    this.wireSearch();
    this.wireChatMenu();
    this.wireAttach();
    this.wireTerminalTab();
    this.wireSettings();

    // Cerrar menús al hacer clic fuera o con Escape
    document.addEventListener("click", (e) => {
      if (!e.target.closest("#menuDrop, #chatDrop, #menuBar, #chatMenu")) this.closeMenus();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") { this.closeMenus(); this.closeSettings(); }
    });
  },

  // ---------- Ventana nativa (Tauri) ----------
  tauriWindow() {
    try { return window.__TAURI__.window.getCurrentWindow(); } catch { return null; }
  },

  windowAction(kind) {
    const win = this.tauriWindow();
    if (!win) {
      this.notice("Este control solo funciona en la app nativa de GOBLIN (no en el navegador).");
      return;
    }
    try {
      if (kind === "close") win.close();
      if (kind === "min") win.minimize();
      if (kind === "max") win.toggleMaximize();
    } catch (e) {
      this.notice("No pude controlar la ventana: " + e.message);
    }
  },

  wireWindowDots() {
    document.getElementById("winClose").addEventListener("click", () => this.windowAction("close"));
    document.getElementById("winMin").addEventListener("click", () => this.windowAction("min"));
    document.getElementById("winMax").addEventListener("click", () => this.windowAction("max"));
  },

  // ---------- Menús File / View / Window ----------
  menus() {
    return {
      file: [
        { label: "Nueva conversación", run: () => Sessions.newSession() },
        { label: "Guardar archivo (Ctrl+S)", run: () => (typeof Editor !== "undefined" && Editor) && Editor.save && Editor.save() },
        { label: "Cerrar GOBLIN", run: () => this.windowAction("close") },
      ],
      view: [
        { label: "Mostrar/ocultar barra lateral", run: () => this.toggleSidebar() },
        { label: "Mostrar/ocultar terminal", run: () => document.getElementById("termChip").click() },
        { label: "Herramientas (marketplace)", run: () => document.getElementById("toolstoreBtn").click() },
        { label: "Ajustes", run: () => this.openSettings() },
      ],
      window: [
        { label: "Minimizar", run: () => this.windowAction("min") },
        { label: "Maximizar / restaurar", run: () => this.windowAction("max") },
      ],
    };
  },

  wireMenuBar() {
    document.querySelectorAll("#menuBar [data-menu]").forEach((span) => {
      span.addEventListener("click", (e) => {
        e.stopPropagation();
        const key = span.dataset.menu;
        const items = this.menus()[key] || [];
        this.showDrop(this.el.drop, items, span.getBoundingClientRect());
      });
    });
  },

  showDrop(container, items, rect) {
    this.closeMenus();
    container.innerHTML = "";
    for (const it of items) {
      const b = document.createElement("button");
      b.textContent = it.label;
      b.addEventListener("click", (e) => {
        e.stopPropagation();
        this.closeMenus();
        try { it.run(); } catch (err) { this.notice("Error: " + err.message); }
      });
      container.appendChild(b);
    }
    container.style.left = Math.round(rect.left) + "px";
    container.style.top = Math.round(rect.bottom + 4) + "px";
    container.hidden = false;
    this.openDrop = container;
  },

  closeMenus() {
    if (this.openDrop) this.openDrop.hidden = true;
    this.openDrop = null;
  },

  // ---------- Barra lateral: ☰ ← → ⌕ ----------
  toggleSidebar() {
    this.el.sidebar.classList.toggle("collapsed");
  },

  wireSidebarIcons() {
    document.getElementById("toggleSidebar").addEventListener("click", () => this.toggleSidebar());
    document.getElementById("navBack").addEventListener("click", () => this.stepConversation(-1));
    document.getElementById("navFwd").addEventListener("click", () => this.stepConversation(1));
    document.getElementById("searchConv").addEventListener("click", () => {
      const box = document.getElementById("convSearch");
      box.hidden = !box.hidden;
      if (!box.hidden) box.focus();
    });
  },

  // Va a la conversación anterior/siguiente de la lista (solo las que tienen título guardado)
  stepConversation(dir) {
    const items = [...document.querySelectorAll("#convList .conv .t")];
    if (!items.length) return;
    let idx = items.findIndex((t) => t.parentElement.classList.contains("active"));
    idx = idx < 0 ? 0 : idx + dir;
    if (idx < 0 || idx >= items.length) { this.notice("No hay más conversaciones en esa dirección."); return; }
    items[idx].click();
  },

  wireSearch() {
    const box = document.getElementById("convSearch");
    box.addEventListener("input", () => {
      const q = box.value.trim().toLowerCase();
      document.querySelectorAll("#convList .conv").forEach((c) => {
        c.hidden = !!q && !c.textContent.toLowerCase().includes(q);
      });
    });
  },

  // ---------- Barra lateral: navegación ----------
  wireSidebarNav() {
    // Historial: recarga la lista de conversaciones y la resalta brevemente.
    // (Solo es pulsable con la barra lateral desplegada; ☰ la despliega.)
    document.getElementById("histBtn").addEventListener("click", () => {
      if ((typeof Sessions !== "undefined" && Sessions)) Sessions.refresh();
      const list = document.getElementById("convList");
      list.scrollIntoView({ behavior: "smooth", block: "start" });
      list.classList.add("flash");
      setTimeout(() => list.classList.remove("flash"), 900);
    });
    document.getElementById("custBtn").addEventListener("click", () => this.openSettings());
    document.getElementById("settingsBtn").addEventListener("click", () => this.openSettings());
  },

  // ---------- ⋮ del chat ----------
  wireChatMenu() {
    const btn = document.getElementById("chatMenu");
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const items = [
        { label: "Generar informe de pentest", run: () => document.getElementById("reportBtn").click() },
        { label: "Borrar esta conversación", run: () => (typeof Sessions !== "undefined" && Sessions) && Sessions.remove(Chat.sessionId) },
        { label: "Nueva conversación", run: () => Sessions.newSession() },
      ];
      this.showDrop(this.el.drop, items, btn.getBoundingClientRect());
    });
  },

  // ---------- + : adjuntar archivo de texto ----------
  wireAttach() {
    const btn = document.getElementById("attachBtn");
    const file = document.getElementById("attachFile");
    const input = document.getElementById("input");
    btn.addEventListener("click", () => file.click());
    file.addEventListener("change", () => {
      const f = file.files && file.files[0];
      if (!f) return;
      if (f.size > 200 * 1024) { this.notice("El archivo es muy grande (máximo 200 KB)."); file.value = ""; return; }
      const reader = new FileReader();
      reader.onload = () => {
        const header = `Archivo adjunto: ${f.name}\n\`\`\`\n${reader.result}\n\`\`\`\n\n`;
        input.value = header + input.value;
        input.focus();
        file.value = "";
      };
      reader.onerror = () => this.notice("No pude leer el archivo.");
      reader.readAsText(f);
    });
  },

  // ---------- Pestaña bash de la terminal ----------
  // La pestaña "● bash" solo aparece con la terminal abierta: su clic enfoca la
  // terminal (no la cierra; para cerrarla está el botón ⌃).
  wireTerminalTab() {
    document.getElementById("termTabBtn").addEventListener("click", () => {
      const input = document.querySelector("#termBody textarea");
      if (input) input.focus();
      else document.getElementById("termBody").click();
    });
  },

  // ---------- Ajustes (aprobación + modo) ----------
  wireSettings() {
    document.getElementById("settingsClose").addEventListener("click", () => this.closeSettings());
    document.getElementById("settingsModal").addEventListener("click", (e) => {
      if (e.target.id === "settingsModal") this.closeSettings();
    });
    document.getElementById("setApproval").addEventListener("change", async (e) => {
      try {
        await API._post("/api/approval-level", { session_id: Chat.sessionId, level: e.target.value });
        this.settingsNote("Nivel de aprobación guardado.");
      } catch (err) { this.settingsNote("No se pudo guardar: " + err.message); }
    });
    document.getElementById("setMode").addEventListener("change", async (e) => {
      try {
        const r = await API.setMode(Chat.sessionId, e.target.value);
        this.settingsNote(r.warning || "Modo guardado.");
        if ((typeof App !== "undefined" && App)) App.refreshStatus();
      } catch (err) { this.settingsNote("No se pudo guardar: " + err.message); }
    });
  },

  async openSettings() {
    this.closeMenus();
    const modal = document.getElementById("settingsModal");
    modal.hidden = false;
    this.settingsNote("Cargando…");
    try {
      const [lvl, mode] = await Promise.all([
        API._get("/api/approval-level?session_id=" + encodeURIComponent(Chat.sessionId)),
        API.mode(Chat.sessionId),
      ]);
      document.getElementById("setApproval").value = lvl.level;
      document.getElementById("setMode").value = mode.mode;
      this.settingsNote("");
    } catch (err) {
      this.settingsNote("No se pudo leer la configuración. ¿Está corriendo el backend? (" + err.message + ")");
    }
  },

  closeSettings() {
    document.getElementById("settingsModal").hidden = true;
  },

  settingsNote(text) {
    const n = document.getElementById("settingsNote");
    if (n) n.textContent = text;
  },

  // Aviso breve dentro del chat (no usa alert, que bloquea la app)
  notice(text) {
    if ((typeof Chat !== "undefined" && Chat) && Chat.addMessage) Chat.addMessage("ai", text, "GOBLIN");
    else console.warn("[GOBLIN]", text);
  },
};

window.Chrome = Chrome;
