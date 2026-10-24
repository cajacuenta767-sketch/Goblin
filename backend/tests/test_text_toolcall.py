"""Pruebas del respaldo de tool-calling por texto (Spec 022)."""
from text_toolcall import parse_text_toolcall


def test_python_dict_is_recovered_as_run_shell():
    r = parse_text_toolcall("{'command': 'whoami', 'cwd': '/home/user'}")
    assert r is not None
    assert r["tool"] == "run_shell"
    assert r["args"]["command"] == "whoami"


def test_qwen_tool_call_tag_is_parsed():
    txt = '<tool_call>{"name": "run_shell", "arguments": {"command": "id"}}</tool_call>'
    r = parse_text_toolcall(txt)
    assert r == {"tool": "run_shell", "args": {"command": "id"}}


def test_wrapped_json_without_tags_is_parsed():
    r = parse_text_toolcall('{"name": "make_dir", "arguments": {"path": "/tmp/x"}}')
    assert r == {"tool": "make_dir", "args": {"path": "/tmp/x"}}


def test_normal_text_is_not_a_tool_call():
    assert parse_text_toolcall("Hola, ¿en qué te ayudo?") is None


def test_unknown_json_is_not_executed():
    assert parse_text_toolcall('Ejemplo: {"foo": 1}') is None
