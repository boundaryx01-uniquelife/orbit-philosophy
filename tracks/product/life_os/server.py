"""Serve the synthetic chat preview locally. No login, API, or data storage."""

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("LIFE_OS_PORT", "8765"))
FILES = {
    "/": (ROOT / "static" / "index.html", "text/html; charset=utf-8"),
    "/app.js": (ROOT / "static" / "app.js", "text/javascript; charset=utf-8"),
    "/style.css": (ROOT / "static" / "style.css", "text/css; charset=utf-8"),
    "/fixtures/first_flow.synthetic.json": (ROOT / "fixtures" / "first_flow.synthetic.json", "application/json; charset=utf-8"),
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        item = FILES.get(urlsplit(self.path).path)
        if item is None:
            self.send_error(404)
            return
        path, content_type = item
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; base-uri 'none'; form-action 'self'; object-src 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self.send_error(405)


if __name__ == "__main__":
    print(f"Synthetic Life OS chat: http://127.0.0.1:{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
