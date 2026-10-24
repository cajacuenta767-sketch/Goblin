// === GOBLIN — Sidebar de sesiones (persistencia) ===

const Sessions = {
  el: { list: null },

  init() {
    this.el.list = document.getElementById("convList");
    this.refresh();
  },

  async refresh() {
    try {
      const r = await API.sessions();
      const sessions = r.sessions || [];
      this.el.list.innerHTML = "";
      if (!sessions.length) {
        this.el.list.innerHTML = '<div class="conv active"><span class="t">Nueva conversación</span><span class="age">ahora</span></div>';
        return;
      }
      for (const s of sessions) {
        const div = document.createElement("div");
        div.className = "conv" + (s.id === Chat.sessionId ? " active" : "");
        div.innerHTML = `<span class="t"></span><span class="del" title="Borrar">✕</span>`;
        div.querySelector(".t").textContent = s.title || "Sin título";
        div.querySelector(".t").addEventListener("click", () => this.open(s.id));
        div.querySelector(".del").addEventListener("click", (e) => { e.stopPropagation(); this.remove(s.id); });
        this.el.list.appendChild(div);
      }
    } catch { /* si el backend no responde, se deja el placeholder */ }
  },

  async open(sid) {
    try {
      const r = await API.sessionMessages(sid);
      Chat.sessionId = sid;
      // Limpiar chat y cargar los mensajes guardados
      document.querySelectorAll("#messages .msg").forEach((m) => m.remove());
      for (const m of (r.messages || [])) {
        if (m.role === "user") Chat.addMessage("user", m.content);
        else if (m.role === "assistant") Chat.addMessage("ai", m.content, m.model);
      }
      this.refresh();
      if ((typeof Findings !== "undefined" && Findings)) Findings.refresh();
    } catch { /* ignore */ }
  },

  async remove(sid) {
    if (!confirm("¿Borrar esta conversación?")) return;
    try {
      await API.deleteSession(sid);
      if (sid === Chat.sessionId) {
        Chat.sessionId = "sess-" + Date.now();
        document.querySelectorAll("#messages .msg").forEach((m, i) => { if (i > 0) m.remove(); });
      }
      this.refresh();
    } catch { /* ignore */ }
  },

  newSession() {
    Chat.sessionId = "sess-" + Date.now();
    document.querySelectorAll("#messages .msg").forEach((m, i) => { if (i > 0) m.remove(); });
    this.refresh();
    if ((typeof Findings !== "undefined" && Findings)) Findings.refresh();
  },
};
