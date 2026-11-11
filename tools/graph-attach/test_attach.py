#!/usr/bin/env python3
"""Offline test for attach.py: runs it against a local stand-in for Microsoft's two endpoints.

Checks the token request, the immutable-id header, the draft check, the attachment body, that a
file already on the draft is not attached twice, and that a sent message is refused.
Run: python3 tools/graph-attach/test_attach.py
"""
import base64
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = {"attachments": [], "log": [], "is_draft": True}


class Fake(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, code, obj):
        raw = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path.endswith("/oauth2/v2.0/token"):
            form = urllib.parse.parse_qs(body.decode())
            STATE["log"].append(("token", self.path, form))
            return self.reply(200, {"access_token": "TESTTOKEN"})
        if self.path.endswith("/attachments"):
            STATE["log"].append(("attach", self.path, dict(self.headers)))
            STATE["attachments"].append(json.loads(body))
            return self.reply(201, {"id": "att%d" % len(STATE["attachments"])})
        self.reply(404, {})

    def do_GET(self):
        STATE["log"].append(("get", self.path, dict(self.headers)))
        if self.headers.get("Authorization") != "Bearer TESTTOKEN":
            return self.reply(401, {})
        if "/attachments" in self.path:
            return self.reply(200, {"value": [{"name": a["name"]} for a in STATE["attachments"]]})
        self.reply(200, {"isDraft": STATE["is_draft"], "subject": "RE: test"})


def run(args, env):
    p = subprocess.run([sys.executable, os.environ.get("ATTACH_SCRIPT") or os.path.join(HERE, "attach.py")] + args, env=env, capture_output=True, text=True)
    return p.returncode, p.stdout.strip().splitlines()


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % srv.server_port
    env = {k: v for k, v in os.environ.items() if not k.lower().endswith("_proxy")}
    env.update(MS_LOGIN_BASE=base, MS_GRAPH_BASE=base + "/v1.0", NO_PROXY="127.0.0.1", no_proxy="127.0.0.1")

    with tempfile.TemporaryDirectory() as d:
        pdf = os.path.join(d, "x.pdf")
        open(pdf, "wb").write(b"%PDF-1.4 test file")
        mid = "AAkALgAAAAAAHYQDEapmEc2byACqAC-EWg0AL3a-im-0QUy36P4C5gyoUgAB_test="

        code, out = run(["sales@example.com", mid, pdf, "Zapcart Mutual NDA.pdf"], dict(env))
        assert code == 2 and out[-1] == "NO_KEY", out

        env.update(MS_TENANT_ID="tenant-1", MS_CLIENT_ID="client-1", MS_CLIENT_SECRET="s3cret")
        code, out = run(["sales@example.com", mid, pdf, "Zapcart Mutual NDA.pdf"], env)
        assert code == 0 and out[-1] == "OK", out
        assert "s3cret" not in "\n".join(out), "the secret must never be printed"
        kind, path, form = STATE["log"][0]
        assert kind == "token" and path == "/tenant-1/oauth2/v2.0/token"
        assert form["grant_type"] == ["client_credentials"] and form["scope"] == ["https://graph.microsoft.com/.default"]
        gets = [x for x in STATE["log"] if x[0] == "get"]
        assert gets[0][1].startswith("/v1.0/users/sales%40example.com/messages/" + urllib.parse.quote(mid, safe=""))
        assert gets[0][2].get("Prefer") == 'IdType="ImmutableId"'
        att = STATE["attachments"][0]
        assert att["@odata.type"] == "#microsoft.graph.fileAttachment" and att["name"] == "Zapcart Mutual NDA.pdf"
        assert att["contentType"] == "application/pdf" and base64.b64decode(att["contentBytes"]) == b"%PDF-1.4 test file"

        code, out = run(["sales@example.com", mid, pdf, "Zapcart Mutual NDA.pdf"], env)
        assert code == 0 and out[0].startswith("already attached") and len(STATE["attachments"]) == 1, out

        STATE["is_draft"] = False
        code, out = run(["sales@example.com", mid, pdf, "Other.pdf"], env)
        assert code == 3 and out[-1] == "NOT_A_DRAFT" and len(STATE["attachments"]) == 1, out

    print("all checks passed")


if __name__ == "__main__":
    main()
