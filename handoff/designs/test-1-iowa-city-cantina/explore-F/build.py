"""Explore-F: IMMERSIVE NIGHT SCENE. Builds menu.html from ../build/draft_doc.json, renders letter + phone PNGs,
checks item/price parity and contrast (declared backing colours + worst sampled pixel inside every text box)."""
import json, math, pathlib, random
from playwright.sync_api import sync_playwright
from PIL import Image

HERE = pathlib.Path(__file__).parent
DRAFT = json.loads((HERE.parent / "build" / "draft_doc.json").read_text())
FONTS = (HERE.parent / "build" / "fonts").resolve()
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

# ---------- sourced content ----------
ITEMS = {}
for s in DRAFT["sections"]:
    for it in s["items"]:
        ITEMS[it["id"]] = it
    for sb in s["subs"]:
        for it in sb["items"]:
            ITEMS[it["id"]] = it
assert len(ITEMS) == 14

FRAC = {0.25: "¼", 0.5: "½", 0.75: "¾"}

def qty(c):
    q, u = c["quantity"], c["unit"]
    qs = FRAC.get(q) or (str(int(q)) if float(q).is_integer() else str(q))
    if u == "dash":
        u = "dash" if q == 1 else "dashes"
    return f"{qs} {u}"

def ingredients(it):
    """Components (quantity + unit) minus hidden components and garnish (garnish goes to the serve line)."""
    hidden = {k for k, v in it["meta"].get("public_components", {}).items() if v is False}
    out = []
    for c in it["components"]:
        slug = c["name"].lower().replace(" ", "-")
        if slug in hidden or c["role"] == "Garnish":
            continue
        name = c["name"].lower()
        if it["id"] == "beta_daiquiri" and c["name"] == "Demerara Syrup":
            name = "house demerara syrup"  # draft desc: "house demerara syrup"; component role "House prep"
        out.append(f"{qty(c)} {name}")
    return out

# method / glass / garnish from phg.recipe_versions (cited in ../round-17/proposal.md)
SERVE = {
    "beta_margarita": "shaken · rocks · lime wheel",
    "beta_manhattan": "stirred · coupe · cocktail cherry",
    "beta_old_fashioned": "stirred · rocks · large cube · orange peel",
    "beta_daiquiri": "shaken · coupe · lime coin",
}

def price(it):
    v = it["prices"][0]["value"]
    return str(int(v)) if float(v).is_integer() else f"{v:.2f}"

def cocktail(iid):
    it = ITEMS[iid]
    ing = " · ".join(ingredients(it))
    return (f'<div class="item ck" data-id="{iid}"><div class="row"><span class="nm">{it["name"]}</span>'
            f'<span class="ld"></span><span class="pr">{price(it)}</span></div>'
            f'<div class="ing">{ing}</div><div class="sv">{SERVE[iid]}</div></div>')

def simple(iid):
    it = ITEMS[iid]
    return (f'<div class="item sm" data-id="{iid}"><div class="row"><span class="nm">{it["name"]}</span>'
            f'<span class="ld"></span><span class="pr">{price(it)}</span></div>'
            f'<div class="ds">{it["desc"]}</div></div>')

def sub(name):
    return f'<div class="sub"><span>{name}</span></div>'

# ---------- ART layer (text-free SVG) ----------
rnd = random.Random(7)

def stars(n, w, h):
    s = []
    for _ in range(n):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h) ** 1.0, rnd.choice([0.5, 0.6, 0.8, 1.0, 1.3])
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#e9e6ff" opacity="{rnd.uniform(.25,.8):.2f}"/>')
    return "".join(s)

