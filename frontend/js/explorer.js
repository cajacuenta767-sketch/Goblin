// === GOBLIN — Explorador de archivos ===
// Lista el contenido real del workspace/sistema vía /api/files.
// El backend devuelve el listado como texto; aquí lo parseamos a items.

const Explorer = {
  el: { list: null, path: null, refresh: null, view: null },
  cwd: ".",

  init() {
    this.el.list = document.getElementById("wsList");
    this.el.path = document.getElementById("wsPath");
    this.el.refresh = document.getElementById("wsRefresh");
    this.el.view = document.getElementById("wsView");

    this.el.refresh.addEventListener("click", () => this.load(this.cwd));
    this.load(".");
  },

  // Parsea la salida de list_dir: líneas "[DIR ] nombre" o "[FILE] nombre (123 B)"
  parse(listing) {
    const items = [];
    const lines = (listing || "").split("\n");
    for (const line of lines) {
      const m = line.match(/^\[(DIR |FILE)\]\s+(.+?)(?:\s+\(\d+\s*B\))?$/);
      if (m) {
        items.push({ isDir: m[1].trim() === "DIR", name: m[2].trim() });
      }
    }
    return items;
  },

  async load(path) {
    try {
      const resp = await API.files(path);
      if (!resp.ok) { this.el.list.innerHTML = `<div class="ws-item">${resp.error || "error"}</div>`; return; }
      this.cwd = path;
      // primera línea del listing suele ser "Contenido de /ruta:"
      const firstLine = (resp.listing || "").split("\n")[0] || "";
      const shownPath = firstLine.replace(/^Contenido de /, "").replace(/:$/, "");
      this.el.path.textContent = shownPath || path;
      this.el.path.title = shownPath || path;

      const items = this.parse(resp.listing);
      this.el.list.innerHTML = "";
      this.el.view.classList.remove("show");

      // botón "subir"
      const up = document.createElement("div");
      up.className = "ws-item dir";
      up.textContent = "📁 ..";
      up.addEventListener("click", () => this.load(this._parent(shownPath || path)));
      this.el.list.appendChild(up);

      for (const it of items) {
        const div = document.createElement("div");
        div.className = "ws-item" + (it.isDir ? " dir" : "");
        div.textContent = (it.isDir ? "📁 " : "📄 ") + it.name;
        const full = this._join(shownPath || path, it.name);
        div.addEventListener("click", () => it.isDir ? this.load(full) : this.view(full));
        this.el.list.appendChild(div);
      }
    } catch (e) {
      this.el.list.innerHTML = `<div class="ws-item">No se pudo listar: ${e.message}</div>`;
    }
  },

  view(path) {
    // Abre el archivo en el editor Monaco (Spec 007)
    if (window.Editor) Editor.open(path);
  },

  refresh() { this.load(this.cwd); },

  _parent(p) {
    if (!p || p === "/" || p === ".") return ".";
    const parts = p.replace(/\/+$/,"").split("/");
    parts.pop();
    return parts.length ? parts.join("/") || "/" : "/";
  },

  _join(base, name) {
    if (base === "." || base === "") return name;
    return base.replace(/\/+$/,"") + "/" + name;
  },
};
