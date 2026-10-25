// === GOBLIN — Dictado por voz (Web Speech API del navegador) ===
// El usuario habla y el texto aparece en el input. No usa Whisper (ahorra RAM).

const Voice = {
  rec: null,
  listening: false,
  el: { btn: null, input: null },

  init() {
    this.el.btn = document.getElementById("micBtn");
    this.el.input = document.getElementById("input");
    if (!this.el.btn) return;

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      // Sin Web Speech API (p. ej. WebKitGTK en Linux): se oculta el botón.
      // Antes mostraba un alert() nativo al pulsarlo.
      this.el.btn.style.display = "none";
      return;
    }

    this.rec = new SR();
    this.rec.lang = "es-ES";
    this.rec.interimResults = true;
    this.rec.continuous = false;

    let base = "";
    this.rec.onresult = (e) => {
      let text = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        text += e.results[i][0].transcript;
      }
      this.el.input.value = (base ? base + " " : "") + text;
      this.el.input.dispatchEvent(new Event("input"));
    };
    this.rec.onend = () => this.stop();
    this.rec.onerror = () => this.stop();

    this.el.btn.addEventListener("click", () => {
      if (this.listening) { this.rec.stop(); return; }
      base = this.el.input.value.trim();
      try { this.rec.start(); this.start(); } catch { /* ya escuchando */ }
    });
  },

  start() {
    this.listening = true;
    this.el.btn.classList.add("listening");
    this.el.btn.title = "Escuchando... (clic para parar)";
  },

  stop() {
    this.listening = false;
    this.el.btn.classList.remove("listening");
    this.el.btn.title = "Dictado por voz";
    this.el.input.focus();
  },
};
