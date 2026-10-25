// === GOBLIN — Panel de engagement: alcance, hosts y snippets (Spec 041) ===
// El alcance lo edita SOLO el usuario aquí; la IA no puede ampliarlo (Spec 036).
// Todo se pinta con textContent: los datos de la base nunca se interpretan como HTML.

const Engagement = {
  el: {},
  tab: "scope",

  init() {
    this.el.panel = document.getElementById("engPanel");
    this.el.scopeInput = document.getElementById("scopeInput");
    this.el.termInput = document.getElementById("termInput");
    this.el.scopeList = document.getElementById("scopeList");
    this.el.termList = document.getElementById("termList");
    this.el.hostsBody = document.getElementById("hostsBody");
    this.el.snips = document.getElementById("snipList");
    this.el.note = document.getElementById("engNote");
    if (!this.el.panel) return;

    this.el.panel.querySelectorAll(".eng-tab").forEach((t) =>
      t.addEventListener("click", () => this.show(t.dataset.tab)));
    document.getElementById("scopeAdd").addEventListener("click", () => this.add("scope", this.el.scopeInput));
    document.getElementById("termAdd").addEventListener("click", () => this.add("term", this.el.termInput));
    this.el.scopeInput.addEventListener("keydown", (e) => { if (e.key === "Enter") this.add("scope", this.el.scopeInput); });
    this.el.termInput.addEventListener("keydown", (e) => { if (e.key === "Enter") this.add("term", this.el.termInput); });
    this.loadSnippets();
    this.refresh();
  },

  sid() { return Chat.sessionId; },

  show(tab) {
    this.tab = tab;
    this.el.panel.querySelectorAll(".eng-tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === tab));
    this.el.panel.querySelectorAll(".eng-pane").forEach((p) => { p.hidden = p.dataset.pane !== tab; });
    if (tab === "hosts") this.refresh();
  },

  note(msg, error = false) {
    this.el.note.textContent = msg || "";
    this.el.note.classList.toggle("err", !!error);
  },

  async add(kind, input) {
    const texto = input.value.trim();
    if (!texto) return;
    try {
      const d = await API.scopeAdd(this.sid(), kind, texto);
      input.value = "";
      this.render(d);
      this.note(kind === "scope" ? "Añadido al alcance." : "Término añadido. Nunca sale a la nube.");
    } catch (e) {
      this.note(e.message, true);
    }
  },

  async remove(kind, entry) {
    try {
      this.render(await API.scopeRemove(this.sid(), kind, entry));
      this.note("Quitado.");
    } catch (e) {
      this.note(e.message, true);
    }
  },

  async refresh() {
    if (!this.el.panel) return;
    try { this.render(await API.scope(this.sid())); } catch { /* backend sin responder: se reintenta */ }
    try { this.renderHosts((await API.hosts(this.sid())).hosts || []); } catch { /* idem */ }
  },

  render(d) {
    this.renderList(this.el.scopeList, d.scope || [], "scope");
    this.renderList(this.el.termList, d.terms || [], "term");
  },

  renderList(ul, items, kind) {
    ul.replaceChildren();
    if (!items.length) {
      const vacio = document.createElement("div");
      vacio.className = "eng-empty";
      vacio.textContent = kind === "scope"
        ? "Sin objetivos. Añade la IP, el rango o el dominio autorizado por escrito."
        : "Sin términos. Añade nombres de cliente o dominios que no deban salir a la nube.";
      ul.append(vacio);
      return;
    }
    for (const it of items) {
      const fila = document.createElement("div");
      fila.className = "eng-item";
      const texto = document.createElement("span");
      texto.textContent = it;
      texto.title = it;
      const quitar = document.createElement("button");
      quitar.className = "eng-x";
      quitar.textContent = "✕";
      quitar.title = "Quitar";
      quitar.addEventListener("click", () => this.remove(kind, it));
      fila.append(texto, quitar);
      ul.append(fila);
    }
  },

  renderHosts(hosts) {
    const body = this.el.hostsBody;
    body.replaceChildren();
    if (!hosts.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 4;
      td.className = "eng-empty";
      td.textContent = "Sin puertos. Se llenan cuando nmap termina un escaneo.";
      tr.append(td);
      body.append(tr);
      return;
    }
    for (const h of hosts) {
      const tr = document.createElement("tr");
      for (const valor of [h.host, `${h.port}/${h.proto}`, h.service || "", h.version || ""]) {
        const td = document.createElement("td");
        td.textContent = valor;
        tr.append(td);
      }
      body.append(tr);
    }
  },

  // Snippets: clic los pone en el campo de entrada. No los ejecuta.
  async loadSnippets() {
    try {
      const d = await API.snippets();
      this.el.snips.replaceChildren();
      for (const [cat, items] of Object.entries(d.categories || {})) {
        const titulo = document.createElement("div");
        titulo.className = "eng-snip-cat";
        titulo.textContent = cat.replace(/_/g, " ");
        this.el.snips.append(titulo);
        for (const it of items) {
          const b = document.createElement("button");
          b.className = "eng-snip";
          b.textContent = it.name;
          b.title = "Insertar en el campo de entrada (no se ejecuta)";
          b.addEventListener("click", () => this.insert(it.code, it.name));
          this.el.snips.append(b);
        }
      }
    } catch {
      this.el.snips.textContent = "No pude cargar los snippets.";
    }
  },

  insert(code, name) {
    Chat.el.input.value = code;
    Chat.el.input.dispatchEvent(new Event("input"));
    Chat.el.input.focus();
    this.note(`Insertado «${name}». Revísalo antes de enviar.`);
  },
};
