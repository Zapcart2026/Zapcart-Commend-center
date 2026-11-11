#!/usr/bin/env python3
"""orgs.json (deterministic mail aggregates) + class_out (role labels) + Zoho Books
-> register documents and ArtifactData batch files.

Usage: build2.py <scratchpad>
"""
import json, re, sys, os, glob, hashlib, collections, shutil

BASE = sys.argv[1]
BF = os.path.join(BASE, "backfill")
OUT = os.path.join(BASE, "registers")
RECENT = "2026-10-12"
ROLES = {"supplier", "customer", "both", "platform", "logistics", "finance_gov", "service", "prospect", "other"}
FREEMAIL_RE = re.compile(r"@")

def clean_id(s):
    s = re.sub(r"[^A-Za-z0-9_\-.~:@+]", "_", s.strip().lower())[:180]
    return s if s not in ("", ".", "..") else "x_" + hashlib.sha1(s.encode()).hexdigest()[:8]

def key_of(email):
    email = (email or "").strip().lower()
    if "@" not in email: return ""
    dom = email.split("@", 1)[1]
    if dom == "zapcart.qa": return ""
    return dom

def _never_contact():
    """The never-contact list is business-confidential, so it is NOT in this repository.
    Put it in backfill/never_contact.json: {"contains": ["..."], "exact": ["..."],
    "domains_except": {"example.net": ["allowed.person@example.net"]}, "hands_off_contains": ["..."]}"""
    f = os.path.join(BF, "never_contact.json")
    return json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {}
NC = _never_contact()

def dnc_of(k, contacts):
    if any(x in k for x in NC.get("contains", [])) or k in NC.get("exact", []):
        return "On the never-contact list."
    for dom, allowed in (NC.get("domains_except") or {}).items():
        if k == dom or k.endswith("." + dom):
            return "Only %s may be contacted here. Everyone else is on the never-contact list." % ", ".join(allowed)
    return ""

orgs = json.load(open(os.path.join(BF, "orgs.json"), encoding="utf-8"))
labels, bad = {}, []
for f in sorted(glob.glob(os.path.join(BF, "class_out", "C*.json"))):
    try:
        for x in json.load(open(f, encoding="utf-8")):
            if isinstance(x, dict) and x.get("k"): labels[x["k"].strip().lower()] = x
    except Exception as e:
        bad.append("%s: %s" % (os.path.basename(f), e))
events = json.load(open(os.path.join(BF, "events_raw.json"), encoding="utf-8"))
zoho = json.load(open(os.path.join(BF, "zoho.json"), encoding="utf-8"))

# ---- Zoho: which contacts have real paper
docs_by, due_by = collections.defaultdict(collections.Counter), collections.Counter()
last_doc = {}
def touch(cid, d):
    if d: last_doc[cid] = max(last_doc.get(cid, ""), d[:10])
for e in zoho.get("estimates", []):
    if e.get("status") != "draft": docs_by[e.get("customer_id")]["quotes"] += 1; touch(e.get("customer_id"), e.get("date"))
for s in zoho.get("sales_orders", []):
    if s.get("status") not in ("draft", "void"): docs_by[s.get("customer_id")]["orders"] += 1; touch(s.get("customer_id"), s.get("date"))
for i in zoho.get("invoices", []):
    if i.get("status") in ("void", "draft"): continue
    docs_by[i.get("customer_id")]["invoices"] += 1; touch(i.get("customer_id"), i.get("date"))
    if (i.get("balance") or 0) > 0: due_by[i.get("customer_id")] += i["balance"]
for p in zoho.get("purchase_orders", []):
    if p.get("status") != "draft": docs_by[p.get("vendor_id")]["POs"] += 1; touch(p.get("vendor_id"), p.get("date"))
zmap = collections.defaultdict(list)          # org key -> zoho contacts
zoho_only = []
for c in zoho.get("contacts", []):
    em = (c.get("email") or "").strip().lower()
    k = em if em in orgs else key_of(em)
    if k and k in orgs: zmap[k].append(c)
    elif docs_by.get(c["id"]): zoho_only.append(c)

ev_by = collections.defaultdict(list)
for e in events:
    for k in e["orgs"]: ev_by[k].append(e)

if os.path.isdir(OUT): shutil.rmtree(OUT)
for d in ("companies", "activity", "batches"): os.makedirs(os.path.join(OUT, d))
writes, used, roles, unlabelled = [], set(), collections.Counter(), 0

