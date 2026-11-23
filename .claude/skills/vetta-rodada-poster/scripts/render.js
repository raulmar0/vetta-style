#!/usr/bin/env node
// Render poster HTML files to PNG: <name>.png (1x) and 2x/<name>.png (2x).
// Waits for the in-page layout script (headline fit) to set body[data-ready="1"].
// Usage: node render.js file1.html [file2.html ...]
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');

function loadPlaywright() {
  const roots = [
    __dirname,
    path.join(__dirname, '..'),
    path.join(__dirname, '..', '..', '..', '..'), // raíz del kit
    process.cwd(),
  ];
  for (const r of roots) {
    try { return require(require.resolve('playwright', { paths: [r] })); } catch (e) { /* next */ }
  }
  try { return require('playwright'); } catch (e) { /* next */ }
  console.error('No encuentro playwright. Corre ./setup.sh (o en la raíz del kit: npm install && npx playwright install chromium).');
  process.exit(1);
}
const { chromium } = loadPlaywright();

(async () => {
  const files = process.argv.slice(2);
  if (!files.length) { console.error('Uso: node render.js poster.html [...]'); process.exit(1); }
  const browser = await chromium.launch();
  for (const f of files) {
    const abs = path.resolve(f);
    const html = fs.readFileSync(abs, 'utf8');
    const w = +(/data-w="(\d+)"/.exec(html) || [])[1];
    const h = +(/data-h="(\d+)"/.exec(html) || [])[1];
    if (!w || !h) { console.error(`sin data-w/data-h: ${abs}`); continue; }
    for (const scale of [1, 2]) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: scale });
      const page = await ctx.newPage();
      await page.goto(pathToFileURL(abs).href, { waitUntil: 'networkidle' });
      await page.waitForFunction(() => document.body.dataset.ready === '1', null, { timeout: 20000 });
      await page.waitForTimeout(150);
      const name = path.basename(abs).replace(/\.html$/, '.png');
      const out = scale === 1 ? path.join(path.dirname(abs), name) : path.join(path.dirname(abs), '2x', name);
      fs.mkdirSync(path.dirname(out), { recursive: true });
      await page.screenshot({ path: out, clip: { x: 0, y: 0, width: w, height: h } });
      console.log(`png ${out} (${w * scale}x${h * scale})`);
      await ctx.close();
    }
  }
  await browser.close();
})();
