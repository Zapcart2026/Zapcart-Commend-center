# Zapcart AI Workspace — architecture

Owner: Farhan Shaikh, Zapcart Technology W.L.L., Doha, Qatar.
Decided 1 Nov 2026. This file is the single source of truth for who does what.

## The split

**Claude owns operations. ChatGPT owns marketing. Nothing else.**

| Work | Runs on | Why |
|---|---|---|
| Customer search / lead hunting | Claude | Needs screening against suppression, sanctions, contact history |
| Supplier search and verification | Claude | Needs evidence rules (photos, serials, location) before VERIFIED |
| RFQ search and supplier radar | Claude | Feeds the same quotes/rfqs tables |
| Quotation follow-ups and reminders | Claude | Cadence rules, one reminder per quote per day |
| Inbound email monitoring and reply drafts | Claude | Must read the live thread before answering |
| Export / NVIDIA / OEM change watch | Claude | Compliance holds live in the same database |
| Quotations and margin calculation | Claude | Landed cost + 105% advance rule |
| **Marketing email to new customers worldwide** | **ChatGPT** | Volume outreach with the company profile attached |

One rule settles every future argument: **if it touches a quote, an RFQ, a supplier,
a price, a compliance hold or an existing thread, it is Claude. If it is a first-touch
marketing email to a stranger, it is ChatGPT.**

## The three layers

1. **Control surface** — the Command Center, a web page reachable from any phone:
   https://claude.ai/artifact/TX7WQ6z6WKwFNfUSkmctWo
   Every open item appears there with a button that performs it.
2. **Engines** — the things that actually run on a schedule.
   - Claude Operations Dispatcher, hourly, in Anthropic's cloud. Runs with the laptop off.
   - ChatGPT Marketing Engine, on the laptop or ChatGPT cloud.
   - (Optional) this repo's API workspace, once API keys exist.
3. **Database** — one store, no second copies. Today the Command Center database.
   `db/schema.sql` here is the same shape, for when the workspace takes over.

## What this repo is

The workspace from the diagram: one mobile-friendly dashboard (chat, projects,
agents, approvals, history) talking to Claude API and OpenAI API, with specialised
agents on top and one shared database underneath.

It is **built but not running**. It needs two API keys and a host. See `CHANGEOVER.md`.

## Honest note on cost

Moving the operations agents from the Claude subscription to the Claude API will most
likely **increase** the bill at this volume, not reduce it — a subscription is flat,
API is per token, and the dispatcher is a long prompt running 720 times a month.

The real saving is deleting duplicate schedules. See `CHANGEOVER.md` for the numbers.
