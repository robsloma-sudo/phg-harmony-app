"""K1 render + measured gates (technique from build20b/render.py: Playwright + Chromium, 300 dpi letter,
1170-wide phone, bleed PDF with crop marks, worst-pixel contrast against a text-free render)."""
import json, math, pathlib, re, sys
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

HERE = pathlib.Path(__file__).resolve().parent
URL = (HERE / "menu.html").as_uri()
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
DSF = 3.125  # 816 css px * 3.125 = 2550 px
PAPER = "#F4EFE4"

HIDE = ("const st=document.createElement('style');st.id='hide';st.textContent='.tx,.tx *{color:transparent!important;-webkit-text-stroke:0!important}';"
        "document.head.appendChild(st);")
UNHIDE = "document.getElementById('hide').remove();"

# every text element (.tx): per text-node line rects, colour, size
TEXTS = r"""(sel) => {
 const pg = document.querySelector(sel); const P = pg.getBoundingClientRect();
 const out = [];
 pg.querySelectorAll('.tx').forEach(el => {
   if (!el.offsetParent) return;
   if (el.querySelector('.tx')) return;  // leaf .tx only
   const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const rects = []; let n;
   while ((n = w.nextNode())) { if (!n.textContent.trim()) continue; const r = document.createRange(); r.selectNodeContents(n);
     for (const a of r.getClientRects()) if (a.width > 0 && a.height > 0) rects.push([a.left - P.left, a.top - P.top + (sel === 'body' ? scrollY : 0), a.width, a.height]); }
   const s = getComputedStyle(el);
   out.push({text: el.innerText.trim().replace(/\s+/g, ' '), cls: el.className, color: s.color, size_px: parseFloat(s.fontSize), rects});
 });
 return out;
}"""

CONTENT = r"""(sel) => {
 const root = document.querySelector(sel); const P = root.getBoundingClientRect();
 const t = (e) => e ? e.innerText.trim().replace(/\s+/g, ' ') : null;
 const items = [...root.querySelectorAll('[data-name]')].filter(e => e.offsetParent).map(it => {
   const nm = it.querySelector('.nm'), pr = it.querySelector('.pr');
   const tr = e => { const r = document.createRange(); r.selectNodeContents(e); return [...r.getClientRects()].filter(a => a.width > 0); };
   const rs = tr(nm); const last = rs[rs.length - 1]; const prr = tr(pr)[0];
   const fs = parseFloat(getComputedStyle(nm).fontSize);
   return {name: t(nm), price: t(pr), status: it.dataset.status, table: it.classList.contains('tr'),
     sensory: t(it.querySelector('.sd,.ssd')), ingredients: t(it.querySelector('.ig')), garnish: t(it.querySelector('.gar')), glass: t(it.querySelector('.gls')),
     ring: !!it.querySelector('.ring'), cls: t(it.querySelector('.c-cl')), nom: t(it.querySelector('.c-nom')), region: t(it.querySelector('.c-rg')),
     oak: (it.querySelector('.oak[data-oak]') || {dataset: {}}).dataset.oak || null, glyph: !!it.querySelector('svg.gl'),
     gar_in_ig: !!(it.querySelector('.ig') && it.querySelector('.gar') && it.querySelector('.ig').contains(it.querySelector('.gar'))),
     gap_em: (prr.left - last.right) / fs, same_line: Math.abs(prr.bottom - last.bottom) < fs * 0.5,
     price_right: prr.right - P.left, name_font_px: fs};
 });
 const heads = [...root.querySelectorAll('h2,h3')].filter(e => e.offsetParent).map(h => t(h));
 const gsd = [...root.querySelectorAll('.gsd')].map(e => ({group: t(e.parentElement.querySelector('h3')), sensory: t(e)}));
 const alltext = root.innerText;
 const furrows = [...root.querySelectorAll('.fwl')].length;
 const art = [...root.querySelectorAll('svg.field, svg.bfield')].filter(e => e.offsetParent !== null || getComputedStyle(e).display !== 'none').map(e => { const r = e.getBoundingClientRect(); return [r.left - P.left, r.top - P.top, r.right - P.left, r.bottom - P.top]; });
 const leg = root.querySelector('.legend'); const legTop = leg ? leg.getBoundingClientRect().top - P.top : null;
 const menuBottom = Math.max(...[...root.querySelectorAll('.menu .tx')].filter(e => e.offsetParent).map(e => e.getBoundingClientRect().bottom - P.top));
 const rings = [...root.querySelectorAll('.ring:not(.k)')].filter(e => e.offsetParent).map(e => e.getBoundingClientRect().left - P.left);
 return {items, heads, gsd, alltext, furrows, art, legTop, menuBottom, rings_min_left: rings.length ? Math.min(...rings) : null};
}"""

def lum(c):
    f = lambda v: (v / 255) / 12.92 if v / 255 <= 0.04045 else (((v / 255) + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])
def cr(a, b):
    la, lb = lum(a), lum(b); return (max(la, lb) + .05) / (min(la, lb) + .05)
def rgb(s):
    v = s[s.index("(") + 1:s.index(")")].split(","); return tuple(int(float(x)) for x in v[:3])

