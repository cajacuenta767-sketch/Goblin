// === GOBLIN — Arranque y estado global ===

window.GOBLIN = {
  model: null,     // modelo activo (null = usa el default del backend)
  mode: "Local",   // Local / Híbrido / Manual (Fase 2.5)
};

const App = {
  async init() {
    await this.inlineLogos();   // mete el SVG del goblin inline para poder animarlo
    Chat.init();
    Approvals.init();
    Editor.init();
    Explorer.init();
    Terminal_.init();
    if (window.Voice) Voice.init();
    if (window.Sessions) Sessions.init();
    if (window.Findings) Findings.init();
    this.wireUI();
    await this.loadInfo();
    await this.refreshStatus();
    // refrescar RAM/CPU y estado de Ollama cada 5 s
    setInterval(() => this.refreshStatus(), 5000);
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
      if (window.Sessions) Sessions.newSession();
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
