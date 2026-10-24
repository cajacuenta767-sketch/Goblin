#!/usr/bin/env python3
"""
apply_spec022.py — Aplica la Spec 022 (respaldo de tool-calling) a GOBLIN.

Lo escribió Claude completo. Este script hace ediciones MECÁNICAS (reemplazo de
texto exacto, con verificación), NO interpreta ni reescribe código. Si algo no
coincide exacto con lo esperado, ABORTA sin tocar nada y te dice qué pasó.

Qué hace:
  1. Crea backend/text_toolcall.py (el parser de respaldo).
  2. Edita backend/agent.py:
       - añade el import del parser
       - añade la clase _FakeCall
       - ajusta el SYSTEM_PROMPT (para que no dispare herramientas con un "hola")
       - engancha el respaldo en el bucle _step()
  3. Crea el symlink ~/goblin -> la carpeta real (para que la app nativa
     encuentre el backend).
  4. Imprime info de verificación (DEFAULT_MODEL y schema de run_shell) para
     revisar que el nombre del argumento coincide.

Uso:
  python3 apply_spec022.py                      # usa /home/hide/Downloads/Goblin
  python3 apply_spec022.py /ruta/a/Goblin       # o la ruta que le pases

Hace copia de seguridad: backend/agent.py.bak-spec022
Es idempotente: si ya está aplicado, lo detecta y no lo duplica.
"""

import os
import sys
import shutil

PROJECT = sys.argv[1] if len(sys.argv) > 1 else "/home/hide/Downloads/Goblin"

# ---------------------------------------------------------------------------
# Contenido del parser (idéntico al probado por Claude).
# ---------------------------------------------------------------------------
TEXT_TOOLCALL = r'''"""
backend/text_toolcall.py

Respaldo de tool-calling por texto (Spec 022).

La plantilla de Ollama de DeepHat YA soporta <tool_call>...</tool_call> y el
backend SÍ pasa tools=SCHEMAS. El problema es que DeepHat-V1-7B, por ser un
modelo pequeño, no respeta el formato de forma fiable: a veces emite la llamada
como texto suelto, incluso con comillas simples estilo Python
({'command': 'whoami', 'cwd': '/home/user'}). Ollama solo reconoce el formato
exacto, así que tool_calls llega vacío y el texto crudo termina en el chat.

Este parser recupera esas llamadas mal formateadas. Para evitar falsos positivos
solo devuelve algo si reconoce una herramienta real; además run_shell y las
demás peligrosas siguen pasando por aprobación.
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any

try:
    from tools.registry import TOOLS as _REGISTRY_TOOLS  # type: ignore
    _KNOWN = set(_REGISTRY_TOOLS.keys())
except Exception:  # noqa: BLE001
    _KNOWN = {
        "list_dir", "read_file", "write_file", "make_dir", "move_path",
        "copy_path", "delete_path", "search_files", "disk_usage", "run_shell",
        "add_finding", "generate_report", "set_target", "clear_target",
        "get_target", "get_snippet", "parse_nmap", "parse_nikto",
        "term_run", "term_read",
    }

_TOOLCALL_TAG_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
_FIRST_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def _loads_any(raw: str) -> dict[str, Any] | None:
    raw = raw.strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, ValueError):
        pass
    try:
        data = ast.literal_eval(raw)
        return data if isinstance(data, dict) else None
    except (ValueError, SyntaxError):
        return None


def _infer_tool(data: dict[str, Any]) -> str | None:
    name = data.get("name") or data.get("tool") or data.get("function")
    if isinstance(name, str) and name in _KNOWN:
        return name
    keys = set(data.keys())
    if ("command" in keys or "cmd" in keys) and "run_shell" in _KNOWN:
        return "run_shell"
    if {"path", "content"} <= keys and "write_file" in _KNOWN:
        return "write_file"
    if keys == {"path"} and "read_file" in _KNOWN:
        return "read_file"
    return None


def _extract_args(data: dict[str, Any]) -> dict[str, Any]:
    if isinstance(data.get("arguments"), dict):
        return dict(data["arguments"])
    if isinstance(data.get("args"), dict):
        return dict(data["args"])
    args = dict(data)
    for meta in ("name", "tool", "function", "arguments", "args"):
        args.pop(meta, None)
    return args


def parse_text_toolcall(content: str) -> dict[str, Any] | None:
    if not content or "{" not in content:
        return None
    candidates: list[str] = []
    tagged = _TOOLCALL_TAG_RE.search(content)
    if tagged:
        candidates.append(tagged.group(1))
    else:
        first = _FIRST_OBJ_RE.search(content)
        if first:
            candidates.append(first.group(0))
    for raw in candidates:
        data = _loads_any(raw)
        if data is None:
            continue
        tool = _infer_tool(data)
        if tool is None:
            continue
        return {"tool": tool, "args": _extract_args(data)}
    return None
'''

