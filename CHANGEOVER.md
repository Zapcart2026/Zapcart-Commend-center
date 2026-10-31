# Changeover — 1 November 2026

What to switch off, what to keep, what to create. Ten minutes of clicking.

---

## 1. The money leak (do this first)

Your ChatGPT **"Zapcart Command Center — Automatic"** task runs **every 2 minutes**.

    30 runs/hour x 24 hours x 30 days = 21,600 runs a month

That one task almost certainly costs more than everything else you run, combined, and
it duplicates work the hourly Claude dispatcher already does. **Delete it.**

This is the money-saving plan. Not switching to API — deleting duplicates. Moving the
operations agents to the Claude API would probably raise the bill, because a
subscription is flat and API is charged per token on a long prompt 720 times a month.

---

## 2. ChatGPT — delete these 9 scheduled tasks

Claude already does every one of them, from the same database, with the suppression,
sanctions and evidence rules applied. Running both means double emails to the same
companies and two versions of the truth.

| Task | Schedule | Who does it now |
|---|---|---|
| Zapcart Command Center — Automatic | every 2 min | Claude dispatcher, hourly |
| GPU Server Lead Monitor | hourly | Claude dispatcher, step 6 |
| Zapcart Unified Hourly Master | hourly | Claude dispatcher |
| Zapcart Hourly Operations Worker | hourly | Claude dispatcher |
| Zapcart RFQ & Supplier Radar | custom | Claude dispatcher, steps 4 and 6 |
| NVIDIA Supply & Export Watch | daily 07:53 | Claude dispatcher, export watch |
| Zapcart OEM Change Watch | custom | Claude dispatcher, market watch |
| Zapcart Weekly Procurement Priorities | daily 07:00 | Claude daily digest, 08:20 Doha |
| Review WordPress Maintenance Updates | Sundays 08:00 | keep or delete — your call, not ops |

Also delete the two paused ones — **Jetson 2000 RFQ Hourly** and
**5,000 Workstation Supplier Search** — they will restart if anyone unpauses them.

Also stop the **Codex Desktop "Command Center master"** thread (`01a16ffc`) and the
Windows task **`zapcart-ai-employee-hourly`**. Both still send real email from sales@
and b2b@ and neither checks what Claude has already sent.

---

## 3. ChatGPT — create ONE task

Name: **Zapcart Marketing Engine**
Schedule: every 2 hours

Prompt to paste: see `docs/chatgpt-marketing-engine.md` in this repo.

It does one job: first-touch marketing email to new companies worldwide, with the
Zapcart company profile attached. It never touches a quote, an RFQ, a supplier
negotiation, a price or an existing email thread. Those are Claude's.

---

## 4. Claude — already done, nothing for you to click

- Operations Dispatcher: **active, hourly, 24/7 in the cloud.** Works with the laptop
  off. If your usage limit is hit, the run fails and the *next hour runs normally* —
  it resumes by itself, you do not have to restart anything.
- Lead Engine: **disabled** (merged into the dispatcher).
- Weekly Work Summary: **disabled** (merged into the Friday digest).

---

## 5. On sending volume

"Marketing email every minute" will get `zapcart.qa` onto spam blocklists within days.
When that happens the blocklist does not distinguish marketing from business — your
quotes, your RFQs and your customer replies stop being delivered too. The domain that
earns the money is the same domain doing the marketing.

The marketing engine in `docs/chatgpt-marketing-engine.md` is set to a volume that
grows as the domain proves itself, with a hard stop on bounces. Raise it whenever you
want, but raise it from a warm domain, not a cold one.

---

## 6. On Russia and sanctioned destinations

Automated outreach does not go to Russia, Belarus, Iran, North Korea, Syria, Cuba or
occupied Ukraine. You said you will handle those approaches personally — that is the
right split, and it stays that way.

Two things worth knowing before you do: a large amount of ordinary server, CPU,
storage and networking hardware is **also** on the EU/US/UK dual-use control lists for
Russia, not just NVIDIA GPUs. And Qatari banks will generally refuse to clear the
payment regardless of what the goods are. The blocker is usually the bank, not the
product.

---

## 7. The API workspace (the diagram you drew)

Built in this repo. It needs from you:

    ANTHROPIC_API_KEY=...     (console.anthropic.com)
    OPENAI_API_KEY=...        (platform.openai.com)

Put them in `.env`, then `npm install && npm start`. It runs on any host — a cheap VPS,
Render, Azure App Service, or your own machine. Until those keys exist the Command
Center artifact stays the live control surface, and it is working today.
