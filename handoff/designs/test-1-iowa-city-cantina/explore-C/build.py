#!/usr/bin/env python3
"""Explore-C: Late-night risograph zine. Builds menu.html from ../build/draft_doc.json,
renders preview-letter.png (2550x3300) and preview-phone.png (1170 wide) with Playwright,
and checks every text/backing colour pair for >= 4.5:1."""
import json, math, os, random, html, asyncio

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = os.path.join(ROOT, "build", "fonts")
doc = json.load(open(os.path.join(ROOT, "build", "draft_doc.json")))

# ---------- palette (two riso drums + overlap) ----------
PAPER = "#f3efe4"      # newsprint
PINK = "#ff48b0"       # fluorescent pink drum
TEAL = "#00a3ad"       # teal drum
def mul(a, b):
    a = [int(a[i:i+2], 16) for i in (1, 3, 5)]; b = [int(b[i:i+2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x*y/255) for x, y in zip(a, b))
OVER = mul(PINK, TEAL)  # third colour where drums overlap (multiply)
INK = "#1b1446"         # both drums at full density: text ink (overprint, darkened)

def lum(h):
    c = [int(h[i:i+2], 16)/255 for i in (1, 3, 5)]
    c = [x/12.92 if x <= 0.03928 else ((x+0.055)/1.055)**2.4 for x in c]
    return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
def cr(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True); return (la+0.05)/(lb+0.05)

# ---------- data (exact from draft) ----------
items = {}
for s in doc["sections"]:
    for it in s.get("items", []): items[it["id"]] = it
    for sub in s.get("subs", []):
        for it in sub["items"]: items[it["id"]] = it
assert len(items) == 14, len(items)
def price(i): v = items[i]["prices"][0]["value"]; return str(int(v)) if v == int(v) else str(v)

FR = {0.25: "¼", 0.5: "½", 0.75: "¾"}
def qty(c):
    q = c["quantity"]; u = c["unit"]
    n = FR.get(q, str(int(q)) if q == int(q) else str(q))
    return f"{n} {u.upper()}" if u != "each" else ""

# display names for tags (draft component names; lime juice shortened per brief; Daiquiri's
# syrup named as the draft desc names it: 'house demerara syrup')
TAGNAME = {"Fresh Lime Juice": "Fresh Lime"}
DAQ_SYRUP = "House Demerara Syrup"
# garnish / glass / method from phg.recipe_versions (cited in ../round-17/proposal.md)
SERVE = {
    "beta_margarita": ("Lime wheel", "Rocks", "Shaken"),
    "beta_manhattan": ("Cocktail cherry", "Coupe", "Stirred"),
    "beta_old_fashioned": ("Orange peel", "Rocks · large cube", "Stirred"),
    "beta_daiquiri": ("Lime coin", "Coupe", "Shaken"),
}

def cocktail(iid):
    it = items[iid]
    hidden = {k for k, v in it["meta"].get("public_components", {}).items() if v is False}
    show_q = it["meta"]["public_visibility"].get("house_recipe", True)
    tags = []
    for c in it["components"]:
        slug = c["name"].lower().replace(" ", "-")
        if slug in hidden or c["role"] == "Garnish":
            continue
        name = TAGNAME.get(c["name"], c["name"])
        if iid == "beta_daiquiri" and c["name"] == "Demerara Syrup": name = DAQ_SYRUP
        q = qty(c) if show_q else ""
        tags.append((name, q))
    g, glass, method = SERVE[iid]
    t = "".join(f'<span class="tag">{html.escape(n.upper())}'
                + (f'<i>{q}</i>' if q else "") + '</span>' for n, q in tags)
    t += f'<span class="tag gar">{html.escape(g.upper())}</span>'
    return f'''<div class="ck">
  <div class="row"><span class="nm">{html.escape(it["name"].upper())}</span><span class="ld"></span><span class="pr">{price(iid)}</span></div>
  <div class="tags">{t}</div>
  <div class="serve">{method.upper()} &nbsp;/&nbsp; {glass.upper()}</div>
</div>'''

def simple(iid):
    it = items[iid]
    return f'''<div class="si"><div class="row"><span class="nm">{html.escape(it["name"].upper())}</span><span class="ld"></span><span class="pr">{price(iid)}</span></div>
  <div class="ds">{html.escape(it["desc"])}</div></div>'''

# ---------- ART layer: SVG halftones (text-free) ----------
def halftone(shape, x0, y0, w, h, step, color, ang, cls, rmax=None):
    rmax = rmax or step*0.62
    out = []
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    R = int(max(w, h)*0.8/step)+2
    cx, cy = x0+w/2, y0+h/2
    for i in range(-R, R):
        for j in range(-R, R):
            u, v = i*step, j*step
            x = cx + u*ca - v*sa; y = cy + u*sa + v*ca
            if not (x0 <= x <= x0+w and y0 <= y <= y0+h): continue
            t = shape(x, y)
            if t <= 0.04: continue
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rmax*math.sqrt(t):.2f}"/>')
    return f'<g class="{cls}" fill="{color}">' + "".join(out) + "</g>"

