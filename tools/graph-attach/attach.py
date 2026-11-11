#!/usr/bin/env python3
"""Attach files to an existing Outlook DRAFT through Microsoft Graph.

The Outlook connector can create and edit drafts but cannot attach files. This tool adds the
attachment to a draft that already exists, so the email is complete when it is opened for review.
It never sends anything: the app permission it needs is Mail.ReadWrite (application), not Mail.Send.

Credentials are read from the environment and are never printed:
    MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET

Usage:
    attach.py <mailbox> <draft message id> <file path> <attachment name> [<file path> <name> ...]

Exit text (last line): OK | NO_KEY | NOT_A_DRAFT | ERROR <detail>
"""
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

LOGIN = os.environ.get("MS_LOGIN_BASE", "https://login.microsoftonline.com")
GRAPH = os.environ.get("MS_GRAPH_BASE", "https://graph.microsoft.com/v1.0")
MAX_BYTES = 2_900_000  # Graph's simple attachment call takes files under 3 MB


def call(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw) if raw else {}


def main(argv):
    tenant, client, secret = (os.environ.get(k, "") for k in ("MS_TENANT_ID", "MS_CLIENT_ID", "MS_CLIENT_SECRET"))
    if not (tenant and client and secret):
        print("NO_KEY")
        return 2
    if len(argv) < 4 or len(argv) % 2:
        print("ERROR usage: attach.py <mailbox> <draft id> <file> <name> [<file> <name> ...]")
        return 2
    mailbox, mid, pairs = argv[0], argv[1], argv[2:]

    form = urllib.parse.urlencode({"client_id": client, "client_secret": secret, "grant_type": "client_credentials",
                                   "scope": "https://graph.microsoft.com/.default"}).encode()
    token = call("%s/%s/oauth2/v2.0/token" % (LOGIN, urllib.parse.quote(tenant)), form)["access_token"]

    base = "%s/users/%s/messages/%s" % (GRAPH, urllib.parse.quote(mailbox), urllib.parse.quote(mid, safe=""))
    head = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    # The connector hands out immutable ids; Graph needs this header to accept them. Fall back to
    # plain ids if the message is not found that way.
    for prefer in ('IdType="ImmutableId"', None):
        h = dict(head, **({"Prefer": prefer} if prefer else {}))
        try:
            msg = call(base + "?$select=isDraft,subject", headers=h)
            break
        except urllib.error.HTTPError as e:
            if e.code not in (400, 404) or prefer is None:
                raise
    if not msg.get("isDraft"):
        print("NOT_A_DRAFT")
        return 3

    have = {a.get("name") for a in call(base + "/attachments?$select=name", headers=h).get("value", [])}
    for i in range(0, len(pairs), 2):
        path, name = pairs[i], pairs[i + 1]
        if name in have:
            print("already attached: " + name)
            continue
        blob = open(path, "rb").read()
        if len(blob) > MAX_BYTES:
            print("ERROR %s is %d bytes; the limit is %d" % (name, len(blob), MAX_BYTES))
            return 4
        body = {"@odata.type": "#microsoft.graph.fileAttachment", "name": name,
                "contentType": mimetypes.guess_type(name)[0] or "application/octet-stream",
                "contentBytes": base64.b64encode(blob).decode()}
        call(base + "/attachments", json.dumps(body).encode(), h, "POST")
        print("attached: " + name)

    names = sorted(a.get("name") for a in call(base + "/attachments?$select=name", headers=h).get("value", []))
    print("on the draft now: " + ", ".join(names))
    print("OK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300].replace("\n", " ")
        print("ERROR HTTP %s %s" % (e.code, detail))
        sys.exit(1)
    except Exception as e:  # network, file, JSON
        print("ERROR %s: %s" % (type(e).__name__, e))
        sys.exit(1)
