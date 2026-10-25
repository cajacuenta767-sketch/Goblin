// === GOBLIN — Editor de código (Monaco) con pestañas (Specs 007, 043 RF2–RF3) ===
// Monaco se sirve desde frontend/vendor/monaco (scripts/fetch-monaco.sh): no hace falta internet.
// Cada archivo abierto es un modelo de Monaco con su pestaña. Los cambios sin guardar se marcan
// con un punto; cerrar una pestaña con cambios pide confirmarlo en línea (nunca confirm()).

const Editor = {
  monaco: null,
  instance: null,
  ready: false,
  loading: null,
  tabs: [],          // { path, name, model, saved, dirty, armed, timer }
  active: null,      // ruta de la pestaña activa
  seq: 0,            // número para que cada modelo tenga una URI distinta

  el: { panel: null, body: null, tabs: null, aviso: null, save: null, close: null },

  init() {
    this.el.panel = document.getElementById("editorPanel");
    this.el.body = document.getElementById("editorBody");
    this.el.tabs = document.getElementById("editorTabs");
    this.el.aviso = document.getElementById("editorAviso");
    this.el.save = document.getElementById("editorSave");
    this.el.close = document.getElementById("editorClose");

    this.el.save.addEventListener("click", () => this.save());
    this.el.close.addEventListener("click", () => this.cerrarActiva());
  },

  // Carga Monaco una sola vez desde vendor/monaco. Si falta, reintentará en la próxima apertura.
  loadMonaco() {
    if (this.ready) return Promise.resolve(true);
    if (this.loading) return this.loading;
    this.loading = new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = "vendor/monaco/vs/loader.js";
      script.onerror = () => { this.loading = null; resolve(false); };
      script.onload = () => {
        require.config({ paths: { vs: "vendor/monaco/vs" } });
        require(["vs/editor/editor.main"], () => {
          this.monaco = window.monaco;
          this.ready = true;
          resolve(true);
        }, () => { this.loading = null; resolve(false); });
      };
      document.head.appendChild(script);
    });
    return this.loading;
  },

  langFromName(name) {
    const ext = (name.split(".").pop() || "").toLowerCase();
    const map = { js:"javascript", ts:"typescript", py:"python", sh:"shell", bash:"shell",
      html:"html", css:"css", json:"json", md:"markdown", rs:"rust", go:"go", c:"c",
      cpp:"cpp", java:"java", rb:"ruby", php:"php", sql:"sql", yml:"yaml", yaml:"yaml",
      xml:"xml", conf:"ini", ini:"ini", txt:"plaintext" };
    return map[ext] || "plaintext";
  },

  tabDe(path) {
    return this.tabs.find((t) => t.path === path) || null;
  },

  async open(path) {
    if (this.tabDe(path)) { this.activar(path); return; }

    const ok = await this.loadMonaco();
    if (!ok) {
      this.el.panel.classList.add("show");
      this.mostrarAviso("Editor no disponible: falta Monaco. Ejecuta ./scripts/fetch-monaco.sh una vez con internet.");
      return;
    }

    let contenido;
    try {
      const r = await API.readFile(path);
      if (!r.ok) {
        this.el.panel.classList.add("show");
        this.mostrarAviso("No se pudo abrir: " + (r.error || path));
        return;
      }
      contenido = r.content;
    } catch (e) {
      this.mostrarAviso("Error leyendo el archivo: " + e.message);
      return;
    }

    if (this.tabDe(path)) { this.activar(path); return; }   // se abrió mientras esperábamos

    this.seq += 1;
    const uri = this.monaco.Uri.parse(`goblin://archivo/${this.seq}/${encodeURIComponent(path)}`);
    const model = this.monaco.editor.createModel(contenido, this.langFromName(path), uri);
    const tab = { path, name: path.split("/").pop(), model, saved: contenido,
      dirty: false, armed: false, timer: null };
    model.onDidChangeContent(() => this.marcarSucio(tab));
    this.tabs.push(tab);
    this.activar(path);
  },

  activar(path) {
    const tab = this.tabDe(path);
    if (!tab) return;
    this.active = path;
    this.el.panel.classList.add("show");
    if (!this.instance) {
      this.instance = this.monaco.editor.create(this.el.body, {
        model: tab.model, theme: "vs-dark", fontSize: 13,
        fontFamily: '"JetBrains Mono", monospace', minimap: { enabled: true },
        automaticLayout: true, scrollBeyondLastLine: false,
      });
      // Ctrl+S guarda la pestaña activa
      this.instance.addCommand(this.monaco.KeyMod.CtrlCmd | this.monaco.KeyCode.KeyS, () => this.save());
    } else if (this.instance.getModel() !== tab.model) {
      this.instance.setModel(tab.model);
    }
    this.mostrarAviso(tab.armed ? this.textoAvisoCierre(tab) : "");
    this.pintarPestanas();
  },

  marcarSucio(tab) {
    const sucio = tab.model.getValue() !== tab.saved;
    if (sucio === tab.dirty) return;
    tab.dirty = sucio;
    if (!sucio) this.desarmar(tab);
    this.pintarPestanas();
  },

  desarmar(tab) {
    tab.armed = false;
    clearTimeout(tab.timer);
    if (this.active === tab.path) this.mostrarAviso("");
  },

  textoAvisoCierre(tab) {
    return `«${tab.name}» tiene cambios sin guardar. Pulsa ✕ otra vez para cerrarla sin guardar, o Ctrl+S para guardar.`;
  },

  // Primer clic en ✕ con cambios: aviso en línea. Segundo clic (en pocos segundos): cierra.
  cerrarPestana(path) {
    const tab = this.tabDe(path);
    if (!tab) return;
    if (tab.dirty && !tab.armed) {
      tab.armed = true;
      clearTimeout(tab.timer);
      tab.timer = setTimeout(() => { this.desarmar(tab); this.pintarPestanas(); }, 8000);
      this.activar(path);
      return;
    }
    this.quitar(tab);
  },

  cerrarActiva() {
    if (this.active) this.cerrarPestana(this.active);
  },

  quitar(tab) {
    const i = this.tabs.indexOf(tab);
    if (i < 0) return;
    this.tabs.splice(i, 1);
    clearTimeout(tab.timer);
    if (this.active === tab.path) {
      const siguiente = this.tabs[i] || this.tabs[i - 1];
      if (siguiente) this.activar(siguiente.path);
      else this.ocultar();
    }
    tab.model.dispose();
    this.pintarPestanas();
  },

  ocultar() {
    this.active = null;
    if (this.instance) this.instance.setModel(null);
    this.el.panel.classList.remove("show");
    this.mostrarAviso("");
    this.pintarPestanas();
  },

  async save(path = this.active) {
    const tab = path && this.tabDe(path);
    if (!tab) return;
    const contenido = tab.model.getValue();
    try {
      const r = await API.writeFile(tab.path, contenido);
      if (!r.ok) { this.mostrarAviso("No se pudo guardar: " + (r.error || "")); return; }
      tab.saved = contenido;
      this.marcarSucio(tab);
      this.destacarGuardado();
    } catch (e) {
      this.mostrarAviso("Error al guardar: " + e.message);
    }
  },

  destacarGuardado() {
    this.el.save.textContent = "✓ Guardado";
    clearTimeout(this.timerGuardado);
    this.timerGuardado = setTimeout(() => { this.el.save.textContent = "💾 Guardar"; }, 1500);
  },

  mostrarAviso(texto) {
    this.el.aviso.textContent = texto || "";
    this.el.aviso.hidden = !texto;
  },

  pintarPestanas() {
    const cont = this.el.tabs;
    cont.textContent = "";
    for (const t of this.tabs) {
      const esActiva = t.path === this.active;
      const pest = document.createElement("div");
      pest.className = "editor-tab" + (esActiva ? " active" : "") + (t.dirty ? " dirty" : "");
      pest.setAttribute("role", "tab");
      pest.setAttribute("aria-selected", String(esActiva));
      pest.title = t.path;

      const nombre = document.createElement("span");
      nombre.className = "editor-tab-name";
      nombre.textContent = t.name;
      pest.appendChild(nombre);

      if (t.dirty) {
        const punto = document.createElement("span");
        punto.className = "editor-tab-dot";
        punto.textContent = "●";
        punto.title = "Cambios sin guardar";
        pest.appendChild(punto);
      }

      const x = document.createElement("span");
      x.className = "editor-tab-x";
      x.textContent = "✕";
      x.title = "Cerrar pestaña";
      x.addEventListener("click", (e) => { e.stopPropagation(); this.cerrarPestana(t.path); });
      pest.appendChild(x);

      pest.addEventListener("click", () => this.activar(t.path));
      cont.appendChild(pest);
    }
  },
};
