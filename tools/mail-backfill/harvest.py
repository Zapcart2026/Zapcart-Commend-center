#!/usr/bin/env python3
"""Pull every Outlook search result out of the fetcher transcripts into one flat file.

The fetchers only page the mailbox; nothing is re-typed by a model. Each tool result is
matched back to the call that produced it, so every message keeps its mailbox and folder.
Usage: harvest.py <subagents_dir> <out.jsonl>
"""
import json, sys, os, glob, collections

SUB, OUT = sys.argv[1], sys.argv[2]
TOOL = "mcp__Microsoft_365__outlook_email_search"
msgs, calls_seen, per_file = {}, 0, {}
chains = {}   # (mb, folder, query) -> [pages, finished]

def blocks(content):
    if isinstance(content, str):
        yield content
    elif isinstance(content, list):
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text": yield b.get("text", "")
            elif isinstance(b, str): yield b

def objects(text):
    """A result block is one JSON object, or several concatenated."""
    dec, i, n = json.JSONDecoder(), 0, len(text)
    while i < n:
        while i < n and text[i] in " \r\n\t": i += 1
        if i >= n or text[i] != "{": break
        try:
            obj, j = dec.raw_decode(text, i)
        except ValueError:
            break
        yield obj; i = j

for f in sorted(glob.glob(os.path.join(SUB, "agent-*.jsonl"))):
    calls, got = {}, 0
    for line in open(f, encoding="utf-8", errors="replace"):
        try: ev = json.loads(line)
        except ValueError: continue
        m = ev.get("message") or {}
        c = m.get("content")
        if not isinstance(c, list): continue
        for b in c:
            if not isinstance(b, dict): continue
            if b.get("type") == "tool_use" and b.get("name") == TOOL:
                calls[b["id"]] = b.get("input") or {}
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                inp = calls[b["tool_use_id"]]
                calls_seen += 1
                mb = (inp.get("mailboxOwnerEmail") or "farhan@zapcart.qa").split("@")[0].lower()
                folder = (inp.get("folderName") or "").lower() or "all"
                ck = (mb, folder, inp.get("query") or "", inp.get("sender") or "")
                ch = chains.setdefault(ck, [0, False])
                has_next, any_obj = False, False
                for t in blocks(b.get("content")):
                    for o in objects(t):
                        any_obj = True
                        if o.get("nextCursor") or o.get("nextOffset") is not None and o.get("moreResults"): has_next = True
                        if "id" not in o or "subject" not in o: continue
                        key = (mb, o["id"])
                        if key in msgs: continue
                        msgs[key] = dict(mb=mb, folder=folder, id=o["id"], subject=o.get("subject") or "",
                                         sender=(o.get("sender") or "").lower(), sender_name=o.get("senderName") or "",
                                         to=o.get("namedRecipients") or [], rcpt=[r.lower() for r in (o.get("recipients") or [])],
                                         date=(o.get("sentDateTime") or o.get("receivedDateTime") or "")[:19],
                                         summary=(o.get("summary") or "").replace("\r", ""), att=bool(o.get("hasAttachments")),
                                         imid=o.get("internetMessageId") or "")
                        got += 1
                txt = " ".join(blocks(b.get("content")))
                failed = b.get("is_error") or ("error" in txt[:200].lower() and not any_obj)
                if not failed:
                    ch[0] += 1
                    if not has_next: ch[1] = True
    if got: per_file[os.path.basename(f)] = got

with open(OUT, "w", encoding="utf-8") as fh:
    for m in sorted(msgs.values(), key=lambda m: (m["mb"], m["folder"], m["date"])):
        fh.write(json.dumps(m, ensure_ascii=False) + "\n")
by = collections.Counter((m["mb"], m["folder"]) for m in msgs.values())
span = {}
for m in msgs.values():
    k = (m["mb"], m["folder"]); d = m["date"][:10]
    lo, hi = span.get(k, ("9999", "0000")); span[k] = (min(lo, d), max(hi, d))
json.dump([dict(mb=k[0], folder=k[1], query=k[2], sender=k[3], pages=v[0], finished=v[1]) for k, v in chains.items()],
          open(OUT.replace(".jsonl", "") + "_chains.json", "w"), indent=0)
print("search calls with results:", calls_seen, "| transcripts with mail:", len(per_file), "| messages:", len(msgs))
for k in sorted(by): print("  %-8s %-11s %5d   %s .. %s" % (k[0], k[1], by[k], span[k][0], span[k][1]))
