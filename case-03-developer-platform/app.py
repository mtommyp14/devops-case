import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]
PR_NUMBER = os.environ.get("PR_NUMBER", "local")
GENERATION = os.environ.get("GENERATION", "1")


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            with psycopg.connect(DATABASE_URL, connect_timeout=2) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT count(*) FROM preview_items")
                    count = cur.fetchone()[0]
                    if path == "/items":
                        cur.execute("SELECT item_id, label, amount FROM preview_items ORDER BY item_id")
                        items = [{"id": r[0], "label": r[1], "amount": r[2]} for r in cur.fetchall()]
                    else:
                        items = None
            if path == "/health":
                self.reply(200, {"status": "ready", "synthetic_items": count, "pr": PR_NUMBER, "generation": GENERATION})
            elif path == "/items":
                self.reply(200, {"pr": PR_NUMBER, "generation": GENERATION, "items": items})
            elif path == "/":
                self.reply(200, {"service": "PR preview", "pr": PR_NUMBER, "generation": GENERATION, "synthetic_items": count})
            else:
                self.reply(404, {"error": "not found"})
        except Exception as exc:
            self.reply(503, {"status": "not ready", "reason": type(exc).__name__})

    def log_message(self, fmt, *args):
        print(json.dumps({"event": "http", "message": fmt % args}), flush=True)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
