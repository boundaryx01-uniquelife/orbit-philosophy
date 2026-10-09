"""End-to-end API checks using synthetic records and separate browser cookie jars."""
import base64
import http.cookiejar
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen

ROOT = Path(__file__).resolve().parent
SCENARIOS = {item["id"]: item for item in json.loads((ROOT / "fixtures" / "first_flow.synthetic.json").read_text())}


class Browser:
    def __init__(self, origin):
        self.origin = origin
        self.csrf = ""
        self.opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, path, method="GET", data=None):
        headers = {"Origin": self.origin, "X-CSRF-Token": self.csrf}
        body = None if data is None else json.dumps(data).encode()
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.origin + path, data=body, headers=headers, method=method)
        try:
            response = self.opener.open(request, timeout=5)
        except HTTPError as error:
            response = error
        raw = response.read()
        result = json.loads(raw) if response.headers.get("Content-Type", "").startswith("application/json") else raw
        if isinstance(result, dict) and "csrf" in result:
            self.csrf = result["csrf"]
        return response.status, result


class FlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        cls.origin = f"http://127.0.0.1:{cls.port}"
        cls.env = dict(os.environ, LIFE_OS_DB=str(Path(cls.tmp.name) / "data.sqlite3"), LIFE_OS_PORT=str(cls.port))
        cls.start_server()

    @classmethod
    def start_server(cls):
        cls.server = subprocess.Popen([sys.executable, str(ROOT / "server.py")], env=cls.env, stdout=subprocess.DEVNULL, stderr=sys.stderr)
        for _ in range(50):
            if cls.server.poll() is not None:
                raise RuntimeError("server exited")
            try:
                urlopen(cls.origin, timeout=.2).close()
                return
            except OSError:
                time.sleep(.1)
        raise RuntimeError("server did not start")

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.wait(timeout=5)
        cls.tmp.cleanup()

    def test_two_sessions_two_accounts_and_recovery(self):
        phone, pc, other = (Browser(self.origin) for _ in range(3))
        password_a, password_b = secrets.token_urlsafe(16), secrets.token_urlsafe(16)
        self.assertEqual(phone.call("/api/register", "POST", {"name":"sample-a","password":password_a})[0], 200)
        self.assertEqual(pc.call("/api/login", "POST", {"name":"sample-a","password":password_a})[0], 200)
        self.assertEqual(other.call("/api/register", "POST", {"name":"sample-b","password":password_b})[0], 200)
        code, case = phone.call("/api/cases", "POST", {"question":SCENARIOS["question_without_measurement"]["case"]["question"]})
        self.assertEqual(code, 201)
        cid = case["id"]
        self.assertEqual(len(case["evidence"]), 0)
        self.assertIn("자료가 없어도", case["proposals"][-1]["suggestion"])
        proposal_id = case["proposals"][-1]["id"]
        self.assertEqual(other.call(f"/api/cases/{cid}")[0], 404)
        self.assertEqual(other.call(f"/api/cases/{cid}", "PUT", {"question":"침범"})[0], 404)
        self.assertEqual(other.call(f"/api/cases/{cid}", "DELETE")[0], 404)
        self.assertEqual(other.call(f"/api/cases/{cid}/feedback/{proposal_id}", "PUT", {"reaction":"good"})[0], 404)
        self.assertEqual(other.call("/api/cases")[1]["cases"], [])
        self.assertEqual(pc.call("/api/cases")[1]["cases"][0]["id"], cid)

        code, changed = phone.call(f"/api/cases/{cid}/feedback/{proposal_id}", "PUT", {"reaction":"consider","did_act":"unknown","felt_result":""})
        self.assertEqual(code, 200)
        self.assertEqual(changed["proposals"][-1]["feedback"]["did_act"], "unknown")
        self.assertEqual(changed["proposals"][-1]["feedback"]["outcome_status"], "unknown")
        self.assertIsNone(changed["proposals"][-1]["feedback"]["execution_recorded_at"])
        self.assertIsNone(changed["proposals"][-1]["feedback"]["outcome_recorded_at"])
        self.assertEqual(changed["proposals"][-1]["feedback"]["felt_result"], "")
        self.assertEqual(pc.call(f"/api/cases/{cid}")[1]["proposals"][-1]["feedback"]["reaction"], "consider")
        self.assertEqual(pc.call(f"/api/cases/{cid}/feedback/{proposal_id}", "PUT", {"reaction":"not_fit","did_act":"no","felt_result":""})[0], 200)
        self.assertEqual(phone.call(f"/api/cases/{cid}")[1]["proposals"][-1]["feedback"]["reaction"], "not_fit")
        self.assertEqual(phone.call(f"/api/cases/{cid}/feedback/{proposal_id}", "DELETE")[0], 200)
        self.assertIsNone(pc.call(f"/api/cases/{cid}")[1]["proposals"][-1]["feedback"])

        # A bad CSRF token cannot change this case.
        old = pc.csrf
        pc.csrf = "wrong"
        self.assertEqual(pc.call(f"/api/cases/{cid}", "PUT", {"question":"침범"})[0], 403)
        pc.csrf = old
        self.assertEqual(pc.call(f"/api/cases/{cid}", "PUT", {"question":"수정된 합성 질문"})[0], 200)
        self.assertEqual(phone.call(f"/api/cases/{cid}")[1]["question"], "수정된 합성 질문")

        # Restart with the same SQLite database; session and case survive.
        self.server.terminate(); self.server.wait(timeout=5)
        self.start_server()
        self.assertEqual(pc.call(f"/api/cases/{cid}")[1]["question"], "수정된 합성 질문")
        self.assertEqual(other.call(f"/api/cases/{cid}")[0], 404)
        self.assertEqual(phone.call(f"/api/cases/{cid}", "DELETE")[0], 200)
        self.assertEqual(pc.call(f"/api/cases/{cid}")[0], 404)

    def test_synthetic_measurements_and_attachment_isolation(self):
        first, second = Browser(self.origin), Browser(self.origin)
        first.call("/api/register", "POST", {"name":"measure-a","password":secrets.token_urlsafe(16)})
        second.call("/api/register", "POST", {"name":"measure-b","password":secrets.token_urlsafe(16)})
        fixture = SCENARIOS["measurements_with_incomplete_activity_log"]
        cid = first.call("/api/cases", "POST", {"question":fixture["case"]["question"]})[1]["id"]
        for evidence in fixture["evidence"]:
            code, _ = first.call(f"/api/cases/{cid}/evidence", "POST", {
                "source": evidence["source_label"],
                "source_type": evidence["source_type"],
                "observed_at": evidence["observed_at"][:10],
                "note": evidence["summary"],
                "category": "useful",
            })
            self.assertEqual(code, 200)
        first_evidence = first.call(f"/api/cases/{cid}")[1]["evidence"][0]["id"]
        self.assertEqual(first.call(f"/api/cases/{cid}/claims", "POST", {"kind":"observed","text":"출처 없는 단정"})[0], 400)
        self.assertEqual(first.call(f"/api/cases/{cid}/claims", "POST", {"kind":"inferred","text":"불확실성 없는 추론"})[0], 400)
        self.assertEqual(first.call(f"/api/cases/{cid}/evidence", "POST", {"source":"합성 메모","observed_at":"2026-02-30"})[0], 400)
        self.assertEqual(first.call(f"/api/cases/{cid}/evidence/{first_evidence}", "PUT", {"category":"optional"})[1]["evidence"][0]["category"], "optional")
        code, result = first.call(f"/api/cases/{cid}/claims", "POST", {"kind":"observed","evidence_id":first_evidence,"text":"합성 수치 두 개가 기록됨"})
        self.assertEqual(code, 200)
        self.assertEqual(result["claims"][0]["kind"], "observed")
        first.call(f"/api/cases/{cid}/claims", "POST", {"kind":"inferred","text":"차이의 의미는 제한적으로 읽어야 함","uncertainty":"측정 조건과 운동 기록이 불완전함"})
        code, result = first.call(f"/api/cases/{cid}/proposals", "POST", {})
        self.assertEqual(code, 200)
        self.assertIn("측정", result["proposals"][-1]["unknown"])
        self.assertIn("원인을 단정할 수 없습니다", result["proposals"][-1]["rationale"])
        file = {"name":"synthetic.txt","mime":"text/plain","base64":base64.b64encode(b"synthetic only").decode()}
        result = first.call(f"/api/cases/{cid}/evidence", "POST", {"source":"합성 메모","observed_at":"2026-04-01","note":"검사용","file":file})[1]
        eid = result["evidence"][-1]["id"]
        self.assertEqual(first.call(f"/api/evidence/{eid}/file"), (200, b"synthetic only"))
        self.assertEqual(second.call(f"/api/evidence/{eid}/file")[0], 404)
        self.assertEqual(first.call(f"/api/cases/{cid}/evidence/{eid}", "DELETE")[0], 200)
        self.assertEqual(first.call(f"/api/evidence/{eid}/file")[0], 404)


if __name__ == "__main__":
    unittest.main()
