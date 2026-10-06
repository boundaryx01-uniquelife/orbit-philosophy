"""Local phase-two conversation slice. Synthetic tests only; not a deployed service."""

import hashlib
import json
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .engine import DOMAIN_RULES, ModelUnavailable, ask_model, infer_domain

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("PHASE2_DB", ROOT.parent / "data" / "phase2.sqlite3"))
HOST = os.environ.get("PHASE2_HOST", "127.0.0.1")
PORT = int(os.environ.get("PHASE2_PORT", "8767"))
ORIGIN = os.environ.get("PHASE2_ORIGIN", f"http://127.0.0.1:{PORT}")
COOKIE_NAME = "phase2_session"
MAX_BODY = 10_000
URL_PATTERN = re.compile(r"https://[^\s<>\"']{1,1000}")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def uid():
    return secrets.token_urlsafe(16)


@contextmanager
def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=10000")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with db() as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS workspaces(id TEXT PRIMARY KEY, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS threads(id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, title TEXT NOT NULL, domain TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1);
        CREATE INDEX IF NOT EXISTS threads_owner ON threads(workspace_id, updated_at);
        CREATE TABLE IF NOT EXISTS turns(id TEXT PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES threads(id) ON DELETE CASCADE, role TEXT NOT NULL CHECK(role IN ('user','assistant')), body TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS turns_thread ON turns(thread_id, created_at);
        CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES threads(id) ON DELETE CASCADE, turn_id TEXT NOT NULL REFERENCES turns(id) ON DELETE CASCADE, url TEXT NOT NULL, verification TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, thread_id TEXT REFERENCES threads(id) ON DELETE CASCADE, domain TEXT, source_turn_id TEXT REFERENCES turns(id) ON DELETE CASCADE, text TEXT NOT NULL, scope TEXT NOT NULL CHECK(scope IN ('thread','domain','global')), status TEXT NOT NULL CHECK(status IN ('proposed','confirmed','rejected')), created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS memories_owner ON memories(workspace_id, status, scope);
        CREATE TABLE IF NOT EXISTS feedback(thread_id TEXT PRIMARY KEY REFERENCES threads(id) ON DELETE CASCADE, reaction TEXT NOT NULL DEFAULT '', purchased TEXT NOT NULL DEFAULT 'unknown', outcome TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL);
        """)


def clean_text(value, limit=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"내용을 1~{limit}자로 입력해 주세요.")
    return value.strip()


def links_from_message(message):
    urls = []
    for raw in URL_PATTERN.findall(message):
        url = raw.rstrip(".,)]}>…")
        parsed = urlsplit(url)
        if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password and url not in urls:
            urls.append(url)
    return urls[:5]


def thread_owned(connection, thread_id, workspace_id):
    return connection.execute("SELECT * FROM threads WHERE id=? AND workspace_id=?", (thread_id, workspace_id)).fetchone()


def usable_memories(connection, workspace_id, domain, thread_id):
    return [dict(row) for row in connection.execute("""
        SELECT id,text,scope,domain,thread_id,source_turn_id FROM memories
        WHERE workspace_id=? AND status='confirmed'
        AND (scope='global' OR (scope='domain' AND domain=?) OR (scope='thread' AND thread_id=?))
        ORDER BY updated_at DESC LIMIT 30
    """, (workspace_id, domain, thread_id or ""))]


def thread_data(connection, thread_id, workspace_id):
    thread = thread_owned(connection, thread_id, workspace_id)
    if not thread:
        return None
    result = dict(thread)
    result.pop("workspace_id")
    result["turns"] = [dict(row) for row in connection.execute(
        "SELECT id,role,body,created_at FROM turns WHERE thread_id=? ORDER BY created_at,rowid", (thread_id,))]
    result["evidence"] = [dict(row) for row in connection.execute(
        "SELECT id,turn_id,url,verification,created_at FROM evidence WHERE thread_id=? ORDER BY created_at,rowid", (thread_id,))]
    result["memories"] = [dict(row) for row in connection.execute("""
        SELECT id,thread_id,domain,source_turn_id,text,scope,status,created_at,updated_at
        FROM memories WHERE workspace_id=? AND (thread_id=? OR status='confirmed' AND (scope='global' OR scope='domain' AND domain=?))
        ORDER BY created_at,rowid
    """, (workspace_id, thread_id, thread["domain"]))]
    result["feedback"] = dict(connection.execute("SELECT * FROM feedback WHERE thread_id=?", (thread_id,)).fetchone())
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # No paths, chat text, cookies or model errors in HTTP logs.

    def reply(self, status, data, cookie=None):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def payload(self):
        if self.headers.get("Origin") != ORIGIN:
            raise PermissionError("이 화면에서만 변경할 수 있습니다.")
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise ValueError("JSON 요청이 필요합니다.")
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("요청 크기를 확인해 주세요.") from error
        if not 0 < size <= MAX_BODY:
            raise ValueError("요청 크기를 확인해 주세요.")
        try:
            data = json.loads(self.rfile.read(size))
        except json.JSONDecodeError as error:
            raise ValueError("JSON 형식을 확인해 주세요.") from error
        if not isinstance(data, dict):
            raise ValueError("객체를 보내 주세요.")
        return data

    def workspace(self, connection, create=False):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            token = cookie[COOKIE_NAME].value
        except (KeyError, ValueError):
            token = None
        if token:
            row = connection.execute("SELECT workspace_id FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
            if row:
                return row["workspace_id"], None
        if not create:
            return None, None
        workspace_id, token, stamp = uid(), secrets.token_urlsafe(32), now()
        connection.execute("INSERT INTO workspaces VALUES(?,?)", (workspace_id, stamp))
        connection.execute("INSERT INTO sessions VALUES(?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), workspace_id, stamp))
        secure = "; Secure" if ORIGIN.startswith("https://") else ""
        cookie_header = f"{COOKIE_NAME}={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=2592000{secure}"
        return workspace_id, cookie_header

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            body = (ROOT / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'")
            self.end_headers()
            return self.wfile.write(body)
        if path == "/api/bootstrap":
            with db() as connection:
                workspace_id, cookie = self.workspace(connection, create=True)
                threads = [dict(row) for row in connection.execute("SELECT id,title,domain,updated_at FROM threads WHERE workspace_id=? ORDER BY updated_at DESC LIMIT 50", (workspace_id,))]
                connection.commit()
                return self.reply(200, {"threads": threads, "model_ready": bool(os.environ.get("PHASE2_MODEL_API_KEY") and os.environ.get("PHASE2_MODEL_NAME")), "domains": list(DOMAIN_RULES)}, cookie)
        if path.startswith("/api/threads/"):
            with db() as connection:
                workspace_id, _ = self.workspace(connection)
                result = thread_data(connection, path.removeprefix("/api/threads/"), workspace_id) if workspace_id else None
                return self.reply(200, result) if result else self.reply(404, {"error": "대화를 찾을 수 없습니다."})
        self.reply(404, {"error": "찾을 수 없습니다."})

    def change(self, method):
        path = urlsplit(self.path).path
        try:
            data = self.payload()
            with db() as connection:
                workspace_id, _ = self.workspace(connection)
                if not workspace_id:
                    return self.reply(401, {"error": "화면을 다시 열어 세션을 시작해 주세요."})
                if path == "/api/chat" and method == "POST":
                    return self.chat(connection, workspace_id, data)
                if path.startswith("/api/memories/") and method in ("PUT", "DELETE"):
                    memory_id = path.removeprefix("/api/memories/")
                    item = connection.execute("SELECT * FROM memories WHERE id=? AND workspace_id=?", (memory_id, workspace_id)).fetchone()
                    if not item:
                        return self.reply(404, {"error": "기억 후보를 찾을 수 없습니다."})
                    if method == "DELETE":
                        connection.execute("DELETE FROM memories WHERE id=?", (memory_id,))
                    else:
                        status = data.get("status")
                        if status not in ("confirmed", "rejected"):
                            raise ValueError("확인 또는 사용 안 함을 선택해 주세요.")
                        text = clean_text(data.get("text", item["text"]), 300)
                        scope = data.get("scope", item["scope"])
                        if scope not in ("thread", "domain", "global"):
                            raise ValueError("기억 범위를 확인해 주세요.")
                        connection.execute("UPDATE memories SET status=?,text=?,scope=?,updated_at=? WHERE id=?", (status, text, scope, now(), memory_id))
                    connection.commit()
                    return self.reply(200, thread_data(connection, item["thread_id"], workspace_id))
                if path.startswith("/api/feedback/") and method == "PUT":
                    thread_id = path.removeprefix("/api/feedback/")
                    if not thread_owned(connection, thread_id, workspace_id):
                        return self.reply(404, {"error": "대화를 찾을 수 없습니다."})
                    reaction, purchased, outcome = data.get("reaction"), data.get("purchased"), data.get("outcome")
                    if reaction not in ("", "helpful", "consider", "not_fit") or purchased not in ("unknown", "yes", "no") or not isinstance(outcome, str) or len(outcome) > 500:
                        raise ValueError("반응 내용을 확인해 주세요.")
                    connection.execute("UPDATE feedback SET reaction=?,purchased=?,outcome=?,updated_at=? WHERE thread_id=?", (reaction, purchased, outcome.strip(), now(), thread_id))
                    connection.commit()
                    return self.reply(200, thread_data(connection, thread_id, workspace_id))
                if path.startswith("/api/threads/") and method == "DELETE":
                    thread_id = path.removeprefix("/api/threads/")
                    if not thread_owned(connection, thread_id, workspace_id):
                        return self.reply(404, {"error": "대화를 찾을 수 없습니다."})
                    connection.execute("DELETE FROM threads WHERE id=?", (thread_id,))
                    connection.commit()
                    return self.reply(200, {"deleted": True})
                return self.reply(404, {"error": "찾을 수 없습니다."})
        except PermissionError as error:
            self.reply(403, {"error": str(error)})
        except (ValueError, TypeError) as error:
            self.reply(400, {"error": str(error)})
        except ModelUnavailable as error:
            self.reply(503, {"error": str(error)})
        except sqlite3.Error:
            self.reply(500, {"error": "저장에 실패했습니다. 잠시 뒤 다시 시도해 주세요."})

    def chat(self, connection, workspace_id, data):
        message = clean_text(data.get("message"))
        thread_id = data.get("thread_id")
        explicit_domain = data.get("domain")
        if explicit_domain is not None and explicit_domain not in DOMAIN_RULES:
            raise ValueError("분야를 확인해 주세요.")
        existing = None
        if thread_id is not None:
            if not isinstance(thread_id, str):
                raise ValueError("대화 ID를 확인해 주세요.")
            existing = thread_owned(connection, thread_id, workspace_id)
            if not existing:
                return self.reply(404, {"error": "대화를 찾을 수 없습니다."})
        domain = explicit_domain or (existing["domain"] if existing else infer_domain(message))
        past = [dict(row) for row in connection.execute("SELECT role,body FROM turns WHERE thread_id=? ORDER BY created_at,rowid", (thread_id,))] if existing else []
        upcoming_turn_id = uid()
        links = links_from_message(message)
        evidence = [dict(row) for row in connection.execute("SELECT id,url,verification FROM evidence WHERE thread_id=? ORDER BY created_at", (thread_id,))] if existing else []
        new_evidence = [{"id": uid(), "url": url, "verification": "user_link_unverified"} for url in links]
        context_evidence = (evidence + new_evidence)[-12:]
        facts = usable_memories(connection, workspace_id, domain, thread_id)
        prior_feedback = dict(connection.execute("SELECT reaction,purchased,outcome FROM feedback WHERE thread_id=?", (thread_id,)).fetchone()) if existing else None
        response = ask_model(domain, past + [{"role": "user", "body": message}], facts, context_evidence, prior_feedback)
        stamp = now()
        if not existing:
            thread_id = uid()
            connection.execute("INSERT INTO threads VALUES(?,?,?,?,?,?,1)", (thread_id, workspace_id, message[:60], domain, stamp, stamp))
            connection.execute("INSERT INTO feedback VALUES(?,?,?,?,?)", (thread_id, "", "unknown", "", stamp))
        else:
            connection.execute("UPDATE threads SET domain=?,updated_at=?,revision=revision+1 WHERE id=?", (domain, stamp, thread_id))
        connection.execute("INSERT INTO turns VALUES(?,?,?,?,?)", (upcoming_turn_id, thread_id, "user", message, stamp))
        connection.execute("INSERT INTO turns VALUES(?,?,?,?,?)", (uid(), thread_id, "assistant", response["reply"], now()))
        for item in new_evidence:
            connection.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?)", (item["id"], thread_id, upcoming_turn_id, item["url"], item["verification"], stamp))
        for item in response["memory_candidates"]:
            connection.execute("INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,?)", (
                uid(), workspace_id, thread_id, domain if item["scope"] == "domain" else None,
                upcoming_turn_id, item["text"], item["scope"], "proposed", stamp, stamp))
        connection.commit()
        return self.reply(200, thread_data(connection, thread_id, workspace_id))

    def do_POST(self):
        self.change("POST")

    def do_PUT(self):
        self.change("PUT")

    def do_DELETE(self):
        self.change("DELETE")


if __name__ == "__main__":
    init_db()
    print(f"Phase-two development server: {ORIGIN}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
