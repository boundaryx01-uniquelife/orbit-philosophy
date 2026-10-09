"""Check that the synthetic preview has no login or write API."""

import os
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent


class PreviewBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        cls.origin = f"http://127.0.0.1:{cls.port}"
        cls.server = subprocess.Popen(
            [sys.executable, str(ROOT / "server.py")],
            env={**os.environ, "LIFE_OS_PORT": str(cls.port)},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(50):
            try:
                urlopen(cls.origin, timeout=0.2).close()
                return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("preview server did not start")

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.wait(timeout=5)

    def test_chat_only_and_no_write_endpoint(self):
        with urlopen(self.origin) as response:
            page = response.read().decode()
            self.assertIn('id="composer"', page)
            self.assertNotIn('type="password"', page)
            self.assertIsNone(response.headers.get("Set-Cookie"))
        with urlopen(self.origin + "/fixtures/first_flow.synthetic.json") as response:
            self.assertIn(b'"synthetic": true', response.read())
        with self.assertRaises(HTTPError) as failure:
            urlopen(Request(self.origin + "/api/register", data=b"{}", method="POST"))
        self.assertEqual(failure.exception.code, 405)


if __name__ == "__main__":
    unittest.main()
