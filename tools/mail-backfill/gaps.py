#!/usr/bin/env python3
"""Which planned searches are still incomplete, and what date range is left in each.
Results come newest first, so what is missing is the OLD end of each range."""
import json, sys, os, re, datetime as dt, collections
BASE = sys.argv[1]
plan = json.load(open(os.path.join(BASE, "backfill/tasks/_plan.json")))
chains = {(c["mb"], c["folder"], c["query"]): c for c in json.load(open(os.path.join(BASE, "backfill/raw_chains.json")))}
rows = [json.loads(l) for l in open(os.path.join(BASE, "backfill/raw.jsonl"))]
isre = re.compile(r"\bre\b|\bfw\b|\bfwd\b", re.I)
by = collections.defaultdict(list)
for r in rows: by[(r["mb"], r["folder"])].append(r)
gaps = []
for p in plan:
    q = p["query"]
    m = re.match(r"received:(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})\s*(.*)", q)
    if not m: continue
    a, b, rest = m.groups()
    mb = (p.get("mailboxOwnerEmail") or "farhan@").split("@")[0]
    k = (mb, p["folderName"].lower(), q)
    c = chains.get(k)
    if c and c["finished"]: continue
    if not c or c["pages"] == 0:
        left_to = b
    else:
        got = [r["date"][:10] for r in by[(mb, p["folderName"].lower())] if a <= r["date"][:10] <= b and isre.search(r["subject"])]
        # trust only as many as this chain could have returned
        got.sort(reverse=True)
        got = got[:25 * c["pages"]]
        left_to = got[-1] if got else b
    gaps.append(dict(mb=mb, folder=p["folderName"], a=a, b=left_to, rest=rest))
days = 0
calls = []
for g in gaps:
    d = dt.date.fromisoformat(g["a"])
    while d <= dt.date.fromisoformat(g["b"]):
        q = dict(folderName=g["folder"], query=("received:%s..%s %s" % (d, d, g["rest"])).strip(), limit=25)
        if g["mb"] != "farhan": q["mailboxOwnerEmail"] = g["mb"] + "@zapcart.qa"
        key = json.dumps(q, sort_keys=True)
        if key not in {json.dumps(x, sort_keys=True) for x in calls}:
            ck = (g["mb"], g["folder"].lower(), q["query"])
            if not (ck in chains and chains[ck]["finished"]): calls.append(q)
        d += dt.timedelta(days=1)
print("incomplete searches:", len(gaps), "| single-day calls needed:", len(calls))
print(collections.Counter(((c.get("mailboxOwnerEmail") or "farhan@").split("@")[0], c["folderName"]) for c in calls))
json.dump(calls, open(os.path.join(BASE, "backfill/tasks/_gaps.json"), "w"))
