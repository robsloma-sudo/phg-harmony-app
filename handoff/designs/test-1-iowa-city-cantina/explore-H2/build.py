#!/usr/bin/env python3
"""Explore H2 - "Sun & Furrow". TEST-1 Iowa City cantina bar menu (round 2 of direction H).

The gesture is one continuous single-weight line: a plough path (boustrophedon) that runs curved
contour furrows around a terracotta sun and turns at each headland with a squared greca step. The
sun and the ploughed land are one drawing and one horizon. The furrow pitch U (12 css px) is also
the vertical unit of the reading layer (item gap = U, section gap = 3U).

The wordmark CANTINA is set in Chango (after lettering by the Mexican illustrator Ernesto "Chango"
Garcia Cabral), fitted to the full measure. Inside the sun it knocks out to cream.

Outputs: menu.html, preview-letter.png (2550x3300), preview-phone.png (1170 wide),
contrast.json (worst-pixel contrast per text run), layout.json (geometry), eye_travel.json.
"""
import glob, io, json, math, os, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFT = HERE.parent / "build" / "draft_doc.json"
FONTS = (HERE / "fonts").as_uri()

CREAM, INK, INK2, TERRA = "#F3EBDD", "#1E1A17", "#5B5149", "#A6472A"
U = 13  # furrow pitch = layout unit (css px, letter)

# ---------------------------------------------------------------- content (draft text, nothing added)
# Cocktails: full component names + garnish from phg.recipe_versions (per the Coordinator's round-2
# brief; the same garnishes appear in explore-D/variations.md from the recipe read). Manhattan's
# aromatic bitters stay hidden (public_components). Old Fashioned (house_recipe=false): names only.
DESC = {
    "beta_margarita": "Tequila blanco · fresh lime juice · orange liqueur · agave syrup · lime wheel. Bright and citrus-forward.",
    "beta_manhattan": "Rye whiskey · sweet vermouth · cocktail cherry",
    "beta_daiquiri": "White rum · fresh lime juice · demerara syrup · lime coin",
    "beta_old_fashioned": "Brown butter-washed bourbon · demerara syrup · aromatic bitters · orange peel",
    "beta_czech_pilsner": "Crisp pale lager",
    "beta_dry_hopped_ipa": "Hop-forward draft IPA",
    "beta_amber_lager": "Toasty amber lager",
    "beta_blanco_tequila": "Blanco tequila pour",
    "beta_anejo_tequila": "Añejo tequila pour",
    "beta_cognac_vsop": "VSOP Cognac pour",
    "beta_malbec": "Dry red wine",
    "beta_pinot_grigio": "Dry white wine",
    "beta_brut_rose": "Dry sparkling rosé",
    "beta_dry_cider": "Dry sparkling cider",
}
# Order (round-2 brief): Margarita first; Spirits (Agave, Brandy) before Wine. Sub heads kept.
ITEM_ORDER = {"sub_cocktails_classics": ["beta_margarita", "beta_manhattan"]}
COLUMNS = [["sec_cocktails", "sec_beer"], ["sec_spirits", "sec_wine", "sec_cider"]]


def fmt_price(v):
    return str(int(v)) if v == int(v) else f"{v:.2f}"


def load():
    doc = json.loads(DRAFT.read_text())
    secs = {s["id"]: s for s in doc["sections"]}
    seen, cols = [], []
    for ids in COLUMNS:
        blocks = []
        for sid in ids:
            s = secs[sid]
            groups = [(None, s["items"])] if s.get("items") else []
            for sub in s.get("subs", []):
                items = sub["items"]
                if sub["id"] in ITEM_ORDER:
                    by = {i["id"]: i for i in items}
                    items = [by[k] for k in ITEM_ORDER[sub["id"]]]
                    assert len(items) == len(sub["items"])
                groups.append((sub["name"], items))
            gs = []
            for name, items in groups:
                rows = []
                for it in items:
                    assert len(it["prices"]) == 1
                    seen.append(it["id"])
                    rows.append({"id": it["id"], "name": it["name"], "desc": DESC[it["id"]],
                                 "price": fmt_price(it["prices"][0]["value"])})
                gs.append({"sub": name, "rows": rows})
            blocks.append({"name": s["name"], "groups": gs})
        cols.append(blocks)
    all_ids = [i["id"] for s in doc["sections"] for i in s.get("items", [])] + \
              [i["id"] for s in doc["sections"] for sub in s.get("subs", []) for i in sub["items"]]
    assert sorted(seen) == sorted(all_ids), "item coverage mismatch"
    return cols


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;")


