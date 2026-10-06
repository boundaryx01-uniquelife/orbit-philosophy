"""End-to-end checks for the local synthetic shopping demo."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ShoppingFlowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.port = free_port()
        self.origin = f"http://127.0.0.1:{self.port}"
        self.environment = dict(os.environ, SHOPPING_DEMO_DB=str(Path(self.temp.name) / "demo.sqlite3"),
                                SHOPPING_DEMO_PORT=str(self.port))
        self.start_server()

    def tearDown(self):
        self.stop_server()
        self.temp.cleanup()

    def start_server(self):
        self.process = subprocess.Popen([sys.executable, str(ROOT / "server.py")], env=self.environment,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            try:
                self.request("/api/state")
                return
            except URLError:
                time.sleep(.05)
        self.fail("server did not start")

    def stop_server(self):
        self.process.terminate()
        self.process.wait(timeout=5)

    def request(self, path, method="GET", payload=None, origin=None):
        headers = {}
        body = None
        if payload is not None:
            headers = {"Content-Type": "application/json", "Origin": self.origin if origin is None else origin}
            body = json.dumps(payload, ensure_ascii=False).encode()
        request = Request(self.origin + path, data=body, headers=headers, method=method)
        with urlopen(request, timeout=3) as response:
            return json.load(response)

    def test_conversation_source_edit_delete_and_restart(self):
        initial = self.request("/api/state")
        self.assertIsNone(initial["criterion"])
        self.assertEqual(len(initial["turns"]), 2)

        chosen = self.request("/api/turns", "POST", {"body": "모서리까지 덮는 게 중요해요", "priority": "case"})
        source = chosen["criterion"]
        self.assertEqual(source["body"], "모서리까지 덮는 게 중요해요")
        self.assertEqual(source["scope"], "이 구매 건")
        self.assertIn("케이스형", chosen["evaluation"]["headline"])
        turn_id = source["turn_id"]

        noted = self.request("/api/turns", "POST", {"body": "가격도 살펴봐 주세요"})
        self.assertEqual(noted["criterion"]["turn_id"], turn_id)
        considered = self.request("/api/feedback", "PUT", {
            "reaction": "consider", "purchased": "unknown", "outcome": ""})
        self.assertEqual(considered["feedback"]["purchased"], "unknown")
        self.assertEqual(considered["feedback"]["outcome"], "")

        changed = self.request("/api/turns/" + turn_id, "PATCH", {
            "body": "이번에는 얇게 붙이는 쪽이 좋아요", "priority": "film"})
        self.assertIn("필름형", changed["evaluation"]["headline"])
        self.assertEqual(changed["criterion"]["turn_id"], turn_id)
        revised_turn = next(turn for turn in changed["turns"] if turn["id"] == turn_id)
        self.assertEqual(revised_turn["revisions"][0]["body"], "모서리까지 덮는 게 중요해요")

        self.stop_server()
        self.start_server()
        restored = self.request("/api/state")
        self.assertIn("필름형", restored["evaluation"]["headline"])
        self.assertEqual(restored["feedback"]["reaction"], "consider")
        self.assertEqual(restored["feedback"]["purchased"], "unknown")

        deleted = self.request("/api/turns/" + turn_id, "DELETE", {})
        self.assertIsNone(deleted["criterion"])
        self.assertIn("원하는 보호 범위", deleted["evaluation"]["headline"])
        self.assertNotIn("이번에는 얇게", json.dumps(deleted, ensure_ascii=False))
        self.assertNotIn("모서리까지 덮는 게", json.dumps(deleted, ensure_ascii=False))

    def test_invalid_write_origin_is_rejected(self):
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/turns", "POST", {"body": "임의 변경"}, origin="http://example.invalid")
        self.assertEqual(caught.exception.code, 403)
        self.assertEqual(len(self.request("/api/state")["turns"]), 2)


if __name__ == "__main__":
    unittest.main()
