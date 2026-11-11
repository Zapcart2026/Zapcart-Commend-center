import { AGENTS } from './agents/index.js';
import { callClaude } from './providers/claude.js';
import { callOpenAI } from './providers/openai.js';
import { db, setting, logRunStart, logRunEnd, requestApproval } from './db.js';

const TICK_MS = 60_000;

/**
 * Runs agents on their own interval.
 *
 * Outages are the normal case, not the exception: an API key can run out of credit, a
 * rate limit can last an hour, the host can reboot. The scheduler never backfills the
 * runs it missed - it simply runs once on the next tick and carries on. That is what
 * "do not stop, pick up where you left off" means in practice: no pile-up, no double
 * emails, no manual restart.
 */
export function startScheduler() {
  if (process.env.SCHEDULER_ENABLED !== '1') {
    console.log('[scheduler] disabled (SCHEDULER_ENABLED is not 1)');
    return;
  }
  console.log('[scheduler] running');
  tick();
  setInterval(tick, TICK_MS);
}

async function tick() {
  for (const agent of AGENTS) {
    if (!agent.everyMinutes) continue;
    const key = `last_run:${agent.id}`;
    const last = Number(setting.get(key, 0));
    const dueAt = last + agent.everyMinutes * 60_000;
    if (Date.now() < dueAt) continue;

    // Claim the slot before the call, so a crash mid-run cannot cause a double run.
    setting.set(key, Date.now());
    runAgent(agent, 'Scheduled run. Report what you did, in plain sentences.').catch(
      (e) => console.error(`[scheduler] ${agent.id}:`, e.message)
    );
  }
}

export async function runAgent(agent, prompt, context = []) {
  const runId = logRunStart(agent.id);
  try {
    const call = agent.provider === 'openai' ? callOpenAI : callClaude;
    const { text, usage } = await call({
      system: agent.system,
      messages: [...context, { role: 'user', content: prompt }],
    });

    logRunEnd(runId, { status: 'ok', summary: text.slice(0, 4000), usage });

    // No agent sends anything. It asks.
    if (!agent.autoApprove && looksActionable(text)) {
      requestApproval({
        agent: agent.id,
        kind: 'other',
        title: `${agent.name}: output needs your decision`,
        body: text,
        priority: 'High',
      });
    }
    return { text, usage };
  } catch (err) {
    logRunEnd(runId, {
      status: err.retryable ? 'retry_later' : 'failed',
      error: err.message,
    });
    // A retryable failure is left alone on purpose: the next tick picks it up.
    throw err;
  }
}

function looksActionable(text) {
  return /\b(draft|send|email|quote|quotation|rfq|approve|supplier|customer)\b/i.test(
    text || ''
  );
}

export function recentRuns(limit = 50) {
  return db
    .prepare('SELECT * FROM agent_runs ORDER BY id DESC LIMIT ?')
    .all(limit);
}