def menu_html(cols):
    out = []
    for i, blocks in enumerate(cols):
        out.append(f'<div class="col col{i+1}">')
        for b in blocks:
            out.append(f'<section><h2>{esc(b["name"])}</h2>')
            for g in b["groups"]:
                if g["sub"]:
                    out.append(f'<h3>{esc(g["sub"])}</h3>')
                for r in g["rows"]:
                    out.append(f'<div class="it"><p class="np"><span class="n">{esc(r["name"])}</span>'
                               f'<span class="p">{r["price"]}</span></p>'
                               f'<p class="d">{esc(r["desc"])}</p></div>')
            out.append('</section>')
        out.append('</div>')
    return "\n".join(out)


# ---------------------------------------------------------------- the gesture (one continuous line)
def art_geometry(s=1.0, ox=0.0, oy=0.0, W=816):
    """One continuous plough line. Letter-space geometry mapped by p' = (ox + x*s, oy + y*s).

    Furrow k follows the hill contour y_k(x) = Y0 + k*U - H*bump(x), bump = gaussian under the sun,
    with the pitch opening slightly over the crest (contours spread on the gentle hilltop). The line
    ploughs right->left, turns at the left headland with a squared greca hairpin, ploughs back
    left->right and turns again off the right trim (bleed). Headland turns step outward pair by pair
    (x = 88, 64, 40): the stepped fret. The sun sets behind the first furrow: the disc is clipped
    by the hill crest, so sun and land share one horizon line.
    """
    cx, cy, r = 648, 100, 170
    Y0, H, sig, n = 272, 62, 250, 6
    heads = [88, 64, 40]
    Wl = W / s if s != 1 else W   # letter-space width of this page

    def bump(x):
        return math.exp(-((x - cx) / sig) ** 2)

    def fy(k, x):
        return Y0 - H * bump(x) + k * U * (1 + 0.35 * bump(x))

    def P(x, y):
        return f"{ox + x*s:.2f},{oy + y*s:.2f}"

    xr = (W - ox) / s + 24          # right turn, beyond the trim
    d = []
    for k in range(n):
        j = k // 2
        xl = heads[j]
        xs = [xr - i * 4 for i in range(int((xr - xl) / 4) + 1)] + [xl]
        if k % 2 == 0:   # right -> left
            pts = [(x, fy(k, x)) for x in xs]
            if k == 0:
                d.append("M" + P(*pts[0]))
            else:
                d.append("L" + P(xr, fy(k, xr)))
            d.extend("L" + P(*p) for p in pts[1:])
            d.append("L" + P(xl, fy(k + 1, xl)))          # squared headland turn (greca hairpin)
        else:            # left -> right
            pts = [(x, fy(k, x)) for x in reversed(xs)]
            d.extend("L" + P(*p) for p in pts[1:])
    # hill silhouette for the sun clip: everything above furrow 0
    hill = [(x, fy(0, x)) for x in range(-40, int(xr) + 41, 4)]
    clip = "M" + P(-40, -400) + "L" + P(xr + 40, -400) + "".join("L" + P(*p) for p in reversed(hill)) + "Z"
    return {"cx": ox + cx*s, "cy": oy + cy*s, "r": r*s, "path": " ".join(d), "hill": clip,
            "bottom": oy + fy(n - 1, heads[-1])*s, "crest_y": oy + fy(0, cx)*s,
            "stroke": max(1.5, 2.2*s)}


def art_svg(g, W, H, wm_x, wm_w, wm_base):
    return f"""<svg class="art" width="{W}" height="{H}" viewBox="0 0 {W} {H}" overflow="visible">
<defs><clipPath id="hill"><path d="{g['hill']}"/></clipPath>
<clipPath id="sun"><circle cx="{g['cx']:.2f}" cy="{g['cy']:.2f}" r="{g['r']:.2f}"/></clipPath></defs>
<circle cx="{g['cx']:.2f}" cy="{g['cy']:.2f}" r="{g['r']:.2f}" fill="{TERRA}" clip-path="url(#hill)"/>
<path d="{g['path']}" fill="none" stroke="{INK}" stroke-width="{g['stroke']:.2f}" stroke-linejoin="miter" stroke-linecap="square"/>
<text class="wmk" x="{wm_x}" y="{wm_base}" textLength="{wm_w}" lengthAdjust="spacing" fill="{INK}">CANTINA</text>
<text class="wmk" x="{wm_x}" y="{wm_base}" textLength="{wm_w}" lengthAdjust="spacing" fill="{CREAM}" clip-path="url(#sun)" aria-hidden="true">CANTINA</text>
</svg>"""


LAYOUTS = {
    # letter: all four text margins 64 px (0.667 in, 16.9 mm); wordmark cap top at 64
    "letter": dict(W=816, H=1056, geom=art_geometry(), wm_x=64, wm_w=688, cap_top=64),
    # phone: top zone scaled 0.497 into a 24 px margin
    "phone": dict(W=390, H=None, geom=art_geometry(0.497, 24 - 64*0.497, 24 - 64*0.497 + 8, W=390), wm_x=24, wm_w=342, cap_top=32),
}


