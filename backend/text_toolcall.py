"""
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
