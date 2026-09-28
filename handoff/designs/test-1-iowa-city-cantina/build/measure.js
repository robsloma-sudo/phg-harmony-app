() => {
  const pg = document.querySelector('.page').getBoundingClientRect();
  const cols = [...document.querySelectorAll('.col')];
  const colOf = el => { const c = el.closest('.col'); return c ? cols.indexOf(c) + 1 : null; };
  const box = b => ({x: b.left - pg.left, y: b.top - pg.top, w: b.width, h: b.height});
  const tight = el => { const r = document.createRange(); r.selectNodeContents(el); const rs = [...r.getClientRects()].filter(a => a.width > 0);
    if (!rs.length) return box(el.getBoundingClientRect());
    const x = Math.min(...rs.map(a => a.left)), y = Math.min(...rs.map(a => a.top)), R = Math.max(...rs.map(a => a.right)), B = Math.max(...rs.map(a => a.bottom));
    return {x: x - pg.left, y: y - pg.top, w: R - x, h: B - y, lines: new Set(rs.map(a => Math.round(a.top))).size}; };
  const bl = el => { const s = document.createElement('span'); s.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline'; el.appendChild(s); const y = s.getBoundingClientRect().top - pg.top; s.remove(); return y; };
  const out = [];
  const push = (kind, el, o = {}) => {
    const t = o.tight ? tight(el) : box(el.getBoundingClientRect());
    const rec = Object.assign({kind, column: colOf(el), text: (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 140)}, t);
    if (o.slot) rec.slot = box(o.slot.getBoundingClientRect());
    if (o.baseline) rec.baseline = bl(el);
    for (const k of ['ref', 'level', 'note']) if (o[k]) rec[k] = o[k];
    out.push(rec);
  };
  push('image', document.querySelector('.banner'), {note: 'bespoke papel picado banner (SVG, 9 motifs)'});
  push('header', document.querySelector('.title'), {tight: true, slot: document.querySelector('.title'), baseline: true, level: 'title'});
  push('subheader', document.querySelector('.loc'), {tight: true, slot: document.querySelector('.loc'), baseline: true, level: 'location'});
  push('divider', document.querySelector('.mastrule'), {note: 'double rule (1.5pt + 0.5pt) inside a 12pt slot'});
  push('divider', document.querySelector('.divider'), {note: 'dotted column divider'});
  document.querySelectorAll('.sec').forEach(s => {
    const h = s.querySelector('.hrow');
    push('header', h.querySelector('h2'), {tight: true, slot: h, baseline: true, level: 'section', ref: s.dataset.id});
    push('ornament', h.querySelector('.kicker'), {tight: true, slot: h, baseline: true, level: 'kicker', ref: s.dataset.id});
  });
  document.querySelectorAll('.sub').forEach(s => {
    push('subheader', s.querySelector('h3'), {tight: true, slot: s, baseline: true, level: 'sub', ref: s.dataset.id});
    push('divider', s.querySelector('.subrule'), {ref: s.dataset.id, note: 'subheader hairline'});
  });
  document.querySelectorAll('.item').forEach(it => {
    const r = it.querySelector('.row'), d = it.querySelector('.desc');
    push('item_block', it, {ref: it.dataset.ref});
    push('item_name', it.querySelector('.name'), {tight: true, slot: r, baseline: true, ref: it.dataset.ref});
    push('price', it.querySelector('.price'), {tight: true, slot: r, baseline: true, ref: it.dataset.ref});
    push('description', d, {tight: true, slot: d, baseline: true, ref: it.dataset.ref});
  });
  const em = document.querySelector('.endmark'); if (em) push('ornament', em, {note: 'column end mark (three diamonds + hairlines)'});
  document.querySelectorAll('.foot .fr').forEach(e => push('divider', e, {note: 'footer hairline'}));
  document.querySelectorAll('.foot .agave').forEach(e => push('ornament', e, {note: 'agave ornament (SVG)'}));
  push('ornament', document.querySelector('.foot .salud'), {tight: true, baseline: true, note: 'footer sign-off'});
  // last baseline of each description (multi-line)
  const lastBl = [...document.querySelectorAll('.desc')].map(d => ({ref: d.parentElement.dataset.ref, last: bl(d)}));
  const colBox = cols.map(c => box(c.getBoundingClientRect()));
  const colsBox = box(document.querySelector('.cols').getBoundingClientRect());
  const foot = box(document.querySelector('.foot').getBoundingClientRect());
  return {page: {w: pg.width, h: pg.height}, elements: out, cols: colBox, colsBox, foot, lastBl};
}