def build(cls, wm_size, wm_base):
    cols = load()
    L = LAYOUTS[cls]
    H = L["H"] or 1600
    art = art_svg(L["geom"], L["W"], H, L["wm_x"], L["wm_w"], wm_base)
    g = L["geom"]
    top_cols = g["bottom"] + (3*U if cls == "letter" else 58)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Cantina - bar menu (explore H2, Sun &amp; Furrow)</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@font-face{{font-family:Ch;font-weight:400;src:url({FONTS}/Chango-400.ttf)}}
@font-face{{font-family:Gd;font-weight:400;src:url({FONTS}/EBGaramond-400.ttf)}}
@font-face{{font-family:Gd;font-weight:500;src:url({FONTS}/EBGaramond-500.ttf)}}
@font-face{{font-family:Gd;font-weight:400;font-style:italic;src:url({FONTS}/EBGaramond-400i.ttf)}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{CREAM}}}
:root{{--u:{U}px}}
.page{{position:relative;overflow:hidden;background:{CREAM};color:{INK};font-family:Gd;width:{L['W']}px;height:{H}px}}
.art{{position:absolute;left:0;top:0}}
.wmk{{font-family:Ch;font-size:{wm_size:.2f}px}}
.sub{{position:absolute;font-weight:500;color:{INK2};text-transform:uppercase;white-space:nowrap}}
.col{{position:absolute;top:{top_cols:.0f}px}}
h2{{font-weight:500;color:{TERRA};text-transform:uppercase}}
h3{{font-weight:500;color:{INK2};text-transform:uppercase}}
.np{{font-weight:500}}
.p{{font-weight:400;color:{INK2};font-variant-numeric:lining-nums tabular-nums;margin-left:.9em}}
.d{{font-style:italic;color:{INK2}}}

body.letter .sub{{left:64px;top:{wm_base + 28:.0f}px;font-size:13px;letter-spacing:.28em}}
body.letter .col{{width:322px}}
body.letter .col1{{left:64px}} body.letter .col2{{left:430px}}
body.letter section+section{{margin-top:calc(var(--u)*4)}}
body.letter h2{{font-size:18px;letter-spacing:.16em;line-height:1;margin-bottom:var(--u)}}
body.letter h3{{font-size:11.5px;letter-spacing:.22em;line-height:1;margin:var(--u) 0 calc(var(--u)*.6)}}
body.letter h2+h3{{margin-top:0}}
body.letter .it{{margin-bottom:var(--u)}}
body.letter .np{{font-size:17.5px;line-height:1.2}}
body.letter .d{{font-size:13.25px;line-height:1.3}}