# ---------------------------------------------------------------------------
# Ediciones en agent.py (reemplazo exacto).
# ---------------------------------------------------------------------------
IMPORT_ANCHOR = "from tools import SCHEMAS, NEEDS_APPROVAL, run_tool\n"
IMPORT_ADD = IMPORT_ANCHOR + "from text_toolcall import parse_text_toolcall\n"

FAKECALL_ANCHOR = "client = Client(host=config.OLLAMA_HOST)\n"
FAKECALL_ADD = FAKECALL_ANCHOR + (
    "\n\n"
    "class _FakeCall:\n"
    '    """Imita una tool_call de Ollama para el respaldo por texto (Spec 022)."""\n'
    "    def __init__(self, name, args):\n"
    '        self.function = type("F", (), {"name": name, "arguments": args})()\n'
)

PROMPT_OLD = (
    "explica en una frase qué harás y por qué. Usa SIEMPRE las herramientas para actuar \"\n"
    "    \"sobre el sistema, no solo describas los comandos. Responde en español. "
)
PROMPT_NEW = (
    "explica en una frase qué harás y por qué. Usa herramientas SOLO cuando el usuario \"\n"
    "    \"pida una acción concreta sobre el sistema; ante saludos o preguntas generales, \"\n"
    "    \"responde en texto y no llames ninguna herramienta. Responde en español. "
)

STEP_OLD = (
    "        if not msg.tool_calls:\n"
    '            s["steps"] = 0\n'
    "            # Guardar la respuesta final de la IA en la base de datos.\n"
)
STEP_NEW = (
    "        if not msg.tool_calls:\n"
    "            # Respaldo (Spec 022): DeepHat a veces escribe la tool call como\n"
    "            # texto suelto en vez del formato <tool_call> nativo. La recuperamos.\n"
    '            fallback = parse_text_toolcall(msg.content or "")\n'
    "            if fallback is not None:\n"
    "                print(f\"[GOBLIN] Tool call recuperada por texto: {fallback['tool']}\")\n"
    '                s["queue"] = [_FakeCall(fallback["tool"], fallback["args"])]\n'
    "                continue\n"
    '            s["steps"] = 0\n'
    "            # Guardar la respuesta final de la IA en la base de datos.\n"
)


def fail(msg):
    print(f"\n[ABORTADO] {msg}")
    print("No se modificó nada (o se restauró la copia). Revisa y dime qué salió.")
    sys.exit(1)


def patch_once(text, old, new, label):
    if new.split("\n")[1] in text or (label == "import" and IMPORT_ADD.strip() in text):
        print(f"  [ya aplicado] {label}")
        return text
    n = text.count(old)
    if n == 0:
        fail(f"No encontré el texto a cambiar para «{label}». "
             f"Quizá el archivo ya cambió. Pega agent.py y lo reviso.")
    if n > 1:
        fail(f"El texto de «{label}» aparece {n} veces; no es seguro reemplazar.")
    print(f"  [ok] {label}")
    return text.replace(old, new, 1)


