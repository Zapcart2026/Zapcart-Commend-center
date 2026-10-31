# Zapcart – Finish Everything (run this in the Claude session on the Windows PC)

Run end to end. Do not stop, and do not ask questions, until every item below is done and verified. If one item is blocked, log the blocker in `COMMAND_CENTER\BLOCKERS.md` and continue with the next item. Report only at the end, with proof for each item.

Follow all Zapcart org rules: the email rules, the cash and deal rules, and the NVIDIA/GPU export-control rules. Do not send anything that the playbook says to draft.

## 0. Free the C: drive and move everything into OneDrive (do this FIRST)
All work files, memories, histories, exports and registers must live in
the OneDrive folder `01 Zapcart Shared Records` (cloud: `01 Zapcart Shared Records` in OneDrive), not loose on the PC.
1. Measure first: list the 30 largest folders on C: (WinDirStat-style, or `Get-ChildItem` sizes) and write the result to `COMMAND_CENTER\DISK_REPORT.md`. Show what is using the space before touching anything.
2. Move, don't delete: move Zapcart work folders (TOOLS, COMMAND_CENTER, registers, CHATGPT_EXPORT, memories, histories, Codex data) into the right numbered subfolder, mainly `06 Automation and Bots\Zapcart AI Employee (Claude)`. Update the paths in `TOOLS\*.ps1`, the playbook and the hourly task so they use the OneDrive paths. Run the Command Center build once to prove it still works.
3. Verify sync: OneDrive shows green ticks and no pending uploads or errors before anything local is removed.
4. Make files cloud-only: right-click the Zapcart folders, "Free up space" (or `attrib +U -P` on the folder tree), and turn on Settings, Files On-Demand and Storage Sense so OneDrive files stay online-only.
5. Safe junk to clear without asking: `%TEMP%`, Windows Update cleanup, Recycle Bin, browser caches, `C:\Windows\Temp`, old installers in Downloads that have a copy in OneDrive.
6. Ask before deleting anything else: personal files, the Windows folder, program files, anything not in the list above. Never delete a Zapcart file that has no verified OneDrive copy.
7. Finish with `DISK_REPORT.md` showing free space before and after, and what moved where.

## 1. Read everything in ChatGPT (browser)
Open every one of these and read it fully, not just the title:
1. All 14 paused scheduled tasks. Open each one and copy its full prompt text, schedule and last output into `CHATGPT_EXPORT\tasks\<name>.md`.
2. Every chat in the history, newest to oldest, until the history ends. Save each as `CHATGPT_EXPORT\chats\<date>_<title>.md`. Pull out its rules, decisions, contacts, quotes and open actions.
3. All custom GPTs, Agents, the ChatGPT Project (instructions and files) and Codex tasks and repos. Save the instructions for each.
4. If a page fails to load, reload it, and use the data export (Settings, Data controls, Export) as a fallback.

## 2. Merge
- Build `MASTER_PLAYBOOK.md`: one merged set of rules, duties, schedules and templates, with no duplicates and no conflicts. Where two sources conflict, keep the stricter rule and note it.
- Update `MERGE_MAP` so every task, chat, GPT, Agent and project is mapped to one of: folded into the Claude hourly task, weekly duty, on hold, or retired.
- Move all open actions found in the chats (replies owed, quotes pending, RFQs to chase) into the registers.

## 3. Build and verify the automation
- Update the Claude hourly task so it uses `MASTER_PLAYBOOK.md`.
- Run the live attachment test: send one email with `07_Company_Profile_ZAPCART.pdf` attached from sales@ to farhan@. Confirm the attachment arrived. Show the result.
- Build the cheaper path: send through the local script, and use Claude only to judge replies. Pause bulk RFQ volume until reply rates are understood.
- Cloud refresh: publish the Command Center as a hosted Claude Artifact page with the shared database. At the end of each hourly run, push the registers' figures to it. It must work with the PC off, showing the last push.

## 4. Command Center
- Add the real logo and brand colours (look for them on zapcart.qa and in the company profile PDF).
- Show tasks merged, chats processed, open actions, RFQ stats, drafts waiting, follow-ups due and run log.

## 5. Finish
- Write `COMMAND_CENTER\DONE_REPORT.md`: for each item above, the evidence (file paths, send confirmation, page URL, counts).
- Do NOT delete ChatGPT tasks or chats. List them for the user to delete by hand.

## 6. Quotation follow-up cadence (standing rule, never stops until answered or closed)
- Day 0: quote sent. Day 1: first reminder. Day 2: second reminder. Then every 2 days until the customer answers or the lead is marked closed.
- Before any reminder, check the thread: if the customer replied, or a reminder already went out for that step, do nothing (never two follow-ups for the same quote).
- Send as sales@zapcart.qa, reply-all on the last email in the existing thread, never a new chain. Keep Farhan, Subhan and sales@ in CC plus everyone on the client side. Use the Zapcart Sales signature.
- Skip: quotes past the customer's stated closing date, NVIDIA/GPU threads until export check is clear, threads in active negotiation (reply as a draft instead).
- Mark a thread replied/closed in the Command Center as soon as it is answered in Outlook.

## STATUS 31 Oct 2026 (read before running)
Done in the cloud already, do NOT redo: the hourly 24/7 Zapcart Operations Dispatcher (Claude routine, Microsoft 365 connector, Opus 5.5), the company database and Command Center (https://claude.ai/artifact/TX7WQ6z6WKwFNfUSkmctWo), the quote follow-up cadence, the daily 08:20 digest, the Lead Engine merge (disabled), the five old routines (merged and removed). Company profile link is in the database (ops/assets).
Still needed on the PC, in this order:
1. Switch OFF the local "zapcart-ai-employee-hourly" task and any other local sender. The cloud dispatcher is the only sender now.
2. Section 0 (disk cleanup to OneDrive).
3. Sections 1-2 (ChatGPT tasks, chats, GPTs, Agents, Project, Codex: read everything, save to CHATGPT_EXPORT in OneDrive '06 Automation and Bots', merge into MASTER_PLAYBOOK.md and the Command Center database collections ops/merge_map and tasks). Fallback if the browser is unreliable: ChatGPT Settings > Data controls > Export data, then process conversations.json.
4. Write DONE_REPORT.md. List ChatGPT items for the owner to delete by hand; delete nothing yourself.
Sections 3, 4 and 6 above are superseded by the cloud dispatcher.