body.phone .sub{{left:24px;top:{g['bottom'] + 20:.0f}px;font-size:10.5px;letter-spacing:.2em}}
body.phone .col{{position:static;width:auto}}
body.phone .cols{{position:absolute;left:24px;right:24px;top:{top_cols:.0f}px}}
body.phone .col+.col{{margin-top:calc(var(--u)*3)}}
body.phone section+section{{margin-top:calc(var(--u)*3)}}
body.phone h2{{font-size:18px;letter-spacing:.16em;line-height:1;margin-bottom:var(--u)}}
body.phone h3{{font-size:11.5px;letter-spacing:.22em;line-height:1;margin:var(--u) 0 calc(var(--u)*.6)}}
body.phone h2+h3{{margin-top:0}}
body.phone .it{{margin-bottom:var(--u)}}
body.phone .np{{font-size:17px;line-height:1.2}}
body.phone .d{{font-size:14px;line-height:1.3}}
</style></head>
<body class="{cls}"><div class="page">
{art}
<h1 class="sr">CANTINA</h1>
<p class="sub">&amp; cocktail bar &#183; Iowa City, Iowa</p>
<div class="cols">
{menu_html(cols)}
</div>
</div></body></html>""".replace('<h1 class="sr">CANTINA</h1>', '<h1 style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">Cantina</h1>')


FIT_JS = """(w) => { const c=document.createElement('canvas').getContext('2d'); c.font='100px Ch';
  const m=c.measureText('CANTINA'); return {w100:m.width, asc100:m.actualBoundingBoxAscent}; }"""

CONTRAST_JS = """() => { const out=[]; const walker=document.createTreeWalker(document.querySelector('.page'),NodeFilter.SHOW_TEXT);
  let n; while(n=walker.nextNode()){ if(!n.textContent.trim()) continue; const el=n.parentElement;
    if(el.closest('svg')||el.tagName==='H1') continue;
    const r=document.createRange(); r.selectNodeContents(n); for(const b of r.getClientRects()){
      if(b.width<1) continue; out.push({t:n.textContent.trim().slice(0,40),c:getComputedStyle(el).color,
      role:el.className||el.tagName,x:b.x,y:b.y,w:b.width,h:b.height});}}
  return out;}"""

GEOM_JS = """() => { const q=s=>[...document.querySelectorAll(s)].map(e=>{const b=e.getBoundingClientRect();
  return {sel:s,text:(e.textContent||'').trim().slice(0,30),x:+b.left.toFixed(1),y:+b.top.toFixed(1),w:+b.width.toFixed(1),h:+b.height.toFixed(1)}});
  const W=document.querySelector('.page').getBoundingClientRect().width;
  const travel=[...document.querySelectorAll('.np')].map(e=>{const n=e.querySelector('.n').getBoundingClientRect(),
    p=e.querySelector('.p').getBoundingClientRect(); return {item:e.querySelector('.n').textContent,
    gap_px:+(p.left-n.right).toFixed(1), name_start_to_price_end_pct:+(100*(p.right-n.left)/W).toFixed(1),
    gap_pct:+(100*(p.left-n.right)/W).toFixed(2)}});
  const ext=(()=>{let x0=1e9,y0=1e9,x1=0,y1=0;document.querySelectorAll('.sub,.col,.wmk').forEach(e=>{const b=e.getBoundingClientRect();
      x0=Math.min(x0,b.left);y0=Math.min(y0,b.top);x1=Math.max(x1,b.right);y1=Math.max(y1,b.bottom)});return [x0,y0,x1,y1]})();
  return {page:q('.page')[0],wordmark:q('.wmk')[0],sub:q('.sub')[0],columns:q('.col'),section_heads:q('h2'),
    sub_heads:q('h3'),items:q('.it'),text_extent:ext,eye_travel:travel} }"""


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast_check(page, scale):
    from PIL import Image
    boxes = page.evaluate(CONTRAST_JS)
    page.add_style_tag(content=".page p, .page h2, .page h3, .page span{color:transparent !important}")
    img = Image.open(io.BytesIO(page.screenshot(full_page=True))).convert("RGB")
    res = []
    for b in boxes:
        rgb = tuple(int(float(v)) for v in re.findall(r"[\d.]+", b["c"])[:3])
        L1 = lum(rgb)
        x0, y0 = max(0, int(b["x"] * scale)), max(0, int(b["y"] * scale))
        x1, y1 = min(img.width, int((b["x"] + b["w"]) * scale)), min(img.height, int((b["y"] + b["h"]) * scale))
        worst = 99
        for px in set(img.crop((x0, y0, x1, y1)).getdata()):
            worst = min(worst, (max(L1, lum(px)) + 0.05) / (min(L1, lum(px)) + 0.05))
        res.append({"text": b["t"], "role": b["role"], "min": round(worst, 2)})
    res.sort(key=lambda r: r["min"])
    return res


def main():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    report, layout = {}, {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")))
        for name, cls, w, dsf in [("preview-letter.png", "letter", 816, 3.125), ("preview-phone.png", "phone", 390, 3)]:
            L = LAYOUTS[cls]
            pg = b.new_page(viewport={"width": w, "height": 1056 if cls == "letter" else 844}, device_scale_factor=dsf)
            tmp = HERE / f".render-{cls}.html"
            # pass 1: measure Chango, fit CANTINA to the measure with ~3% added spacing
            tmp.write_text(build(cls, 100, 200))
            pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
            m = pg.evaluate(FIT_JS)
            size = 100 * L["wm_w"] / (m["w100"] * 1.03)
            base = L["cap_top"] + m["asc100"] * size / 100
            html = build(cls, size, base)
            if cls == "letter":
                (HERE / "menu.html").write_text(html)
            tmp.write_text(html)
            pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
            if cls == "phone":
                bottom = pg.evaluate("() => document.querySelector('.cols').getBoundingClientRect().bottom")
                pg.evaluate(f"() => {{document.querySelector('.page').style.height='{int(bottom + 24)}px'}}")
            layout[name] = pg.evaluate(GEOM_JS)
            layout[name]["wordmark_font_px"] = round(size, 2)
            layout[name]["art"] = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in L["geom"].items() if k != "path"}
            pg.screenshot(path=str(HERE / name), full_page=True)
            report[name] = contrast_check(pg, dsf)
            tmp.unlink()
            pg.close()
        b.close()
    (HERE / "contrast.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (HERE / "layout.json").write_text(json.dumps(layout, indent=1, ensure_ascii=False))
    for k, v in report.items():
        print(k, "worst:", v[:2])
    for k, v in layout.items():
        et = v["eye_travel"]
        print(k, "text extent:", v["text_extent"], "max eye travel %:", max(e["name_start_to_price_end_pct"] for e in et),
              "cols:", [(c["y"], round(c["y"] + c["h"])) for c in v["columns"]], "art bottom:", v["art"]["bottom"])


if __name__ == "__main__":
    main()
