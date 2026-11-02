"""Local mock deployment target with a synthetic health-failure switch."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.environ.get("DUMMY_DEPLOY_TOKEN", "local-only-demo-token")
FAIL_RELEASE = os.environ.get("FAIL_RELEASE", "v2-bad")
active_release = "v1-stable"
active_hash = "bootstrap"


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, value):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/state":
            self.send_json(200, {"release": active_release, "artifact_sha256": active_hash})
        elif self.path == "/health":
            status = 503 if active_release == FAIL_RELEASE else 200
            self.send_json(status, {"status": "failed" if status != 200 else "ok", "release": active_release})
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        global active_release, active_hash
        if self.path != "/deploy":
            self.send_json(404, {"error": "not found"})
            return
        if self.headers.get("Authorization") != f"Bearer {TOKEN}":
            self.send_json(403, {"error": "controller authorization required"})
            return
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            release, digest = data["release"], data["artifact_sha256"]
            if not isinstance(release, str) or len(release) > 80:
                raise ValueError("invalid release")
        except (ValueError, KeyError, json.JSONDecodeError):
            self.send_json(400, {"error": "invalid deployment request"})
            return
        active_release, active_hash = release, digest
        self.send_json(200, {"accepted": True, "release": active_release})

    def log_message(self, fmt, *args):
        print(json.dumps({"event": "target", "message": fmt % args}), flush=True)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
