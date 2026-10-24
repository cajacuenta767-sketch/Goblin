"""
Persistencia de GOBLIN con SQLite (stdlib, sin dependencias).
Guarda sesiones de chat, mensajes, hallazgos de pentest y el log de auditoría.
La base de datos vive en data/goblin.db (git-ignored).
"""
import sqlite3
import time
import uuid
from pathlib import Path

import config

DB_PATH = config.ROOT / "data" / "goblin.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # más seguro ante cierres a media escritura
    return conn


def init() -> None:
    """Crea las tablas si no existen."""
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id         TEXT PRIMARY KEY,
            title      TEXT,
            target     TEXT,
            model      TEXT,
            created_at REAL,
            updated_at REAL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role       TEXT,
            content    TEXT,
            model      TEXT,
            created_at REAL
        );
        CREATE TABLE IF NOT EXISTS findings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT,
            severity    TEXT,
            title       TEXT,
            host        TEXT,
            port        TEXT,
            description TEXT,
            evidence    TEXT,
            created_at  REAL
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            tool       TEXT,
            arguments  TEXT,
            result     TEXT,
            approved   INTEGER,
            created_at REAL
        );
        """)


# ---------- Sesiones ----------
def create_session(title: str = "Nueva conversación", model: str | None = None) -> str:
    sid = str(uuid.uuid4())
    now = time.time()
    with _conn() as c:
        c.execute(
            "INSERT INTO sessions (id, title, model, created_at, updated_at) VALUES (?,?,?,?,?)",
            (sid, title, model or config.DEFAULT_MODEL, now, now),
        )
    return sid


def ensure_session(sid: str, model: str | None = None) -> None:
    """Crea la sesión si no existe (para IDs que vienen del frontend)."""
    with _conn() as c:
        row = c.execute("SELECT id FROM sessions WHERE id=?", (sid,)).fetchone()
        if row is None:
            now = time.time()
            c.execute(
                "INSERT INTO sessions (id, title, model, created_at, updated_at) VALUES (?,?,?,?,?)",
                (sid, "Nueva conversación", model or config.DEFAULT_MODEL, now, now),
            )


def set_title(sid: str, title: str) -> None:
    with _conn() as c:
        c.execute("UPDATE sessions SET title=?, updated_at=? WHERE id=?", (title[:80], time.time(), sid))


def list_sessions() -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]


def delete_session(sid: str) -> None:
    with _conn() as c:
        c.execute("DELETE FROM messages WHERE session_id=?", (sid,))
        c.execute("DELETE FROM findings WHERE session_id=?", (sid,))
        c.execute("DELETE FROM sessions WHERE id=?", (sid,))


# ---------- Mensajes ----------
def add_message(sid: str, role: str, content: str, model: str | None = None) -> None:
    now = time.time()
    with _conn() as c:
        c.execute(
            "INSERT INTO messages (session_id, role, content, model, created_at) VALUES (?,?,?,?,?)",
            (sid, role, content, model, now),
        )
        c.execute("UPDATE sessions SET updated_at=? WHERE id=?", (now, sid))


def get_messages(sid: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content, model, created_at FROM messages WHERE session_id=? ORDER BY id",
            (sid,),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- Hallazgos (Spec 006) ----------
def add_finding(sid: str, severity: str, title: str, host: str = "",
                port: str = "", description: str = "", evidence: str = "") -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO findings (session_id, severity, title, host, port, description, evidence, created_at)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (sid, severity, title, host, port, description, evidence, time.time()),
        )
        return cur.lastrowid


def list_findings(sid: str) -> list[dict]:
    order = "CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 " \
            "WHEN 'low' THEN 3 ELSE 4 END"
    with _conn() as c:
        rows = c.execute(f"SELECT * FROM findings WHERE session_id=? ORDER BY {order}", (sid,)).fetchall()
        return [dict(r) for r in rows]


def delete_finding(fid: int) -> None:
    with _conn() as c:
        c.execute("DELETE FROM findings WHERE id=?", (fid,))


# ---------- Auditoría ----------
def log_action(sid: str, tool: str, arguments: str, result: str, approved: bool) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO audit_log (session_id, tool, arguments, result, approved, created_at)"
            " VALUES (?,?,?,?,?,?)",
            (sid, tool, arguments, result[:2000], 1 if approved else 0, time.time()),
        )


def get_audit(sid: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT * FROM audit_log WHERE session_id=? ORDER BY id", (sid,)).fetchall()
        return [dict(r) for r in rows]
