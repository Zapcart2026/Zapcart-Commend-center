const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const DIR = __dirname;
const dataUri = (f, mime) =>
  `data:${mime};base64,` + fs.readFileSync(path.join(DIR, f)).toString('base64');

// Chromium's own header/footer templates repeat correctly on every page.
// CSS position:fixed does NOT - it lands mid-page. Images must be data URIs:
// the template runs in an isolated context that cannot reach file:// assets.
const LOGO = dataUri('assets/logo.png', 'image/png');

const header = `
<div style="width:100%;font-family:Helvetica,Arial,sans-serif;-webkit-print-color-adjust:exact;
            padding:0 14mm;box-sizing:border-box;">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;">
    <img src="${LOGO}" style="height:11mm">
    <div style="text-align:right;font-size:6.6pt;color:#16486D;line-height:1.5;">
      Office No: 2, Floor 1, Zone 25, Street 850, Building No: 94, Doha, Qatar<br>
      CR 229287 &nbsp;|&nbsp; Tax ID 5008104978<br>
      www.zapcart.qa &nbsp;|&nbsp; sales@zapcart.qa &nbsp;|&nbsp; +974 7140 9292
    </div>
  </div>
  <div style="height:0.5mm;background:#16486D;margin-top:2mm;"></div>
  <div style="display:flex;height:2.4mm;">
    <span style="flex:0 0 32%;background:#30BEE6"></span>
    <span style="flex:0 0 16%;background:#F5CE2B"></span>
    <span style="flex:1 1 auto;background:#EB3834"></span>
  </div>
</div>`;

const footer = `
<div style="width:100%;font-family:Helvetica,Arial,sans-serif;-webkit-print-color-adjust:exact;
            padding:0 14mm;box-sizing:border-box;">
  <div style="text-align:right;font-size:6.2pt;color:#54626f;padding-bottom:1mm;">
    Page <span class="pageNumber"></span> of <span class="totalPages"></span>
  </div>
  <div style="background:#16486D;color:#fff;text-align:center;font-family:'Courier New',monospace;
              font-weight:bold;font-size:7.4pt;letter-spacing:.06em;padding:2.6mm 0;">
    ZAPCART TECHNOLOGY W.L.L. &nbsp;|&nbsp; www.zapcart.qa &nbsp;|&nbsp; sales@zapcart.qa
  </div>
</div>`;

(async () => {
  const jobs = process.argv.slice(2);
  if (!jobs.length) { console.error('usage: node render.js <file.html> ...'); process.exit(1); }

  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();

  for (const f of jobs) {
    const abs = path.resolve(f);
    const out = abs.replace(/\.html$/, '.pdf');
    await page.goto('file://' + abs, { waitUntil: 'networkidle' });
    await page.pdf({
      path: out,
      format: 'A4',
      printBackground: true,
      displayHeaderFooter: true,
      headerTemplate: header,
      footerTemplate: footer,
      margin: { top: '30mm', bottom: '21mm', left: '14mm', right: '14mm' },
    });
    console.log('wrote', path.basename(out));
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
