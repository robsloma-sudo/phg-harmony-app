// Proof that a design is what Menu Studio draws: loads the real app (index.html at the repo root), opens Menu Studio,
// feeds the .menu.json to the app's own mdcFileLoad, redraws, and exports the app's canvas as PNG.
//   node studio-check.cjs <file.menu.json> <out.png>
// Prints what the app loaded (title, sections, size, pages, overflow, any load message or page error).
// Fabric 5.3.0 is fetched once from the npm registry into ../styles/vendor (cdnjs may be blocked by the sandbox proxy).
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || '/opt/node22/lib/node_modules/playwright');
const APP = path.resolve(__dirname, '../../../../index.html');
const VENDOR = path.resolve(__dirname, '../styles/vendor');
function fabricPath() {
  const f = path.join(VENDOR, 'fabric.min.js');
  if (fs.existsSync(f)) return f;
  fs.mkdirSync(VENDOR, { recursive: true });
  const tgz = path.join(VENDOR, 'fabric.tgz');
  execFileSync('curl', ['-sS', '-o', tgz, 'https://registry.npmjs.org/fabric/-/fabric-5.3.0.tgz']);
  execFileSync('tar', ['xzf', tgz, '-C', VENDOR, 'package/dist/fabric.min.js']);
  fs.renameSync(path.join(VENDOR, 'package/dist/fabric.min.js'), f);
  fs.rmSync(path.join(VENDOR, 'package'), { recursive: true, force: true }); fs.rmSync(tgz);
  return f;
}
(async () => {
  const [inFile, outPng] = process.argv.slice(2);
  if (!inFile || !outPng) { console.error('usage: node studio-check.cjs <file.menu.json> <out.png>'); process.exit(2); }
  const fab = fabricPath();
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  // Offline: serve Fabric locally, block every other network request (the check never talks to Supabase).
  await p.route('**/*', r => {
    const u = r.request().url();
    if (u.startsWith('file:')) return r.continue();
    if (/fabric\.js\/5\.3\.0\/fabric\.min\.js$/.test(u)) return r.fulfill({ path: fab, contentType: 'application/javascript' });
    return r.abort();
  });
  await p.goto('file://' + APP, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForTimeout(2500);
  const r = await p.evaluate(async (txt) => {
    const out = {};
    try {
      if (typeof harmonyOpen === 'function') harmonyOpen('menu', 'own');
      await new Promise(r => setTimeout(r, 1200));
      mdcFileLoad(txt, 'designer.menu.json');
      await new Promise(r => setTimeout(r, 1200));
      MDC.edit = null; mdcDraw();
      out.load_message = MDC.fileMsg || null;
      out.title = MDC.doc && MDC.doc.title;
      out.sections = MDC.doc && MDC.doc.sections.map(s => s.name);
      out.size = MDC.sizeKey; out.columns = MDC.style.page.cols; out.pages = mdcPageCount(); out.overflow = MDC.overflow;
      out.png = MDC.canvas.toDataURL({ format: 'png', multiplier: 2, left: 0, top: 0, width: mdcPageW(), height: mdcPageH() * out.pages });
    } catch (e) { out.error = String(e && e.stack || e); }
    return out;
  }, fs.readFileSync(inFile, 'utf8'));
  if (r.png) { fs.writeFileSync(outPng, Buffer.from(r.png.split(',')[1], 'base64')); delete r.png; }
  r.page_errors = errs;
  console.log(JSON.stringify(r, null, 2));
  await b.close();
  process.exit(r.error || r.load_message || errs.length ? 1 : 0);
})();
