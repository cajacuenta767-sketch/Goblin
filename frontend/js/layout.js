// === GOBLIN — Layout con ratón (Spec 040) ===
// Divisores arrastrables, paneles que se acoplan a otra zona arrastrando su cabecera y
// disposición guardada en localStorage. Solo ratón.
// Los nodos se MUEVEN, no se recrean: el chat, la terminal y el editor conservan su estado.

const Layout = {
  KEY: "goblin.layout.v1",
  MIN: 120,                       // tamaño mínimo de un panel al arrastrar un divisor (px)
  ZONES: ["left", "center", "right"],
  PANELS: ["sidebar", "chat", "terminal", "right", "engagement"],
  IDS: { sidebar: "sidebar", chat: "chat", terminal: "termPanel", right: "right", engagement: "engPanel" },
  LABEL: { sidebar: "Barra lateral", chat: "Chat", terminal: "Terminal", right: "Explorador y editor", engagement: "Engagement" },
  // Proporción por defecto dentro de su zona (crecimiento flex; al arrastrar pasa a píxeles).
  GROW: { sidebar: 60, engagement: 40, chat: 78, terminal: 22, right: 1 },
  // Proporción para un panel que llega a una zona nueva.
  GROW_NUEVO: { sidebar: 50, engagement: 30, chat: 60, terminal: 25, right: 50 },

  state: null,
  zone: {},          // left/center/right → contenedor
  split: {},         // "lc" y "cr" → divisores verticales
  justDocked: false,

  defaults() {
    return {
      zones: { left: ["sidebar", "engagement"], center: ["chat", "terminal"], right: ["right"] },
      widths: { left: 240, right: 300 },
      grow: { ...this.GROW },
      collapsed: {},
    };
  },

  el(id) { return document.getElementById(this.IDS[id]); },

  init() {
    const main = document.getElementById("main");
    if (!main) return;
    for (const z of this.ZONES) {
      const div = document.createElement("div");
      div.className = "zone";
      div.id = "zone-" + z;
      this.zone[z] = div;
    }
    this.split.lc = this.makeSplitV("lc");
    this.split.cr = this.makeSplitV("cr");
    main.append(this.zone.left, this.split.lc, this.zone.center, this.split.cr, this.zone.right);

    for (const id of this.PANELS) {
      const el = this.el(id);
      if (el) el.classList.add("dock-panel");
    }
    this.load();
    this.wireHandles();
    // Un clic que termina un arrastre no debe activar el botón de debajo.
    document.addEventListener("click", (ev) => {
      if (this.justDocked) { ev.stopPropagation(); ev.preventDefault(); }
    }, true);
    window.addEventListener("resize", () => this.apply());
    this.apply();
  },

  // ---------- Estado guardado ----------
  load() {
    let saved = null;
    try { saved = JSON.parse(localStorage.getItem(this.KEY) || "null"); } catch { saved = null; }
    this.state = this.valid(saved) ? this.complete(saved) : this.defaults();
  },

  valid(s) {
    if (!s || !s.zones || !s.widths || !s.grow) return false;
    const ids = this.ZONES.flatMap((z) => (Array.isArray(s.zones[z]) ? s.zones[z] : []));
    const unicos = new Set(ids);
    if (unicos.size !== ids.length) return false;                       // un panel en dos sitios
    return ids.every((id) => this.PANELS.includes(id));
  },

  // Un panel nuevo (que la versión guardada no conoce) entra en el centro al final.
  complete(s) {
    const presentes = new Set(this.ZONES.flatMap((z) => s.zones[z]));
    for (const id of this.PANELS) {
      if (!presentes.has(id)) s.zones.center.push(id);
      if (!(id in s.grow)) s.grow[id] = this.GROW_NUEVO[id] || 30;
    }
    s.collapsed = s.collapsed || {};
    return s;
  },

  save() {
    try { localStorage.setItem(this.KEY, JSON.stringify(this.state)); } catch { /* sin almacenamiento: no pasa nada */ }
  },

  reset() {
    this.state = this.defaults();
    this.save();
    this.apply();
  },

  // ---------- Aplicar la disposición al DOM ----------
  apply() {
    const st = this.state;
    for (const z of this.ZONES) {
      for (const id of st.zones[z]) {
        const el = this.el(id);
        if (el) this.zone[z].appendChild(el);      // mover, no recrear
      }
    }
    for (const z of this.ZONES) this.layoutZone(z);

    const sidebar = this.el("sidebar");
    const iconos = !!(sidebar && sidebar.classList.contains("collapsed"));
    const izq = this.zoneShown("left");
    const cen = this.zoneShown("center");
    const der = this.zoneShown("right");
    this.zone.left.style.display = izq ? "" : "none";
    this.zone.right.style.display = der ? "" : "none";
    this.zone.left.style.width = (iconos ? 44 : st.widths.left) + "px";
    this.zone.right.style.width = st.widths.right + "px";
    this.split.lc.style.display = izq && cen ? "" : "none";
    this.split.lc.classList.toggle("disabled", iconos);
    this.split.cr.style.display = cen && der ? "" : "none";
    this.fitTerminal();
  },

  zoneShown(z) {
    return this.state.zones[z].some((id) => {
      const el = this.el(id);
      return el && getComputedStyle(el).display !== "none";
    });
  },

  // Coloca los divisores horizontales entre paneles visibles y fija el tamaño de cada uno.
  layoutZone(z) {
    const zone = this.zone[z];
    zone.querySelectorAll(":scope > .splitter.h").forEach((n) => n.remove());
    let anterior = null;
    for (const id of this.state.zones[z]) {
      const el = this.el(id);
      if (!el) continue;
      el.style.flex = this.flexFor(id);
      el.classList.toggle("dock-collapsed", !!this.state.collapsed[id]);
      if (!this.shown(el)) continue;
      if (anterior) zone.insertBefore(this.makeSplitH(), el);
      anterior = el;
    }
  },

  flexFor(id) {
    if (this.state.collapsed[id]) return "0 0 auto";
    const g = this.state.grow[id] || 1;
    return `${g} 1 0px`;
  },

  shown(el) { return !!el && getComputedStyle(el).display !== "none"; },

  // ---------- Divisores ----------
  makeSplitV(which) {
    const d = document.createElement("div");
    d.className = "splitter v";
    d.title = "Arrastra para cambiar el ancho";
    d.addEventListener("pointerdown", (e) => this.dragV(e, which, d));
    return d;
  },

  makeSplitH() {
    const d = document.createElement("div");
    d.className = "splitter h";
    d.title = "Arrastra para cambiar el alto";
    d.addEventListener("pointerdown", (e) => this.dragH(e, d));
    return d;
  },

  dragV(e, which, splitter) {
    if (e.button !== 0 || splitter.classList.contains("disabled")) return;
    e.preventDefault();
    const x0 = e.clientX;
    const zona = which === "lc" ? this.zone.left : this.zone.right;
    const w0 = zona.getBoundingClientRect().width;
    splitter.classList.add("active");
    document.body.classList.add("dragging");
    const move = (ev) => {
      const dx = ev.clientX - x0;
      const max = window.innerWidth - 400;
      if (which === "lc") {
        this.state.widths.left = this.clamp(w0 + dx, 160, max);
        this.zone.left.style.width = this.state.widths.left + "px";
      } else {
        this.state.widths.right = this.clamp(w0 - dx, 200, max);
        this.zone.right.style.width = this.state.widths.right + "px";
      }
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      splitter.classList.remove("active");
      document.body.classList.remove("dragging");
      this.save();
      this.fitTerminal();
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up, { once: true });
  },

  dragH(e, splitter) {
    if (e.button !== 0) return;
    const a = this.prevShown(splitter);
    const b = this.nextShown(splitter);
    if (!a || !b) return;
    e.preventDefault();
    const zona = splitter.parentElement;
    const visibles = [...zona.children].filter((n) => n.classList.contains("dock-panel") && this.shown(n));
    // Fijar todos en píxeles actuales: así el resto de paneles no cambia al arrastrar el par.
    const px = new Map(visibles.map((n) => [n, n.getBoundingClientRect().height]));
    for (const n of visibles) {
      const id = this.idOf(n);
      this.state.grow[id] = px.get(n);
      n.style.flex = `${px.get(n)} 1 0px`;
    }
    const total = px.get(a) + px.get(b);
    if (total < 2 * this.MIN) return;
    const a0 = px.get(a);
    const y0 = e.clientY;
    const idA = this.idOf(a), idB = this.idOf(b);
    splitter.classList.add("active");
    document.body.classList.add("dragging");
    const move = (ev) => {
      const na = this.clamp(a0 + (ev.clientY - y0), this.MIN, total - this.MIN);
      this.state.grow[idA] = na;
      this.state.grow[idB] = total - na;
      a.style.flex = `${na} 1 0px`;
      b.style.flex = `${total - na} 1 0px`;
      this.fitTerminal();
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      splitter.classList.remove("active");
      document.body.classList.remove("dragging");
      this.save();
      this.fitTerminal();
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up, { once: true });
  },

  prevShown(n) {
    let p = n.previousElementSibling;
    while (p && !(p.classList.contains("dock-panel") && this.shown(p))) p = p.previousElementSibling;
    return p;
  },

  nextShown(n) {
    let p = n.nextElementSibling;
    while (p && !(p.classList.contains("dock-panel") && this.shown(p))) p = p.nextElementSibling;
    return p;
  },

  idOf(el) {
    return this.PANELS.find((id) => this.el(id) === el);
  },

  // ---------- Acoplar: arrastrar la cabecera a otra zona ----------
  wireHandles() {
    for (const id of this.PANELS) {
      const el = this.el(id);
      const h = el && el.querySelector(":scope > .dock-handle");
      if (!h) continue;
      h.addEventListener("pointerdown", (e) => this.startDock(e, id));
      if (id !== "sidebar") {
        h.addEventListener("dblclick", (e) => {
          if (e.target.closest("button, input, .eng-tab")) return;
          this.toggleCollapse(id);
        });
      }
    }
  },

  startDock(e, id) {
    if (e.button !== 0) return;
    const x0 = e.clientX, y0 = e.clientY;
    let activo = false, objetivo = null, fantasma = null, linea = null, borde = null;

    const onMove = (ev) => {
      if (!activo) {
        if (Math.hypot(ev.clientX - x0, ev.clientY - y0) < 6) return;   // umbral: no es un clic
        activo = true;
        document.body.classList.add("dragging");
        fantasma = document.createElement("div");
        fantasma.className = "dock-ghost";
        fantasma.textContent = this.LABEL[id];
        linea = document.createElement("div");
        linea.className = "dock-indicator";
        borde = document.createElement("div");
        borde.className = "dock-edge";
        document.body.append(fantasma, linea, borde);
      }
      fantasma.style.left = ev.clientX + 14 + "px";
      fantasma.style.top = ev.clientY + 14 + "px";
      objetivo = this.dropAt(ev.clientX, ev.clientY, id);
      this.showTarget(objetivo, linea, borde);
    };

    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      if (activo) {
        if (objetivo) this.moveTo(id, objetivo.zone, objetivo.index);
        fantasma.remove(); linea.remove(); borde.remove();
        document.body.classList.remove("dragging");
        this.justDocked = true;
        setTimeout(() => { this.justDocked = false; }, 300);
      }
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp, { once: true });
  },

  // Dónde caería el panel con el puntero en (x, y): zona + posición entre los paneles visibles.
  dropAt(x, y, movingId) {
    const W = window.innerWidth;
    const otrosDe = (z) => this.state.zones[z].filter((i) => i !== movingId);
    if (x < 28) return { zone: "left", index: otrosDe("left").length, edge: true };
    if (x > W - 28) return { zone: "right", index: otrosDe("right").length, edge: true };
    for (const z of this.ZONES) {
      const zona = this.zone[z];
      if (zona.style.display === "none") continue;
      const r = zona.getBoundingClientRect();
      if (x < r.left || x > r.right || y < r.top || y > r.bottom) continue;
      const otros = [...zona.children].filter((n) =>
        n.classList.contains("dock-panel") && this.idOf(n) !== movingId && this.shown(n));
      let index = otros.length;
      for (let i = 0; i < otros.length; i++) {
        const br = otros[i].getBoundingClientRect();
        if (y < br.top + br.height / 2) { index = i; break; }
      }
      return { zone: z, index, otros, rect: r };
    }
    return null;
  },

  showTarget(t, linea, borde) {
    borde.style.display = t && t.edge ? "block" : "none";
    if (t && t.edge) {
      borde.style.left = t.zone === "left" ? "0" : "";
      borde.style.right = t.zone === "right" ? "0" : "";
    }
    if (!t || t.edge) { linea.style.display = "none"; return; }
    linea.style.display = "block";
    const r = t.rect;
    linea.style.left = r.left + "px";
    linea.style.width = r.width + "px";
    if (t.otros.length === 0) {
      linea.style.top = r.top + "px";
    } else if (t.index < t.otros.length) {
      linea.style.top = t.otros[t.index].getBoundingClientRect().top - 2 + "px";
    } else {
      linea.style.top = t.otros[t.otros.length - 1].getBoundingClientRect().bottom - 2 + "px";
    }
  },

  moveTo(id, z, index) {
    const st = this.state;
    const previa = this.ZONES.find((k) => st.zones[k].includes(id));
    for (const k of this.ZONES) st.zones[k] = st.zones[k].filter((x) => x !== id);
    const lista = st.zones[z];
    lista.splice(Math.min(index, lista.length), 0, id);
    // Al cambiar de zona, el panel toma el tamaño de su nueva zona; al reordenar, conserva el suyo.
    if (previa !== z) st.grow[id] = this.GROW_NUEVO[id] || 30;
    this.save();
    this.apply();
  },

  toggleCollapse(id) {
    this.state.collapsed[id] = !this.state.collapsed[id];
    this.save();
    this.apply();
  },

  fitTerminal() {
    requestAnimationFrame(() => {
      if (typeof Terminal_ !== "undefined" && Terminal_.open && Terminal_.fit) {
        try { Terminal_.fit.fit(); Terminal_.sendResize(); } catch { /* terminal aún no iniciada */ }
      }
    });
  },

  clamp(v, min, max) { return Math.max(min, Math.min(max, v)); },
};
