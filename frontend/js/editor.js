// === GOBLIN — Editor de código (Monaco) ===

const Editor = {
  monaco: null,
  instance: null,
  ready: false,
  currentPath: null,

  el: { panel: null, body: null, file: null, save: null, close: null },

  init() {
    this.el.panel = document.getElementById("editorPanel");
    this.el.body = document.getElementById("editorBody");
    this.el.file = document.getElementById("editorFile");
    this.el.save = document.getElementById("editorSave");
    this.el.close = document.getElementById("editorClose");

    this.el.save.addEventListener("click", () => this.save());
    this.el.close.addEventListener("click", () => this.hide());
  },

  // Carga Monaco una sola vez (lazy, desde el CDN)
  loadMonaco() {
    return new Promise((resolve) => {
      if (this.ready) return resolve();
      if (typeof require === "undefined") { resolve(); return; }
      require.config({ paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.0/min/vs" } });
      require(["vs/editor/editor.main"], () => {
        this.monaco = window.monaco;
        this.ready = true;
        resolve();
      });
    });
  },

  langFromName(name) {
    const ext = (name.split(".").pop() || "").toLowerCase();
    const map = { js:"javascript", ts:"typescript", py:"python", sh:"shell", bash:"shell",
      html:"html", css:"css", json:"json", md:"markdown", rs:"rust", go:"go", c:"c",
      cpp:"cpp", java:"java", rb:"ruby", php:"php", sql:"sql", yml:"yaml", yaml:"yaml",
      xml:"xml", conf:"ini", ini:"ini", txt:"plaintext" };
    return map[ext] || "plaintext";
  },

  async open(path) {
    await this.loadMonaco();
    if (!this.ready) { alert("Monaco no cargó (sin conexión a la CDN)."); return; }

    let content = "";
    try {
      const r = await API.readFile(path);
      if (!r.ok) { alert("No se pudo abrir: " + (r.error || path)); return; }
      content = r.content;
    } catch (e) { alert("Error leyendo el archivo: " + e.message); return; }

    this.currentPath = path;
    this.el.file.textContent = path.split("/").pop();
    this.el.file.title = path;
    this.el.panel.classList.add("show");

    const lang = this.langFromName(path);
    if (this.instance) {
      this.instance.setValue(content);
      this.monaco.editor.setModelLanguage(this.instance.getModel(), lang);
    } else {
      this.instance = this.monaco.editor.create(this.el.body, {
        value: content, language: lang, theme: "vs-dark",
        fontSize: 13, fontFamily: '"JetBrains Mono", monospace',
        minimap: { enabled: true }, automaticLayout: true, scrollBeyondLastLine: false,
      });
      // Ctrl+S guarda
      this.instance.addCommand(this.monaco.KeyMod.CtrlCmd | this.monaco.KeyCode.KeyS, () => this.save());
    }
  },

  async save() {
    if (!this.instance || !this.currentPath) return;
    const content = this.instance.getValue();
    try {
      const r = await API.writeFile(this.currentPath, content);
      if (r.ok) {
        this.el.file.textContent = this.currentPath.split("/").pop() + " ✓";
        setTimeout(() => { this.el.file.textContent = this.currentPath.split("/").pop(); }, 1500);
      } else { alert("No se pudo guardar: " + (r.error || "")); }
    } catch (e) { alert("Error al guardar: " + e.message); }
  },

  hide() {
    this.el.panel.classList.remove("show");
    this.currentPath = null;
  },
};
