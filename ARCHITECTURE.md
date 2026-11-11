# Zapcart AI Workspace — architecture

Owner: Farhan Shaikh, Zapcart Technology W.L.L., Doha, Qatar.
Decided 4 Nov 2026. This file is the single source of truth for who does what.

## The split

**ChatGPT does three things. Claude Cloud does everything else.**

| Runs on ChatGPT | Why it stays there |
|---|---|
| Worldwide **customer search** | Broad discovery across the globe, LinkedIn, social, every continent |
| Worldwide **supplier search** | Same reach, same kind of work |
| **Marketing** — first-touch email to new companies | Volume outreach with the company profile attached |

Everything else runs as a **Claude cloud scheduled task**, 24/7, with the laptop off.

## The two kinds of Claude agent

This distinction is the thing that keeps the system safe.

**One sender.** Exactly one agent is allowed to send email: the hourly
**Operations Dispatcher**. It owns inbound mail, reply drafts, quotation and RFQ
follow-ups, and outreach drafts.

**Many watchers.** Every other cloud agent is a WATCH agent. It researches and
records. It never sends email, never drafts, never contacts a company, never
registers on a portal, never submits a tender. When it finds something that needs
an email, it writes a row on the Control Board and stops.

In October 2026 several automations sent from the same mailboxes at once. The
result was a do-not-contact breach to a supplier on the never-contact list,
emails that went out with unfilled `[__ cores]` placeholders, and export-controlled
GPU RFQs leaving the building. One sender, many watchers is the rule that prevents
a repeat.

## The cloud watch agents

| Agent | Cadence | Job |
|---|---|---|
| NVIDIA Supply and Export Watch | daily | US/EU/UK control and entity-list changes; GPU allocation news |
| H100 and Data Centre GPU Stock Watch | twice daily | Availability and indicative price movement on open deals |
| GCC Buyer Watch | twice daily, Sun–Thu | Tenders, data centre builds, refresh cycles across the GCC |
| OEM Change Watch | every 2 days | EOL, supersessions and spec changes on parts we actually quote |
| RFQ and Tender Radar | daily | Public tender notices in Qatar, GCC and India. Record only |
| Weekly Procurement Priorities | Mondays | Ranks the week by money at risk and deadline |
| Monday Post Ideas | Mondays | Three posts tied to real news, with source and date |
| Website and Domain Health Check | Sundays | zapcart.qa, its TLS certificate and the company-profile link |

Each prompt was written and then checked by three independent reviewers against
three lenses: *can this send email*, *does it carry the export rules*, and *is it
scoped to its own mandate*. Anything a lens rejected was rewritten.

## The records

Since 11 Nov 2026 the Control Board database is also the company register, and the
Dispatcher is its record keeper. Nobody types anything in.

| Collection | What it holds |
|---|---|
| `companies` | One document per outside organisation, keyed by email domain: role, contacts, what they sell or buy, first and last contact, who wrote last, NDA and registration status, Zoho Books summary, never-contact and hands-off flags |
| `activity` | The log: every RFQ, offer, quotation, order, invoice, payment, dispute, NDA, registration and end-user form |
| `compliance` | One end-user file per NVIDIA data-centre deal: what was stated to whom, which forms went out, and every contradiction |
| `docs` | The documents Farhan attaches by hand: NDA, customer registration form, company profile |

It was seeded from six months of mail and Zoho Books (see `tools/mail-backfill/`). Each hour
the Dispatcher reads what arrived and what the three mailboxes sent, updates the company,
logs what happened, prepares an NDA draft for each new trading partner and a registration
form once a quotation is approved, and refuses to draft any GPU email whose end-user details
differ from the deal's file. `ops/supplier_index` in the company database is a one-document
list of every supplier that has actually answered, which the RFQ sweep reads before it looks
for strangers.

The Outlook connector cannot attach files, so NDA and registration emails are drafts that
Farhan sends after attaching the PDF from Records, Documents — or, once share links are stored
in `ops/assets`, emails that carry the link.

The source of the board page is `control-board/index.html`; the document templates are in
`documents/` (the signature and stamp image is deliberately not in the repository).

## The three layers

1. **Control surface** — the Control Board, reachable from any phone or PC:
   https://claude.ai/artifact/BzDjpcTEGnMWXwPZfpLxG4
   Everything waiting on Farhan, with the button that performs it. Done and Later
   are stored server-side; no agent may overwrite them.
2. **Engines** — the dispatcher and the watch agents above, in Anthropic's cloud.
3. **Database** — one store. The Dashboard artifact
   (https://claude.ai/artifact/TX7WQ6z6WKwFNfUSkmctWo) holds quotes, RFQs,
   suppliers, offers, leads and the run log. `db/schema.sql` here is the same shape
   for when the API workspace takes over.

## What this repo is

The workspace from the architecture diagram: one mobile-friendly dashboard with
chat, projects, agents, approvals and history, talking to the Claude API for
operations and the OpenAI API for marketing, over one shared database.

It is **built but not running**. It needs two API keys and a host. See `CHANGEOVER.md`.

## Honest note on cost

Moving the operations agents from the Claude subscription to the Claude API will
most likely **increase** the bill at this volume, not reduce it — a subscription is
flat, API is per token, and the dispatcher is a long prompt running 720 times a month.

The saving came from deleting duplicates. The ChatGPT task that ran every two
minutes was 21,600 runs a month on its own.
