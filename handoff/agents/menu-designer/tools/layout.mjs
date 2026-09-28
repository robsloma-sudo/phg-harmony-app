// Port of Menu Studio's flow (index.html: mdcDraw, mdcCursorFit, mdcSectionHeight, mdcItemHeight, mdcColWidth…).
// Same numbers, same break rules: atomic sections, column target balancing, page feet at H - M.
// Used by the designer's fit check and by the renderer, so a preview lands where Menu Studio will draw it.
// Keep in step with index.html if its layout changes (search "atomic-sections drop").

export const MDC_DPI = 96;
export const MDC_ADV = { title: 8, subtitle: 9, section: 11, sub: 9, name: 4, desc: 4 };
export const MDC_SIZES = {
  letter_p: [8.5, 11], letter_l: [11, 8.5], legal_p: [8.5, 14], legal_l: [14, 8.5], tabloid: [11, 17], tabloid_l: [17, 11],
  half: [5.5, 8.5], half_l: [8.5, 5.5], a4_p: [8.27, 11.69], a4_l: [11.69, 8.27], a5_p: [5.83, 8.27], a5_l: [8.27, 5.83],
  tent: [4, 6], tent_l: [6, 4], five_seven_p: [5, 7], five_seven_l: [7, 5], rack_p: [4.25, 11], rack_l: [11, 4.25], square8: [8, 8],
};

