"""Local Life OS prototype. Only synthetic data belongs in this repository."""
import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("LIFE_OS_DB", ROOT / "data" / "life_os.sqlite3"))
HOST = os.environ.get("LIFE_OS_HOST", "127.0.0.1")
PORT = int(os.environ.get("LIFE_OS_PORT", "8765"))
PUBLIC_ORIGIN = os.environ.get("LIFE_OS_ORIGIN", f"http://127.0.0.1:{PORT}")
HTTPS = PUBLIC_ORIGIN.startswith("https://")
MAX_BODY = 3_000_000
MAX_FILE = 2_000_000
FILE_TYPES = {"image/png", "image/jpeg", "application/pdf", "text/plain"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


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


SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, salt BLOB NOT NULL, password_hash BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, csrf TEXT NOT NULL, expires TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, question TEXT NOT NULL, created TEXT NOT NULL, updated TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE, source TEXT NOT NULL, observed_at TEXT NOT NULL, note TEXT NOT NULL, category TEXT NOT NULL, filename TEXT, mime TEXT, file_data BLOB, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS claims(id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE, evidence_id TEXT REFERENCES evidence(id) ON DELETE SET NULL, kind TEXT NOT NULL, text TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS preferences(id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE, kind TEXT NOT NULL, text TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE, observation TEXT NOT NULL, unknown TEXT NOT NULL, suggestion TEXT NOT NULL, rationale TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS feedback(id TEXT PRIMARY KEY, proposal_id TEXT NOT NULL UNIQUE REFERENCES proposals(id) ON DELETE CASCADE, reaction TEXT NOT NULL, did_act TEXT NOT NULL DEFAULT 'unknown', felt_result TEXT NOT NULL DEFAULT '', updated TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS chronicle(id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE, event TEXT NOT NULL, detail TEXT NOT NULL, created TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS cases_owner ON cases(user_id, updated);
"""


def init_db():
    with db() as connection:
        connection.executescript(SCHEMA)


def uid():
    return secrets.token_urlsafe(16)


def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)


def text(value, max_length, required=True):
    if not isinstance(value, str):
        raise ValueError("문자열을 입력해 주세요.")
    value = value.strip()
    if len(value) > max_length or (required and not value):
        raise ValueError("입력 길이를 확인해 주세요.")
    return value


def rows(connection, table, key, value):
    return [dict(r) for r in connection.execute(f"SELECT * FROM {table} WHERE {key}=? ORDER BY created, id", (value,))]


def case_data(connection, case_id, user_id):
    case = connection.execute("SELECT * FROM cases WHERE id=? AND user_id=?", (case_id, user_id)).fetchone()
    if not case:
        return None
    result = dict(case)
    result.pop("user_id")
    result["evidence"] = rows(connection, "evidence", "case_id", case_id)
    for item in result["evidence"]:
        item.pop("file_data")
        item["has_file"] = bool(item["filename"])
    for table in ("claims", "preferences", "proposals", "chronicle"):
        result[table] = rows(connection, table, "case_id", case_id)
    for item in result["proposals"]:
        found = connection.execute("SELECT * FROM feedback WHERE proposal_id=?", (item["id"],)).fetchone()
        item["feedback"] = dict(found) if found else None
    return result


def create_proposal(connection, case_id):
    evidence = rows(connection, "evidence", "case_id", case_id)
    prefs = rows(connection, "preferences", "case_id", case_id)
    prior = connection.execute("""SELECT f.reaction FROM feedback f JOIN proposals p ON p.id=f.proposal_id
        WHERE p.case_id=? ORDER BY f.updated DESC LIMIT 1""", (case_id,)).fetchone()
    if not evidence:
        observation = "아직 질문 이외의 근거가 없습니다."
        unknown = "언제, 어떤 상황에서 반복되는지 알지 못합니다."
        suggestion = "최근 떠오르는 구체적인 한 장면을 알려주실래요? 자료가 없어도 괜찮습니다."
        rationale = "상황을 먼저 알면 필요하지 않은 자료나 행동을 요구하지 않을 수 있습니다."
    elif len(evidence) >= 2 and any("측정" in e["source"] or "InBody" in e["source"] for e in evidence):
        observation = "서로 다른 시점의 자료가 있습니다. 기록된 값의 차이는 확인할 수 있습니다."
        unknown = "측정 시간·기기·컨디션의 차이와 변화의 원인은 확인되지 않았습니다."
        suggestion = "두 측정의 조건이 비슷했는지 먼저 확인해 볼까요?"
        rationale = "단발 측정치와 불완전한 운동 기록만으로 원인을 단정할 수 없습니다."
    else:
        observation = f"{evidence[-1]['source']} ({evidence[-1]['observed_at']}) 자료와 사용자의 설명이 있습니다."
        unknown = "이 자료만으로 원인이나 앞으로의 결과를 알 수 없습니다."
        suggestion = "지금 가장 부담이 되는 조건 하나를 알려주실래요?"
        rationale = "생활 제약을 확인해야 부담이 적은 다음 선택을 함께 찾을 수 있습니다."
    if prefs:
        rationale += " 기록된 제약도 이번 판단의 참고 맥락입니다."
    if prior and prior["reaction"] == "not_fit":
        suggestion = "이전 제안이 맞지 않았던 이유를 한 가지 알려주실래요?"
        rationale += " 이전 반응을 현재 사례에만 참고하며 고정 성향으로 판단하지 않습니다."
    proposal_id = uid()
    connection.execute("INSERT INTO proposals VALUES(?,?,?,?,?,?,?)", (proposal_id, case_id, observation, unknown, suggestion, rationale, now()))
    connection.execute("INSERT INTO chronicle VALUES(?,?,?,?,?)", (uid(), case_id, "proposal", "근거와 모르는 점을 구분해 질문 또는 제안 하나를 생성", now()))
    return proposal_id


class Handler(BaseHTTPRequestHandler):
    server_version = "LifeOS/0.1"

    def log_message(self, *_):
        pass  # Avoid logging private paths or user supplied text.

    def reply(self, status, data, cookie=None):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def fail(self, status, message):
        self.reply(status, {"error": message})

    def payload(self):
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise ValueError("JSON 요청이 필요합니다.")
        size = int(self.headers.get("Content-Length", "0"))
        if size < 1 or size > MAX_BODY:
            raise ValueError("요청 크기를 확인해 주세요.")
        data = json.loads(self.rfile.read(size))
        if not isinstance(data, dict):
            raise ValueError("객체가 필요합니다.")
        return data

    def session(self, connection):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            token = cookie["life_os_session"].value
        except (KeyError, ValueError):
            return None
        return connection.execute("SELECT user_id,csrf FROM sessions WHERE token_hash=? AND expires>?", (hashlib.sha256(token.encode()).hexdigest(), now())).fetchone()

    def check_write(self, session=None):
        if self.headers.get("Origin") != PUBLIC_ORIGIN:
            self.fail(403, "허용되지 않은 출처입니다.")
            return False
        if session and not hmac.compare_digest(self.headers.get("X-CSRF-Token", ""), session["csrf"]):
            self.fail(403, "세션 확인에 실패했습니다.")
            return False
        return True

    def serve_static(self, path):
        names = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"), "/style.css": ("style.css", "text/css")}
        if path not in names:
            self.send_error(404)
            return
        filename, mime = names[path]
        body = (ROOT / "static" / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; base-uri 'none'; form-action 'self'; object-src 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if not path.startswith("/api/"):
            return self.serve_static(path)
        with db() as connection:
            session = self.session(connection)
            if not session:
                return self.fail(401, "로그인이 필요합니다.")
            user_id = session["user_id"]
            parts = path.strip("/").split("/")
            if path == "/api/me":
                name = connection.execute("SELECT name FROM users WHERE id=?", (user_id,)).fetchone()[0]
                return self.reply(200, {"name": name, "csrf": session["csrf"]})
            if path == "/api/cases":
                ids = connection.execute("SELECT id FROM cases WHERE user_id=? ORDER BY updated DESC", (user_id,))
                return self.reply(200, {"cases": [case_data(connection, row[0], user_id) for row in ids]})
            if len(parts) == 3 and parts[:2] == ["api", "cases"]:
                result = case_data(connection, parts[2], user_id)
                return self.reply(200, result) if result else self.fail(404, "기록을 찾을 수 없습니다.")
            if len(parts) == 4 and parts[:2] == ["api", "cases"] and parts[3] == "file":
                return self.fail(404, "파일을 찾을 수 없습니다.")
            if len(parts) == 4 and parts[:2] == ["api", "evidence"] and parts[3] == "file":
                row = connection.execute("""SELECT e.filename,e.mime,e.file_data FROM evidence e
                    JOIN cases c ON c.id=e.case_id WHERE e.id=? AND c.user_id=?""", (parts[2], user_id)).fetchone()
                if not row or row[2] is None:
                    return self.fail(404, "파일을 찾을 수 없습니다.")
                self.send_response(200)
                self.send_header("Content-Type", row[1])
                self.send_header("Content-Length", str(len(row[2])))
                self.send_header("Content-Disposition", "attachment; filename=\"evidence\"")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return self.wfile.write(row[2])
        self.fail(404, "경로를 찾을 수 없습니다.")

    def do_POST(self):
        self.change("POST")

    def do_PUT(self):
        self.change("PUT")

    def do_DELETE(self):
        self.change("DELETE")

    def change(self, method):
        path = urlsplit(self.path).path
        if not path.startswith("/api/"):
            return self.fail(404, "경로를 찾을 수 없습니다.")
        with db() as connection:
            session = self.session(connection)
            if not self.check_write(session):
                return
            if path in ("/api/register", "/api/login") and method == "POST":
                try:
                    data = self.payload()
                    name = text(data.get("name"), 40)
                    password = text(data.get("password"), 200)
                    if len(password) < 10:
                        raise ValueError("비밀번호는 10자 이상이어야 합니다.")
                    if path == "/api/register":
                        salt = secrets.token_bytes(16)
                        user_id = uid()
                        try:
                            connection.execute("INSERT INTO users VALUES(?,?,?,?)", (user_id, name, salt, password_hash(password, salt)))
                        except sqlite3.IntegrityError:
                            return self.fail(409, "이미 사용 중인 계정 이름입니다.")
                    else:
                        user = connection.execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()
                        if not user or not hmac.compare_digest(password_hash(password, user["salt"]), user["password_hash"]):
                            return self.fail(401, "계정 이름 또는 비밀번호가 맞지 않습니다.")
                        user_id = user["id"]
                    token, csrf = uid(), uid()
                    expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(timespec="seconds")
                    connection.execute("INSERT INTO sessions VALUES(?,?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), user_id, csrf, expires))
                    cookie = f"life_os_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=604800" + ("; Secure" if HTTPS else "")
                    connection.commit()
                    return self.reply(200, {"name": name, "csrf": csrf}, cookie)
                except (ValueError, json.JSONDecodeError) as exc:
                    return self.fail(400, str(exc))
                except sqlite3.Error:
                    connection.rollback()
                    return self.fail(503, "저장소 오류로 완료하지 못했습니다. 다시 시도해 주세요.")
            if not session:
                return self.fail(401, "로그인이 필요합니다.")
            user_id = session["user_id"]
            if path == "/api/logout" and method == "POST":
                cookie = SimpleCookie()
                cookie.load(self.headers.get("Cookie", ""))
                token = cookie["life_os_session"].value
                connection.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
                connection.commit()
                return self.reply(200, {"ok": True}, "life_os_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0")
            try:
                data = self.payload() if method != "DELETE" else {}
                parts = path.strip("/").split("/")
                if path == "/api/cases" and method == "POST":
                    question = text(data.get("question"), 2000)
                    case_id = uid()
                    connection.execute("INSERT INTO cases VALUES(?,?,?,?,?,1)", (case_id, user_id, question, now(), now()))
                    connection.execute("INSERT INTO chronicle VALUES(?,?,?,?,?)", (uid(), case_id, "case_created", "질문으로 시작", now()))
                    create_proposal(connection, case_id)
                    connection.commit()
                    return self.reply(201, case_data(connection, case_id, user_id))
                if len(parts) < 3 or parts[:2] != ["api", "cases"]:
                    return self.fail(404, "경로를 찾을 수 없습니다.")
                case_id = parts[2]
                if not connection.execute("SELECT 1 FROM cases WHERE id=? AND user_id=?", (case_id, user_id)).fetchone():
                    return self.fail(404, "기록을 찾을 수 없습니다.")
                if method == "DELETE" and len(parts) == 3:
                    connection.execute("DELETE FROM cases WHERE id=? AND user_id=?", (case_id, user_id))
                    connection.commit()
                    return self.reply(200, {"ok": True})
                if method == "PUT" and len(parts) == 3:
                    connection.execute("UPDATE cases SET question=?,updated=? WHERE id=?", (text(data.get("question"), 2000), now(), case_id))
                    event = "case_edited"
                elif len(parts) == 4 and parts[3] == "evidence" and method == "POST":
                    source = text(data.get("source"), 120)
                    observed_at = text(data.get("observed_at"), 40)
                    note = text(data.get("note", ""), 4000, False)
                    category = text(data.get("category", "useful"), 20)
                    if category not in ("essential", "useful", "optional"):
                        raise ValueError("자료 분류가 올바르지 않습니다.")
                    filename = mime = file_data = None
                    if data.get("file") is not None:
                        file = data["file"]
                        if not isinstance(file, dict):
                            raise ValueError("첨부 형식이 올바르지 않습니다.")
                        filename = text(file.get("name"), 120)
                        mime = text(file.get("mime"), 80)
                        if mime not in FILE_TYPES:
                            raise ValueError("PNG, JPEG, PDF, 텍스트 파일만 첨부할 수 있습니다.")
                        try:
                            file_data = base64.b64decode(file.get("base64", ""), validate=True)
                        except (ValueError, TypeError):
                            raise ValueError("첨부를 읽지 못했습니다.")
                        if not file_data or len(file_data) > MAX_FILE:
                            raise ValueError("첨부는 2MB 이하여야 합니다.")
                    connection.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?,?)", (uid(), case_id, source, observed_at, note, category, filename, mime, file_data, now()))
                    event = "evidence_added"
                elif len(parts) == 4 and parts[3] == "claims" and method == "POST":
                    kind = text(data.get("kind"), 20)
                    if kind not in ("observed", "inferred"):
                        raise ValueError("관찰 또는 추론을 선택해 주세요.")
                    evidence_id = data.get("evidence_id")
                    if evidence_id and not connection.execute("SELECT 1 FROM evidence WHERE id=? AND case_id=?", (evidence_id, case_id)).fetchone():
                        raise ValueError("이 사례의 근거가 아닙니다.")
                    connection.execute("INSERT INTO claims VALUES(?,?,?,?,?,?)", (uid(), case_id, evidence_id, kind, text(data.get("text"), 1000), now()))
                    event = "claim_added"
                elif len(parts) == 4 and parts[3] == "preferences" and method == "POST":
                    kind = text(data.get("kind"), 20)
                    if kind not in ("preference", "constraint"):
                        raise ValueError("선호 또는 제약을 선택해 주세요.")
                    connection.execute("INSERT INTO preferences VALUES(?,?,?,?,?)", (uid(), case_id, kind, text(data.get("text"), 1000), now()))
                    event = "preference_added"
                elif len(parts) == 4 and parts[3] == "proposals" and method == "POST":
                    create_proposal(connection, case_id)
                    event = "proposal_requested"
                elif len(parts) == 5 and parts[3] == "feedback" and method == "PUT":
                    proposal_id = parts[4]
                    if not connection.execute("SELECT 1 FROM proposals WHERE id=? AND case_id=?", (proposal_id, case_id)).fetchone():
                        return self.fail(404, "제안을 찾을 수 없습니다.")
                    reaction = text(data.get("reaction"), 20)
                    did_act = text(data.get("did_act", "unknown"), 20)
                    if reaction not in ("good", "consider", "not_fit", "keep") or did_act not in ("unknown", "yes", "no"):
                        raise ValueError("반응 상태가 올바르지 않습니다.")
                    felt = text(data.get("felt_result", ""), 1000, False)
                    connection.execute("""INSERT INTO feedback VALUES(?,?,?,?,?,?)
                        ON CONFLICT(proposal_id) DO UPDATE SET reaction=excluded.reaction,did_act=excluded.did_act,
                        felt_result=excluded.felt_result,updated=excluded.updated""", (uid(), proposal_id, reaction, did_act, felt, now()))
                    event = "feedback_saved"
                elif len(parts) == 5 and parts[3] == "feedback" and method == "DELETE":
                    proposal_id = parts[4]
                    connection.execute("DELETE FROM feedback WHERE proposal_id=? AND proposal_id IN (SELECT id FROM proposals WHERE case_id=?)", (proposal_id, case_id))
                    event = "feedback_deleted"
                elif len(parts) == 5 and parts[3] == "evidence" and method == "DELETE":
                    connection.execute("DELETE FROM evidence WHERE id=? AND case_id=?", (parts[4], case_id))
                    event = "evidence_deleted"
                elif len(parts) == 5 and parts[3] == "evidence" and method == "PUT":
                    category = text(data.get("category"), 20)
                    if category not in ("essential", "useful", "optional"):
                        raise ValueError("자료 분류가 올바르지 않습니다.")
                    cursor = connection.execute("UPDATE evidence SET category=? WHERE id=? AND case_id=?", (category, parts[4], case_id))
                    if not cursor.rowcount:
                        return self.fail(404, "자료를 찾을 수 없습니다.")
                    event = "evidence_reclassified"
                else:
                    return self.fail(404, "경로를 찾을 수 없습니다.")
                connection.execute("UPDATE cases SET updated=?,revision=revision+1 WHERE id=?", (now(), case_id))
                connection.execute("INSERT INTO chronicle VALUES(?,?,?,?,?)", (uid(), case_id, event, "사용자 변경 기록", now()))
                connection.commit()
                return self.reply(200, case_data(connection, case_id, user_id))
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                return self.fail(400, str(exc))
            except sqlite3.Error:
                connection.rollback()
                return self.fail(503, "저장소 오류로 완료하지 못했습니다. 입력을 확인하고 다시 시도해 주세요.")


if __name__ == "__main__":
    init_db()
    print(f"Life OS local server: {PUBLIC_ORIGIN}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
