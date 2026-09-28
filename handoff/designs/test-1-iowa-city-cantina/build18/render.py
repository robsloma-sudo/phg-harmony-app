"""Round 18 render + measured gates. Letter 2550x3300 (300 dpi), trim PDF, bleed PDF with crop marks, phone 1170 wide.
Contrast is measured at the WORST PIXEL: the page is rendered a second time with all text transparent (art + texture only),
and every text line box is scanned pixel by pixel against the text's computed colour."""
import json, math, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "round-18"
URL = (OUT / "menu.html").as_uri()
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
DSF = 3.125  # 96 css px/in * 3.125 = 300 dpi -> 2550 x 3300
PT2MM = 25.4 / 72

MEASURE = r"""() => {
 const pg = document.querySelector('.page').getBoundingClientRect(), K = 0.75;
 const rects = el => { if (el instanceof SVGElement) { const a = el.getBoundingClientRect(); return [a]; }
   const r = document.createRange(); r.selectNodeContents(el); return [...r.getClientRects()].filter(a => a.width > 0 && a.height > 0); };
 const tight = el => { const rs = rects(el); const x = Math.min(...rs.map(a => a.left)), y = Math.min(...rs.map(a => a.top)), R = Math.max(...rs.map(a => a.right)), B = Math.max(...rs.map(a => a.bottom));
   return {x: (x - pg.left) * K, y: (y - pg.top) * K, w: (R - x) * K, h: (B - y) * K, lines: new Set(rs.map(a => Math.round(a.top))).size,
           line_rects: rs.map(a => [(a.left - pg.left) * K, (a.top - pg.top) * K, a.width * K, a.height * K])}; };
 const box = el => { const a = el.getBoundingClientRect(); return {x: (a.left - pg.left) * K, y: (a.top - pg.top) * K, w: a.width * K, h: a.height * K}; };
 const sty = el => { const s = getComputedStyle(el); const c = el instanceof SVGElement ? s.fill : s.color; return {color: c, font: s.fontFamily.split(',')[0].replace(/['"]/g, ''), size_pt: parseFloat(s.fontSize) * (el instanceof SVGElement ? 1 : K), weight: s.fontWeight, style: s.fontStyle, tracking_em: (parseFloat(s.letterSpacing) || 0) / parseFloat(s.fontSize)}; };
 const els = [];
 const add = (kind, el, extra = {}) => els.push(Object.assign({kind, text: (el.textContent || '').trim().replace(/\s+/g, ' ')}, tight(el), sty(el), extra));
 const colOf = el => { const c = el.closest('.col'); if (!c) return 'full'; return c.dataset.col === 'L' ? 'left' : 'right'; };
 add('title', document.querySelector('.wm.print .wmtext'), {ref: 'title', note: 'CANTINA wordmark, SVG text cut as paper (Fraunces 760, 92 pt, tracking -0.012em); sun behind the first A'});
 add('tagline', document.querySelector('.subline'), {ref: 'subtitle', note: 'venue line + location'});
 document.querySelectorAll('.menu .hrow').forEach(h => { const col = colOf(h);
   add('header', h.querySelector('h2'), {ref: h.dataset.id, column: col});
   const t = h.querySelector('.tag, .pour'); if (t) add(t.classList.contains('tag') ? 'tagline' : 'label', t, {ref: h.dataset.id, column: col, note: t.classList.contains('tag') ? 'the one italic section tagline' : 'pour label for the Spirits prices'}); });
 document.querySelectorAll('.menu .sub').forEach(s => { const h = s.querySelector('h3'); if (h) add('subheader', h, {ref: s.dataset.id, column: colOf(s)}); });
 const pairs = [];
 document.querySelectorAll('.menu .item').forEach(it => { const col = colOf(it);
   const n = it.querySelector('.name'), p = it.querySelector('.price'), d = it.querySelector('.desc'), l = it.querySelector('.lead');
   add('item_name', n, {ref: it.dataset.ref, column: col}); add('price', p, {ref: it.dataset.ref, column: col}); if (d) add('description', d, {ref: it.dataset.ref, column: col});
   els.push(Object.assign({kind: 'leader', ref: it.dataset.ref, column: col, note: '0.6 pt dotted leader, #7C3322'}, box(l)));
   const nb = tight(n), pb = tight(p), cb = box(it.closest('.col')), lb = box(l);
   pairs.push({ref: it.dataset.ref, column: col, name_right: nb.x + nb.w, price_left: pb.x, price_right: pb.x + pb.w, column_w: cb.w, travel_pt: pb.x - (nb.x + nb.w), travel_frac: (pb.x - (nb.x + nb.w)) / cb.w, leader_w: lb.w,
     measure_w: box(it.querySelector('.row')).w, block_top: box(it).y, block_bottom: box(it).y + box(it).h, name_x: nb.x}); });
 const cv = document.createElement('canvas').getContext('2d');
 const xh = el => { const s = getComputedStyle(el); cv.font = `${s.fontStyle} ${s.fontWeight} ${s.fontSize} ${s.fontFamily}`; const mx = cv.measureText('x'), mH = cv.measureText('H');
   return {size_pt: parseFloat(s.fontSize) * K, x_height_pt: mx.actualBoundingBoxAscent * K, cap_height_pt: mH.actualBoundingBoxAscent * K}; };
 const leg = {item_name: xh(document.querySelector('.menu .name')), price: xh(document.querySelector('.menu .price')), description: xh(document.querySelector('.menu .desc')), subheader: xh(document.querySelector('.menu h3')), header: xh(document.querySelector('.menu h2')), section_tagline: xh(document.querySelector('.menu .tag'))};
 const art = box(document.querySelector('.art.print'));
 const q = s => document.querySelector(s);
 const lastBottom = el => { const ds = [...el.querySelectorAll('.desc, .row')]; return Math.max(...ds.map(d => (d.getBoundingClientRect().bottom - pg.top) * K)); };
 const secEl = id => q(`.menu [data-id="${id}"]`);
 const secboxes = {cocktails: {top: box(secEl('sec_cocktails')).y, bottom: lastBottom(secEl('sec_cocktails'))},
   spirits: {top: box(secEl('sec_spirits')).y, bottom: lastBottom(secEl('sec_spirits'))},
   pair: {top: box(q('.menu .pair')).y}, left_end: lastBottom(q('.menu .pair .col[data-col=L]')), wine_end: lastBottom(q('.menu .pair .col[data-col=R]'))};
 const cols = [...document.querySelectorAll('.menu .col')].map(c => Object.assign(box(c), {col: c.dataset.col, measure: box(c.querySelector('.row')).w}));
 const top = parseFloat(getComputedStyle(q('.page')).getPropertyValue('--top'));
 return {page: {w: pg.width * K, h: pg.height * K}, els, pairs, leg, art, secboxes, cols, top, pair_bottoms: [secboxes.left_end, secboxes.wine_end], menu: box(q('.menu'))};
}"""