def agave(cx, by, size, fill, rim, n=11, lean=0.0):
    """Rosette of tapered leaves radiating up from (cx, by)."""
    out = []
    for k in range(n):
        a = math.radians(-90 + (k - (n - 1) / 2) * (150 / (n - 1)) + lean + rnd.uniform(-5, 5))
        L = size * (0.55 + 0.45 * math.cos(a + math.pi / 2) ** 0.6 if math.cos(a + math.pi / 2) > 0 else 0.55) * rnd.uniform(.85, 1.05)
        tx, ty = cx + L * math.cos(a), by + L * math.sin(a)
        w = size * 0.075
        nx, ny = -math.sin(a) * w, math.cos(a) * w
        mx, my = cx + L * .45 * math.cos(a), by + L * .45 * math.sin(a)
        d = (f"M{cx-nx*.6:.1f},{by-ny*.6:.1f} Q{mx-nx*1.6:.1f},{my-ny*1.6:.1f} {tx:.1f},{ty:.1f} "
             f"Q{mx+nx*1.6:.1f},{my+ny*1.6:.1f} {cx+nx*.6:.1f},{by+ny*.6:.1f}Z")
        out.append(f'<path d="{d}" fill="{fill}"/>')
        out.append(f'<path d="M{cx:.1f},{by:.1f} Q{mx-nx*1.2:.1f},{my-ny*1.2:.1f} {tx:.1f},{ty:.1f}" fill="none" stroke="{rim}" stroke-width="{max(.6,size*.008):.2f}" opacity=".55"/>')
    return "".join(out)

def fireflies(n, x0, x1, y0, y1):
    return "".join(f'<circle cx="{rnd.uniform(x0,x1):.1f}" cy="{rnd.uniform(y0,y1):.1f}" r="{rnd.uniform(1.2,2.6):.1f}" fill="#fff1a8" filter="url(#glow)" opacity="{rnd.uniform(.6,1):.2f}"/>' for _ in range(n))

DEFS = """<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#070a22"/><stop offset=".55" stop-color="#141a4a"/><stop offset="1" stop-color="#262a62"/></linearGradient>
<radialGradient id="halo"><stop offset="0" stop-color="#cfd6ff" stop-opacity=".45"/><stop offset=".35" stop-color="#8e98e0" stop-opacity=".16"/><stop offset="1" stop-color="#3a4290" stop-opacity="0"/></radialGradient>
<radialGradient id="lamp"><stop offset="0" stop-color="#ffc56b" stop-opacity=".95"/><stop offset=".25" stop-color="#ff9a3d" stop-opacity=".45"/><stop offset="1" stop-color="#ff7a1f" stop-opacity="0"/></radialGradient>
<linearGradient id="adobe" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4a3547"/><stop offset="1" stop-color="#2a1f33"/></linearGradient>
<linearGradient id="haze" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#262a62" stop-opacity="0"/><stop offset="1" stop-color="#3b3f80" stop-opacity=".55"/></linearGradient>
<filter id="glow" x="-300%" y="-300%" width="700%" height="700%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="soft"><feGaussianBlur stdDeviation="1.2"/></filter>
</defs>"""

def sky_svg():
    # 816 x 700, top-anchored: sky, stars, moon + halo, thin cloud bands. Bleeds with the page (slice).
    return (f'<svg class="art sky" viewBox="0 0 816 700" preserveAspectRatio="xMidYMin slice" aria-hidden="true">{DEFS}'
            '<rect x="-20" y="-20" width="856" height="760" fill="url(#sky)"/>' + stars(170, 816, 640) +
            '<circle cx="676" cy="118" r="210" fill="url(#halo)"/>'
            '<circle cx="676" cy="118" r="50" fill="#f3edd6"/>'
            '<circle cx="662" cy="104" r="9" fill="#e2dac0" opacity=".7"/><circle cx="690" cy="134" r="6" fill="#e2dac0" opacity=".6"/><circle cx="694" cy="100" r="4" fill="#e2dac0" opacity=".5"/>'
            '<g opacity=".14" filter="url(#soft)"><ellipse cx="560" cy="160" rx="170" ry="7" fill="#c9cff5"/><ellipse cx="200" cy="120" rx="140" ry="5" fill="#c9cff5"/></g>'
            '</svg>')

