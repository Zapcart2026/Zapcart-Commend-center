# Mail history backfill

How six months of Outlook mail became the company register on 11 Nov 2026, and how to run it again.

The Outlook connector can only be called by a model, and having a model re-type every message
is slow, costly and lossy. So the work is split:

1. **Fetch** — light agents make read-only `outlook_email_search` calls and do nothing else
   (`FETCHER.md`, `FETCHER2.md`). Their raw results land in the session's subagent transcripts.
2. **Harvest** — `harvest.py` reads those transcripts and writes every message, exactly as
   returned, to `raw.jsonl`. No model touches the data. `gaps.py` lists searches that were
   throttled or cut off at 25 results so they can be re-run in smaller date slices.
3. **Aggregate** — `aggregate.py` groups messages by outside organisation (email domain),
   de-duplicates copies of the same email across mailboxes, drops warm-up traffic and
   unanswered first-touch outreach, and writes one compact evidence card per organisation.
4. **Label** — agents read the cards and decide only the role (supplier, customer, prospect...)
   and a one-line status (`CLASSIFIER.md`).
5. **Build and load** — `build2.py` merges the labels with Zoho Books (quotes, orders,
   invoices, purchase orders) into `companies` and `activity` documents plus a one-document
   supplier index; loader agents write them to the Control Board database (`LOADER.md`).

Search slicing that works with the connector: `folderName` plus a KQL date range inside
`query`, for example `received:2026-09-01..2026-09-02 subject:RE NOT Maureen-objective`.
Keep each slice under 25 messages so no page cursor is needed, and keep to a few calls at a
time per mailbox — Microsoft throttles beyond about four concurrent requests.

Coverage of the 11 Nov run: about 7,000 messages read (Sent Items of farhan@, sales@ and b2b@
since 10 May; the b2b@ inbox since 10 May; the sales@ and farhan@ inboxes for the last 30 days),
5,000 kept after removing warm-up traffic, cold outreach and duplicates, 1,074 organisations.
Slices that held more than 25 conversation emails in one day were capped at the newest 25.

From here on the hourly Dispatcher keeps the records itself; this is only needed to rebuild.

`smoke_board.js` renders `control-board/index.html` against the built register with a stub
database and reports runtime errors and horizontal overflow at phone and desktop widths.
