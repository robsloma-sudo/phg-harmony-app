// Render a Menu Studio file (.menu.json) exactly as Menu Studio lays it out:
//   page-N.png   full print resolution (300 dpi; letter = 2550 x 3300). Never downscaled.
//   menu.pdf     vector PDF at trim size
//   menu-print.pdf  0.125" bleed + crop marks, for a print shop
//   phone.png    phone preview (390 CSS px wide @3x), single column, wrapped descriptions
//   render.json  measured overflow report from the real browser layout
// Usage: node render.mjs <file.menu.json> <outDir> [--dpi 300]

import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { layout, priceText, MDC_DPI } from './layout.mjs';
import { MDC_FONTS } from '../styles/looks.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const FONT_DIR = path.resolve(here, '../styles/fonts');

// Real font first (exact on machines that have it), then a metric-compatible stand-in for previews.
const STACKS = [
  `Georgia, 'Gelasio', serif`,
  `'Times New Roman', Times, 'Nimbus Roman', 'Liberation Serif', serif`,
  `Palatino, 'Palatino Linotype', 'P052', 'Gelasio', serif`,
  `Helvetica, Arial, 'Nimbus Sans', 'Liberation Sans', sans-serif`,
  `'Avenir Next', Avenir, 'Nunito Sans', 'Segoe UI', sans-serif`,
  `'Trebuchet MS', 'Fira Sans', Tahoma, sans-serif`,
  `'Century Gothic', 'URW Gothic', Futura, sans-serif`,
  `'Courier New', Courier, 'Nimbus Mono PS', 'Liberation Mono', monospace`,
];
if (STACKS.length !== MDC_FONTS.length) throw new Error('font stacks out of step with MDC_FONTS');

// Fonts are inlined as data: URIs: a page loaded with setContent is about:blank and may not read file:// fonts.
let _faces = null;
export function fontFaces() {
  if (_faces) return _faces;
  _faces = fs.readFileSync(path.join(FONT_DIR, 'fonts.css'), 'utf8')
    .replace(/url\('([^']+)'\)/g, (m, f) => `url(data:font/woff2;base64,${fs.readFileSync(path.join(FONT_DIR, f)).toString('base64')})`);
  return _faces;
}
export { STACKS };

const escH = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function css(st, over) {
  const s = Object.assign({}, st, over || {});
  return `font-family:${STACKS[s.f]};font-size:${s.s}px;font-weight:${s.w};font-style:${s.i ? 'italic' : 'normal'};` +
         `letter-spacing:${(s.sp || 0) / 1000}em;color:${s.c};line-height:1.16;white-space:pre;`;
}
const txt = (t, st) => st.cs === 'upper' ? String(t).toUpperCase() : st.cs === 'lower' ? String(t).toLowerCase() : String(t);

