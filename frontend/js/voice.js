// === GOBLIN — Dictado por voz con Whisper local (Spec 042) ===
// El navegador graba el audio (MediaRecorder) y el backend lo transcribe en ESTE equipo con
// faster-whisper. El audio nunca sale de la máquina. Si Whisper no está listo, el botón 🎤 se
// oculta y la barra de estado dice por qué (GET /api/voice/status).

const Voice = {
  el: { btn: null, input: null, estado: null },
  recorder: null,
  stream: null,
  chunks: [],
  timer: null,
  timerAviso: null,
  base: "",
  busy: false,
  estadoBase: "Dictado: —",
  MAX_MS: 60000,           // RF2: máximo 60 s por grabación

  async init() {
    this.el.btn = document.getElementById("micBtn");
    this.el.input = document.getElementById("input");
    this.el.estado = document.getElementById("stVoice");
    if (!this.el.btn) return;
    this.el.btn.style.display = "none";          // oculto hasta confirmar que está listo

    let st = { available: false, reason: "No se pudo consultar el dictado." };
    try {
      st = await API.voiceStatus();
    } catch { /* backend caído: el botón se queda oculto */ }

    const sePuedeGrabar = !!(window.MediaRecorder && navigator.mediaDevices
      && navigator.mediaDevices.getUserMedia);
    if (!sePuedeGrabar) {
      this.pintarEstado(false, "este navegador no puede grabar audio");
      return;
    }
    if (!st.available) {
      this.pintarEstado(false, st.reason);
      return;
    }
    this.el.btn.style.display = "";
    this.el.btn.addEventListener("click", () => this.alternar());
    this.pintarEstado(true, `listo (${st.model})`);
  },

  // Barra de estado: "Dictado: listo (base)" o "Dictado: no disponible" (motivo en el tooltip).
  pintarEstado(listo, detalle) {
    if (!this.el.estado) return;
    this.estadoBase = listo ? `Dictado: ${detalle}` : "Dictado: no disponible";
    this.el.estado.textContent = this.estadoBase;
    this.el.estado.title = listo ? "Dictado por voz (Whisper local)" : detalle;
  },

  // Mensaje temporal en la barra de estado (sin alert()).
  avisar(texto) {
    if (!this.el.estado) return;
    this.el.estado.textContent = `Dictado: ${texto}`;
    clearTimeout(this.timerAviso);
    this.timerAviso = setTimeout(() => { this.el.estado.textContent = this.estadoBase; }, 6000);
  },

  pintar(estado) {
    const b = this.el.btn;
    b.classList.toggle("listening", estado === "grabando");
    b.classList.toggle("busy", estado === "transcribiendo");
    b.title = {
      grabando: "Grabando… (clic para parar; máximo 60 s)",
      transcribiendo: "Transcribiendo en este equipo…",
      libre: "Dictado por voz (Whisper local)",
    }[estado] || "Dictado por voz";
  },

  alternar() {
    if (this.busy) return;
    if (this.recorder && this.recorder.state === "recording") { this.parar(); return; }
    this.grabar();
  },

  async grabar() {
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      this.avisar("sin acceso al micrófono (" + e.message + ")");
      return;
    }
    this.stream = stream;
    this.chunks = [];
    this.base = this.el.input.value.trim();
    try {
      this.recorder = new MediaRecorder(stream);
    } catch {
      this.cerrarMicro();
      this.avisar("no se pudo iniciar la grabación");
      return;
    }
    this.recorder.ondataavailable = (e) => { if (e.data && e.data.size) this.chunks.push(e.data); };
    this.recorder.onstop = () => this.finalizar();
    this.recorder.start();
    this.timer = setTimeout(() => this.parar(), this.MAX_MS);
    this.pintar("grabando");
  },

  parar() {
    clearTimeout(this.timer);
    if (this.recorder && this.recorder.state === "recording") this.recorder.stop();
  },

  cerrarMicro() {
    if (this.stream) this.stream.getTracks().forEach((t) => t.stop());
    this.stream = null;
  },

  async finalizar() {
    const tipo = (this.recorder && this.recorder.mimeType) || "audio/webm";
    this.cerrarMicro();
    const audio = new Blob(this.chunks, { type: tipo });
    this.chunks = [];
    if (audio.size === 0) { this.pintar("libre"); return; }

    this.busy = true;
    this.pintar("transcribiendo");
    try {
      const r = await API.transcribe(audio);
      const texto = (r.text || "").trim();
      if (texto) {
        // RF3: el texto va al campo; no se envía solo.
        this.el.input.value = (this.base ? this.base + " " : "") + texto;
        this.el.input.dispatchEvent(new Event("input"));
      } else {
        this.avisar("no se entendió nada");
      }
    } catch (e) {
      this.avisar(e.message);
    } finally {
      this.busy = false;
      this.pintar("libre");
      this.el.input.focus();
    }
  },
};
