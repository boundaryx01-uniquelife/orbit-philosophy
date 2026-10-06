"""Synthetic checks for conversation, memory scope and ownership."""

import http.cookiejar
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

from phase2.app import engine, server
from phase2.app import search, telegram
from datetime import datetime, timedelta, timezone
from io import BytesIO


class FlowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_db = server.DB_PATH
        self.previous_origin = server.ORIGIN
        server.DB_PATH = Path(self.temp.name) / "phase2.sqlite3"
        server.init_db()
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.port = self.http.server_address[1]
        server.ORIGIN = f"http://127.0.0.1:{self.port}"
        self.runner = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.runner.start()
        self.first = self.client()
        self.second = self.client()

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.runner.join(timeout=3)
        server.DB_PATH = self.previous_db
        server.ORIGIN = self.previous_origin
        self.temp.cleanup()

    def client(self):
        return build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, client, path, method="GET", payload=None, origin=None):
        body = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
        headers = {"Content-Type": "application/json", "Origin": server.ORIGIN if origin is None else origin} if body is not None else {}
        request = Request(server.ORIGIN + path, data=body, headers=headers, method=method)
        with client.open(request, timeout=4) as response:
            return json.load(response)

    def test_conversation_scope_feedback_and_isolation(self):
        self.call(self.first, "/api/bootstrap")
        observed = []

        def fake_model(domain, turns, facts, evidence, feedback=None):
            observed.append({"domain": domain, "facts": facts, "evidence": evidence, "feedback": feedback})
            if len(observed) == 1:
                return {"reply": "현재 링크의 가격은 확인되지 않았습니다. 측면 보호가 우선인지 알려주세요.",
                        "memory_candidates": [
                            {"text": "이번 전자제품은 측면 보호가 중요함", "scope": "thread"},
                            {"text": "모든 구매에서 배송비 포함 총액을 보고 싶음", "scope": "global"}],
                        "referenced_evidence_ids": []}
            return {"reply": "앞선 총액 기준을 참고했습니다. 이 제품의 크기를 먼저 확인할까요?", "memory_candidates": [], "referenced_evidence_ids": []}

        with patch.object(server, "ask_model", side_effect=fake_model):
            first = self.call(self.first, "/api/chat", "POST", {"message": "전자 기기 케이스를 비교해 주세요. 이번에는 측면 보호가 중요하고, 모든 구매에서 배송비 포함 총액을 보고 싶어요. https://example.com/item"})
            self.assertEqual(first["domain"], "electronics")
            self.assertEqual(len(first["turns"]), 2)
            self.assertEqual(first["evidence"][0]["verification"], "user_link_unverified")
            self.assertEqual(len(first["memories"]), 2)
            self.assertTrue(all(item["status"] == "proposed" for item in first["memories"]))
            self.assertEqual(observed[0]["facts"], [])
            thread_id = first["id"]

            for memory in first["memories"]:
                confirmed = self.call(self.first, "/api/memories/" + memory["id"], "PUT", {"status": "confirmed"})
                self.assertTrue(any(item["id"] == memory["id"] and item["status"] == "confirmed" for item in confirmed["memories"]))
            scoped_id = first["memories"][0]["id"]
            edited = self.call(self.first, "/api/memories/" + scoped_id, "PUT", {"status": "confirmed", "text": "이번 기기는 측면 보호를 우선함", "scope": "thread"})
            self.assertEqual(next(item["text"] for item in edited["memories"] if item["id"] == scoped_id), "이번 기기는 측면 보호를 우선함")

            feedback = self.call(self.first, "/api/feedback/" + thread_id, "PUT", {"reaction": "consider", "purchased": "unknown", "outcome": ""})
            self.assertEqual(feedback["feedback"]["purchased"], "unknown")
            self.assertEqual(feedback["feedback"]["outcome"], "")

            second = self.call(self.first, "/api/chat", "POST", {"message": "오래 쓰는 사무용 의자를 살펴봐 주세요."})
            self.assertEqual(second["domain"], "office")
            self.assertEqual([item["text"] for item in observed[1]["facts"]], ["모든 구매에서 배송비 포함 총액을 보고 싶음"])
            self.assertNotIn("측면 보호", json.dumps(observed[1]["facts"], ensure_ascii=False))
            self.assertEqual(second["feedback"]["purchased"], "unknown")

            third = self.call(self.first, "/api/chat", "POST", {"thread_id": thread_id, "message": "이전에 한 제안을 다시 살펴봐 주세요."})
            self.assertEqual(third["feedback"]["reaction"], "consider")
            self.assertEqual(observed[2]["feedback"]["purchased"], "unknown")
            self.call(self.first, "/api/memories/" + scoped_id, "DELETE", {})
            reloaded = self.call(self.first, "/api/threads/" + thread_id)
            self.assertFalse(any(item["id"] == scoped_id for item in reloaded["memories"]))

        self.call(self.second, "/api/bootstrap")
        with self.assertRaises(HTTPError) as caught:
            self.call(self.second, "/api/threads/" + thread_id)
        self.assertEqual(caught.exception.code, 404)
        with self.assertRaises(HTTPError) as caught:
            self.call(self.second, "/api/memories/" + first["memories"][0]["id"], "PUT", {"status": "confirmed"})
        self.assertEqual(caught.exception.code, 404)

        deleted = self.call(self.first, "/api/threads/" + thread_id, "DELETE", {})
        self.assertTrue(deleted["deleted"])
        with self.assertRaises(HTTPError):
            self.call(self.first, "/api/threads/" + thread_id)

    def test_model_failure_does_not_create_a_fake_answer(self):
        self.call(self.first, "/api/bootstrap")
        with patch.object(server, "ask_model", side_effect=server.ModelUnavailable("AI 연결이 없습니다.")):
            with self.assertRaises(HTTPError) as caught:
                self.call(self.first, "/api/chat", "POST", {"message": "전자제품을 고르고 싶어요."})
        self.assertEqual(caught.exception.code, 503)
        self.assertEqual(self.call(self.first, "/api/bootstrap")["threads"], [])

    def test_cross_site_write_is_rejected(self):
        self.call(self.first, "/api/bootstrap")
        with self.assertRaises(HTTPError) as caught:
            self.call(self.first, "/api/chat", "POST", {"message": "임의 기록"}, origin="https://example.invalid")
        self.assertEqual(caught.exception.code, 403)

    def test_source_policies_are_scoped(self):
        self.assertEqual(engine.infer_domain("전자 기기 케이스"), "electronics")
        self.assertEqual(engine.infer_domain("사무용 의자"), "office")
        self.assertEqual(engine.infer_domain("식품 성분"), "daily")
        self.assertEqual(engine.infer_domain("중고차 유지비"), "vehicle")
        self.assertEqual(engine.infer_domain("교실 노트북"), "conversation")  # Ambiguous: do not silently pick one.
        prompt = engine.build_instruction("electronics", [], [])
        self.assertIn("호환성", prompt)
        self.assertNotIn("5년 총비용", prompt)
        self.assertNotIn("Haworth", prompt)

    def test_telegram_link_search_and_reasoned_outreach(self):
        self.call(self.first, "/api/bootstrap")
        answer = {"reply": "검색 요약만 확인했습니다. 원문 가격은 다시 봐야 합니다.", "memory_candidates": [], "referenced_evidence_ids": []}
        observed = []
        def fake_model(domain, turns, facts, evidence, feedback=None):
            observed.append(evidence)
            return answer
        fake_results = [{"url": "https://example.org/synthetic", "title": "합성 검색 결과", "snippet": "합성 요약", "checked_at": "2026-10-06T00:00:00+00:00", "verification": "search_snippet_unverified"}]
        with patch.dict("os.environ", {"PHASE2_TELEGRAM_BOT_TOKEN": "synthetic-token", "PHASE2_SEARCH_API_KEY": "synthetic-search"}), patch.object(server, "ask_model", side_effect=fake_model), patch.object(server, "search_web", return_value=fake_results), patch.object(telegram, "send") as sent:
            first = self.call(self.first, "/api/chat", "POST", {"message": "손목 기기 보호 제품 최신 가격을 비교해 주세요."})
            self.assertEqual(first["search_status"], "snippets_found")
            self.assertEqual(first["evidence"][0]["verification"], "search_snippet_unverified")
            self.assertEqual(observed[0][0]["snippet"], "합성 요약")
            code = self.call(self.first, "/api/telegram/link-code", "POST", {})["code"]
            with self.assertRaises(HTTPError) as caught:
                self.call(self.first, "/api/outreach", "PUT", {"enabled": True})
            self.assertEqual(caught.exception.code, 400)
            telegram.handle_message({"chat": {"type": "private", "id": 1234}, "text": "/start " + code})
            sent.assert_called()
            self.assertTrue(self.call(self.first, "/api/bootstrap")["telegram_linked"])
            self.call(self.first, "/api/outreach", "PUT", {"enabled": True})
            telegram.handle_message({"chat": {"type": "private", "id": 1234}, "text": "이 제품은 측면까지 보호하나요?"})
            reloaded = self.call(self.first, "/api/threads/" + first["id"])
            self.assertEqual(reloaded["turns"][-2]["body"], "이 제품은 측면까지 보호하나요?")
            tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
            with patch.object(telegram, "judge_outreach", return_value={"send": True, "reason": "사용자가 측면 보호 여부를 물었고 결과를 아직 모른다", "message": "측면 보호가 실제로 필요했던 상황이 있었나요?"}):
                telegram.check_outreach(tomorrow)
                telegram.check_outreach(tomorrow)
            self.assertEqual(sent.call_count, 3)  # link, reply, one proactive question
            final = self.call(self.first, "/api/threads/" + first["id"])
            self.assertEqual(final["turns"][-1]["body"], "측면 보호가 실제로 필요했던 상황이 있었나요?")
            with server.db() as connection:
                decisions = connection.execute("SELECT reason,sent FROM outreach_decisions").fetchall()
                self.assertEqual(len(decisions), 1)
                self.assertEqual(decisions[0]["sent"], 1)
            telegram.handle_message({"chat": {"type": "private", "id": 1234}, "text": "/pause"})
            self.assertFalse(self.call(self.first, "/api/bootstrap")["outreach_enabled"])

    def test_external_api_adapters_use_sourced_results(self):
        with patch.dict("os.environ", {"PHASE2_SEARCH_API_KEY": "synthetic-search", "PHASE2_TELEGRAM_BOT_TOKEN": "synthetic-bot"}):
            web = BytesIO(json.dumps({"web": {"results": [{"url": "https://example.org/item", "title": "합성 제품", "description": "합성 검색 요약"}, {"url": "http://example.org/unsafe", "title": "제외"}]}}).encode())
            with patch.object(search, "urlopen", return_value=web) as call:
                results = search.search_web("제품 가격")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["verification"], "search_snippet_unverified")
            self.assertEqual(call.call_args.args[0].get_header("X-subscription-token"), "synthetic-search")
            api = BytesIO(json.dumps({"ok": True, "result": {"message_id": 1}}).encode())
            with patch.object(telegram, "urlopen", return_value=api) as call:
                result = telegram.send("1234", "합성 질문")
            self.assertEqual(result["message_id"], 1)
            self.assertIn("sendMessage", call.call_args.args[0].full_url)


if __name__ == "__main__":
    unittest.main()