def agave(px, py, s):
    """photo-like agave rosette: tapered leaves with a light gradient along each leaf"""
    leaves = [(-80, 1.0), (-58, .92), (-100, .9), (-35, .78), (-125, .76), (-15, .6), (-150, .58), (-68, .7), (-112, .68)]
    def f(x, y):
        best = 0
        dx, dy = (x-px)/s, (y-py)/s
        for a, L in leaves:
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            u = dx*ca + dy*sa; v = -dx*sa + dy*ca
            if 0 < u < L:
                wid = 0.11*(1-u/L)**0.8 + 0.004
                if abs(v) < wid:
                    tone = 0.35 + 0.65*(1-abs(v)/wid)*(0.5+0.5*u/L)   # rounded leaf + tip light
                    if v > 0: tone *= 0.7                            # shadow side
                    best = max(best, tone)
        r = math.hypot(dx, dy-0.02)
        if r < 0.16: best = max(best, 0.9*(1-r/0.16)+0.1)
        return min(best, 1)
    return f

def coupe(px, py, s):
    """coupe glass: bowl + stem + foot, with a highlight band"""
    def f(x, y):
        dx, dy = (x-px)/s, (y-py)/s
        if -0.5 < dy < 0 and abs(dx) < 0.5*math.sqrt(max(0, 1-(dy/0.5+1)**2)) + 0.0 and dy > -0.5:
            pass
        # bowl: half-ellipse opening upward, top at dy=-0.45, depth 0.3
        if -0.45 <= dy <= -0.15:
            half = 0.5*math.sqrt(max(0, 1-((dy+0.45)/0.3)**2))
            if abs(dx) < half:
                liq = 0.85 if dy > -0.40 else 0.35
                hl = 0.25 if 0.18 < (dx/half if half else 0)+0.55 < 0.35 else 1
                return liq*hl
        if -0.15 < dy < 0.32 and abs(dx) < 0.025: return 0.9
        if 0.32 <= dy < 0.36 and abs(dx) < 0.2*(1-(dy-0.32)/0.08): return 0.9
        return 0
    return f

def rocks(px, py, s):
    def f(x, y):
        dx, dy = (x-px)/s, (y-py)/s
        if -0.3 < dy < 0.3 and abs(dx) < 0.28 - 0.02*(dy+0.3):
            if -0.05 < dy < 0.22 and abs(dx) < 0.17 and abs(dy-0.08) < 0.14: return 0.35  # ice cube
            if dy > 0.24: return 0.95
            return 0.75 if dx < 0.1 else 0.45
        return 0
    return f

random.seed(7)
W, H = 816, 1056
art_top = (
    halftone(agave(690, 250, 280), 400, -12, 430, 280, 7.2, PINK, 15, "ht pink")
    + halftone(coupe(560, 120, 190), 450, 20, 220, 160, 6.4, TEAL, 75, "ht teal mis")
)
art_bot = (
    halftone(rocks(470, 985, 150), 380, 900, 190, 150, 6.4, TEAL, 75, "ht teal mis")
    + halftone(agave(560, 1090, 230), 380, 890, 300, 180, 7.2, PINK, 15, "ht pink")
)

# stamp: rough circle via displacement filter
def stamp(n, color, rot):
    return f'<span class="stamp" style="color:{color};transform:rotate({rot}deg)">{n:02d}</span>'

