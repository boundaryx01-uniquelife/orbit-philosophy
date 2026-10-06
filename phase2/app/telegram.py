"""Optional Telegram transport and opt-in outreach worker. Run as a separate process."""

import hashlib
import json
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from . import server
from .engine import ModelUnavailable, judge_outreach


def telegram_call(method, payload):
    token = os.environ.get("PHASE2_TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Telegram 봇 토큰이 없습니다.")
    base = os.environ.get("PHASE2_TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")
    url = f"{base}/bot{token}/{method}"
    request = Request(url, data=urlencode(payload).encode(), method="POST")
    with urlopen(request, timeout=35) as response:
        result = json.load(response)
    if result.get("ok") is not True:
        raise RuntimeError("Telegram 요청에 실패했습니다.")
    return result["result"]


def send(chat_id, text):
    return telegram_call("sendMessage", {"chat_id": chat_id, "text": text[:4000]})


def handle_message(message):
    chat = message.get("chat", {})
    if chat.get("type") != "private" or not isinstance(message.get("text"), str):
        return
    chat_id = str(chat["id"])
    body = message["text"].strip()
    if body.startswith("/start "):
        code = body.split(maxsplit=1)[1].strip()
        with server.db() as connection:
            row = connection.execute("SELECT workspace_id FROM link_codes WHERE code_hash=? AND expires_at>?", (hashlib.sha256(code.encode()).hexdigest(), server.now())).fetchone()
            if not row:
                send(chat_id, "연결 코드가 만료됐거나 잘못됐어요. 웹 화면에서 새 코드를 만들어 주세요.")
                return
            owner = connection.execute("SELECT workspace_id FROM telegram_links WHERE chat_id=?", (chat_id,)).fetchone()
            if owner and owner["workspace_id"] != row["workspace_id"]:
                send(chat_id, "이 Telegram 대화는 이미 다른 공간에 연결돼 있어요. 먼저 /unlink 해주세요.")
                return
            connection.execute("DELETE FROM telegram_links WHERE workspace_id=?", (row["workspace_id"],))
            latest_thread = connection.execute("SELECT id FROM threads WHERE workspace_id=? ORDER BY updated_at DESC LIMIT 1", (row["workspace_id"],)).fetchone()
            connection.execute("INSERT INTO telegram_links(workspace_id,chat_id,thread_id,created_at) VALUES(?,?,?,?)", (row["workspace_id"], chat_id, latest_thread["id"] if latest_thread else None, server.now()))
            connection.execute("DELETE FROM link_codes WHERE code_hash=?", (hashlib.sha256(code.encode()).hexdigest(),))
            connection.commit()
        send(chat_id, "연결됐어요. 여기서 보낸 대화도 웹에 이어집니다. 먼저 말을 걸어도 되는지는 웹 화면에서 따로 켜 주세요.")
        return
    with server.db() as connection:
        link = connection.execute("SELECT workspace_id,thread_id FROM telegram_links WHERE chat_id=?", (chat_id,)).fetchone()
        if not link:
            send(chat_id, "먼저 웹 화면에서 Telegram 연결 코드를 만든 뒤 /start 코드 를 보내 주세요.")
            return
        workspace_id = link["workspace_id"]
        if body == "/pause":
            connection.execute("INSERT INTO outreach_settings(workspace_id,enabled) VALUES(?,0) ON CONFLICT(workspace_id) DO UPDATE SET enabled=0", (workspace_id,))
            connection.commit()
            send(chat_id, "먼저 보내는 메시지를 껐어요. 대화는 계속할 수 있습니다.")
            return
        if body == "/unlink":
            connection.execute("DELETE FROM telegram_links WHERE workspace_id=?", (workspace_id,))
            connection.execute("UPDATE outreach_settings SET enabled=0 WHERE workspace_id=?", (workspace_id,))
            connection.commit()
            send(chat_id, "연결을 끊었어요. 웹에 저장된 대화는 그대로 있습니다.")
            return
        if body.startswith("/"):
            send(chat_id, "메시지를 보내 대화하거나 /pause, /unlink 를 사용할 수 있어요.")
            return
        try:
            result = server.record_chat(connection, workspace_id, body, link["thread_id"])
        except (ValueError, ModelUnavailable) as error:
            send(chat_id, str(error))
            return
        connection.execute("UPDATE telegram_links SET thread_id=? WHERE workspace_id=?", (result["id"], workspace_id))
        connection.commit()
        reply = result["turns"][-1]["body"]
        if result["search_status"] == "failed":
            reply += "\n\n검색 연결에 실패해 최신 정보는 확인하지 못했어요."
        send(chat_id, reply)


