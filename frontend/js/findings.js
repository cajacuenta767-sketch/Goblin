// === GOBLIN — Panel de hallazgos + informe ===

const Findings = {
  el: { panel: null, list: null, count: null, report: null },

  SEV_COLOR: {
    critical: "var(--sev-critical)", high: "var(--sev-high)",
    medium: "var(--sev-medium)", low: "var(--sev-low)", info: "var(--sev-info)",
  },

  init() {
    this.el.panel = document.getElementById("findingsPanel");
    this.el.list = document.getElementById("findingsList");
    this.el.count = document.getElementById("findingsCount");
    this.el.report = document.getElementById("reportBtn");
    const toggle = document.getElementById("findingsToggle");
    if (toggle) toggle.addEventListener("click", () => this.el.panel.classList.toggle("open"));
    if (this.el.report) this.el.report.addEventListener("click", () => this.generateReport());
    this.refresh();
  },

  async refresh() {
    try {
      const r = await API.findings(Chat.sessionId);
      const items = r.findings || [];
      if (this.el.count) this.el.count.textContent = items.length;
      this.el.list.innerHTML = "";
      if (!items.length) {
        this.el.list.innerHTML = '<div class="finding-empty">Sin hallazgos aún.</div>';
        return;
      }
      for (const f of items) {
        const div = document.createElement("div");
        div.className = "finding";
        const color = this.SEV_COLOR[f.severity] || "var(--sev-info)";
        div.innerHTML = `<span class="sev" style="background:${color}"></span>
          <span class="finfo"><b class="ftitle"></b><span class="fmeta"></span></span>`;
        div.querySelector(".ftitle").textContent = f.title;
        div.querySelector(".fmeta").textContent =
          `${f.severity}${f.host ? " · " + f.host : ""}${f.port ? ":" + f.port : ""}`;
        this.el.list.appendChild(div);
      }
    } catch { /* ignore */ }
  },

  async generateReport() {
    try {
      const r = await API.report(Chat.sessionId);
      if (r.report) Chat.addMessage("ai", r.report, "DeepHat");
    } catch (e) {
      Chat.addMessage("error", "No se pudo generar el informe: " + e.message);
    }
  },
};