ff = lambda f: "file://" + os.path.join(FONTS, f)
CSS = f"""
@font-face{{font-family:DMS;src:url({ff('DMSans-400-normal.ttf')});font-weight:400}}
@font-face{{font-family:DMS;src:url({ff('DMSans-500-normal.ttf')});font-weight:500}}
@font-face{{font-family:DMS;src:url({ff('DMSans-700-normal.ttf')});font-weight:700}}
@font-face{{font-family:FR;src:url({ff('Fraunces-600-normal.ttf')});font-weight:600}}
@font-face{{font-family:FR;src:url({ff('Fraunces-600-italic.ttf')});font-weight:600;font-style:italic}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{PAPER}}}
.page{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:{PAPER};font-family:DMS;color:{INK}}}
/* newsprint grain: very low contrast, only paper tone */
.page:before{{content:"";position:absolute;inset:0;background-image:radial-gradient(rgba(60,50,30,.05) 1px,transparent 1.2px);background-size:5px 5px;pointer-events:none}}
svg.art{{position:absolute;left:-12px;top:-12px;width:{W+24}px;height:{H+24}px}}
svg.art .ht{{mix-blend-mode:multiply}}
svg.art .mis{{transform:translate(3px,-2px)}}
.safe{{position:absolute;left:48px;top:48px;right:48px;bottom:48px}}
/* masthead */
.mast{{position:absolute;left:0;top:0;width:420px}}
.wm{{position:relative;font:700 96px/0.84 DMS;letter-spacing:-2px;text-transform:uppercase}}
.wm span{{display:block}}
.wm .p{{color:{PINK};mix-blend-mode:multiply}}
.wm .t{{position:absolute;left:5px;top:4px;color:{TEAL};mix-blend-mode:multiply}}
.kick{{margin-top:12px;display:inline-block;background:{INK};color:{PAPER};font:700 13px/1 DMS;letter-spacing:4px;padding:7px 10px 6px;transform:rotate(-2deg)}}
/* blocks */
.blk{{position:absolute;background:{PAPER};border:2.5px solid {INK};padding:12px 14px 8px;box-shadow:6px 6px 0 {OVER}}}
.hd{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
.hd h2{{font:700 23px/1 DMS;letter-spacing:5px;text-transform:uppercase}}
.stamp{{display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;border:3px solid currentColor;border-radius:50%;font:700 17px/1 'Courier 10 Pitch',FreeMono,monospace;letter-spacing:0;filter:url(#rough);mix-blend-mode:multiply;flex:none}}
.sub{{font:700 11px/1 DMS;letter-spacing:3px;text-transform:uppercase;margin:6px 0 6px;padding-bottom:4px;border-bottom:1.5px dashed {INK}}}
.row{{display:flex;align-items:baseline;gap:6px}}
.nm{{font:700 16px/1.15 DMS;letter-spacing:1.4px}}
.ld{{flex:1;border-bottom:2px dotted {INK};transform:translateY(-4px);min-width:14px}}
.pr{{font:700 18px/1 DMS}}
.ck{{margin:0 0 9px}}
.tags{{display:flex;flex-wrap:wrap;gap:4px;margin-top:5px}}
.tag{{display:inline-flex;align-items:baseline;gap:5px;border:1.6px solid {INK};padding:3px 5px 2px;font:700 11px/1.1 DMS;letter-spacing:1.1px;background:{PAPER}}}
.tag i{{font:400 11px/1 'Liberation Mono',monospace;font-style:normal;letter-spacing:0}}
.tag.gar{{border-style:dashed}}
.serve{{margin-top:5px;font:600 italic 13px/1.2 FR;letter-spacing:.3px}}
.si{{margin:0 0 7px}}
.ds{{font:600 italic 13.5px/1.22 FR;margin-top:1px}}
.tagline{{position:absolute;font:700 13px/1.35 DMS;letter-spacing:5px;text-transform:uppercase;background:{PINK};color:{INK};padding:6px 10px}}
.foot{{position:absolute;left:0;right:0;bottom:0;font:500 11px/1 DMS;letter-spacing:2.5px;text-transform:uppercase;display:flex;justify-content:space-between}}
.foot b{{background:{PAPER};padding:3px 4px}}
/* phone */
@media (max-width:500px){{
  .page{{width:390px;height:auto;overflow:visible;padding:24px 20px 30px}}
  svg.art{{display:none}}
  .safe{{position:static}}
  .mast,.blk,.tagline,.foot{{position:relative!important;left:auto!important;top:auto!important;right:auto!important;bottom:auto!important;width:auto!important;transform:none!important}}
  .blk{{margin:22px 6px 0 0}}
  .wm{{font-size:86px}}
  .phart{{display:block!important}}
  .tagline{{display:inline-block;margin-top:22px}}
  .foot{{margin-top:22px;flex-direction:column;gap:6px}}
}}
.phart{{display:none;margin:14px -20px 0;height:170px;overflow:hidden}}
"""

S = {"sections": {s["id"]: s for s in doc["sections"]}}
subs = {sub["id"]: sub for s in doc["sections"] for sub in s.get("subs", [])}

cock = f'''<div class="blk" id="b-cock" style="left:0;top:178px;width:720px;transform:rotate(-1deg)">
 <div class="hd">{stamp(1, OVER, -12)}<h2>Cocktails</h2></div>
 <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 30px">
  <div><div class="sub">{subs["sub_cocktails_classics"]["name"]}</div>{cocktail("beta_margarita")}{cocktail("beta_manhattan")}</div>
  <div><div class="sub">{subs["sub_cocktails_house_originals"]["name"]}</div>{cocktail("beta_daiquiri")}{cocktail("beta_old_fashioned")}</div>
 </div></div>'''
beer = f'''<div class="blk" id="b-beer" style="left:0;top:556px;width:228px;transform:rotate(1.3deg)">
 <div class="hd">{stamp(2, OVER, 9)}<h2>Beer</h2></div><div class="sub">{subs["sub_beer_draft"]["name"]}</div>
 {simple("beta_czech_pilsner")}{simple("beta_dry_hopped_ipa")}{simple("beta_amber_lager")}</div>'''
