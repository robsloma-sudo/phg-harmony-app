"""Round 15 render: letter PNG (300 dpi, full resolution), PDF, phone PNG, and per-card measurement -> measure.json."""
import json, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path("/home/user/phg-harmony-app/handoff/designs/test-1-iowa-city-cantina")
URL = (OUT / "menu.html").as_uri()
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
r2 = lambda v: round(v, 2)

MEASURE = r"""() => {
  const pg = document.querySelector('.page').getBoundingClientRect();
  const box = b => ({x: b.left - pg.left, y: b.top - pg.top, w: b.width, h: b.height});
  const lines = el => { const r = document.createRange(); r.selectNodeContents(el); return [...r.getClientRects()].filter(a => a.width > 0); };
  const tight = el => { const rs = lines(el); if (!rs.length) return box(el.getBoundingClientRect());
    const x = Math.min(...rs.map(a => a.left)), y = Math.min(...rs.map(a => a.top)), R = Math.max(...rs.map(a => a.right)), B = Math.max(...rs.map(a => a.bottom));
    return {x: x - pg.left, y: y - pg.top, w: R - x, h: B - y, lines: Math.max(1, Math.round(el.getBoundingClientRect().height / parseFloat(getComputedStyle(el).lineHeight)))}; };
  const lastLineWords = el => { const tn = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const ws = []; let n;
    while ((n = tn.nextNode())) { const re = /\S+/g; let m; while ((m = re.exec(n.data))) { const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length); ws.push(r.getBoundingClientRect().top); } }
    const nb = el.textContent.split(/[ ]+/); if (!ws.length) return 0; const last = Math.max(...ws); const onLast = ws.filter(y => Math.abs(y - last) < 2).length; return {tokens_on_last_line: onLast, lines: new Set(ws.map(y => Math.round(y))).size}; };
  const T = el => Object.assign({text: (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 160)}, tight(el));
  const cueInfo = it => { const q = it.querySelector('.cue'); if (!q) return null; const r = document.createRange(); r.selectNodeContents(q); const rs = [...r.getClientRects()].filter(a => a.width > 0);
    const ch = it.querySelector('.chr'); const r2_ = document.createRange(); r2_.selectNodeContents(ch); const cr = [...r2_.getClientRects()].filter(a => a.width > 0); const lastTop = Math.max(...cr.map(a => a.top));
    return {lines: new Set(rs.map(a => Math.round(a.top))).size, shares_line_with_description: Math.abs(rs[0].top - lastTop) < 2, words: q.textContent.split(/[\s ]+/).filter(Boolean).length}; };
  const lh = el => parseFloat(getComputedStyle(el).lineHeight);
  const bl = el => { const z = document.createElement('span'); z.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline'; el.appendChild(z); const y = z.getBoundingClientRect().top - pg.top; z.remove(); return y; };
  const cards = [...document.querySelectorAll('.card')].map(c => {
    const cs = getComputedStyle(c), its = [...c.querySelectorAll('.item')];
    const gaps = its.slice(1).map((it, k) => it.previousElementSibling ? it.getBoundingClientRect().top - its[k].getBoundingClientRect().bottom : null).filter(v => v !== null);
    return {n: +c.dataset.n, ref: c.dataset.id, featured: c.classList.contains('featured'), box: box(c.getBoundingClientRect()),
      padding_px: {left: parseFloat(cs.paddingLeft), right: parseFloat(cs.paddingRight), top: parseFloat(cs.paddingTop), bottom: parseFloat(cs.paddingBottom)},
      border_px: parseFloat(cs.borderLeftWidth), face: box(c.querySelector('.face').getBoundingClientRect()), cardno: Object.assign(box(c.querySelector('.cardno').getBoundingClientRect()), {text: c.querySelector('.cardno').innerText.trim()}), fig_svg: box(c.querySelector('.figure svg').getBoundingClientRect()), rows: its.map(it => box(it.querySelector('.row').getBoundingClientRect())), subboxes: [...c.querySelectorAll('.sub')].map(s => box(s.getBoundingClientRect())), verse_pt_size: parseFloat(getComputedStyle(c.querySelector('.verse')).fontSize) * 0.75, name: T(c.querySelector('h2')), verse: T(c.querySelector('.verse')), gloss: T(c.querySelector('.gloss')), verse_clipped: c.querySelector('.verse').scrollWidth > c.querySelector('.verse').clientWidth + 1,
      figure: box(c.querySelector('.figure').getBoundingClientRect()), note: c.querySelector('.note') ? Object.assign(box(c.querySelector('.note').getBoundingClientRect()), {text: c.querySelector('.note').innerText.trim()}) : null, orn: c.querySelector('.orn') ? box(c.querySelector('.orn svg').getBoundingClientRect()) : null, vcol: box(c.querySelector('.vcol').getBoundingClientRect()), name_clipped: [...c.querySelectorAll('.namebar h2, .namebar .gloss')].some(e => e.getBoundingClientRect().right > c.querySelector('.namebar').getBoundingClientRect().right + 0.5 || e.getBoundingClientRect().left < c.querySelector('.namebar').getBoundingClientRect().left - 0.5), cardno_style: (s => ({family: s.fontFamily, style: s.fontStyle, weight: s.fontWeight, size_pt: parseFloat(s.fontSize) * 0.75, color: s.color, background: s.backgroundColor}))(getComputedStyle(c.querySelector('.cardno'))), price_style: (s => ({style: s.fontStyle, weight: s.fontWeight, size_pt: parseFloat(s.fontSize) * 0.75}))(getComputedStyle(c.querySelector('.price'))), body: box(c.querySelector('.body').getBoundingClientRect()),
      name_baseline: bl(c.querySelector('h2')), gloss_baseline: bl(c.querySelector('.gloss')), plabels: [...c.querySelectorAll('.plabel')].map(e => Object.assign(box(e.getBoundingClientRect()), {text: e.innerText.trim(), ref: e.closest('.item').dataset.ref})),
      namebar: Object.assign(box(c.querySelector('.namebar').getBoundingClientRect()), {text: c.querySelector('.namebar').innerText.trim()}),
      item_gaps_px: gaps, line_heights_px: [...c.querySelectorAll('.name,.price,.desc,h3')].map(lh), first_row_y: (c.querySelector('.body .row') || c).getBoundingClientRect().top - pg.top, body_rule_y: c.querySelector('.body').getBoundingClientRect().top - pg.top, content_bottom: Math.max(...[...c.querySelectorAll('.body > *:not(.orn)')].map(e => e.getBoundingClientRect().bottom)) - pg.top,
      subs: [...c.querySelectorAll('.sub')].map(s => ({ref: s.dataset.id, h3: T(s.querySelector('h3'))})),
      items: its.map(it => { const d = it.querySelector('.desc'); return {ref: it.dataset.ref, block: box(it.getBoundingClientRect()), name: T(it.querySelector('.name')), price: T(it.querySelector('.price')),
        desc: d ? Object.assign(T(d), lastLineWords(d), {measure: box(d.getBoundingClientRect())}) : null, pcol: box(it.querySelector('.pcol').getBoundingClientRect()), cue: cueInfo(it)}; })};
  });
  return {page: {w: pg.width, h: pg.height}, cards, banner: box(document.querySelector('.banner').getBoundingClientRect()),
          title: T(document.querySelector('.title')), loc: T(document.querySelector('.loc')), deck: box(document.querySelector('.deck').getBoundingClientRect()),
          foot: box(document.querySelector('.foot').getBoundingClientRect())};
}"""
PHONE = r"""() => { const tb = document.querySelector('.tabs');
  const lastLine = el => { const tn = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const ws = []; let n;
    while ((n = tn.nextNode())) { const re = /\S+/g; let m; while ((m = re.exec(n.data))) { const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length); ws.push(r.getBoundingClientRect().top); } }
    if (!ws.length) return 99; const last = Math.max(...ws); return new Set(ws.map(y => Math.round(y))).size > 1 ? ws.filter(y => Math.abs(y - last) < 2).length : 99; };
  const cues = [...document.querySelectorAll('.item')].filter(i => i.querySelector('.cue')).map(i => { const q = i.querySelector('.cue'); const r = document.createRange(); r.selectNodeContents(q);
    const rs = [...r.getClientRects()].filter(a => a.width > 0); const ch = i.querySelector('.chr'); const r3 = document.createRange(); r3.selectNodeContents(ch); const cr = [...r3.getClientRects()].filter(a => a.width > 0);
    return {ref: i.dataset.ref, lines: new Set(rs.map(a => Math.round(a.top))).size, shares_line_with_description: Math.abs(rs[0].top - Math.max(...cr.map(a => a.top))) < 2, words: q.textContent.split(/[\s\u00a0]+/).filter(Boolean).length}; });
  return {cues, scrollWidth: document.documentElement.scrollWidth, tabs: getComputedStyle(tb).position, tab_count: document.querySelectorAll('.tab').length,
    tabbar_scroll_vs_client: [tb.scrollWidth, tb.clientWidth], tab_rects: [...document.querySelectorAll('.tab')].map(t => { const r = t.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right)]; }),
    active_label: (document.querySelector('.tab.active .lbl') || {}).innerText, active_bg: getComputedStyle(document.querySelector('.tab.active')).backgroundColor, inactive_bg: getComputedStyle(document.querySelector('.tab:not(.active)')).backgroundColor,
    min_last_line_tokens: Math.min(...[...document.querySelectorAll('.desc,.name,h2')].map(lastLine)),
    cards: [...document.querySelectorAll('.card')].map(c => { const r = c.getBoundingClientRect(); return {n: +c.dataset.n, x: r.left, w: r.width, y: r.top + scrollY, transform: getComputedStyle(c).transform, frame_transform: getComputedStyle(c, '::before').transform, verse_px: parseFloat(getComputedStyle(c.querySelector('.verse')).fontSize), first_row_bottom_from_card_top: c.querySelector('.body .row').getBoundingClientRect().bottom - r.top, first_desc_bottom_from_card_top: (c.querySelector('.body .item').getBoundingClientRect().bottom - r.top), figure_px: c.querySelector('.figure').getBoundingClientRect().width, cardno_px: parseFloat(getComputedStyle(c.querySelector('.cardno')).fontSize), cardno_style: getComputedStyle(c.querySelector('.cardno')).fontStyle, price_px: parseFloat(getComputedStyle(c.querySelector('.price')).fontSize), gloss_offset_px: (() => { const f = e => { const z = document.createElement('span'); z.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline'; e.appendChild(z); const y = z.getBoundingClientRect().top; z.remove(); return y; }; return f(c.querySelector('.gloss')) - f(c.querySelector('h2')); })(), face_h: c.querySelector('.face').getBoundingClientRect().height}; }), tabbar_h: tb.getBoundingClientRect().height, viewport_h: innerHeight, chips: [...document.querySelectorAll('.tab')].map(t => ({text: t.querySelector('.tno').innerText, bg: getComputedStyle(t).backgroundColor, color: getComputedStyle(t).color, w: t.getBoundingClientRect().width, h: t.getBoundingClientRect().height, top: t.getBoundingClientRect().top})), desc_last_line_tokens: [...document.querySelectorAll('.desc')].map(d => [d.parentElement.dataset.ref, lastLine(d)])}; }"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=3.125)
    pg.goto(URL, wait_until="load"); pg.evaluate("document.fonts.ready")
    fonts = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').length")
    M = pg.evaluate(MEASURE)
    pg.locator(".page").screenshot(path=str(OUT / "preview-letter.png"))
    pg.pdf(path=str(OUT / "menu.pdf"), width="8.5in", height="11in", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
    ph = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    ph.goto(URL, wait_until="load"); ph.evaluate("document.fonts.ready")
    PH = ph.evaluate(PHONE)
    ph.screenshot(path=str(OUT / "preview-phone.png"), full_page=True)
    b.close()

im = Image.open(OUT / "preview-letter.png").convert("RGB")
diff = ImageChops.difference(im, Image.new("RGB", im.size, (0xF6, 0xEE, 0xDF))).convert("L").point(lambda v: 255 if v > 24 else 0)
bx = diff.getbbox(); sx = im.size[0] / 612; sy = im.size[1] / 792
ink = {"left": r2(bx[0] / sx), "top": r2(bx[1] / sy), "right": r2(612 - bx[2] / sx), "bottom": r2(792 - bx[3] / sy)}
json.dump({"M": M, "ph": PH, "ink": ink, "fonts": fonts, "png": list(im.size), "phone_png": list(Image.open(OUT / "preview-phone.png").size)},
          open(HERE / "measure.json", "w"), indent=1, ensure_ascii=False)
print("fonts", fonts, "ink", ink, "png", im.size, "phone", PH["scrollWidth"], PH["tabs"])
