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
        self.assertEqual(engine.infer_domain("교실 노트북"), "shopping")  # Ambiguous: do not silently pick one.
        prompt = engine.build_instruction("electronics", [], [])
        self.assertIn("호환성", prompt)
        self.assertNotIn("5년 총비용", prompt)
        self.assertNotIn("Haworth", prompt)


if __name__ == "__main__":
    unittest.main()
