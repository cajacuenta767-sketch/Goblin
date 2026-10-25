// === GOBLIN — Barra de estado y progreso en vivo (Spec 037, 041) ===
// Mientras GOBLIN responde, muestra qué herramienta corre y cuánto lleva.
// En reposo actualiza el contexto estimado y el objetivo cada 5 s.

const Status = {
  timer: null,
  idle: null,

  init() {
    this.idle = setInterval(() => { if (!Chat.busy) this.tick(); }, 5000);
    this.tick();
  },

  start() {
    this.stop();
    this.tick();
    this.timer = setInterval(() => this.tick(), 1000);
  },

  stop() {
    clearInterval(this.timer);
    this.timer = null;
  },

  fmt(n) { return n >= 1000 ? (n / 1000).toFixed(1) + "k" : String(n || 0); },

  async tick() {
    try {
      const st = await API.chatStatus(Chat.sessionId);
      document.getElementById("stContext").textContent = `~${this.fmt(st.context_tokens)} / ${this.fmt(st.context_limit)}`;
      if (Chat.busy) {
        const texto = st.action
          ? `⚡ ejecutando ${st.action}… ${Math.round(st.elapsed_s)} s`
          : "GOBLIN está pensando…";
        document.getElementById("typingText").textContent = texto;
      }
    } catch { /* backend sin responder: la barra conserva lo último */ }
    try {
      const t = await API.getTarget();
      document.getElementById("stTarget").textContent = t.target || "ninguno";
    } catch { /* idem */ }
    const modo = document.getElementById("stMode");
    if (modo) modo.classList.toggle("warn", /híbrid|hybrid/i.test(modo.textContent));
  },
};