export function layout(file) {
  const S = file.style, P = S.page, doc = file.doc;
  const [wIn, hIn] = MDC_SIZES[file.size] || MDC_SIZES.letter_p;
  const W = wIn * MDC_DPI, H = hIn * MDC_DPI, M = P.margin * MDC_DPI;
  const colMax = W > H ? 8 : 3;
  const n = Math.min(Math.max(1, Math.floor(P.cols || 1)), colMax);
  const gutter = (P.gutter === undefined || P.gutter === null) ? 18 : Math.max(0, Number(P.gutter));
  const colW = (W - M * 2 - (n - 1) * gutter) / n;
  const colX = i => M + i * (colW + gutter);
  const fullW = W - M * 2;
  const ops = [];

  const itemH = it => S.name.s + MDC_ADV.name + (it.desc ? S.desc.s + MDC_ADV.desc : 0);
  const hdescH = node => (node && node.desc) ? S.desc.s + MDC_ADV.desc : 0;
  const sectionH = sec => {
    if (sec.pos) return 0;                       // mdcSectionHeight: a pinned section takes no flow height
    let t = S.section.s + MDC_ADV.section + P.secGap + hdescH(sec);
    for (const it of sec.items) t += itemH(it) + P.itemGap;
    for (const sub of sec.subs) { if (!sub.items.length) continue; t += S.sub.s + MDC_ADV.sub + 6 + hdescH(sub); for (const it of sub.items) t += itemH(it) + P.itemGap; }
    return t;
  };
  const flowH = doc.sections.reduce((a, s) => a + sectionH(s), 0);
  const usable = H - 2 * M;
  const cur = { col: 0, y: M, bandTop: M, bandBottom: M, target: n > 1 ? Math.min(usable, Math.ceil(flowH / n)) : 0, remaining: flowH };
  const colFoot = y => (Math.floor(y / H) + 1) * H - M;
  const fitAt = h => {
    const full = cur.y + h > colFoot(cur.y);
    const done = cur.target && cur.col + 1 < n && (cur.y + h > cur.bandTop + cur.target);
    if (!full && !done) return;
    if (cur.y <= cur.bandTop + 1) return;
    if (cur.y > cur.bandBottom) cur.bandBottom = cur.y;
    if (cur.col + 1 < n) { cur.col++; cur.y = cur.bandTop; return; }
    const nextTop = (Math.floor(cur.bandBottom / H) + 1) * H + M;
    cur.col = 0; cur.bandTop = nextTop; cur.y = nextTop; cur.bandBottom = nextTop;
    if (cur.target && cur.remaining > 0) cur.target = Math.min(H - 2 * M, Math.ceil(cur.remaining / n));
  };
  const bandClose = () => { if (cur.y > cur.bandBottom) cur.bandBottom = cur.y; cur.col = 0; cur.y = cur.bandBottom; return cur.y; };
  const bandOpen = y => { cur.col = 0; cur.bandTop = y; cur.y = y; cur.bandBottom = y; };

  // Masthead
  let y = M;
  ops.push({ t: 'head', lvl: 'title', text: doc.title, x: M, y, w: fullW, W });
  y += S.title.s + MDC_ADV.title;
  if (doc.subtitle) { ops.push({ t: 'head', lvl: 'subtitle', text: doc.subtitle, x: M, y, w: fullW, W }); y += S.subtitle.s + MDC_ADV.subtitle; }
  if (P.rules) { ops.push({ t: 'rule', x: M, y, w: fullW }); y += 22; } else y += 10;
  bandOpen(y);

  const overflow = [], held = [];
  const flowItems = items => { for (const it of items) { fitAt(itemH(it)); ops.push({ t: 'item', item: it, x: colX(cur.col), y: cur.y, w: colW, inline: P.priceAlign === 'inline' || n > 1 }); cur.y += itemH(it) + P.itemGap; } };
  for (const sec of doc.sections) {
    if (sec.breakCol && !sec.breakBefore) { if (cur.y > cur.bandTop + 1) fitAt(1e9); }
    if (sec.breakBefore) { const bb = bandClose(); const pTop = Math.floor(bb / H) * H; if (bb > pTop + M + 1) bandOpen(pTop + H + M); else bandOpen(bb); }
    const sh = S.section.s + MDC_ADV.section;
    if (sec.pos) {
      // Pinned section (mdcDraw: held, drawn in pass two at pos; the flow still advances by secGap).
      held.push(sec); cur.y += P.secGap; continue;
    }
    if (P.spanHeads) {
      let hy = bandClose();
      ops.push({ t: 'head', lvl: 'section', text: sec.name, x: M, y: hy, w: fullW, W, placed: false, node: sec });
      hy += sh;
      if (sec.desc) { ops.push({ t: 'hdesc', text: sec.desc, x: M, y: hy, w: fullW }); hy += hdescH(sec); }
      bandOpen(hy);
    } else {
      const secH = sectionH(sec);
      if (secH > usable) { overflow.push({ name: sec.name, h: secH, fits: usable }); fitAt(sh + S.name.s); } else fitAt(secH);
      cur.remaining -= secH;
      ops.push({ t: 'head', lvl: 'section', text: sec.name, x: colX(cur.col), y: cur.y, w: colW, W, role: sec.designer_role, node: sec });
      cur.y += sh;
      if (sec.desc) { ops.push({ t: 'hdesc', text: sec.desc, x: colX(cur.col), y: cur.y, w: colW, node: sec }); cur.y += hdescH(sec); }
    }
    flowItems(sec.items);
    for (const sub of sec.subs) {
      if (!sub.items.length) continue;
      const subH = S.sub.s + MDC_ADV.sub;
      fitAt(subH);
      ops.push({ t: 'head', lvl: 'sub', text: sub.name, x: colX(cur.col), y: cur.y, w: colW, W, node: sub });
      cur.y += subH;
      if (sub.desc) { ops.push({ t: 'hdesc', text: sub.desc, x: colX(cur.col), y: cur.y, w: colW, node: sub }); cur.y += hdescH(sub); }
      flowItems(sub.items);
      cur.y += 6;
    }
    cur.y += P.secGap;
  }
  // Where each column of page 1 ends (for balance scoring).
  const colEnds = Array(n).fill(0);
  for (const op of ops) { if (op.y >= H || op.t === 'rule' || (op.t === 'head' && (op.lvl === 'title' || op.lvl === 'subtitle'))) continue;
    const c = Math.max(0, Math.round((op.x - M) / (colW + gutter))); const h = op.t === 'item' ? itemH(op.item) : S[op.lvl]?.s || S.desc.s;
    colEnds[Math.min(n - 1, c)] = Math.max(colEnds[Math.min(n - 1, c)], op.y + h); }
  const used = colEnds.filter(v => v > 0);
  const imbalance = used.length > 1 ? (Math.max(...used) - Math.min(...used)) / usable : 0;
  // Pass two: pinned sections (mdcDrawBlock, placed => heading left-aligned at pos). Items inside a pinned block are
  // not drawn: the app's mdcDrawBlock calls mdcFlowItems with the wrong arguments (reported to the lead developer),
  // so the designer only pins item-less blocks such as the colophon footer.
  for (const sec of held) {
    const pg = Math.max(0, Math.floor(sec.pos.page || 0));
    const left = Math.min(Math.max(Number(sec.pos.x) || 0, 0), 0.95) * W, top = pg * H + (Number(sec.pos.y) || 0) * H;
    const wAvail = Math.max(120, Math.min(colW, W - left - M));
    ops.push({ t: 'head', lvl: 'section', text: sec.name, x: left, y: top, w: wAvail, W, placed: true, node: sec, role: sec.designer_role });
    if (sec.desc) ops.push({ t: 'hdesc', text: sec.desc, x: left, y: top + S.section.s + MDC_ADV.section, w: wAvail, node: sec });
  }
  // Bottom of the last drawn line on the last page (Fabric text box = size x 1.16), for margin justification.
  let contentBottom = 0;
  for (const op of ops) {
    const h = op.t === 'rule' ? 1 : op.t === 'item' ? (op.item.desc ? S.name.s + MDC_ADV.name + S.desc.s * 1.16 : S.name.s * 1.16)
            : op.t === 'hdesc' ? S.desc.s * 1.16 : ((op.node?.format?.[op.lvl]?.s) || S[op.lvl].s) * 1.16;
    if (op.node?.pos) continue;                 // flow bottom only; the pinned footer is placed separately
    contentBottom = Math.max(contentBottom, op.y + h);
  }
  contentBottom -= (Math.max(1, Math.ceil((Math.max(cur.y, cur.bandBottom) + M) / H)) - 1) * H;
  const end = Math.max(cur.y, cur.bandBottom) + M;
  const pages = Math.max(1, Math.ceil(end / H));
  // How full is the last page (0..1) — the designer uses it to decide whether to open the layout up.
  const lastPageUsed = (Math.max(cur.y, cur.bandBottom) - (pages - 1) * H - M) / usable;
  return { W, H, M, n, colW, gutter, pages, ops, overflow, flowH, imbalance, colEnds, contentBottom, lastPageUsed: Math.max(0, Math.min(1, lastPageUsed)) };
}

export function priceText(it) {
  const out = [];
  for (const p of it.prices || []) {
    if (p.value === null || p.value === undefined || p.value === '') continue;
    const v = Number(p.value); if (!isFinite(v)) continue;
    const s2 = (Math.round(v * 100) % 100 === 0) ? String(Math.round(v)) : v.toFixed(2);
    out.push(p.label ? `${p.label} ${s2}` : s2);
  }
  return out.join('  /  ');
}
