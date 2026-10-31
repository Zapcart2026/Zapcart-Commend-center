# Zapcart Command Center

Zapcart Technology W.L.L., Doha, Qatar — IT hardware sourcing and B2B trading.

## Live today

**Command Center** (phone and laptop, no install):
https://claude.ai/artifact/TX7WQ6z6WKwFNfUSkmctWo

Everything waiting on Farhan appears on its **Do now** tab with a button that performs
it — the Outlook draft, the WhatsApp message, the portal. It is refreshed every hour by
the Claude Operations Dispatcher, which runs in the cloud with the laptop switched off.

## Read these two first

- `ARCHITECTURE.md` — who does what. Claude owns operations, ChatGPT owns marketing.
- `CHANGEOVER.md` — the ten minutes of clicking that removes the duplicate schedules,
  including the ChatGPT task running **every 2 minutes**.

## This repository

The API workspace from the architecture diagram: one mobile-friendly dashboard with
chat, projects, agents, approvals and history, talking to the Claude API for operations
and the OpenAI API for marketing, over one shared database.

    cp .env.example .env     # add ANTHROPIC_API_KEY and OPENAI_API_KEY
    npm install
    npm start                # http://localhost:8080/?t=YOUR_WORKSPACE_TOKEN

`SCHEDULER_ENABLED=0` by default, so nothing fires until you say so. No agent sends
anything on its own — every outbound item lands in the approvals queue first.

    src/agents/      sourcing, quotations, email, compliance, quality, developer, marketing
    src/providers/   Claude API and OpenAI API clients
    src/scheduler.js intervals, and how an outage resumes by itself
    db/schema.sql    the one database
    docs/            the ChatGPT marketing engine prompt, ready to paste
