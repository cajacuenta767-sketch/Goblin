"""Tests de las herramientas de archivos."""
from tools import registry


def test_make_and_list_dir():
    assert "creada" in registry.run_tool("make_dir", {"path": "t_tools"})
    assert "t_tools" in registry.run_tool("list_dir", {"path": "."})


def test_write_and_read():
    registry.run_tool("write_file", {"path": "t_tools/a.txt", "content": "hola goblin"})
    assert "hola goblin" in registry.run_tool("read_file", {"path": "t_tools/a.txt"})


def test_copy_and_move():
    registry.run_tool("write_file", {"path": "t_tools/b.txt", "content": "x"})
    assert "Copiado" in registry.run_tool("copy_path", {"src": "t_tools/b.txt", "dst": "t_tools/c.txt"})
    assert "Movido" in registry.run_tool("move_path", {"src": "t_tools/c.txt", "dst": "t_tools/d.txt"})


def test_search():
    registry.run_tool("write_file", {"path": "t_tools/e.txt", "content": "clave secreta aqui"})
    assert "secreta" in registry.run_tool("search_files", {"query": "secreta", "path": "t_tools"})


def test_disk_usage():
    assert "GB" in registry.run_tool("disk_usage", {"path": "."})


def test_delete_cleanup():
    assert "Eliminado" in registry.run_tool("delete_path", {"path": "t_tools"})


def test_unknown_tool():
    assert "desconocida" in registry.run_tool("no_existe", {})