function pageHTML(file, L, p) {
  const S = file.style, P = S.page, top = p * L.H;
  let h = '';
  for (const op of L.ops) {
    if (Math.floor(op.y / L.H) !== p) continue;
    const y = op.y - top;
    if (op.t === 'rule') h += `<div style="position:absolute;left:${op.x}px;top:${y}px;width:${op.w}px;border-top:1px solid ${P.rule}"></div>`;
    else if (op.t === 'head') {
      const st = S[op.lvl], al = st.al || 'left';
      const pos = op.lvl === 'title' || op.lvl === 'subtitle'
        ? (al === 'center' ? `left:0;width:${op.W}px;text-align:center` : al === 'right' ? `left:${op.x}px;width:${op.w}px;text-align:right` : `left:${op.x}px`)
        : (al === 'center' ? `left:0;width:${op.W}px;text-align:center` : al === 'right' ? `left:${op.x}px;width:${op.w}px;text-align:right` : `left:${op.x}px`);
      h += `<div class="t" style="position:absolute;top:${y}px;${pos};${css(st)}">${escH(txt(op.text, st))}</div>`;
    } else if (op.t === 'hdesc') h += `<div class="t" style="position:absolute;left:${op.x}px;top:${y}px;${css(S.desc)}">${escH(op.text)}</div>`;
    else if (op.t === 'item') {
      const it = op.item, fo = it.format || {};
      const nameSt = Object.assign({}, S.name, fo.name || {});
      const badgeSize = Math.max(7, Math.round(S.desc.s * 0.7));
      const badges = (it.badges || []).map(b => `<span style="margin-left:6px;position:relative;top:2px;font-family:${STACKS[S.desc.f]};font-size:${badgeSize}px;letter-spacing:0.12em;color:${S.sub.c};line-height:1">${escH(String(b).toUpperCase())}</span>`).join('');
      const pt = priceText(it);
      const priceSt = Object.assign({}, S.price, fo.price || {});
      const dots = P.dots && !op.inline && pt;
      let row = `<span style="${css(nameSt)}">${escH(txt(it.name, nameSt))}</span>` +
        (it.brand ? `<span style="${css(S.brand, fo.brand)}">&nbsp;${escH(it.brand)}</span>` : '') + badges;
      if (pt) row += op.inline
        ? `<span style="margin-left:8px;${css(priceSt)}">${escH(pt)}</span>`
        : `<span style="flex:1 1 auto;min-width:12px;margin:0 6px;align-self:flex-start;height:${Math.round(S.name.s * 0.8)}px;${dots ? `border-bottom:0.75px dashed ${S.price.c};opacity:.6;` : ''}"></span><span style="${css(priceSt)}">${escH(pt)}</span>`;
      h += `<div class="row" data-name="${escH(it.name)}" style="position:absolute;left:${op.x}px;top:${y}px;width:${op.w}px;display:flex;align-items:flex-start">${row}</div>`;
      if (it.desc) h += `<div class="t desc" data-name="${escH(it.name)}" data-w="${op.w}" style="position:absolute;left:${op.x}px;top:${y + S.name.s + 4}px;${css(S.desc, fo.desc)}">${escH(it.desc)}</div>`;
    }
  }
  return h;
}

function docHTML(file, L, { bleed = 0, slug = 0, marks = false } = {}) {
  const P = file.style.page, off = bleed + slug;
  const PW = L.W + off * 2, PH = L.H + off * 2;
  const fontCss = fontFaces();
  let body = '';
  for (let p = 0; p < L.pages; p++) {
    let m = '';
    if (marks) {
      // Crop marks in the slug, aligned to the trim edge, kept clear of the bleed.
      const L1 = off, R1 = off + L.W, T1 = off, B1 = off + L.H, len = slug - 6;
      const k = 'position:absolute;background:#000';
      for (const [x, y] of [[L1, T1], [R1, T1], [L1, B1], [R1, B1]]) {
        const hx = x === L1 ? 0 : x + bleed + 6, vy = y === T1 ? 0 : y + bleed + 6;
        m += `<div style="${k};left:${hx}px;top:${y - 0.25}px;width:${len}px;height:0.5px"></div>`;
        m += `<div style="${k};left:${x - 0.25}px;top:${vy}px;width:0.5px;height:${len}px"></div>`;
      }
    }
    body += `<section class="pg" style="width:${PW}px;height:${PH}px">` +
      (marks ? `<div style="position:absolute;left:${slug}px;top:${slug}px;width:${L.W + 2 * bleed}px;height:${L.H + 2 * bleed}px;background:${P.bg}"></div>` : '') +
      `<div class="trim" style="position:absolute;left:${off}px;top:${off}px;width:${L.W}px;height:${L.H}px;background:${P.bg};overflow:visible">${pageHTML(file, L, p)}</div>${m}</section>`;
  }
  return `<!doctype html><html><head><meta charset="utf-8"><style>${fontCss}
    html,body{margin:0;padding:0;background:${marks ? '#fff' : P.bg}} .pg{position:relative;overflow:hidden;break-after:page;page-break-after:always}
    .pg:last-child{break-after:auto;page-break-after:auto} *{-webkit-print-color-adjust:exact;print-color-adjust:exact;box-sizing:border-box}
    @page{size:${PW}px ${PH}px;margin:0}</style></head><body>${body}</body></html>`;
}

