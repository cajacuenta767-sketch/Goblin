// === GOBLIN — Panel de chat ===

const Chat = {
  sessionId: "sess-" + Date.now(),
  busy: false,

  el: {
    messages: null, input: null, sendBtn: null, typing: null, progress: null,
  },

  init() {
    this.el.messages = document.getElementById("messages");
    this.el.input = document.getElementById("input");
    this.el.sendBtn = document.getElementById("sendBtn");
    this.el.typing = document.getElementById("typing");
    this.el.progress = document.getElementById("progress");

    this.el.sendBtn.addEventListener("click", () => this.send());
    this.el.input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); this.send(); }
    });
    // auto-crecer el textarea
    this.el.input.addEventListener("input", () => {
      this.el.input.style.height = "auto";
      this.el.input.style.height = Math.min(this.el.input.scrollHeight, 160) + "px";
    });
  },

  setBusy(on) {
    this.busy = on;
    this.el.typing.classList.toggle("show", on);
    this.el.progress.classList.toggle("active", on);
    this.el.sendBtn.style.opacity = on ? "0.5" : "1";
    if (window.App && App.setThinking) App.setThinking(on);  // anima el goblin
  },

  // Renderiza Markdown de forma segura-ish y resalta código
  renderMarkdown(text) {
    const html = marked.parse(text || "");
    return html;
  },

  addMessage(role, content, model) {
    const div = document.createElement("div");
    div.className = "msg " + role;

    if (role === "user") {
      div.innerHTML = `<div class="who">Tú</div><div class="bubble"></div>`;
      div.querySelector(".bubble").textContent = content;
    } else if (role === "tool") {
      div.innerHTML = `<div class="who">herramienta</div><div class="bubble"></div>`;
      div.querySelector(".bubble").textContent = content;
    } else if (role === "error") {
      div.innerHTML = `<div class="who">GOBLIN</div><div class="bubble"></div>`;
      div.querySelector(".bubble").textContent = content;
    } else {
      const tagClass = (model && model.toLowerCase().includes("gemini")) ? "model-tag gemini" : "model-tag";
      const tagName = (model && model.toLowerCase().includes("gemini")) ? "Gemini" : "DeepHat";
      div.innerHTML = `<div class="who">GOBLIN <span class="${tagClass}">${tagName}</span></div>
                       <div class="bubble">${this.renderMarkdown(content)}</div>`;
      div.querySelectorAll("pre code").forEach((b) => { try { hljs.highlightElement(b); } catch {} });
    }

    // Insertar antes del indicador de typing
    this.el.messages.insertBefore(div, this.el.typing);
    this.scrollDown();
  },

  scrollDown() { this.el.messages.scrollTop = this.el.messages.scrollHeight; },

  // Procesa la respuesta del backend (texto, aprobación o error)
  handle(resp) {
    if (!resp) return;
    if (resp.type === "approval") {
      Approvals.show(resp);          // delega en el módulo de aprobaciones
      this.setBusy(false);
    } else if (resp.type === "error") {
      this.addMessage("error", resp.content);
      this.setBusy(false);
    } else { // text
      this.addMessage("ai", resp.content, resp.model);
      this.setBusy(false);
      Explorer.refresh();            // por si la IA cambió archivos
      if (window.Sessions) Sessions.refresh();   // actualizar sidebar
      if (window.Findings) Findings.refresh();   // por si registró hallazgos
    }
  },

  async send() {
    const text = this.el.input.value.trim();
    if (!text || this.busy) return;
    this.el.input.value = "";
    this.el.input.style.height = "auto";
    this.addMessage("user", text);
    this.setBusy(true);
    try {
      const resp = await API.chat(this.sessionId, text, window.GOBLIN.model);
      this.handle(resp);
    } catch (e) {
      this.addMessage("error", "No se pudo contactar el backend: " + e.message);
      this.setBusy(false);
    }
  },
};
