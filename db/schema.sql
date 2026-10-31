-- Zapcart AI Workspace - one database for everything.
-- Supplier evidence, RFQs, CRM, agent logs, persistent memory.

CREATE TABLE IF NOT EXISTS companies (
  id            INTEGER PRIMARY KEY,
  kind          TEXT NOT NULL CHECK (kind IN ('customer','supplier','both')),
  name          TEXT NOT NULL,
  country       TEXT,
  website       TEXT,
  email         TEXT,
  phone         TEXT,
  source_url    TEXT,
  -- suppliers: VERIFIED needs evidence, never a website alone
  status        TEXT NOT NULL DEFAULT 'lead',
  notes         TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (name, country)
);
CREATE INDEX IF NOT EXISTS idx_companies_email ON companies(email);

CREATE TABLE IF NOT EXISTS suppression (
  id         INTEGER PRIMARY KEY,
  value      TEXT NOT NULL UNIQUE,   -- email address or domain
  reason     TEXT,
  added_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS quotes (
  id            INTEGER PRIMARY KEY,
  ref           TEXT UNIQUE,
  company_id    INTEGER REFERENCES companies(id),
  item          TEXT,
  qty           INTEGER,
  currency      TEXT DEFAULT 'USD',
  sell_total    REAL,
  landed_cost   REAL,
  advance_rcvd  REAL DEFAULT 0,
  status        TEXT NOT NULL DEFAULT 'draft',
  valid_until   TEXT,
  sent_at       TEXT,
  last_chase_at TEXT,
  chase_count   INTEGER NOT NULL DEFAULT 0,
  thread_id     TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rfqs (
  id          INTEGER PRIMARY KEY,
  ref         TEXT UNIQUE,
  company_id  INTEGER REFERENCES companies(id),
  part_number TEXT,
  qty         INTEGER,
  status      TEXT NOT NULL DEFAULT 'open',
  closes_at   TEXT,
  thread_id   TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Supplier offers. Stock claims are classified, never assumed current.
CREATE TABLE IF NOT EXISTS offers (
  id            INTEGER PRIMARY KEY,
  company_id    INTEGER REFERENCES companies(id),
  part_number   TEXT NOT NULL,
  manufacturer  TEXT,
  condition     TEXT,
  qty           INTEGER,
  unit_price    REAL,
  currency      TEXT,
  location      TEXT,
  lead_time     TEXT,
  warranty      TEXT,
  terms         TEXT,
  quoted_on     TEXT,
  valid_until   TEXT,
  stock_class   TEXT CHECK (stock_class IN
                  ('CONFIRMED_CURRENT','HISTORICAL','MARKET_INDICATION','UNVERIFIED')),
  evidence      TEXT,          -- photos, serials, message id
  red_flags     TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_offers_pn ON offers(part_number);

-- Nothing leaves the building without a row here first.
CREATE TABLE IF NOT EXISTS approvals (
  id           INTEGER PRIMARY KEY,
  agent        TEXT NOT NULL,
  kind         TEXT NOT NULL,     -- email, quote, payment, other
  title        TEXT NOT NULL,
  body         TEXT,
  recipient    TEXT,
  payload      TEXT,              -- JSON the executor needs
  open_url     TEXT,
  priority     TEXT NOT NULL DEFAULT 'High',
  state        TEXT NOT NULL DEFAULT 'waiting'
                 CHECK (state IN ('waiting','approved','rejected','done','failed')),
  created_at   TEXT NOT NULL DEFAULT (datetime('now')),
  decided_at   TEXT,
  result       TEXT
);
CREATE INDEX IF NOT EXISTS idx_approvals_state ON approvals(state);

CREATE TABLE IF NOT EXISTS agent_runs (
  id          INTEGER PRIMARY KEY,
  agent       TEXT NOT NULL,
  started_at  TEXT NOT NULL DEFAULT (datetime('now')),
  ended_at    TEXT,
  status      TEXT NOT NULL DEFAULT 'running',
  summary     TEXT,
  error       TEXT,
  in_tokens   INTEGER,
  out_tokens  INTEGER
);
CREATE INDEX IF NOT EXISTS idx_runs_agent ON agent_runs(agent, started_at DESC);

CREATE TABLE IF NOT EXISTS projects (
  id          INTEGER PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE,
  about       TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
  id          INTEGER PRIMARY KEY,
  project_id  INTEGER REFERENCES projects(id),
  role        TEXT NOT NULL,
  content     TEXT NOT NULL,
  agent       TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_messages_project ON messages(project_id, id);

-- Persistent memory and scheduler state.
CREATE TABLE IF NOT EXISTS settings (
  key        TEXT PRIMARY KEY,
  value      TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
