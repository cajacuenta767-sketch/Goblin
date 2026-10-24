// === GOBLIN — Capa de API (todas las llamadas al backend) ===
// El frontend NUNCA toca lógica: solo llama a estos endpoints.

const API = {
  async _post(path, body) {
    const r = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status} en ${path}`);
    return r.json();
  },

  async _get(path) {
    const r = await fetch(path);
    if (!r.ok) throw new Error(`HTTP ${r.status} en ${path}`);
    return r.json();
  },

  // Chat: envía un mensaje al agente
  chat(sessionId, message, model) {
    return this._post("/api/chat", { session_id: sessionId, message, model });
  },

  // Responde una aprobación pendiente
  approve(sessionId, approved) {
    return this._post("/api/approve", { session_id: sessionId, approved });
  },

  // Lista archivos de una ruta
  files(path = ".") {
    return this._get("/api/files?path=" + encodeURIComponent(path));
  },

  // Lee el contenido de un archivo (editor)
  readFile(path) {
    return this._get("/api/file?path=" + encodeURIComponent(path));
  },

  // Guarda el contenido de un archivo (editor)
  writeFile(path, content) {
    return this._post("/api/file", { path, content });
  },

  // Sesiones (persistencia)
  sessions() { return this._get("/api/sessions"); },
  sessionMessages(sid) { return this._get("/api/sessions/" + encodeURIComponent(sid)); },
  async deleteSession(sid) {
    const r = await fetch("/api/sessions/" + encodeURIComponent(sid), { method: "DELETE" });
    return r.json();
  },

  // Hallazgos e informe
  findings(sid) { return this._get("/api/findings/" + encodeURIComponent(sid)); },
  report(sid) { return this._get("/api/report/" + encodeURIComponent(sid)); },

  // Modo del router (local / hybrid / manual)
  mode(sid) { return this._get("/api/mode?session_id=" + encodeURIComponent(sid)); },
  setMode(sid, mode) { return this._post("/api/mode", { session_id: sid, mode }); },

  // Detener la respuesta en curso (Spec 024)
  stop(sid) { return this._post("/api/stop", { session_id: sid }); },

  // Marketplace de herramientas
  toolstore() { return this._get("/api/toolstore"); },
  installTool(toolId) { return this._post("/api/toolstore/install", { tool_id: toolId }); },

  // Modelos instalados en Ollama
  models() { return this._get("/api/models"); },

  // Info general de la app
  info() { return this._get("/api/info"); },

  // Estado de Ollama
  health() { return this._get("/api/health"); },

  // Diagnóstico de primer uso
  diagnostics() { return this._get("/api/diagnostics"); },

  // Target (Polybar)
  getTarget() { return this._get("/api/target"); },
  setTarget(target) { return this._post("/api/target", { target }); },

  // Uso de sistema (RAM/CPU) — si el backend lo expone
  async system() {
    try { return await this._get("/api/system"); }
    catch { return null; }
  },
};