def ground_svg():
    # 816 x 420, bottom-anchored: mesas, adobe wall with lantern light, agave field in three depth rows, fireflies.
    g = [f'<svg class="art ground" viewBox="0 0 816 420" preserveAspectRatio="xMidYMax slice" aria-hidden="true">{DEFS}']
    g.append('<path d="M-20,150 L60,120 L150,128 L190,104 L300,110 L340,132 L470,126 L520,100 L640,104 L700,128 L836,118 L836,420 L-20,420Z" fill="#1b1f4c"/>')
    g.append('<rect x="-20" y="118" width="856" height="60" fill="url(#haze)"/>')
    # adobe wall with coping, a gate arch and three lanterns
    g.append('<path d="M-20,176 L836,168 L836,236 L-20,242Z" fill="url(#adobe)"/>')
    g.append('<path d="M-20,172 L836,164 L836,172 L-20,180Z" fill="#6a4d5c"/>')
    g.append('<path d="M376,238 L376,196 Q408,164 440,196 L440,236Z" fill="#170f1f"/>')
    g.append('<path d="M382,238 L382,198 Q408,172 434,198 L434,236Z" fill="#ff9a3d" opacity=".22"/>')
    for lx in (150, 408, 668):
        g.append(f'<circle cx="{lx}" cy="186" r="70" fill="url(#lamp)"/>')
        g.append(f'<rect x="{lx-5}" y="178" width="10" height="15" rx="2" fill="#ffd489"/><rect x="{lx-6}" y="175" width="12" height="3" fill="#3a2530"/>')
    # agave rows: far (hazy, small), mid, near (silhouette with moon rim)
    for x in range(-10, 840, 34):
        g.append(agave(x + rnd.uniform(-8, 8), 262 + rnd.uniform(-4, 4), 34, "#243a5a", "#8fa6d6", n=9))
    g.append('<rect x="-20" y="236" width="856" height="40" fill="#1a2350" opacity=".35"/>')
    for x in range(0, 840, 62):
        g.append(agave(x + rnd.uniform(-12, 12), 318 + rnd.uniform(-6, 6), 62, "#16293d", "#7f9bd0", n=11))
    g.append('<rect x="-20" y="300" width="856" height="130" fill="#0b1422"/>')
    for x, s, ln in ((40, 150, 8), (250, 118, -4), (520, 132, 5), (790, 160, -8)):
        g.append(agave(x, 432, s, "#0a121d", "#9fb5e6", n=13, lean=ln))
    g.append(fireflies(34, 10, 806, 150, 400))
    g.append('</svg>')
    return "".join(g)

def lantern_svg():
    # hanging lantern prop on a post (bottom-left); its tag is an HTML backing field
    return ('<svg class="lantern" viewBox="0 0 120 220" aria-hidden="true">'
            '<circle cx="78" cy="96" r="60" fill="url(#lamp)"/>'
            '<rect x="8" y="10" width="9" height="210" fill="#2a1a14"/><rect x="8" y="22" width="78" height="7" fill="#2a1a14"/>'
            '<line x1="78" y1="29" x2="78" y2="62" stroke="#1d130e" stroke-width="2"/>'
            '<path d="M64,62 L92,62 L88,70 L68,70Z" fill="#23160f"/>'
            '<rect x="66" y="70" width="24" height="40" rx="3" fill="#ffcf7a"/>'
            '<rect x="66" y="70" width="24" height="40" rx="3" fill="none" stroke="#23160f" stroke-width="2.5"/>'
            '<line x1="78" y1="70" x2="78" y2="110" stroke="#23160f" stroke-width="2"/>'
            '<path d="M64,110 L92,110 L86,118 L70,118Z" fill="#23160f"/>'
            '<line x1="72" y1="118" x2="64" y2="138" stroke="#caa877" stroke-width="1.2"/>'
            '</svg>')

# ---------- TEXT layer ----------
COCKTAILS = (f'<section class="card cocktails" id="c-cocktails"><h2>Cocktails</h2><div class="cols">'
             f'<div class="col">{sub("Classics")}{cocktail("beta_margarita")}{cocktail("beta_manhattan")}</div>'
             f'<div class="col">{sub("House Originals")}{cocktail("beta_daiquiri")}{cocktail("beta_old_fashioned")}</div>'
             f'</div></section>')
