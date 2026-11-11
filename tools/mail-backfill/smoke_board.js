// Smoke-test the Control Board page against the prepared register documents, with a stub in
// place of the live database. Catches runtime errors and layout breaks before publishing.
// Usage: node smoke_board.js <scratchpad> <out-dir>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = process.argv[2], OUT = process.argv[3];
fs.mkdirSync(OUT, { recursive: true });
const load = (dir) => {
  const d = path.join(BASE, dir);
  if (!fs.existsSync(d)) return [];
  return fs.readdirSync(d).filter(f => f.endsWith('.json') && !f.startsWith('_'))
    .map(f => ({ id: f.replace(/\.json$/, ''), data: JSON.parse(fs.readFileSync(path.join(d, f), 'utf8')) }));
};
const unwrap = (rows) => rows.map(r => ({ id: r.id, data: r.data.data || r.data }));
const data = {
  board: unwrap(load('live2/board')),
  agents: [],
  companies: load('registers/companies'),
  activity: load("registers/activity"),
  meta: [{ id: "setup", data: JSON.parse(fs.readFileSync(path.join(BASE, "ledger/meta_setup.json"), "utf8")) }],
  compliance: load('registers_compliance'),
  docs: [{ id: 'nda', data: { label: 'Mutual NDA', kind: 'PDF', order: 1, url: '/_blob/x', note: 'Test note' } }],
};
const page_html = fs.readFileSync(path.join(BASE, 'board/index.html'), 'utf8');
const stub = `
<script>
(function(){
  var DATA=${JSON.stringify(data).replace(/</g, '\\u003c')};
  function snap(rows){var docs=rows.map(function(r){return {id:r.id,exists:true,data:function(){return r.data},metadata:{fromCache:false}}});
    return {docs:docs,size:docs.length,empty:!docs.length,metadata:{fromCache:false,hasPendingWrites:false},docChanges:function(){return []}}}
  function q(name,rows){
    var o={where:function(){return o},
      orderBy:function(f,d){rows=rows.slice().sort(function(a,b){var x=String(a.data[f]||""),y=String(b.data[f]||"");return d==="desc"?y.localeCompare(x):x.localeCompare(y)});return q(name,rows)},
      limit:function(n){return q(name,rows.slice(0,n))},
      get:function(){return Promise.resolve(snap(rows))},
      onSnapshot:function(next){setTimeout(function(){next(snap(rows))},20);return function(){}},
      doc:function(id){return {update:function(){return Promise.resolve()},set:function(){return Promise.resolve()}}}};
    return o}
  var db={collection:function(n){return q(n,DATA[n]||[])},
    doc:function(path){var a=path.split("/"),r=(DATA[a[0]]||[]).filter(function(x){return x.id===a[1]})[0];
      return {onSnapshot:function(next){setTimeout(function(){next({exists:!!r,id:a[1],data:function(){return r&&r.data}})},20);return function(){}}}}};
  window.claude={use:function(n){return Promise.resolve(n==="db"?db:n==="user"?{can:function(){return true}}:null)}};
})();
</script>`;
const doc = `<!doctype html><html><head><meta charset="utf8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>${stub}${page_html}</body></html>`;
const file = path.join(OUT, 'board_test.html');
fs.writeFileSync(file, doc);

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const errors = [];
  for (const [name, vp, scheme] of [['phone', { width: 390, height: 844 }, 'light'], ['desktop', { width: 1100, height: 800 }, 'dark']]) {
    const ctx = await browser.newContext({ viewport: vp, colorScheme: scheme, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    page.on('pageerror', e => errors.push(name + ': ' + e.message));
    page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource|ERR_/.test(m.text())) errors.push(name + ' console: ' + m.text()); });
    await page.goto('file://' + file);
    await page.waitForTimeout(400);
    const chip = (t) => page.locator('#strip .chip', { hasText: t }).first();
    await chip('Records').click();
    await page.waitForTimeout(400);
    await page.screenshot({ path: path.join(OUT, name + '-companies.png') });
    const first = page.locator('#rres .r .hd').first();
    if (await first.count()) { await first.click(); await page.waitForTimeout(100); await page.screenshot({ path: path.join(OUT, name + '-company-open.png') }); }
    for (const t of ['Suppliers', 'Customers', 'Waiting on us', 'Other', 'Prospects', 'All']) {
      await page.locator('#rres .seg .chip', { hasText: t }).first().click(); await page.waitForTimeout(60);
    }
    await page.fill('#rq', 'seagate'); await page.waitForTimeout(100);
    await page.fill('#rq', '');
    for (const t of ['Onboarding', 'Log', 'GPU files', 'Documents', 'Setup check']) {
      await page.locator('#rseg .chip', { hasText: t }).click(); await page.waitForTimeout(150);
      await page.screenshot({ path: path.join(OUT, name + '-' + t.toLowerCase().replace(/\W+/g, '') + '.png') });
      if (t === 'GPU files') { const g = page.locator('#rres .r .hd').first(); if (await g.count()) { await g.click(); await page.waitForTimeout(100); await page.screenshot({ path: path.join(OUT, name + '-gpu-open.png') }); } }
    }
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(name, 'horizontal overflow px:', overflow);
    await chip('Do now').click(); await page.waitForTimeout(100);
    await page.screenshot({ path: path.join(OUT, name + '-board.png') });
    await ctx.close();
  }
  await browser.close();
  console.log(errors.length ? 'ERRORS:\n' + errors.join('\n') : 'no runtime errors');
})().catch(e => { console.error(e); process.exit(1); });
