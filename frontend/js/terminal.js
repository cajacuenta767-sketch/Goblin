// === GOBLIN — Terminal (xterm.js ↔ WebSocket al pty del backend) ===

const Terminal_ = {
  term: null,
  fit: null,
  ws: null,
  open: false,
  started: false,

  el: { panel: null, body: null, toggle: null, chip: null },

  init() {
    this.el.panel = document.getElementById("termPanel");
    this.el.body = document.getElementById("termBody");
    this.el.toggle = document.getElementById("termToggle");
    this.el.chip = document.getElementById("termChip");

    this.el.chip.addEventListener("click", () => this.toggle());
    this.el.toggle.addEventListener("click", () => this.toggle());
    window.addEventListener("resize", () => { if (this.open && this.fit) this.fit.fit(); });
  },

  toggle() {
    this.open = !this.open;
    this.el.panel.classList.toggle("show", this.open);
    if (this.open) {
      if (!this.started) this.start();
      setTimeout(() => { if (this.fit) { this.fit.fit(); this.sendResize(); } }, 50);
    }
  },

  start() {
    if (typeof window.Terminal === "undefined") {
      this.el.body.textContent = "xterm.js no cargó (sin conexión a la CDN).";
      return;
    }
    this.started = true;
    this.term = new window.Terminal({
      fontFamily: '"JetBrains Mono", monospace',
      fontSize: 13,
      theme: { background: "#0a0a0b", foreground: "#c8c8c8", cursor: "#3ddc84" },
      cursorBlink: true,
    });
    try {
      this.fit = new window.FitAddon.FitAddon();
      this.term.loadAddon(this.fit);
    } catch { this.fit = null; }
    this.term.open(this.el.body);
    if (this.fit) this.fit.fit();

    // Conectar WebSocket al pty del backend
    const proto = location.protocol === "https:" ? "wss" : "ws";
    this.ws = new WebSocket(`${proto}://${location.host}/ws/terminal`);

    this.ws.onopen = () => this.sendResize();
    this.ws.onmessage = (e) => this.term.write(e.data);
    this.ws.onclose = () => this.term.write("\r\n\x1b[90m[terminal cerrada]\x1b[0m\r\n");
    this.ws.onerror = () => this.term.write("\r\n\x1b[31m[error de conexión con la terminal]\x1b[0m\r\n");

    // Lo que el usuario teclea va al pty
    this.term.onData((d) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) this.ws.send(d);
    });
  },

  sendResize() {
    if (this.term && this.ws && this.ws.readyState === WebSocket.OPEN) {
      const { rows, cols } = this.term;
      this.ws.send(JSON.stringify({ resize: [rows, cols] }));
    }
  },
};