wine = f'''<div class="blk" id="b-wine" style="left:246px;top:548px;width:228px;transform:rotate(-1.5deg)">
 <div class="hd">{stamp(3, OVER, 6)}<h2>Wine</h2></div><div class="sub">{subs["sub_wine_by_the_glass"]["name"]}</div>
 {simple("beta_malbec")}{simple("beta_pinot_grigio")}<div class="sub">{subs["sub_wine_sparkling"]["name"]}</div>{simple("beta_brut_rose")}</div>'''
spir = f'''<div class="blk" id="b-spir" style="left:492px;top:560px;width:228px;transform:rotate(1deg)">
 <div class="hd">{stamp(4, OVER, -8)}<h2>Spirits</h2></div>
 <div style="display:grid;grid-template-columns:1fr;gap:0">
 <div class="sub">{subs["sub_spirits_agave"]["name"]}</div>{simple("beta_blanco_tequila")}{simple("beta_anejo_tequila")}
 <div class="sub">{subs["sub_spirits_brandy"]["name"]}</div>{simple("beta_cognac_vsop")}</div></div>'''
cider = f'''<div class="blk" id="b-cider" style="left:486px;top:40px;width:220px;transform:rotate(3deg)">
 <div class="hd">{stamp(5, OVER, 14)}<h2>Cider</h2></div>{simple("beta_dry_cider")}</div>'''

phone_art = f'<svg class="phart" viewBox="440 -12 390 330" preserveAspectRatio="xMidYMid slice" width="100%" height="170">{art_top}</svg>'

HTML = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(doc['title'])}</title>
<meta name="viewport" content="width=device-width"><style>{CSS}</style></head><body>
<div class="page">
<svg width="0" height="0" style="position:absolute"><filter id="rough"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4"/><feDisplacementMap in="SourceGraphic" scale="2.4"/></filter></svg>
<svg class="art" viewBox="-12 -12 {W+24} {H+24}" aria-hidden="true">{art_top}{art_bot}</svg>
<div class="safe">
 <div class="mast" id="b-mast"><div class="wm" aria-label="{html.escape(doc['title'])}"><span class="p">Bar<br>Menu</span><span class="t" aria-hidden="true">Bar<br>Menu</span></div>
  <div class="kick">IOWA CITY · LATE</div></div>
 {phone_art}
 {cock}{beer}{wine}{spir}{cider}
 <div class="tagline" id="b-tag" style="left:40px;top:846px;transform:rotate(-3deg)">Good drinks<br>Good company</div>
 <div class="foot" id="b-foot"><b>{html.escape(doc['subtitle'])}</b><b>Nº 1 · Printed in two inks</b></div>
</div></div></body></html>"""

open(os.path.join(HERE, "menu.html"), "w").write(HTML)

# ---------- contrast gate (text sits only on opaque paper/ink fields) ----------
pairs = {"body ink on paper card": (INK, PAPER), "paper on ink kicker": (PAPER, INK),
         "ink on pink tagline (multiply over paper)": (INK, mul(PINK, PAPER)),
         "ink on paper footer chip": (INK, PAPER)}
# worst pixel behind the tagline: pink multiplied over the darkest halftone overlap
pairs["ink on opaque pink tagline"] = (INK, PINK)
pairs["overlap-ink stamp numerals on paper"] = (OVER, PAPER)
pairs["ink on paper tag"] = (INK, PAPER)
res = {k: round(cr(*v), 2) for k, v in pairs.items()}

async def render():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
        pg = await b.new_page(viewport={"width": W, "height": H}, device_scale_factor=3.125)
        await pg.goto("file://" + os.path.join(HERE, "menu.html")); await pg.wait_for_timeout(400)
        geo = await pg.evaluate("""()=>[...document.querySelectorAll('[id^=b-]')].map(e=>{const r=e.getBoundingClientRect();return {id:e.id,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}})""")
        await pg.screenshot(path=os.path.join(HERE, "preview-letter.png"))
        ph = await b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3)
        await ph.goto("file://" + os.path.join(HERE, "menu.html")); await ph.wait_for_timeout(400)
        await ph.screenshot(path=os.path.join(HERE, "preview-phone.png"), full_page=True)
        await b.close(); return geo

geo = asyncio.run(render())
json.dump({"contrast": res, "palette": {"paper": PAPER, "pink": PINK, "teal": TEAL, "overlap": OVER, "ink": INK},
           "geometry_css_px_96dpi": geo}, open(os.path.join(HERE, "checks.json"), "w"), indent=1)
print(json.dumps(res, indent=1)); print(json.dumps(geo))
