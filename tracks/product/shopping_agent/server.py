"""Local, synthetic shopping conversation prototype. Do not expose on a network."""

import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("SHOPPING_DEMO_DB", ROOT / "data" / "shopping.sqlite3"))
PORT = int(os.environ.get("SHOPPING_DEMO_PORT", "8766"))
ORIGIN = f"http://127.0.0.1:{PORT}"
MAX_BODY = 8192
CASE_ID = "synthetic-protection"
PRIORITIES = {"case", "film", "unsure"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
            CREATE TABLE IF NOT EXISTS shopping_cases (
                id TEXT PRIMARY KEY, purpose TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS turns (
                id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES shopping_cases(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                body TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('note','priority')),
                priority TEXT CHECK(priority IN ('case','film','unsure')),
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS turns_case ON turns(case_id, created_at);
            CREATE TABLE IF NOT EXISTS turn_revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn_id TEXT NOT NULL REFERENCES turns(id) ON DELETE CASCADE,
                body TEXT NOT NULL, kind TEXT NOT NULL, priority TEXT,
                replaced_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS feedback (
                case_id TEXT PRIMARY KEY REFERENCES shopping_cases(id) ON DELETE CASCADE,
                reaction TEXT NOT NULL DEFAULT '', purchased TEXT NOT NULL DEFAULT 'unknown',
                outcome TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
            );
        """)
        if not connection.execute("SELECT 1 FROM shopping_cases WHERE id=?", (CASE_ID,)).fetchone():
            stamp = now()
            connection.execute("INSERT INTO shopping_cases VALUES(?,?,?)", (CASE_ID, "새로 산 손목 기기의 화면 보호", stamp))
            connection.execute("INSERT INTO turns VALUES(?,?,?,?,?,?,?,?)", (
                secrets.token_urlsafe(12), CASE_ID, "user", "새로 산 손목 기기의 화면을 보호할 제품을 찾고 있어요.",
                "note", None, stamp, stamp))
            connection.execute("INSERT INTO turns VALUES(?,?,?,?,?,?,?,?)", (
                secrets.token_urlsafe(12), CASE_ID, "assistant",
                "두 후보는 케이스형과 필름형입니다. 측면·모서리 보호와 얇은 착용감 중 무엇을 우선하시나요?",
                "note", None, stamp, stamp))
            connection.execute("INSERT INTO feedback VALUES(?,?,?,?,?)", (CASE_ID, "", "unknown", "", stamp))


def state(connection):
    turns = [dict(row) for row in connection.execute(
        "SELECT * FROM turns WHERE case_id=? ORDER BY created_at, rowid", (CASE_ID,))]
    for turn in turns:
        turn["revisions"] = [dict(row) for row in connection.execute(
            "SELECT body, kind, priority, replaced_at FROM turn_revisions WHERE turn_id=? ORDER BY id", (turn["id"],))]
    priority_turn = next((turn for turn in reversed(turns)
                          if turn["role"] == "user" and turn["kind"] == "priority"), None)
    priority = priority_turn["priority"] if priority_turn else None
    if priority == "case":
        headline = "케이스형 후보를 먼저 확인하세요"
        reason = "말씀하신 측면·모서리 보호에 더 가까운 형태입니다. 실제 덮임 범위와 터치·버튼 조작은 아직 확인되지 않았습니다."
        next_step = "판매 상세 정보에서 화면과 측면을 어디까지 덮는지 확인"
    elif priority == "film":
        headline = "필름형 후보를 먼저 확인하세요"
        reason = "말씀하신 얇은 착용감에 더 가까운 형태입니다. 실제 두께와 부착 후 사용감은 확인되지 않았습니다."
        next_step = "판매 상세 정보에서 부착 범위와 두께 확인"
    else:
        headline = "원하는 보호 범위를 알려주세요"
        reason = "케이스와 필름은 보호하는 부위가 달라 가격만으로 선택할 수 없습니다."
        next_step = "측면·모서리 보호와 얇은 착용감 중 우선 조건 하나 선택"
    source = None if not priority_turn or priority == "unsure" else {
        "turn_id": priority_turn["id"], "body": priority_turn["body"],
        "scope": "이 구매 건", "confirmed_by": "사용자 선택", "updated_at": priority_turn["updated_at"]}
    feedback = dict(connection.execute("SELECT * FROM feedback WHERE case_id=?", (CASE_ID,)).fetchone())
    return {"case": {"id": CASE_ID, "purpose": "새로 산 손목 기기의 화면 보호"},
            "turns": turns, "criterion": source,
            "evaluation": {"headline": headline, "reason": reason, "next_step": next_step},
            "candidates": [
                {"id": "case", "name": "케이스형 보호대", "price": 6200, "quantity": "1개",
                 "format": "화면·테두리 덮개", "unknown": "실제 덮임 범위·조작성", "fit": "우선 후보" if priority == "case" else "조건 확인 필요"},
                {"id": "film", "name": "부착형 보호 필름", "price": 8500, "quantity": "3장",
                 "format": "화면 부착", "unknown": "측면 덮임·두께", "fit": "우선 후보" if priority == "film" else "조건 확인 필요"}],
            "feedback": feedback,
            "evidence": "모든 상품·가격은 합성 예시입니다. 실제 호환성·배송·반품은 확인되지 않았습니다."}


def checked_text(value, limit=500):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError("내용을 1~500자로 입력해 주세요.")
    return value.strip()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Avoid storing user text and paths in access logs.

    def respond(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def read_payload(self):
        if self.headers.get("Origin") != ORIGIN:
            raise PermissionError("이 로컬 화면에서만 수정할 수 있습니다.")
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise ValueError("JSON 요청이 필요합니다.")
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("요청 크기를 확인해 주세요.") from error
        if not 0 < size <= MAX_BODY:
            raise ValueError("요청 크기를 확인해 주세요.")
        try:
            payload = json.loads(self.rfile.read(size))
        except json.JSONDecodeError as error:
            raise ValueError("JSON 형식을 확인해 주세요.") from error
        if not isinstance(payload, dict):
            raise ValueError("객체가 필요합니다.")
        return payload

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/state":
            with db() as connection:
                return self.respond(200, state(connection))
        if path != "/":
            return self.respond(404, {"error": "찾을 수 없습니다."})
        body = (ROOT / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(body)

    def change(self, method):
        path = urlsplit(self.path).path
        try:
            payload = self.read_payload()
            with db() as connection:
                if path == "/api/turns" and method == "POST":
                    body = checked_text(payload.get("body"))
                    priority = payload.get("priority")
                    if priority is not None and priority not in PRIORITIES:
                        raise ValueError("보호 우선 조건을 확인해 주세요.")
                    stamp = now()
                    connection.execute("INSERT INTO turns VALUES(?,?,?,?,?,?,?,?)", (
                        secrets.token_urlsafe(12), CASE_ID, "user", body,
                        "priority" if priority is not None else "note", priority, stamp, stamp))
                elif path.startswith("/api/turns/") and method in ("PATCH", "DELETE"):
                    turn_id = path.removeprefix("/api/turns/")
                    existing = connection.execute("SELECT * FROM turns WHERE id=? AND case_id=? AND role='user'", (turn_id, CASE_ID)).fetchone()
                    if not existing:
                        return self.respond(404, {"error": "사용자 발화를 찾을 수 없습니다."})
                    if method == "DELETE":
                        connection.execute("DELETE FROM turns WHERE id=?", (turn_id,))
                    else:
                        body = checked_text(payload.get("body"))
                        priority = payload.get("priority")
                        if priority is not None and priority not in PRIORITIES:
                            raise ValueError("보호 우선 조건을 확인해 주세요.")
                        connection.execute("INSERT INTO turn_revisions(turn_id,body,kind,priority,replaced_at) VALUES(?,?,?,?,?)", (
                            turn_id, existing["body"], existing["kind"], existing["priority"], now()))
                        connection.execute("UPDATE turns SET body=?,kind=?,priority=?,updated_at=? WHERE id=?", (
                            body, "priority" if priority is not None else "note", priority, now(), turn_id))
                elif path == "/api/feedback" and method == "PUT":
                    reaction, purchased, outcome = (payload.get("reaction"), payload.get("purchased"), payload.get("outcome"))
                    if reaction not in ("", "helpful", "consider", "not_fit") or purchased not in ("unknown", "yes", "no") or not isinstance(outcome, str) or len(outcome) > 500:
                        raise ValueError("반응 내용을 확인해 주세요.")
                    connection.execute("UPDATE feedback SET reaction=?,purchased=?,outcome=?,updated_at=? WHERE case_id=?", (
                        reaction, purchased, outcome.strip(), now(), CASE_ID))
                else:
                    return self.respond(404, {"error": "찾을 수 없습니다."})
                return self.respond(200, state(connection))
        except PermissionError as error:
            self.respond(403, {"error": str(error)})
        except (ValueError, TypeError) as error:
            self.respond(400, {"error": str(error)})
        except sqlite3.Error:
            self.respond(500, {"error": "저장에 실패했습니다. 다시 시도해 주세요."})

    def do_POST(self):
        self.change("POST")

    def do_PATCH(self):
        self.change("PATCH")

    def do_DELETE(self):
        self.change("DELETE")

    def do_PUT(self):
        self.change("PUT")


if __name__ == "__main__":
    init_db()
    print(f"Synthetic shopping demo: {ORIGIN}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