def emit(coll, did, doc):
    did = clean_id(did)
    while (coll, did) in used: did += "_"
    used.add((coll, did))
    path = os.path.join(OUT, coll, did + ".json")
    json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    writes.append(dict(op="set", collection=coll, doc_id=did, file_path=path))

for k, o in orgs.items():
    lab = labels.get(k)
    if not lab: unlabelled += 1
    role = (lab or {}).get("role") if (lab or {}).get("role") in ROLES else "other"
    why = (lab or {}).get("why") or ""
    zs = zmap.get(k, [])
    zbits = []
    for c in zs[:3]:
        d = docs_by.get(c["id"])
        b = ["Customer" if c.get("type") == "customer" else "Vendor"]
        if d: b += ["%d %s" % (v, n) for n, v in d.items()]
        if due_by.get(c["id"]): b.append("%s %s unpaid" % (c.get("currency") or "QAR", format(round(due_by[c["id"]]), ",")))
        zbits.append(" · ".join(b))
        if d and (d.get("quotes") or d.get("orders") or d.get("invoices")):
            if role in ("supplier",): role = "both"
            elif role in ("prospect", "other"): role, why = "customer", "Zoho Books: " + ", ".join("%d %s" % (v, n) for n, v in d.items())
        if d and d.get("POs"):
            if role in ("customer",): role = "both"
            elif role in ("prospect", "other"): role, why = "supplier", "Zoho Books: %d purchase order(s)" % d["POs"]
    th = o["threads"]
    newest = th[0]
    state = ""
    if o["last"] >= RECENT and role in ("supplier", "customer", "both", "logistics"):
        state = "awaiting_us" if newest["last_dir"] == "in" else "awaiting_them"
    doc = dict(name=((lab or {}).get("name") or "").strip() or k.split("@")[0], role=role, role_why=why[:120],
               country=((lab or {}).get("cc") or "").upper()[:2], contacts=o["contacts"][:8],
               items=[str(x)[:90] for x in ((lab or {}).get("items") or [])][:6],
               first=o["first"], last=o["last"], n=o["n_out"] + o["n_in"], n_out=o["n_out"], n_in=o["n_in"], mb=o["mb"],
               last_subject=newest["subject"][:160], last_gist=((lab or {}).get("gist") or "")[:220], state=state,
               threads=[dict(subject=t["subject"][:140], last=t["last"], by="us" if t["last_dir"] == "out" else "them") for t in th[:4]],
               src="mail history 10 May - 11 Nov 2026")
    sent = [t for t in th if t["last_id"]]
    if sent: doc.update(last_id=sent[0]["last_id"], last_mb=sent[0]["last_mb"])
    if zbits: doc["zoho"] = "; ".join(zbits)
    ph = next((c.get("phone") for c in zs if c.get("phone")), "")
    if ph: doc["phone"] = ph
    note = dnc_of(k, o["contacts"])
    if note: doc.update(dnc=True, note=note, state="")
    if any(x in k for x in NC.get("hands_off_contains", [])): doc.update(hold=True, note="Hands-off: the owner handles this company personally.")
    for e in sorted(ev_by.get(k, []), key=lambda e: e["date"]):
        if e["type"] == "nda": doc["nda"] = dict(s="on record", at=e["date"], note=e["subject"][:140])
        elif e["type"] == "registration": doc["reg"] = dict(s="on record", at=e["date"], note=e["subject"][:140])
    emit("companies", k, doc)
    roles[role] += 1

for c in zoho_only:                                   # customers / vendors with paper in Zoho but no mail thread captured
    d = docs_by[c["id"]]
    role = "customer" if (d.get("quotes") or d.get("orders") or d.get("invoices")) else "supplier"
    if (d.get("quotes") or d.get("orders") or d.get("invoices")) and d.get("POs"): role = "both"
    b = ["Customer" if c.get("type") == "customer" else "Vendor"] + ["%d %s" % (v, n) for n, v in d.items()]
    if due_by.get(c["id"]): b.append("%s %s unpaid" % (c.get("currency") or "QAR", format(round(due_by[c["id"]]), ",")))
    em = (c.get("email") or "").strip().lower()
    nm = " ".join(x for x in (c.get("first_name"), c.get("last_name")) if x).strip()
    doc = dict(name=(c.get("company") or c.get("name") or "").strip(), role=role,
               role_why="Zoho Books: " + ", ".join("%d %s" % (v, n) for n, v in d.items()), country="",
               contacts=[dict(email=em, name=nm)] if em else [], items=[], first=last_doc.get(c["id"], ""), last=last_doc.get(c["id"], ""),
               n=0, mb=[], state="", zoho=" · ".join(b), src="Zoho Books")
    if c.get("phone"): doc["phone"] = c["phone"]
    emit("companies", key_of(em) or ("zoho-" + c["id"]), doc)
    roles[role] += 1