BEER = (f'<section class="card" id="c-beer"><h2>Beer</h2>{sub("Draft")}{simple("beta_czech_pilsner")}'
        f'{simple("beta_dry_hopped_ipa")}{simple("beta_amber_lager")}<h3>Cider</h3>{simple("beta_dry_cider")}</section>')
WINE = (f'<section class="card" id="c-wine"><h2>Wine</h2>{sub("By the Glass")}{simple("beta_malbec")}'
        f'{simple("beta_pinot_grigio")}{sub("Sparkling")}{simple("beta_brut_rose")}</section>')
SPIRITS = (f'<section class="card" id="c-spirits"><h2>Spirits</h2>{sub("Agave")}{simple("beta_blanco_tequila")}'
           f'{simple("beta_anejo_tequila")}{sub("Brandy")}{simple("beta_cognac_vsop")}</section>')

CSS = f"""
@font-face{{font-family:Fraunces;font-weight:600;src:url({FONTS}/Fraunces-600-normal.ttf)}}
@font-face{{font-family:Fraunces;font-weight:700;src:url({FONTS}/Fraunces-700-normal.ttf)}}
@font-face{{font-family:Fraunces;font-weight:600;font-style:italic;src:url({FONTS}/Fraunces-600-italic.ttf)}}
@font-face{{font-family:DMSans;font-weight:400;src:url({FONTS}/DMSans-400-normal.ttf)}}
@font-face{{font-family:DMSans;font-weight:500;src:url({FONTS}/DMSans-500-normal.ttf)}}
@font-face{{font-family:DMSans;font-weight:700;src:url({FONTS}/DMSans-700-normal.ttf)}}
:root{{--ink:#2a1c12;--ink2:#4a3522;--rule:#9c7a4a;--parch:#f1e6ca;--parch2:#e8d9b4;--wood:#4b2e1c;--wood2:#3a2214;--cream:#f6e9c9}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:#0a0d26}}
.page{{position:relative;width:816px;height:1056px;overflow:hidden;background:#141a4a}}
.art{{position:absolute;left:-12px;width:840px;display:block}}  /* 12 CSS px = 3.2 mm bleed past trim */
.sky{{top:-12px;height:720px}}
.ground{{bottom:-12px;height:432px}}
.card{{position:absolute;background:linear-gradient(170deg,var(--parch),var(--parch2));color:var(--ink);border-radius:6px;padding:22px 24px 18px;
  box-shadow:0 0 0 1px #b99a66,0 0 34px 6px rgba(255,176,86,.30),0 18px 40px rgba(0,0,0,.55)}}
.card::before{{content:"";position:absolute;inset:6px;border:1px solid rgba(156,122,74,.55);border-radius:3px;pointer-events:none}}
h2{{font:700 25px/1 Fraunces,serif;letter-spacing:.2em;text-transform:uppercase;color:var(--ink);text-align:center;margin-bottom:10px}}
h2::after{{content:"";display:block;width:54px;height:2px;background:var(--rule);margin:9px auto 0}}
h3{{font:700 19px/1 Fraunces,serif;letter-spacing:.2em;text-transform:uppercase;text-align:center;margin:14px 0 6px;color:var(--ink)}}
.sub{{font:500 12px/1 DMSans,sans-serif;letter-spacing:.22em;text-transform:uppercase;color:#6a4a2a;margin:10px 0 6px;display:flex;align-items:center;gap:8px}}
.sub::after{{content:"";flex:1;height:1px;background:rgba(156,122,74,.6)}}
.item{{margin:0 0 11px}}
.row{{display:flex;align-items:baseline;gap:6px}}
.nm{{font:700 15px/1.25 DMSans,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--ink)}}
.ld{{flex:1;border-bottom:1.5px dotted rgba(74,53,34,.55);transform:translateY(-4px);min-width:14px}}
.pr{{font:700 17px/1 Fraunces,serif;color:var(--ink)}}
.ing{{font:600 14px/1.35 Fraunces,serif;color:var(--ink2);margin-top:3px;padding-right:22px}}
.sv{{font:600 italic 13.5px/1.35 Fraunces,serif;color:#6a4020;margin-top:2px}}
.ds{{font:600 italic 14px/1.3 Fraunces,serif;color:var(--ink2);margin-top:2px}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:30px}}
.ck{{margin-bottom:14px}}
/* props */
.sign{{position:absolute;left:50%;top:40px;transform:translateX(-50%) rotate(-1.2deg);background:linear-gradient(180deg,var(--wood),var(--wood2));
  color:var(--cream);padding:14px 40px 12px;border-radius:5px;text-align:center;box-shadow:inset 0 0 0 2px #2a170d,0 0 26px rgba(255,170,80,.25),0 12px 26px rgba(0,0,0,.6)}}
.sign .wm{{font:700 52px/1 Fraunces,serif;letter-spacing:.34em;margin-right:-.34em}}
.sign .st{{font:500 12.5px/1 DMSans,sans-serif;letter-spacing:.36em;margin-top:8px;text-transform:uppercase;color:#f0dcae}}
.rope{{position:absolute;top:-2px;width:2px;height:48px;background:#c9a676}}
.tag{{position:absolute;background:var(--parch);color:var(--ink);font:700 12.5px/1.35 DMSans,sans-serif;letter-spacing:.24em;text-transform:uppercase;
  padding:9px 12px 8px 20px;border-radius:3px 10px 10px 3px;box-shadow:0 0 22px rgba(255,180,90,.45),0 8px 16px rgba(0,0,0,.5)}}
.tag::before{{content:"";position:absolute;left:7px;top:50%;width:6px;height:6px;margin-top:-3px;border-radius:50%;background:#0b1422}}
.board{{position:absolute;background:linear-gradient(180deg,var(--wood),var(--wood2));color:var(--cream);font:700 13px/1.3 DMSans,sans-serif;letter-spacing:.3em;
  text-transform:uppercase;padding:10px 16px;border-radius:3px;box-shadow:inset 0 0 0 2px #2a170d,0 10px 20px rgba(0,0,0,.6);text-align:center}}
.post{{position:absolute;width:9px;background:#2a1a14}}
.lantern{{position:absolute;width:120px;height:220px}}
/* letter geometry: 36 pt = 48 CSS px safe margin */
.L #c-cocktails{{left:48px;top:170px;width:720px}}
.L #c-beer{{left:48px;top:512px;width:230px}}
.L #c-wine{{left:293px;top:512px;width:230px}}
.L #c-spirits{{left:538px;top:512px;width:230px}}
.L .lantern{{left:40px;bottom:36px}}
.L .tag.t1{{left:110px;bottom:52px;transform:rotate(-5deg)}}
.L .board.b1{{right:70px;bottom:62px;transform:rotate(2deg)}}
.L .post.p1{{right:150px;bottom:0;height:70px}}
/* phone */
.P{{width:390px;height:auto;min-height:1500px;padding:0 0 330px}}
.P .sky{{height:760px}}
.P .ground{{height:400px;left:-225px;width:840px}}
.P .sign{{position:relative;left:auto;top:auto;transform:rotate(-1.2deg);margin:36px auto 0;width:max-content;padding:12px 26px 10px}}
.P .sign .wm{{font-size:40px}}
.P .sign .st{{font-size:11px;letter-spacing:.28em}}
.P .card{{position:relative;margin:26px 18px 0;width:auto}}
.P .cols{{grid-template-columns:1fr;gap:0}}
.P .lantern{{left:10px;bottom:30px}}
.P .tag.t1{{left:84px;bottom:50px;transform:rotate(-5deg)}}
.P .board.b1{{right:16px;bottom:170px;transform:rotate(2deg)}}
.P .post.p1{{right:90px;bottom:0;height:175px}}
"""

