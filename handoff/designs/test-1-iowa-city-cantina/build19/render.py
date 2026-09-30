"""Round 19 render + measured gates. Letter 2550x3300 (300 dpi), trim PDF, bleed PDF with crop marks, phone 1170 wide.
Contrast is measured at the WORST PIXEL: the page is rendered a second time with all text transparent (art + texture only),
and every text line box is scanned pixel by pixel against the text's computed colour."""
import json, math, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "round-19"
URL = (OUT / "menu.html").as_uri()
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
DSF = 3.125  # 96 css px/in * 3.125 = 300 dpi -> 2550 x 3300
PT2MM = 25.4 / 72

MEASURE = r"""() => {
 const pg = document.querySelector('.page').getBoundingClientRect(), K = 0.75;
 const rects = el => { const r = document.createRange(); r.selectNodeContents(el); return [...r.getClientRects()].filter(a => a.width > 0 && a.height > 0); };
 const tight = el => { const rs = rects(el); const x = Math.min(...rs.map(a => a.left)), y = Math.min(...rs.map(a => a.top)), R = Math.max(...rs.map(a => a.right)), B = Math.max(...rs.map(a => a.bottom));
   return {x: (x - pg.left) * K, y: (y - pg.top) * K, w: (R - x) * K, h: (B - y) * K, lines: new Set(rs.map(a => Math.round(a.top))).size,
           line_rects: rs.map(a => [(a.left - pg.left) * K, (a.top - pg.top) * K, a.width * K, a.height * K])}; };
 const box = el => { const a = el.getBoundingClientRect(); return {x: (a.left - pg.left) * K, y: (a.top - pg.top) * K, w: a.width * K, h: a.height * K}; };
 const sty = el => { const s = getComputedStyle(el); return {color: s.color, font: s.fontFamily.split(',')[0].replace(/['"]/g, ''), size_pt: parseFloat(s.fontSize) * K, weight: s.fontWeight, style: s.fontStyle, tracking_em: (parseFloat(s.letterSpacing) || 0) / parseFloat(s.fontSize)}; };
 const els = [];
 const add = (kind, el, extra = {}) => els.push(Object.assign({kind, text: el.innerText.trim().replace(/\s+/g, ' ')}, tight(el), sty(el), extra));
 add('title', document.querySelector('.wm .big'), {ref: 'title', note: 'vertical display wordmark (writing-mode vertical-rl)'});
 add('tagline', document.querySelector('.wm .small'), {ref: 'subtitle', note: 'venue line + location, vertical'});
 document.querySelectorAll('.hrow').forEach(h => { add('header', h.querySelector('h2'), {ref: h.dataset.id, column: 'full'});
   els.push(Object.assign({kind: 'divider', ref: h.dataset.id, column: 'full', note: '0.75 pt section rule'}, (b => ({x: b.x, y: b.y + b.h - 0.75, w: b.w, h: 0.75}))(box(h)))); });
 document.querySelectorAll('.sub').forEach(s => add('subheader', s.querySelector('h3'), {ref: s.dataset.id, column: 'full'}));
 const pairs = [];
 document.querySelectorAll('.item').forEach(it => { const n = it.querySelector('.name'), p = it.querySelector('.price'), d = it.querySelector('.desc') || it.querySelector('.dl'), l = it.querySelector('.lead');
   add('item_name', n, {ref: it.dataset.ref, column: 'full'}); add('price', p, {ref: it.dataset.ref, column: 'full'});
   add('description', d, {ref: it.dataset.ref, column: 'full', note: it.classList.contains('r') ? 'draft words on the name row' : 'ingredient line under the name'});
   const sv = it.querySelector('.serve'); if (sv) add('serve_label', sv, {ref: it.dataset.ref, column: 'full', note: 'glassware from phg.recipe_versions'});
   const nt = it.querySelector('.note'); if (nt) add('description', nt, {ref: it.dataset.ref, column: 'full', note: 'draft tasting note'});
   els.push(Object.assign({kind: 'leader', ref: it.dataset.ref, column: 'full', note: '1.1 pt dotted leader'}, box(l)));
   const rowEnd = it.classList.contains('r') ? tight(it.querySelector('.dl')) : tight(n);
   const nb = tight(n), pb = tight(p), cb = box(it), lb = box(l);
   pairs.push({ref: it.dataset.ref, column: 'full', name_right: nb.x + nb.w, row_text_right: rowEnd.x + rowEnd.w, price_left: pb.x, price_right: pb.x + pb.w, column_w: cb.w,
     travel_pt: pb.x - (rowEnd.x + rowEnd.w), travel_frac: (pb.x - (rowEnd.x + rowEnd.w)) / cb.w, name_to_price_frac: (pb.x - (nb.x + nb.w)) / cb.w, leader_w: lb.w,
     block_top: cb.y, block_bottom: cb.y + cb.h, name_x: nb.x}); });
 add('legal', document.querySelector('.legal'), {ref: 'allergen_line', column: 'full', note: 'generic guest allergen line'});
 // x-heights for the 1 m legibility test
 const cv = document.createElement('canvas').getContext('2d');
 const xh = el => { const s = getComputedStyle(el); cv.font = `${s.fontStyle} ${s.fontWeight} ${s.fontSize} ${s.fontFamily}`; const mx = cv.measureText('x'), mH = cv.measureText('H');
   return {size_pt: parseFloat(s.fontSize) * K, x_height_pt: mx.actualBoundingBoxAscent * K, cap_height_pt: mH.actualBoundingBoxAscent * K}; };
 const leg = {item_name: xh(document.querySelector('.name')), price: xh(document.querySelector('.price')), description: xh(document.querySelector('.desc')), subheader: xh(document.querySelector('h3')), header: xh(document.querySelector('h2')), serve_label: xh(document.querySelector('.serve')), legal: xh(document.querySelector('.legal'))};
 const art = box(document.querySelector('.art.print'));
 const secs = [...document.querySelectorAll('.menu > .sec, .menu > .legal')].map(box);
 const gaps = [...document.querySelectorAll('.sec')].map(s => { const its = [...s.querySelectorAll('.item')]; return its.slice(1).map((it, k) => (it.getBoundingClientRect().top - its[k].getBoundingClientRect().bottom) * K); });
 return {page: {w: pg.width * K, h: pg.height * K}, els, pairs, leg, art, secs, item_gaps: gaps, menu: box(document.querySelector('.menu'))};
}"""

