// === GOBLIN — Arranque y estado global ===

window.GOBLIN = {
  model: null,     // modelo activo (null = usa el default del backend)
  mode: "Local",   // Local / Híbrido / Manual (Fase 2.5)
};

const App = {
  async init() {
    Chat.init();
    Approvals.init();
    Explorer.init();
    this.wireUI();
    await this.loadInfo();
    await this.refreshStatus();
    // refrescar RAM/CPU y estado de Ollama cada 5 s
    setInterval(() => this.refreshStatus(), 5000);
  },

  wireUI() {
    // Nueva conversación: reinicia el chat visual
    document.getElementById("newConv").addEventListener("click", () => {
      document.querySelectorAll(".msg").forEach((m, i) => { if (i > 0) m.remove(); });
    });
    // marked: abrir enlaces en pestaña nueva y no romper con HTML
    if (window.marked) {
      marked.setOptions({ breaks: true, gfm: true });
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