def page(cls):
    return (f'<div class="page {cls}">{sky_svg()}{ground_svg()}'
            f'<div class="sign"><div class="rope" style="left:26px;top:-44px"></div><div class="rope" style="right:26px;top:-44px"></div>'
            f'<div class="wm">CANTINA</div><div class="st">Cocktail Bar · Iowa City</div></div>'
            f'{COCKTAILS}{BEER}{WINE}{SPIRITS}'
            f'<div class="post p1"></div><div class="board b1">Under the<br>same moon</div>'
            f'{lantern_svg()}<div class="tag t1">Good drinks<br>good company</div></div>')

def html(cls):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Cantina · Bar menu</title>'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><style>{CSS}</style></head>'
            f'<body>{page(cls)}</body></html>')

(HERE / "menu.html").write_text(html("L"))
(HERE / "menu-phone.html").write_text(html("P"))

# ---------- checks ----------
def lum(rgb):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)

def cr(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)

JS = r"""() => { const out=[]; document.querySelectorAll('.nm,.pr,.ing,.sv,.ds,h2,h3,.sub span,.wm,.st,.tag,.board').forEach(el=>{
  const b=el.getBoundingClientRect(); const cs=getComputedStyle(el);
  out.push({t:el.innerText.trim().slice(0,40),x:b.left,y:b.top,w:b.width,h:b.height,c:cs.color,fs:cs.fontSize});});
  const items=[...document.querySelectorAll('.item')].map(i=>({id:i.dataset.id,name:i.querySelector('.nm').innerText,price:i.querySelector('.pr').innerText,text:i.innerText}));
  const cards=[...document.querySelectorAll('.card')].map(c=>{const b=c.getBoundingClientRect();return {id:c.id,x:b.left,y:b.top,w:b.width,h:b.height,over:c.scrollHeight>c.clientHeight+1}});
  return {out,items,cards}; }"""

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=CHROME)
    pg = br.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=3.125)
    pg.goto((HERE / "menu.html").as_uri()); pg.wait_for_timeout(400)
    pg.locator(".page").screenshot(path=str(HERE / "preview-letter.png"))
    info = pg.evaluate(JS)
    ph = br.new_page(viewport={"width": 390, "height": 900}, device_scale_factor=3)
    ph.goto((HERE / "menu-phone.html").as_uri()); ph.wait_for_timeout(400)
    ph.locator(".page").screenshot(path=str(HERE / "preview-phone.png"))
    br.close()