// Phone: the same design language, re-flowed for a 390 px screen. Menu Studio publishes digital menus separately;
// this preview shows how the design reads on a phone (QR landing). Type is lifted to phone minimums.
function phoneHTML(file) {
  const S = file.style, P = S.page, doc = file.doc;
  const k = 1.25, lift = (st, min) => Object.assign({}, st, { s: Math.max(min, Math.round(st.s * k)) });
  const T = { title: lift(S.title, 28), subtitle: lift(S.subtitle, 11), section: lift(S.section, 16), sub: lift(S.sub, 11),
              name: lift(S.name, 16), brand: lift(S.brand, 16), desc: lift(S.desc, 14), price: lift(S.price, 16) };
  const c = (st, o) => css(st, o).replace('white-space:pre;', '');
  const fontCss = fontFaces();
  const item = it => {
    const fo = it.format || {}, pt = priceText(it);
    return `<div style="margin:0 0 ${Math.max(12, P.itemGap * 1.6)}px">
      <div style="display:flex;gap:12px;align-items:baseline"><div style="flex:1">${`<span style="${c(Object.assign({}, T.name, fo.name || {}))}">${escH(txt(it.name, T.name))}</span>`}
      ${it.brand ? `<span style="${c(T.brand)}"> ${escH(it.brand)}</span>` : ''}
      ${(it.badges || []).map(b => `<span style="margin-left:6px;font-family:${STACKS[S.desc.f]};font-size:10px;letter-spacing:.12em;color:${S.sub.c};border:1px solid ${S.sub.c};border-radius:3px;padding:1px 4px;vertical-align:2px">${escH(b.toUpperCase())}</span>`).join('')}</div>
      ${pt ? `<div style="${c(T.price)};white-space:nowrap">${escH(pt)}</div>` : ''}</div>
      ${it.desc ? `<div style="${c(T.desc)};margin-top:3px;line-height:1.35">${escH(it.desc)}</div>` : ''}</div>`;
  };
  let body = `<header style="text-align:${S.title.al === 'left' ? 'left' : 'center'};padding:36px 22px 18px;${P.rules ? `border-bottom:1px solid ${P.rule};` : ''}margin:0 0 18px">
    <div style="${c(T.title)}">${escH(txt(doc.title, T.title))}</div>${doc.subtitle ? `<div style="${c(T.subtitle)};margin-top:8px">${escH(txt(doc.subtitle, T.subtitle))}</div>` : ''}</header>`;
  for (const sec of doc.sections) {
    body += `<section style="padding:6px 22px ${Math.max(16, P.secGap)}px"><h2 style="margin:0 0 12px;${c(T.section)}">${escH(txt(sec.name, T.section))}</h2>`;
    if (sec.desc) body += `<div style="${c(T.desc)};margin:-4px 0 12px;line-height:1.35">${escH(sec.desc)}</div>`;
    body += sec.items.map(item).join('');
    for (const sub of sec.subs) if (sub.items.length) body += `<h3 style="margin:14px 0 10px;${c(T.sub)}">${escH(txt(sub.name, T.sub))}</h3>` + sub.items.map(item).join('');
    body += '</section>';
  }
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>${fontCss}
    html,body{margin:0;background:${P.bg};color:${P.ink};-webkit-text-size-adjust:100%} *{box-sizing:border-box}</style></head><body>${body}<div style="height:28px"></div></body></html>`;
}

async function chromium() {
  const require = createRequire(import.meta.url);
  const tries = ['playwright', '/opt/node22/lib/node_modules/playwright', path.join(process.execPath, '../../lib/node_modules/playwright')];
  for (const t of tries) { try { return require(t).chromium; } catch { /* next */ } }
  throw new Error('playwright not found (npm i -g playwright; browsers at PLAYWRIGHT_BROWSERS_PATH)');
}

export async function render(file, outDir, { dpi = 300, phone = true, pdf = true } = {}) {
  fs.mkdirSync(outDir, { recursive: true });
  const L = layout(file);
  const scale = dpi / MDC_DPI;
  const ch = await chromium();
  const browser = await ch.launch();
  const report = { size: file.size, pages: L.pages, columns: L.n, column_width_px: Math.round(L.colW), dpi,
                   pixel_size: [Math.round(L.W * scale), Math.round(L.H * scale)], files: [], overflow_sections: L.overflow, wide_lines: [] };
  try {
    // Print pages at full resolution.
    const ctx = await browser.newContext({ viewport: { width: Math.ceil(L.W), height: Math.ceil(L.H) }, deviceScaleFactor: scale });
    const pg = await ctx.newPage();
    const html = docHTML(file, L);
    fs.writeFileSync(path.join(outDir, 'menu.html'), html);
    await pg.setContent(html, { waitUntil: 'load' });
    await pg.evaluate(() => document.fonts.ready);
    // Real measured overflow: a row or description wider than its column runs into the next column in Menu Studio too.
    report.wide_lines = await pg.evaluate(() => {
      const out = [];
      for (const r of document.querySelectorAll('.row')) {
        const kids = [...r.children]; const need = kids.reduce((a, k) => a + k.getBoundingClientRect().width, 0);
        const spacer = kids.find(k => k.style.flex && k.style.flex.startsWith('1'));
        const natural = need - (spacer ? spacer.getBoundingClientRect().width - 12 : 0);
        if (natural > r.clientWidth + 1) out.push({ item: r.dataset.name, kind: 'name+price', over_px: Math.round(natural - r.clientWidth) });
      }
      for (const d of document.querySelectorAll('.desc')) {
        const w = d.getBoundingClientRect().width;
        if (w > Number(d.dataset.w) + 1) out.push({ item: d.dataset.name, kind: 'description', over_px: Math.round(w - Number(d.dataset.w)) });
      }
      return out;
    });
    const sections = await pg.$$('section.pg');
    for (let i = 0; i < sections.length; i++) {
      const f = `page-${i + 1}.png`;
      await sections[i].screenshot({ path: path.join(outDir, f) });
      report.files.push(f);
    }
    if (pdf) {
      await pg.pdf({ path: path.join(outDir, 'menu.pdf'), width: `${L.W}px`, height: `${L.H}px`, printBackground: true, preferCSSPageSize: true });
      report.files.push('menu.pdf');
      const bleed = 0.125 * MDC_DPI, slug = 0.25 * MDC_DPI;
      const pp = await ctx.newPage();
      await pp.setContent(docHTML(file, L, { bleed, slug, marks: true }), { waitUntil: 'load' });
      await pp.evaluate(() => document.fonts.ready);
      await pp.pdf({ path: path.join(outDir, 'menu-print.pdf'), width: `${L.W + 2 * (bleed + slug)}px`, height: `${L.H + 2 * (bleed + slug)}px`, printBackground: true, preferCSSPageSize: true });
      report.files.push('menu-print.pdf');
    }
    await ctx.close();
    if (phone) {
      const pc = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true });
      const ph = await pc.newPage();
      await ph.setContent(phoneHTML(file), { waitUntil: 'load' });
      await ph.evaluate(() => document.fonts.ready);
      await ph.screenshot({ path: path.join(outDir, 'phone.png'), fullPage: true });
      report.files.push('phone.png');
      await pc.close();
    }
  } finally { await browser.close(); }
  fs.writeFileSync(path.join(outDir, 'render.json'), JSON.stringify(report, null, 2));
  return report;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const [, , inFile, outDir = 'out', ...rest] = process.argv;
  const dpi = Number((rest.join(' ').match(/--dpi\s+(\d+)/) || [])[1] || 300);
  const file = JSON.parse(fs.readFileSync(inFile, 'utf8'));
  render(file, outDir, { dpi }).then(r => console.log(JSON.stringify(r, null, 2))).catch(e => { console.error(e); process.exit(1); });
}