def contrast(full, art, texts, S):
    diff = ImageChops.difference(full, art).convert('L').point(lambda v: 255 if v > 24 else 0)
    res = []
    for e in texts:
        tc = rgb(e["color"]); worst, wpx = 99, None
        for x, y, w, h in e["rects"]:
            bb = (int(x * S), int(y * S), int(math.ceil((x + w) * S)), int(math.ceil((y + h) * S)))
            ib = diff.crop(bb).getbbox()
            if not ib: continue
            bb = (max(bb[0], bb[0] + ib[0] - 2), max(bb[1], bb[1] + ib[1] - 2), min(bb[2], bb[0] + ib[2] + 2), min(bb[3], bb[1] + ib[3] + 2))
            crop = art.crop(bb)
            for n, c in crop.getcolors(crop.size[0] * crop.size[1] + 1):
                r = cr(tc, c)
                if r < worst: worst, wpx = r, c
        res.append({"text": e["text"][:48], "cls": e["cls"], "size_px": e["size_px"], "text_rgb": tc, "worst_bg_rgb": wpx, "worst_ratio": round(worst, 2)})
    return res

def ink_margins(full, art, S, W=612, H=792):
    d = ImageChops.difference(full, art).convert("L").point(lambda v: 255 if v > 40 else 0); bx = d.getbbox()
    return {"left": round(bx[0] / S, 2), "top": round(bx[1] / S, 2), "right": round(W - bx[2] / S, 2), "bottom": round(H - bx[3] / S, 2)}

def run():
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME)
        pg = b.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=DSF)
        pg.goto(URL, wait_until="load"); pg.wait_for_function("document.documentElement.dataset.laid === '1'")
        out["fonts_loaded"] = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family+' '+f.weight+' '+f.style)")
        for side in ("front", "back"):
            sel = f".page.{side}"
            pg.locator(sel).screenshot(path=str(HERE / f"preview-{side}.png"))
            out[f"{side}_texts"] = pg.evaluate(TEXTS, sel)
            out[f"{side}_content"] = pg.evaluate(CONTENT, sel)
        pg.evaluate(HIDE)
        for side in ("front", "back"):
            pg.locator(f".page.{side}").screenshot(path=str(HERE / f"_art-{side}.png"))
        pg.evaluate(UNHIDE)
        # print PDF: each page = trim 612x792 + 9 pt bleed + 18 pt slug, crop marks
        pg2 = b.new_page(viewport={"width": 888, "height": 1128})
        pg2.goto(URL, wait_until="load"); pg2.wait_for_function("document.documentElement.dataset.laid === '1'")
        pg2.evaluate("""() => { const s = document.createElement('style'); s.textContent = `
          @page{size:666pt 846pt;margin:0}
          html,body{background:#fff}
          .sheet{position:relative;width:666pt;height:846pt;break-after:page;overflow:hidden}
          .sheet .page{position:absolute;left:27pt;top:27pt;margin:0;overflow:visible!important}
          .sheet .page::before{content:'';position:absolute;left:-9pt;top:-9pt;width:630pt;height:810pt;background:%s;z-index:-1}
          .cm{position:absolute;background:#000}`; document.head.appendChild(s);
          document.querySelectorAll('.page').forEach(p => { const sh = document.createElement('div'); sh.className = 'sheet'; p.parentNode.insertBefore(sh, p); sh.appendChild(p);
            const bg = document.createElement('div'); Object.assign(bg.style, {position: 'absolute', left: '18pt', top: '18pt', width: '630pt', height: '810pt', background: '#F4EFE4'}); sh.insertBefore(bg, p);
            const add = (l, t, w, h) => { const d = document.createElement('div'); d.className = 'cm'; Object.assign(d.style, {left: l + 'pt', top: t + 'pt', width: w + 'pt', height: h + 'pt'}); sh.appendChild(d); };
            for (const x of [27, 639]) { add(x - .25, 0, .5, 15); add(x - .25, 831, .5, 15); }
            for (const y of [27, 819]) { add(0, y - .25, 15, .5); add(651, y - .25, 15, .5); } });
          furrows(); }""" % PAPER)
        pg2.pdf(path=str(HERE / "menu-print-bleed.pdf"), width="9.25in", height="11.75in", print_background=True, prefer_css_page_size=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        # phone
        ph = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
        ph.goto(URL, wait_until="load"); ph.wait_for_function("document.documentElement.dataset.laid === '1'")
        ph.evaluate("furrows()")
        out["phone_scroll_width"] = ph.evaluate("document.documentElement.scrollWidth")
        out["phone_height"] = ph.evaluate("document.documentElement.scrollHeight")
        out["phone_texts"] = ph.evaluate(TEXTS, "body")
        out["phone_content"] = ph.evaluate(CONTENT, "body")
        ph.screenshot(path=str(HERE / "preview-phone.png"), full_page=True)
        ph.evaluate(HIDE); ph.screenshot(path=str(HERE / "_art-phone.png"), full_page=True)
        b.close()
    S = 2550 / 612
    for side in ("front", "back"):
        full = Image.open(HERE / f"preview-{side}.png").convert("RGB"); art = Image.open(HERE / f"_art-{side}.png").convert("RGB")
        # texts rects are in css px; S_css = 2550/816
        out[f"{side}_contrast"] = contrast(full, art, out[f"{side}_texts"], 2550 / 816)
        out[f"{side}_ink_margins_pt"] = ink_margins(full, art, S)
        out[f"{side}_png"] = list(full.size)
    full = Image.open(HERE / "preview-phone.png").convert("RGB"); art = Image.open(HERE / "_art-phone.png").convert("RGB")
    out["phone_contrast"] = contrast(full, art, out["phone_texts"], 3)
    out["phone_png"] = list(full.size)
    return out

if __name__ == "__main__":
    r = run()
    json.dump(r, open(HERE / "_measure.json", "w"), ensure_ascii=False, indent=1)
    for side in ("front", "back", "phone"):
        c = min(r[f"{side}_contrast"], key=lambda c: c["worst_ratio"])
        print(side, "min contrast", c)
    print(r["front_ink_margins_pt"], r["back_ink_margins_pt"], r["front_png"], r["back_png"], r["phone_png"], r["phone_scroll_width"])
