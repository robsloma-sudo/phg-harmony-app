// Pre-flight against handoff/agents/MENU_DESIGN_SCORECARD.md before a proposal goes to the Coordinator.
// Runs every measured check in §4 on the layout geometry, the content rules the Menu Content Reviewer applies, and a
// local copy of the database's automatic check (no invented items or prices). It does not score taste; it finds
// anything a reviewer would measure as a failure, so it can be fixed first.
//   node selfcheck.mjs <layout.json> <menu.menu.json> [task.json]

import fs from 'node:fs';
import { contrast } from './design.mjs';
import { docCheck, stripSecrets } from './handoff.mjs';
import { itemsOf, listForName } from './draft.mjs';

const r1 = n => Math.round(n * 10) / 10, r2 = n => Math.round(n * 100) / 100;
const SPIRITS = /\b(gin|vodka|rum|rhum|tequila|mezcal|whisk(e)?y|bourbon|rye|scotch|brandy|cognac|armagnac|calvados|pisco|cacha[cç]a|sake|soju|shochu|aquavit|genever|amaro|aperol|campari|vermouth|sherry|port|chartreuse|absinthe|liqueur|blanco|reposado|a[nñ]ejo|sotol|bacanora|wine|prosecco|champagne|cava|beer|lager|cider)\b/i;

