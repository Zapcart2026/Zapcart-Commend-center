const API = 'https://api.anthropic.com/v1/messages';

/** Anthropic Messages API. Operations agents run here. */
export async function callClaude({ system, messages, tools, maxTokens = 8000 }) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) throw new Error('ANTHROPIC_API_KEY is not set');

  const res = await fetch(API, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': key,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: process.env.CLAUDE_MODEL || 'claude-opus-5-5',
      max_tokens: maxTokens,
      system,
      messages,
      ...(tools?.length ? { tools } : {}),
    }),
  });

  if (!res.ok) {
    const detail = await res.text();
    const err = new Error(`Claude API ${res.status}: ${detail.slice(0, 500)}`);
    // 429 and 529 are "come back later", not "this is broken".
    err.retryable = res.status === 429 || res.status >= 500;
    throw err;
  }

  const data = await res.json();
  const text = (data.content || [])
    .filter((b) => b.type === 'text')
    .map((b) => b.text)
    .join('\n');
  return { text, usage: data.usage, raw: data };
}