def outreach_due(connection, current_time):
    """Only one message per new user turn; the model can also decide silence."""
    rows = connection.execute("""
        SELECT l.workspace_id,l.chat_id,l.thread_id,s.last_evaluated_at,s.last_sent_at,s.last_source_turn_id
        FROM telegram_links l JOIN outreach_settings s ON s.workspace_id=l.workspace_id
        WHERE s.enabled=1 AND l.thread_id IS NOT NULL
    """).fetchall()
    due = []
    for row in rows:
        if row["last_evaluated_at"] and current_time - datetime.fromisoformat(row["last_evaluated_at"]) < timedelta(hours=12):
            continue
        if row["last_sent_at"] and current_time - datetime.fromisoformat(row["last_sent_at"]) < timedelta(days=3):
            continue
        latest = connection.execute("SELECT id,created_at FROM turns WHERE thread_id=? AND role='user' ORDER BY created_at DESC,rowid DESC LIMIT 1", (row["thread_id"],)).fetchone()
        if not latest or latest["id"] == row["last_source_turn_id"]:
            continue
        age = current_time - datetime.fromisoformat(latest["created_at"])
        if not timedelta(hours=12) <= age <= timedelta(days=30):
            continue
        due.append((row, latest))
    return due


def check_outreach(current_time=None):
    current_time = current_time or datetime.now(timezone.utc)
    with server.db() as connection:
        due = outreach_due(connection, current_time)
    for link, latest in due:
        with server.db() as connection:
            thread = server.thread_owned(connection, link["thread_id"], link["workspace_id"])
            if not thread:
                continue
            turns = [dict(row) for row in connection.execute("SELECT role,body FROM turns WHERE thread_id=? ORDER BY created_at,rowid", (thread["id"],))]
            facts = server.usable_memories(connection, link["workspace_id"], thread["domain"], thread["id"])
        try:
            decision = judge_outreach(turns, facts)
        except ModelUnavailable:
            continue
        with server.db() as connection:
            # Settings may have changed while the model was thinking.
            active = connection.execute("SELECT enabled,last_source_turn_id FROM outreach_settings WHERE workspace_id=?", (link["workspace_id"],)).fetchone()
            current_link = connection.execute("SELECT chat_id,thread_id FROM telegram_links WHERE workspace_id=?", (link["workspace_id"],)).fetchone()
            current_user = connection.execute("SELECT id FROM turns WHERE thread_id=? AND role='user' ORDER BY created_at DESC,rowid DESC LIMIT 1", (thread["id"],)).fetchone()
            if (not active or not active["enabled"] or active["last_source_turn_id"] == latest["id"]
                    or not current_link or current_link["chat_id"] != link["chat_id"] or current_link["thread_id"] != thread["id"]
                    or not current_user or current_user["id"] != latest["id"]):
                continue
            if decision["send"]:
                try:
                    send(link["chat_id"], decision["message"])
                except (HTTPError, URLError, OSError, RuntimeError):
                    continue
                stamp = server.now()
                connection.execute("INSERT INTO turns VALUES(?,?,?,?,?)", (server.uid(), thread["id"], "assistant", decision["message"], stamp))
                connection.execute("UPDATE threads SET updated_at=?,revision=revision+1 WHERE id=?", (stamp, thread["id"]))
                connection.execute("UPDATE outreach_settings SET last_sent_at=? WHERE workspace_id=?", (stamp, link["workspace_id"]))
            connection.execute("UPDATE outreach_settings SET last_evaluated_at=?,last_source_turn_id=? WHERE workspace_id=?", (server.now(), latest["id"], link["workspace_id"]))
            connection.execute("INSERT INTO outreach_decisions(workspace_id,thread_id,source_turn_id,sent,reason,created_at) VALUES(?,?,?,?,?,?)", (link["workspace_id"], thread["id"], latest["id"], int(decision["send"]), decision["reason"], server.now()))
            connection.commit()


def run():
    if not os.environ.get("PHASE2_TELEGRAM_BOT_TOKEN"):
        raise SystemExit("PHASE2_TELEGRAM_BOT_TOKEN이 필요합니다.")
    server.init_db()
    while True:
        try:
            with server.db() as connection:
                row = connection.execute("SELECT last_update_id FROM telegram_runtime WHERE id=1").fetchone()
                offset = row["last_update_id"] + 1 if row else 0
            updates = telegram_call("getUpdates", {"offset": offset, "timeout": 20, "allowed_updates": '["message"]'})
            for update in updates:
                handle_message(update.get("message", {}))
                with server.db() as connection:
                    connection.execute("INSERT INTO telegram_runtime VALUES(1,?) ON CONFLICT(id) DO UPDATE SET last_update_id=excluded.last_update_id", (update["update_id"],))
            check_outreach()
        except (HTTPError, URLError, OSError, RuntimeError, ValueError):
            time.sleep(10)


if __name__ == "__main__":
    run()