# ---- activity log
KIND = dict(nda="nda", end_user_form="end_user_form", registration="registration", dispute="dispute")
grp = {}
for e in events:
    primary = e["orgs"][0] if e["orgs"] else ""
    g = grp.setdefault((e["type"], primary, e["subject"].lower()), dict(first=e["date"], last=e["date"], n=0, e=e))
    g["first"], g["last"], g["n"] = min(g["first"], e["date"]), max(g["last"], e["date"]), g["n"] + 1
act = []
for (typ, primary, _), g in grp.items():
    lab = labels.get(primary) or {}
    e = g["e"]
    act.append(dict(ts=g["last"], kind=KIND[typ], party=primary, name=lab.get("name") or primary,
                    note="%s (%d email%s%s)" % (e["subject"][:150], g["n"], "" if g["n"] == 1 else "s",
                                               ", from %s" % g["first"] if g["first"] != g["last"] else ""),
                    by="mail history", mb=e["mb"]))
def zact(rows, kind, word, who, skip):
    for r in rows:
        if r.get("status") in skip or not r.get("date"): continue
        extra = (", %s unpaid" % format(round(r["balance"]), ",")) if (r.get("balance") or 0) > 0 else ""
        act.append(dict(ts=r["date"][:10], kind=kind, party="", name=r.get(who) or "",
                        note="%s %s, %s %s, %s%s" % (word, r.get("number"), r.get("currency"), format(round(r.get("total") or 0), ","),
                                                    r.get("status"), extra), by="Zoho Books", ref=r.get("number")))
zact(zoho.get("estimates", []), "quote", "Quotation", "customer", ("draft",))
zact(zoho.get("sales_orders", []), "order", "Sales order", "customer", ("draft", "void"))
zact(zoho.get("invoices", []), "invoice", "Invoice", "customer", ("draft", "void"))
zact(zoho.get("purchase_orders", []), "po_sent", "Purchase order", "vendor", ("draft",))
for x in act:
    h = hashlib.sha1(json.dumps([x["ts"], x["kind"], x["name"], x["note"]], ensure_ascii=False).encode()).hexdigest()[:10]
    emit("activity", "%s-%s-%s" % (x["ts"], x["kind"], h), x)

# ---- one compact index of real suppliers for the RFQ sweep (a single document the Dispatcher can read cheaply)
idx = {}
for w in writes:
    if w["collection"] != "companies": continue
    d = json.load(open(w["file_path"], encoding="utf-8"))
    if d["role"] not in ("supplier", "both") or d.get("dnc") or d.get("hold"): continue
    em = d["contacts"][0]["email"] if d.get("contacts") else ""
    idx[re.sub(r"[^A-Za-z0-9_-]", "_", w["doc_id"])] = " | ".join([w["doc_id"], d["name"], d.get("country") or "", em,
                                                                  "; ".join(d.get("items") or [])[:140], d.get("last") or ""])
json.dump(dict(updated="2026-11-11", note="Every supplier Zapcart has exchanged real emails with since 10 May 2026. "
               "Value = domain | name | country | first contact | what they carry | last contact. Full record: Control Board "
               "collection 'companies', document id = the domain.", s=idx),
          open(os.path.join(OUT, "supplier_index.json"), "w", encoding="utf-8"), ensure_ascii=False)

for i in range(0, len(writes), 50):
    json.dump(writes[i:i + 50], open(os.path.join(OUT, "batches", "%03d.json" % (i // 50)), "w"), ensure_ascii=False)
summary = dict(companies=sum(1 for w in writes if w["collection"] == "companies"), from_mail=len(orgs), zoho_only=len(zoho_only),
               roles=dict(roles), unlabelled=unlabelled, label_files_bad=bad, activity=len(act),
               waiting_on_us=sum(1 for w in writes if w["collection"] == "companies" and json.load(open(w["file_path"]))["state"] == "awaiting_us"),
               batches=(len(writes) + 49) // 50, bytes=sum(os.path.getsize(w["file_path"]) for w in writes))
json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
