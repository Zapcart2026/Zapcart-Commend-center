#!/usr/bin/env python3
"""raw.jsonl (every harvested message) -> one aggregate per outside organisation.

Deterministic: who we wrote to, who wrote to us, which threads, when, and which message is the
newest in each thread. The only judgement left for a model is the role and a one-line gist,
and it gets a compact evidence card per organisation for that (class_in/*.json).

Usage: aggregate.py <scratchpad> [batch_size]
"""
import json, re, sys, os, collections, shutil

BASE = sys.argv[1]
BATCH = int(sys.argv[2]) if len(sys.argv) > 2 else 150
SINCE = "2026-05-10"
RAW = os.path.join(BASE, "backfill", "raw.jsonl")

FREEMAIL = {"gmail.com","yahoo.com","hotmail.com","outlook.com","live.com","icloud.com","yeah.net","163.com",
            "126.com","qq.com","foxmail.com","proton.me","protonmail.com","aol.com","mail.ru","msn.com",
            "ymail.com","rediffmail.com","googlemail.com","me.com","gmx.com","zoho.com","sina.com","139.com",
            "yahoo.co.in","yahoo.co.uk","outlook.sa","hotmail.co.uk","live.in","naver.com","aliyun.com"}
INTERNAL = "zapcart.qa"
# senders that are machines, not counterparties
BOT = re.compile(r"(^|[._-])(no-?reply|noreply|donotreply|do-not-reply|mailer-daemon|postmaster|notifications?|bounce|"
                 r"newsletter|news|alerts?|updates?|digest|automated|system)([._-]|@)", re.I)
AUTO = re.compile(r"^(automatic reply|auto(matic)?[- ]?reply|out of office|undeliverable|delivery status|"
                  r"mail delivery|read:|accepted:|declined:|tentative:)", re.I)
PREFIX = re.compile(r"^\s*((re|fw|fwd|aw|sv|tr|rv)\s*(\[\d+\])?\s*[:：]\s*)+", re.I)
WARM = re.compile(r"Maureen-objective", re.I)
ISRE = re.compile(r"^\s*(re|fw|fwd|aw|sv|tr|rv)\s*(\[\d+\])?\s*[:\uff1a]", re.I)
EVENTS = [("nda", re.compile(r"\b(NC)?NDA\b|non[- ]?disclosure|confidentiality agreement|non[- ]?circumvent", re.I)),
          ("end_user_form", re.compile(r"end[- ]?user\s+(kyc|declaration|statement|certificate|certification|form|undertaking|documentation|intake|compliance|questionnaire|details form)|"
                                       r"intake form|compliance questionnaire|export compliance|\bEUC\b|\bEUS\b|KYC (pack|documentation|documents)", re.I)),
          ("registration", re.compile(r"(vendor|supplier|customer|company|account)\s+(registration|onboarding|application|opening|creation)|"
                                      r"registration form|\bKYC\b|credit application|new account form", re.I)),
          ("dispute", re.compile(r"\brefund|chargeback|legal notice|formal complaint|public prosecution", re.I))]

def key_of(email):
    email = (email or "").strip().lower()
    if "@" not in email or email.startswith("/o="): return ""
    dom = email.split("@", 1)[1]
    if dom == INTERNAL or dom.endswith("." + INTERNAL): return ""
    if "prod.outlook.com" in dom or dom.endswith("onmicrosoft.com"): return ""
    return email if dom in FREEMAIL or dom.startswith("yandex.") else dom

def norm(subject):
    return re.sub(r"\s+", " ", PREFIX.sub("", subject or "")).strip()

rows, seen = [], set()
for line in open(RAW, encoding="utf-8"):
    m = json.loads(line)
    if m["date"][:10] < SINCE: continue
    if WARM.search(m["summary"]) or AUTO.match(m["subject"].strip()): continue
    dk = m.get("imid") or (m["mb"], m["id"])
    if dk in seen: continue                      # the same email filed in two mailboxes counts once
    seen.add(dk); rows.append(m)

orgs, events = {}, []
def acc(k):
    if k not in orgs:
        orgs[k] = dict(contacts={}, threads={}, first="9999", last="0000", n_out=0, n_in=0, mb=set(), conv=False)
    return orgs[k]