# parity
for it in info["items"]:
    src = ITEMS[it["id"]]
    assert it["name"].upper() == src["name"].upper(), it
    assert it["price"] == price(src), it
    assert "bitters" not in it["text"].lower() or it["id"] != "beta_manhattan"
assert len(info["items"]) == 14

# geometry / margins
for c in info["cards"]:
    assert c["x"] >= 48 and c["x"] + c["w"] <= 768 + 0.5 and c["y"] + c["h"] <= 1008, c
print("cards", json.dumps(info["cards"]))

# worst-pixel contrast: inside each text box, background = pixels farthest from the text colour;
# worst = lowest contrast among the 10% most-background-like pixels.
im = Image.open(HERE / "preview-letter.png").convert("RGB")
S = 3.125
worst = []
for t in info["out"]:
    rgb = tuple(int(v) for v in t["c"][t["c"].index("(") + 1:-1].split(",")[:3])
    box = (int(t["x"] * S), int(t["y"] * S), int((t["x"] + t["w"]) * S), int((t["y"] + t["h"]) * S))
    px = list(im.crop(box).getdata())[::3]
    ratios = sorted(cr(rgb, q) for q in px)
    bg = ratios[int(len(ratios) * 0.55):]  # drop glyph + antialias pixels
    worst.append((round(bg[0], 2), t["t"], t["fs"]))
worst.sort()
print("lowest text-box contrasts:", worst[:6])
print("letter", Image.open(HERE / "preview-letter.png").size, "phone", Image.open(HERE / "preview-phone.png").size)