export function selfcheck(layout, file, task = null) {
  const E = layout.elements, pageW = layout.page.width_mm, pageH = layout.page.height_mm, M = layout.page.margins_mm;
  const results = [], fixes = [];
  const check = (id, criterion, ok, detail, fix) => { results.push({ id, criterion, ok, detail }); if (!ok && fix) fixes.push(fix); };
  const text = E.filter(e => e.kind !== 'divider' || e.w_mm > 0);

  // Margins: the smallest distance from any element to each edge equals the declared margin (±1 mm).
  for (let p = 1; p <= layout.page.pages; p++) {
    const on = text.filter(e => e.page === p);
    if (!on.length) continue;
    const d = { top: Math.min(...on.map(e => e.y_mm)), left: Math.min(...on.map(e => e.x_mm)),
                right: Math.min(...on.map(e => pageW - (e.x_mm + e.w_mm))), bottom: Math.min(...on.map(e => pageH - (e.y_mm + e.h_mm))) };
    for (const edge of ['top', 'right', 'bottom', 'left']) {
      const off = d[edge] - M[edge];
      check(`margin_${edge}_p${p}`, 6, Math.abs(off) <= 1, `${edge}: ${r2(d[edge])} mm (declared ${M[edge]}, ${off >= 0 ? '+' : ''}${r2(off)})`,
        Math.abs(off) > 1 ? `Page ${p} ${edge} margin is ${r1(d[edge])} mm against ${M[edge]} declared: ${edge === 'bottom' ? 'justify the flow or pin the footer to the margin' : edge === 'right' ? 'use a right-aligned price column (single column) so prices meet the margin' : 'move the outermost element onto the margin'}.` : null);
    }
  }

  // Columns from the grid.
  const colOf = x => { const xs = layout.grid.column_x_mm; let c = 0; for (let i = 0; i < xs.length; i++) if (x >= xs[i] - 1) c = i; return c; };

  // Left edges: item names in one column share one x (±0.3 mm).
  const names = E.filter(e => e.kind === 'item_name');
  const byCol = k => { const m = new Map(); for (const e of E.filter(x => x.kind === k)) { const key = `${e.page}:${colOf(e.x_mm)}`; if (!m.has(key)) m.set(key, []); m.get(key).push(e); } return m; };
  for (const [key, arr] of byCol('item_name')) {
    const xs = arr.map(e => e.x_mm), spread = Math.max(...xs) - Math.min(...xs);
    check(`left_edge_${key}`, 1, spread <= 0.3, `item names in column ${key}: x spread ${r2(spread)} mm`, spread > 0.3 ? `Item names in column ${key} start at different x (${r2(spread)} mm spread).` : null);
  }

  // Price column: prices in one column share one right edge (±0.3 mm).
  if (layout.grid.price_alignment === 'inline') {
    // One consistent inline style (scorecard criterion 3): every price sits the same distance after its name/badges.
    const gaps = [];
    for (const p of E.filter(e => e.kind === 'price')) {
      const before = E.filter(e => e.ref === p.ref && e.page === p.page && Math.abs(e.y_mm - p.y_mm) < 1 && ['item_name', 'brand', 'label'].includes(e.kind));
      if (before.length) gaps.push(p.x_mm - Math.max(...before.map(e => e.x_mm + e.w_mm)));
    }
    const sp = gaps.length ? Math.max(...gaps) - Math.min(...gaps) : 0;
    check('price_inline_consistency', 3, sp <= 0.3, `inline prices: gap after name ${r2(Math.min(...gaps))}–${r2(Math.max(...gaps))} mm`, sp > 0.3 ? `Inline prices sit at varying distances after their names (${r2(sp)} mm).` : null);
  }
  for (const [key, arr] of (layout.grid.price_alignment === 'inline' ? new Map() : byCol('price'))) {
    const rs = arr.map(e => e.x_mm + e.w_mm), spread = Math.max(...rs) - Math.min(...rs);
    check(`price_column_${key}`, 3, spread <= 0.3, `prices in column ${key}: right-edge spread ${r2(spread)} mm (${layout.grid.price_alignment})`,
      spread > 0.3 ? (layout.grid.price_alignment === 'inline'
        ? `Prices in column ${key} sit inline after each name (Menu Studio forces this above one column): use one column, or ask the lead developer for a right-aligned price column in multi-column layouts.`
        : `Prices in column ${key} do not share one right edge.`) : null);
  }

  // Headers: one size and one x per level and column; consistent space above and below (±0.5 mm).
  for (const lvl of ['section', 'sub']) {
    const hs = E.filter(e => e.level === lvl && (e.kind === 'header' || e.kind === 'subheader'));
    if (!hs.length) continue;
    const hsz = new Set(hs.map(e => r1(e.h_mm)));
    check(`header_size_${lvl}`, 2, hsz.size === 1, `${lvl} header heights: ${[...hsz].join(', ')} mm`, hsz.size > 1 ? `${lvl} headers are not all one size.` : null);
    const m = new Map(); for (const e of hs) { const k = `${e.page}:${colOf(e.x_mm)}`; if (!m.has(k)) m.set(k, new Set()); m.get(k).add(r1(e.x_mm)); }
    for (const [k, xs] of m) check(`header_x_${lvl}_${k}`, 2, xs.size === 1, `${lvl} headers x in ${k}: ${[...xs].join(', ')}`, xs.size > 1 ? `${lvl} headers in ${k} do not share one x.` : null);
    // spacing above/below within the flow
    const flow = E.filter(e => e.kind !== 'label' && e.kind !== 'brand' && e.kind !== 'footer' && e.kind !== 'price' && !(e.kind === 'divider' && e.level === 'leader')).sort((a, b) => a.page - b.page || colOf(a.x_mm) - colOf(b.x_mm) || a.y_mm - b.y_mm);
    const above = [], below = [];
    hs.forEach(h => {
      const col = flow.filter(e => e.page === h.page && colOf(e.x_mm) === colOf(h.x_mm));
      const i = col.indexOf(h);
      if (i > 0 && col[i - 1].kind !== 'divider' && col[i - 1].level !== 'section' && col[i - 1].level !== 'subtitle') above.push(h.y_mm - (col[i - 1].y_mm + col[i - 1].h_mm));
      if (i >= 0 && i < col.length - 1) below.push(col[i + 1].y_mm - (h.y_mm + h.h_mm));
    });
    for (const [nm, arr] of [['above', above], ['below', below]]) if (arr.length > 1) {
      const sp = Math.max(...arr) - Math.min(...arr);
      check(`header_space_${nm}_${lvl}`, 2, sp <= 0.5, `space ${nm} ${lvl} headers: ${r2(Math.min(...arr))}–${r2(Math.max(...arr))} mm`, sp > 0.5 ? `Space ${nm} ${lvl} headers varies by ${r2(sp)} mm.` : null);
    }
  }

  // Spacing: the gap between consecutive items in a section is constant (±0.5 mm).
  const doc = file.doc;
  for (const holder of doc.sections.flatMap(s => [s, ...(s.subs || [])])) {
    const ids = (holder.items || []).map(i => i.id);
    if (ids.length < 3) continue;
    const gaps = [];
    for (let i = 0; i < ids.length - 1; i++) {
      const cur = E.filter(e => e.ref === ids[i] && (e.kind === 'item_name' || e.kind === 'description'));
      const nxt = E.find(e => e.ref === ids[i + 1] && e.kind === 'item_name');
      if (!cur.length || !nxt || nxt.page !== cur[0].page || colOf(nxt.x_mm) !== colOf(cur[0].x_mm)) continue;
      gaps.push(nxt.y_mm - Math.max(...cur.map(e => e.y_mm + e.h_mm)));
    }
    if (gaps.length > 1) { const sp = Math.max(...gaps) - Math.min(...gaps);
      check(`item_gap_${holder.id}`, 6, sp <= 0.5, `${holder.name}: item gaps ${r2(Math.min(...gaps))}–${r2(Math.max(...gaps))} mm`, sp > 0.5 ? `Item spacing in ${holder.name} varies by ${r2(sp)} mm.` : null); }
  }

  // Contrast: every text colour against the page background ≥ 4.5:1.
  const bg = layout.page.background;
  for (const [lvl, t] of Object.entries(layout.type)) {
    const c = contrast(t.colour, bg);
    check(`contrast_${lvl}`, 4, c >= 4.5, `${lvl} ${t.colour} on ${bg}: ${r1(c)}:1`, c < 4.5 ? `${lvl} text contrast is ${r1(c)}:1; raise it to 4.5:1.` : null);
  }

  // Content: every item has a description; cocktails name their spirit and at least two more ingredients.
  for (const { it, s, sub } of itemsOf(doc)) {
    const d = String(it.desc || '').trim();
    const list = it.meta?.section || listForName(sub?.name || s.name);
    check(`desc_${it.id}`, 8, !!d, `${it.name}: ${d ? 'has description' : 'NO description'}`, d ? null : `"${it.name}" needs a description from known facts (recipe, inputs) or a question to the venue.`);
    if (d && (list === 'cocktails' || /cocktail/i.test(sub?.name || s.name))) {
      const parts = d.split(/[,·]|\band\b/).map(x => x.trim()).filter(Boolean);
      const ok = SPIRITS.test(d) && parts.length >= 3;
      check(`cocktail_ingredients_${it.id}`, 8, ok, `${it.name}: ${parts.length} ingredient terms${SPIRITS.test(d) ? '' : ', no spirit named'}`, ok ? null : `"${it.name}" description should name its spirit and at least two more ingredients.`);
    }
  }

  // Database automatic check (local copy).
  if (task) {
    const dc = docCheck(stripSecrets(doc), task.base_doc || null, task.inputs || {});
    check('db_auto_check', 9, dc.ok, dc.ok ? `${dc.items} items, ${dc.sections} sections: no invented items or prices` : dc.problems.join('; '), dc.ok ? null : 'Fix the automatic-check problems: ' + dc.problems.slice(0, 3).join('; '));
  }

  const failed = results.filter(r => !r.ok);
  const byCrit = {};
  for (const r of results) { byCrit[r.criterion] = byCrit[r.criterion] || { pass: 0, fail: 0 }; byCrit[r.criterion][r.ok ? 'pass' : 'fail']++; }
  return { ok: failed.length === 0, checks: results.length, failed: failed.length, by_criterion: byCrit, failures: failed, fixes: [...new Set(fixes)] };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const [, , lp, fp, tp] = process.argv;
  const out = selfcheck(JSON.parse(fs.readFileSync(lp, 'utf8')), JSON.parse(fs.readFileSync(fp, 'utf8')), tp ? JSON.parse(fs.readFileSync(tp, 'utf8')) : null);
  console.log(JSON.stringify(out, null, 2));
  process.exit(out.ok ? 0 : 1);
}
