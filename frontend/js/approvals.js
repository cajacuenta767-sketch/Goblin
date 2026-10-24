// === GOBLIN — Caja de aprobación ===
// Cuando la IA pide una acción peligrosa, se muestra aquí hasta que el usuario decide.

const Approvals = {
  el: { box: null, text: null, ok: null, deny: null },

  // Herramientas destructivas → borde rojo
  DANGEROUS: ["delete_path", "run_shell"],

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
    this.el.text.textContent = `${tool}\n${args}`;
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