HIDE = "document.documentElement.classList.add('notext'); const st=document.createElement('style'); st.textContent='.notext .tx{color:transparent!important}'; document.head.appendChild(st);"

def lum(c):
    f = lambda v: (v / 255) / 12.92 if v / 255 <= 0.04045 else (((v / 255) + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])
def cr(a, b):
    la, lb = lum(a), lum(b); return (max(la, lb) + .05) / (min(la, lb) + .05)
def rgb(s):
    v = s[s.index("(") + 1:s.index(")")].split(","); return tuple(int(float(x)) for x in v[:3])

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=DSF)
    pg.goto(URL, wait_until="load"); pg.evaluate("document.fonts.ready"); pg.evaluate("layoutMenu()")
    fonts = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').length")
    M = pg.evaluate(MEASURE)
    pg.locator(".page").screenshot(path=str(OUT / "preview-letter.png"))
    pg.pdf(path=str(OUT / "menu.pdf"), width="8.5in", height="11in", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
    pg.evaluate(HIDE)
    pg.locator(".page").screenshot(path=str(HERE / "art-only.png"))
    # print PDF with 3.175 mm bleed and crop marks (sheet = trim + 2 x (9 pt bleed + 18 pt slug))
    pg2 = b.new_page(viewport={"width": 888, "height": 1128})
    pg2.goto(URL, wait_until="load"); pg2.evaluate("document.fonts.ready")
    pg2.evaluate("""() => { const s = document.createElement('style'); s.textContent = `
      html,body{background:#fff} body{width:666pt;height:846pt;position:relative}
      .page{position:absolute;left:27pt;top:27pt;overflow:visible!important}
      .page::before{content:'';position:absolute;left:-9pt;top:-9pt;width:630pt;height:810pt;background:#F2E9D6;z-index:-1}
      .cm{position:absolute;background:#000}`; document.head.appendChild(s);
      const add = (l, t, w, h) => { const d = document.createElement('div'); d.className = 'cm'; Object.assign(d.style, {left: l + 'pt', top: t + 'pt', width: w + 'pt', height: h + 'pt'}); document.body.appendChild(d); };
      for (const x of [27, 639]) { add(x - .25, 0, .5, 15); add(x - .25, 831, .5, 15); }
      for (const y of [27, 819]) { add(0, y - .25, 15, .5); add(651, y - .25, 15, .5); } }""")
    pg2.pdf(path=str(OUT / "menu-print-bleed.pdf"), width="9.25in", height="11.75in", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
    ph = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    ph.goto(URL, wait_until="load"); ph.evaluate("document.fonts.ready"); ph.evaluate("layoutMenu()")
    PH = ph.evaluate("""() => ({scrollWidth: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight,
      min_font_px: Math.min(...[...document.querySelectorAll('.tx')].filter(e => e.offsetParent !== null).map(e => parseFloat(getComputedStyle(e).fontSize))),
      pairs: [...document.querySelectorAll('.item')].map(it => { const n = it.querySelector('.name').getBoundingClientRect(), p = it.querySelector('.price').getBoundingClientRect(), c = it.getBoundingClientRect();
        return {ref: it.dataset.ref, travel_frac: (p.left - n.right) / c.width, same_row: Math.abs(n.bottom - p.bottom) < 3}; })})""")
    ph.screenshot(path=str(OUT / "preview-phone.png"), full_page=True)
    PHE = ph.evaluate("""() => [...document.querySelectorAll('.tx')].filter(e => e.offsetParent !== null).map(e => { const r = document.createRange(); r.selectNodeContents(e);
       return {text: (e.textContent||'').trim().slice(0, 40), color: (e instanceof SVGElement ? getComputedStyle(e).fill : getComputedStyle(e).color).replace('rgba','rgb'), rects: [...(e instanceof SVGElement ? [e.getBoundingClientRect()] : r.getClientRects())].filter(a => a.width > 0).map(a => [a.left, a.top + scrollY, a.width, a.height])}; })""")
    ph.evaluate(HIDE); ph.screenshot(path=str(HERE / "art-only-phone.png"), full_page=True)
    b.close()

full = Image.open(OUT / "preview-letter.png").convert("RGB"); art = Image.open(HERE / "art-only.png").convert("RGB")
S = full.size[0] / 612
DIFF = ImageChops.difference(full, art).convert('L').point(lambda v: 255 if v > 24 else 0)
# worst-pixel contrast per text element (over the art/texture only, inside the ink box of each line)
contrast = []
for e in M["els"]:
    if "line_rects" not in e: continue
    tc = rgb(e["color"]); worst = 99; wpx = None
    for x, y, w, h in e["line_rects"]:
        bb = (int(x * S), int(y * S), int(math.ceil((x + w) * S)), int(math.ceil((y + h) * S)))
        ib = DIFF.crop(bb).getbbox()  # ink box of this text line (text layer only), padded 2 px
        if ib: bb = (max(bb[0], bb[0] + ib[0] - 2), max(bb[1], bb[1] + ib[1] - 2), min(bb[2], bb[0] + ib[2] + 2), min(bb[3], bb[1] + ib[3] + 2))
        crop = art.crop(bb)
        for n, c in crop.getcolors(crop.size[0] * crop.size[1] + 1):
            r = cr(tc, c)
            if r < worst: worst, wpx = r, c
    contrast.append({"kind": e["kind"], "ref": e.get("ref"), "text": e["text"][:40], "text_rgb": tc, "worst_bg_rgb": wpx, "worst_ratio": round(worst, 2)})
ph_img = Image.open(HERE / "art-only-phone.png").convert("RGB"); ph_contrast = []
for e in PHE:
    tc = rgb(e["color"]); worst = 99
    for x, y, w, h in e["rects"]:
        crop = ph_img.crop((int(x * 3), int(y * 3), int(math.ceil((x + w) * 3)), int(math.ceil((y + h) * 3))))
        cols = crop.getcolors(crop.size[0] * crop.size[1] + 1) or []
        for n, c in cols: worst = min(worst, cr(tc, c))
    ph_contrast.append({"text": e["text"], "worst_ratio": round(worst, 2)})
# ink margins of the TEXT layer: diff (full - art-only)
d = ImageChops.difference(full, art).convert("L").point(lambda v: 255 if v > 40 else 0); bx = d.getbbox()
ink = {"left": round(bx[0] / S, 2), "top": round(bx[1] / S, 2), "right": round(612 - bx[2] / S, 2), "bottom": round(792 - bx[3] / S, 2)}
json.dump({"M": M, "PH": PH, "contrast": contrast, "phone_contrast": ph_contrast, "ink": ink, "fonts": fonts,
           "png": list(full.size), "phone_png": list(Image.open(OUT / "preview-phone.png").size)}, open(HERE / "measure.json", "w"), indent=1, ensure_ascii=False)
print("fonts", fonts, "png", full.size, "phone", Image.open(OUT / "preview-phone.png").size, PH["scrollWidth"], "ink", ink)
print("min contrast", min(contrast, key=lambda c: c["worst_ratio"]), "\nphone min", min(ph_contrast, key=lambda c: c["worst_ratio"]))
