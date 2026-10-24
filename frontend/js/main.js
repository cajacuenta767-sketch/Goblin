// === GOBLIN — Arranque y estado global ===

window.GOBLIN = {
  model: null,     // modelo activo (null = usa el default del backend)
  mode: "Local",   // Local / Híbrido / Manual (Fase 2.5)
};

const App = {
  async init() {
    // Cada paso va aislado: si uno falla, los demás (y los botones) siguen funcionando.
    const safe = (name, fn) => {
      try { return fn(); } catch (e) { console.error("[GOBLIN] falló " + name + ":", e); }
    };
    await safe("logos", () => this.inlineLogos());
    safe("chat", () => Chat.init());
    safe("aprobaciones", () => Approvals.init());
    safe("editor", () => Editor.init());
    safe("explorador", () => Explorer.init());
    safe("terminal", () => Terminal_.init());
    safe("voz", () => Voice.init());
    safe("sesiones", () => Sessions.init());
    safe("hallazgos", () => Findings.init());
    safe("marketplace", () => ToolStore.init());
    safe("botones de la ventana", () => Chrome.init());
    safe("botones principales", () => this.wireUI());
    await safe("info", () => this.loadInfo());
    await safe("estado", () => this.refreshStatus());
    await safe("diagnóstico", () => this.checkDiagnostics());
    // refrescar RAM/CPU y estado de Ollama cada 5 s
    setInterval(() => safe("estado", () => this.refreshStatus()), 5000);
  },

  // Aviso de primer uso: si falta Ollama o el modelo, lo explica en el chat.
  async checkDiagnostics() {
    try {
      const d = await API.diagnostics();
      if (d && !d.ok && d.problems && d.problems.length) {
        let msg = "⚠️ **Antes de empezar, revisa esto:**\n\n";
        for (const p of d.problems) {
          msg += `- **${p.what}**\n  \`${p.fix}\`\n`;
        }
        Chat.addMessage("ai", msg, "DeepHat");
      }
    } catch { /* si el backend no responde, se ve en la barra de estado */ }
  },

  // Reemplaza los <img> del logo por el SVG inline (así la animación por clase funciona)
  async inlineLogos() {
    try {
      const svg = await (await fetch("assets/goblin.svg")).text();
      document.querySelectorAll("#brandLogo, #sidebarLogo").forEach((img) => {
        const wrap = document.createElement("span");
        wrap.className = img.className + " goblin-logo";
        wrap.innerHTML = svg;
        img.replaceWith(wrap);
      });
    } catch { /* si falla, se quedan los <img> normales */ }
  },

  // Activa/desactiva la animación del goblin (parpadeo + orejas)
  setThinking(on) {
    document.querySelectorAll(".goblin-logo svg").forEach((s) => {
      s.classList.toggle("thinking", on);
    });
  },

  wireUI() {
    // Nueva conversación: crea una sesión nueva (persistente)
    document.getElementById("newConv").addEventListener("click", () => {
      if ((typeof Sessions !== "undefined" && Sessions)) Sessions.newSession();
      else document.querySelectorAll(".msg").forEach((m, i) => { if (i > 0) m.remove(); });
    });
    // marked: abrir enlaces en pestaña nueva y no romper con HTML
    if (window.marked) {
      marked.setOptions({ breaks: true, gfm: true });
    }
    // Selector de modo (Local → Híbrido → Manual) al hacer clic en el chip
    const modeChip = document.getElementById("modeChip");
    if (modeChip) {
      const modes = [
        { key: "local",  label: "◈ Local" },
        { key: "hybrid", label: "◈ Híbrido" },
        { key: "manual", label: "◈ Manual" },
      ];
      let idx = 0;
      modeChip.addEventListener("click", async () => {
        idx = (idx + 1) % modes.length;
        const m = modes[idx];
        try {
          const r = await API.setMode(Chat.sessionId, m.key);
          modeChip.textContent = m.label + " ▾";
          document.getElementById("stMode").textContent = m.label.replace("◈ ", "");
          window.GOBLIN.mode = m.key;
          if (r.warning) Chat.addMessage("ai", "⚠️ " + r.warning, "DeepHat");
        } catch { /* silencioso */ }
      });
    }
  },

  async loadInfo() {
    try {
      const info = await API.info();
      window.GOBLIN.model = null; // usamos el default del backend
      const short = this.shortModel(info.default_model);
      document.getElementById("stModel").textContent = short;
      document.getElementById("welcomeModel").textContent = short;
      document.getElementById("modelChip").textContent = "⬢ " + short + " ▾";
      document.getElementById("stMode").textContent = window.GOBLIN.mode;
    } catch (e) {
      document.getElementById("stModel").textContent = "backend no responde";
    }
  },

  shortModel(full) {
    if (!full) return "DeepHat";
    if (full.toLowerCase().includes("deephat")) return "DeepHat";
    if (full.toLowerCase().includes("gemini")) return "Gemini";
    // último segmento legible
    const seg = full.split("/").pop().split(":")[0];
    return seg.length > 16 ? seg.slice(0, 16) + "…" : seg;
  },

  async refreshStatus() {
    // Estado de Ollama
    try {
      const h = await API.health();
      const dot = document.getElementById("stOllama");
      const txt = document.getElementById("stOllamaText");
      if (h.ollama === "ok") { dot.style.color = "var(--accent)"; txt.textContent = "Ollama"; }
      else { dot.style.color = "var(--red)"; txt.textContent = "Ollama caído"; }
    } catch {
      document.getElementById("stOllama").style.color = "var(--red)";
    }
    // RAM / CPU
    try {
      const s = await API.system();
      if (s && s.ok) {
        document.getElementById("stRam").textContent = `${s.ram_used_gb}/${s.ram_total_gb} GB (${s.ram_percent}%)`;
        document.getElementById("stCpu").textContent = `${s.cpu_percent}%`;
      }
    } catch { /* silencioso */ }
  },
};

document.addEventListener("DOMContentLoaded", () => App.init());