HIDE = "document.documentElement.classList.add('notext'); const st=document.createElement('style'); st.textContent='.notext .tx,.notext .tx *{color:transparent!important}'; document.head.appendChild(st);"

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
    pg.goto(URL, wait_until="load"); pg.evaluate("document.fonts.ready")
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
    ph.goto(URL, wait_until="load"); ph.evaluate("document.fonts.ready")
    PH = ph.evaluate("""() => ({scrollWidth: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight,
      min_font_px: Math.min(...[...document.querySelectorAll('.tx')].filter(e => e.offsetParent !== null).map(e => parseFloat(getComputedStyle(e).fontSize))),
      serve_min_px: Math.min(...[...document.querySelectorAll('.serve,h3')].map(e => parseFloat(getComputedStyle(e).fontSize))),
      grid8: [...document.querySelectorAll('.wm .big,.hrow,h3,.item,.item .row,.item .desc,.item .note,.legal')].map(e => { const t = e.getBoundingClientRect().top + scrollY - document.querySelector('.page').getBoundingClientRect().top; return [e.className || e.tagName, Math.round(t * 100) / 100, Math.abs(t / 8 - Math.round(t / 8)) < 0.02]; }),
      pairs: [...document.querySelectorAll('.item')].map(it => { const n = it.querySelector('.name').getBoundingClientRect(), p = it.querySelector('.price').getBoundingClientRect(), c = it.getBoundingClientRect();
        const r = it.classList.contains('r') ? n : (it.querySelector('.name').getBoundingClientRect()); return {ref: it.dataset.ref, travel_frac: (p.left - n.right) / c.width, same_row: p.top >= n.top - 1 && p.bottom <= n.bottom + 1, leader_px: it.querySelector('.lead').getBoundingClientRect().width}; })})""")
    ph.screenshot(path=str(OUT / "preview-phone.png"), full_page=True)
    PHE = ph.evaluate("""() => [...document.querySelectorAll('.tx')].filter(e => e.offsetParent !== null).map(e => { const r = document.createRange(); r.selectNodeContents(e);
       return {text: e.innerText.trim().slice(0, 40), color: getComputedStyle(e).color.replace('rgba','rgb'), rects: [...r.getClientRects()].filter(a => a.width > 0).map(a => [a.left, a.top + scrollY, a.width, a.height])}; })""")
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
        if e["kind"] == "title": w = min(w, 276 - x)  # vertical line box overhangs into the menu column; glyph ink ends before x = 262 pt
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
