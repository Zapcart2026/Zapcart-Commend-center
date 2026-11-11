import express from 'express';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { db } from './db.js';
import { AGENTS, byId } from './agents/index.js';
import { startScheduler, runAgent, recentRuns } from './scheduler.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
loadEnv();

const app = express();
app.use(express.json({ limit: '1mb' }));

// One shared token. Everything below it is the company's data.
app.use('/api', (req, res, next) => {
  const want = process.env.WORKSPACE_TOKEN;
  if (!want || want === 'change-me-to-a-long-random-string') {
    return res.status(500).json({ error: 'Set WORKSPACE_TOKEN in .env first' });
  }
  const got = req.get('x-workspace-token') || req.query.t;
  if (got !== want) return res.status(401).json({ error: 'unauthorized' });
  next();
});

app.get('/api/agents', (_req, res) =>
  res.json(
    AGENTS.map(({ id, name, provider, everyMinutes }) => ({
      id, name, provider, everyMinutes,
    }))
  )
);

app.get('/api/approvals', (_req, res) =>
  res.json(
    db.prepare(
      `SELECT * FROM approvals WHERE state = 'waiting' ORDER BY
       CASE priority WHEN 'Do now' THEN 0 WHEN 'Urgent' THEN 1
       WHEN 'High' THEN 2 ELSE 3 END, id DESC`
    ).all()
  )
);

app.post('/api/approvals/:id/:decision', (req, res) => {
  const { id, decision } = req.params;
  if (!['approved', 'rejected'].includes(decision)) {
    return res.status(400).json({ error: 'decision must be approved or rejected' });
  }
  const r = db.prepare(
    `UPDATE approvals SET state = ?, decided_at = datetime('now')
     WHERE id = ? AND state = 'waiting'`
  ).run(decision, id);
  if (!r.changes) return res.status(409).json({ error: 'already decided' });
  res.json({ ok: true, id: Number(id), state: decision });
});

app.get('/api/history', (_req, res) => res.json(recentRuns(100)));

app.get('/api/projects', (_req, res) =>
  res.json(db.prepare('SELECT * FROM projects ORDER BY name').all())
);

app.post('/api/projects', (req, res) => {
  const { name, about } = req.body || {};
  if (!name) return res.status(400).json({ error: 'name required' });
  const r = db.prepare('INSERT INTO projects (name, about) VALUES (?, ?)')
    .run(name, about ?? null);
  res.json({ id: r.lastInsertRowid, name, about });
});

app.post('/api/chat', async (req, res) => {
  const { agent = 'developer', message, projectId = null } = req.body || {};
  const a = byId[agent];
  if (!a) return res.status(400).json({ error: `unknown agent: ${agent}` });
  if (!message) return res.status(400).json({ error: 'message required' });

  const history = projectId
    ? db.prepare(
        'SELECT role, content FROM messages WHERE project_id = ? ORDER BY id DESC LIMIT 20'
      ).all(projectId).reverse()
    : [];

  db.prepare(
    'INSERT INTO messages (project_id, role, content, agent) VALUES (?, ?, ?, ?)'
  ).run(projectId, 'user', message, agent);

  try {
    const { text } = await runAgent(a, message, history);
    db.prepare(
      'INSERT INTO messages (project_id, role, content, agent) VALUES (?, ?, ?, ?)'
    ).run(projectId, 'assistant', text, agent);
    res.json({ agent, text });
  } catch (err) {
    res.status(502).json({ error: err.message, retryable: !!err.retryable });
  }
});

app.get('/api/summary', (_req, res) => {
  const one = (sql, ...p) => db.prepare(sql).get(...p);
  res.json({
    waiting: one("SELECT count(*) n FROM approvals WHERE state = 'waiting'").n,
    openQuotes: one("SELECT count(*) n FROM quotes WHERE status NOT IN ('won','lost','closed')").n,
    openRfqs: one("SELECT count(*) n FROM rfqs WHERE status = 'open'").n,
    companies: one('SELECT count(*) n FROM companies').n,
    runs24h: one("SELECT count(*) n FROM agent_runs WHERE started_at > datetime('now','-1 day')").n,
    failed24h: one("SELECT count(*) n FROM agent_runs WHERE status NOT IN ('ok','running') AND started_at > datetime('now','-1 day')").n,
    schedulerOn: process.env.SCHEDULER_ENABLED === '1',
  });
});

app.use(express.static(join(root, 'web')));

const port = Number(process.env.PORT) || 8080;
app.listen(port, () => {
  console.log(`Zapcart AI Workspace on http://localhost:${port}`);
  startScheduler();
});

function loadEnv() {
  try {
    for (const line of readFileSync(join(root, '.env'), 'utf8').split('\n')) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
      if (m && !process.env[m[1]]) process.env[m[1]] = m[2].trim();
    }
  } catch {
    console.warn('No .env file found - copy .env.example to .env');
  }
}