skipped_bot = 0
for m in rows:
    names = {(p.get("address") or "").lower(): (p.get("name") or "").strip() for p in m.get("to") or []}
    internal_sender = m["sender"].endswith("@" + INTERNAL) or m["sender"].startswith("/o=") or not m["sender"]
    if m["folder"] == "sent items" or internal_sender:
        direction, parties = "out", [a for a in m["rcpt"]]
    else:
        if BOT.search(m["sender"]): skipped_bot += 1; continue
        direction, parties = "in", [m["sender"]]
        names[m["sender"]] = m.get("sender_name") or ""
    keys = collections.OrderedDict()
    for a in parties:
        k = key_of(a)
        if k: keys.setdefault(k, []).append(a)
    if not keys: continue
    subj = norm(m["subject"])
    day = m["date"][:10]
    snippet = re.sub(r"\s+", " ", m["summary"]).strip()
    isre = bool(ISRE.match(m["subject"]))
    hay = m["subject"] + " " + m["summary"][:200]
    kinds = [n for n, rx in EVENTS if rx.search(hay)]
    if not isre and not kinds and direction == "out":
        continue          # a first-touch email nobody answered is outreach, not a relationship
    for kd in kinds:
        events.append(dict(type=kd, date=day, dir=direction, orgs=list(keys)[:6], subject=subj[:160], id=m["id"], mb=m["mb"],
                           folder=m["folder"], att=m["att"], snippet=snippet[:200]))
    for k, addrs in keys.items():
        o = acc(k)
        o["conv"] = o["conv"] or isre or direction == "in"
        for a in addrs:
            nm = names.get(a, "")
            if nm.lower() == a: nm = ""
            if a not in o["contacts"] or (nm and not o["contacts"][a]): o["contacts"][a] = nm
        o["first"], o["last"] = min(o["first"], day), max(o["last"], day)
        o["n_" + direction] += 1
        o["mb"].add(m["mb"])
        t = o["threads"].setdefault(subj.lower(), dict(subject=subj, first=day, last="", n_out=0, n_in=0, last_dir="",
                                                       last_at="", last_id="", last_mb="", snippet="", att=False))
        t["n_" + direction] += 1
        t["first"] = min(t["first"], day)
        t["att"] = t["att"] or m["att"]
        if m["date"] >= t["last_at"]:
            t.update(last=day, last_at=m["date"], last_dir=direction, snippet=snippet[:260],
                     last_id=m["id"] if m["folder"] == "sent items" else t["last_id"],
                     last_mb=m["mb"] if m["folder"] == "sent items" else t["last_mb"])

out, cards = {}, []
for k, o in orgs.items():
    th = sorted(o["threads"].values(), key=lambda t: t["last_at"], reverse=True)
    newest = th[0]
    out[k] = dict(contacts=[dict(email=e, name=n) for e, n in list(o["contacts"].items())[:8]],
                  first=o["first"], last=o["last"], n_out=o["n_out"], n_in=o["n_in"], mb=sorted(o["mb"]),
                  threads=[{x: t[x] for x in ("subject", "first", "last", "n_out", "n_in", "last_dir", "last_id", "last_mb", "snippet", "att")}
                           for t in th[:6]], n_threads=len(th), last_dir=newest["last_dir"])
    cards.append(dict(k=k, c=[("%s <%s>" % (n, e)) if n else e for e, n in list(o["contacts"].items())[:3]],
                      out=o["n_out"], inn=o["n_in"],
                      t=[dict(s=t["subject"][:100], d=t["last"], o=t["n_out"], i=t["n_in"], by="zapcart" if t["last_dir"] == "out" else "them",
                              x=t["snippet"][:170]) for t in th[:3]]))

json.dump(out, open(os.path.join(BASE, "backfill", "orgs.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump(events, open(os.path.join(BASE, "backfill", "events_raw.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
cdir = os.path.join(BASE, "backfill", "class_in")
if os.path.isdir(cdir): shutil.rmtree(cdir)
os.makedirs(cdir); os.makedirs(os.path.join(BASE, "backfill", "class_out"), exist_ok=True)
cards.sort(key=lambda c: c["k"])
for i in range(0, len(cards), BATCH):
    json.dump(cards[i:i + BATCH], open(os.path.join(cdir, "C%02d.json" % (i // BATCH + 1)), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)

by = collections.Counter((m["mb"], m["folder"]) for m in rows)
print("messages kept:", len(rows), dict(("%s/%s" % k, v) for k, v in sorted(by.items())), "| bot senders skipped:", skipped_bot)
print("organisations:", len(out), "| two-way:", sum(1 for o in out.values() if o["n_in"] and o["n_out"]),
      "| inbound only:", sum(1 for o in out.values() if o["n_in"] and not o["n_out"]),
      "| outbound only:", sum(1 for o in out.values() if o["n_out"] and not o["n_in"]))
print("classification batches:", (len(cards) + BATCH - 1) // BATCH, "| card bytes:", sum(len(json.dumps(c, ensure_ascii=False)) for c in cards))
print("paperwork events:", dict(collections.Counter(e["type"] for e in events)))
recent = [k for k, o in out.items() if o["last"] >= "2026-10-12"]
print("organisations active since 12 Oct:", len(recent))
