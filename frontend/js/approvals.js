// === GOBLIN — Caja de aprobación ===
// Cuando la IA pide una acción peligrosa, se muestra aquí hasta que el usuario decide.

const Approvals = {
  el: { box: null, text: null, ok: null, deny: null },

  // Herramientas destructivas → borde rojo
  DANGEROUS: ["delete_path", "run_shell", "set_target"],

  init() {
    this.el.box = document.getElementById("approval");
    this.el.text = document.getElementById("approvalText");
    this.el.ok = document.getElementById("approveBtn");
    this.el.deny = document.getElementById("denyBtn");

    this.el.ok.addEventListener("click", () => this.decide(true));
    this.el.deny.addEventListener("click", () => this.decide(false));
  },

  show(resp) {
    const tool = resp.tool;
    const args = JSON.stringify(resp.args, null, 2);
    // Fijar un objetivo exige confirmar la autorización por escrito (Spec 025)
    const aviso = tool === "set_target"
      ? "⚠️ Confirma que tienes autorización POR ESCRITO para este objetivo antes de aprobar.\n\n"
      : "";
    this.el.text.textContent = `${aviso}${tool}\n${args}`;
    // Spec 037, RF2: diff con líneas añadidas (verde) y quitadas (rojo). Todo con textContent.
    const caja = document.getElementById("approvalDiff");
    if (caja) {
      caja.replaceChildren();
      if (resp.diff) {
        for (const ln of resp.diff.split("\n")) {
          const fila = document.createElement("div");
          fila.textContent = ln;
          if (ln.startsWith("+++") || ln.startsWith("---")) fila.className = "hunk";
          else if (ln.startsWith("+")) fila.className = "add";
          else if (ln.startsWith("-")) fila.className = "del";
          else if (ln.startsWith("@@")) fila.className = "hunk";
          caja.append(fila);
        }
        caja.hidden = false;
      } else {
        caja.hidden = true;
      }
    }
    this.el.box.classList.toggle("danger", this.DANGEROUS.includes(tool));
    this.el.box.style.display = "block";
    Chat.scrollDown();
  },

  hide() { this.el.box.style.display = "none"; },

  async decide(approved) {
    this.hide();
    Chat.setBusy(true);
    try {
      const resp = await API.approve(Chat.sessionId, approved);
      Chat.handle(resp);
    } catch (e) {
      Chat.addMessage("error", "Error al procesar la aprobación: " + e.message);
      Chat.setBusy(false);
    }
  },
};
