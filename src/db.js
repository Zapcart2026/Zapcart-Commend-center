import Database from 'better-sqlite3';
import { readFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
mkdirSync(join(root, 'data'), { recursive: true });

export const db = new Database(join(root, 'data', 'zapcart.db'));
db.pragma('journal_mode = WAL');
db.exec(readFileSync(join(root, 'db', 'schema.sql'), 'utf8'));

export const setting = {
  get(key, fallback = null) {
    const r = db.prepare('SELECT value FROM settings WHERE key = ?').get(key);
    return r ? r.value : fallback;
  },
  set(key, value) {
    db.prepare(
      `INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))
       ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at`
    ).run(key, String(value));
  },
};

/** An address or its domain is suppressed. Checked before every send. */
export function isSuppressed(email) {
  if (!email) return true;
  const addr = email.toLowerCase().trim();
  const domain = addr.split('@')[1] || '';
  const row = db
    .prepare('SELECT 1 FROM suppression WHERE lower(value) IN (?, ?)')
    .get(addr, domain);
  return !!row;
}

export function logRunStart(agent) {
  return db.prepare('INSERT INTO agent_runs (agent) VALUES (?)').run(agent)
    .lastInsertRowid;
}

export function logRunEnd(id, { status, summary, error, usage }) {
  db.prepare(
    `UPDATE agent_runs SET ended_at = datetime('now'), status = ?, summary = ?,
     error = ?, in_tokens = ?, out_tokens = ? WHERE id = ?`
  ).run(
    status,
    summary ?? null,
    error ?? null,
    usage?.input_tokens ?? null,
    usage?.output_tokens ?? null,
    id
  );
}

/** Queue something for Farhan. Nothing sends without this. */
export function requestApproval(a) {
  return db
    .prepare(
      `INSERT INTO approvals (agent, kind, title, body, recipient, payload, open_url, priority)
       VALUES (@agent, @kind, @title, @body, @recipient, @payload, @open_url, @priority)`
    )
    .run({
      agent: a.agent,
      kind: a.kind ?? 'other',
      title: a.title,
      body: a.body ?? null,
      recipient: a.recipient ?? null,
      payload: a.payload ? JSON.stringify(a.payload) : null,
      open_url: a.open_url ?? null,
      priority: a.priority ?? 'High',
    }).lastInsertRowid;
}

if (process.argv.includes('--init')) {
  console.log('Database ready at data/zapcart.db');
}