def main():
    backend = os.path.join(PROJECT, "backend")
    agent = os.path.join(backend, "agent.py")
    if not os.path.isfile(agent):
        fail(f"No existe {agent}. Pásame la ruta correcta: python3 apply_spec022.py /ruta/Goblin")

    print(f"=== Spec 022 en {PROJECT} ===")

    # 1) parser
    tc_path = os.path.join(backend, "text_toolcall.py")
    with open(tc_path, "w", encoding="utf-8") as f:
        f.write(TEXT_TOOLCALL)
    print(f"[1] Creado {tc_path}")

    # 2) agent.py
    with open(agent, encoding="utf-8") as f:
        src = f.read()
    bak = agent + ".bak-spec022"
    if not os.path.exists(bak):
        shutil.copy2(agent, bak)
        print(f"[2] Copia de seguridad: {bak}")

    print("[2] Editando agent.py:")
    if IMPORT_ADD.strip() not in src:
        if src.count(IMPORT_ANCHOR) != 1:
            fail("No encontré la línea de import de tools de forma única.")
        src = src.replace(IMPORT_ANCHOR, IMPORT_ADD, 1)
        print("  [ok] import parse_text_toolcall")
    else:
        print("  [ya aplicado] import")

    if "class _FakeCall:" not in src:
        if src.count(FAKECALL_ANCHOR) != 1:
            fail("No encontré la línea del Client de Ollama de forma única.")
        src = src.replace(FAKECALL_ANCHOR, FAKECALL_ADD, 1)
        print("  [ok] clase _FakeCall")
    else:
        print("  [ya aplicado] _FakeCall")

    src = patch_once(src, PROMPT_OLD, PROMPT_NEW, "SYSTEM_PROMPT")
    src = patch_once(src, STEP_OLD, STEP_NEW, "bucle _step (respaldo)")

    with open(agent, "w", encoding="utf-8") as f:
        f.write(src)
    print("[2] agent.py guardado.")

    # verificación de sintaxis
    import py_compile
    try:
        py_compile.compile(agent, doraise=True)
        py_compile.compile(tc_path, doraise=True)
        print("[2] Sintaxis OK (py_compile).")
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, agent)
        fail(f"Error de sintaxis tras editar; restauré la copia. Detalle: {e}")

    # 3) symlink
    home = os.path.expanduser("~")
    link = os.path.join(home, "goblin")
    try:
        real = os.path.realpath(PROJECT)
        if os.path.islink(link) or os.path.exists(link):
            if os.path.realpath(link) == real:
                print(f"[3] Symlink ~/goblin ya apunta a {real}")
            else:
                print(f"[3] OJO: ~/goblin ya existe y apunta a otra cosa. No lo toco.")
        else:
            os.symlink(real, link)
            print(f"[3] Symlink creado: ~/goblin -> {real}")
    except OSError as e:
        print(f"[3] No pude crear el symlink (hazlo a mano): ln -sfn {real} ~/goblin  ({e})")

    # 4) info de verificación
    print("\n=== Verificación (pégale esto a Claude) ===")
    cfg = os.path.join(backend, "config.py")
    if os.path.isfile(cfg):
        with open(cfg, encoding="utf-8") as f:
            for line in f:
                if "DEFAULT_MODEL" in line:
                    print("DEFAULT_MODEL:", line.strip())
    print("\nSchema de run_shell (para confirmar el nombre del argumento):")
    found = False
    for root, _, files in os.walk(os.path.join(backend, "tools")):
        for fn in files:
            if fn.endswith(".py"):
                p = os.path.join(root, fn)
                with open(p, encoding="utf-8") as f:
                    txt = f.read()
                if "run_shell" in txt and ("properties" in txt or "parameters" in txt):
                    print(f"  (ver {p} — busca el schema de run_shell ahí)")
                    found = True
    if not found:
        print("  (no lo ubiqué automáticamente; pega tools/registry.py)")

    print("\n=== LISTO ===")
    print("Ahora: ejecuta los tests y arranca GOBLIN para probar un 'hola' y una acción real.")
    print("  cd", backend, "&& python -m pytest tests/ -q")
    print("Cuando confirmes que funciona, dile a Claude y te prepara el commit.")


if __name__ == "__main__":
    main()
