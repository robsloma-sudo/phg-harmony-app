"""TEST-1 explore-K3 MAPA DE SABOR (the flavor field).

Thesis: the guest's question is "what does it taste like?", so the menu is the answer drawn as a field.

Front: one plotted field, bright <-> rich (x) by clean <-> smoky (y), 12 numbered cocktail points with their glass glyphs,
       an index keyed by large numerals to the full item stack, zero-proof on the bottom margin.
Back:  small multiples, 25 identical micro-cards (class, oak-age bar, region, price) grouped by class; beer, cider, wine.

Content comes only from ../expanded-v1/manifest.json. Every coordinate is a PHG inference (see COORDS and proposal.md).
Run: python3 build.py   -> menu.html, preview-front.png, preview-back.png, preview-phone.png, menu-print-bleed.pdf, gates.json
"""
import json, math, pathlib, re, html as H
from PIL import Image, ImageChops

HERE = pathlib.Path(__file__).parent.resolve()
MAN = json.loads((HERE.parent / "expanded-v1" / "manifest.json").read_text())
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
e = H.escape

# ------------------------------------------------------------------ palette (paper + ink + one field gradient inside the map)
PAPER, INK, INK2, MUTED = "#F3F0E8", "#161513", "#34322E", "#57534B"
FIELD = [(0.00, "#F4DA3C"), (0.22, "#EDBE38"), (0.48, "#B98039"), (0.74, "#5A4536"), (1.00, "#242220")]
LIQ = {"neutral": "#E4DCCB", "campari": "#B2352C", "espresso": "#3A2A21", "cola": "#4A2E23"}

# ------------------------------------------------------------------ content
def price(p): return str(int(p)) if float(p).is_integer() else f"{p:.2f}"
PROPOSED = lambda it: it["status"] != "approved_db"

COCKTAILS = []
for sec, rows in MAN["cocktails"].items():
    for it in rows: COCKTAILS.append(dict(it, sec=sec))
assert len(COCKTAILS) == 12

# PHG inference: x = bright (0) -> rich (10); y = clean (0) -> smoky (10). Reasoning is recorded in proposal.md.
COORDS = {
 "Margarita":                  (2.6, 1.4),
 "Paloma":                     (1.6, 0.5),
 "Ranch Water":                (0.4, 0.8),
 "Manhattan":                  (8.2, 3.3),
 "Batanga":                    (4.7, 2.0),
 "Carajillo":                  (8.6, 5.9),
 "Brown Butter Old Fashioned": (9.5, 4.3),
 "House Daiquiri":             (3.9, 0.3),
 "Mezcal Negroni":             (6.7, 8.7),
 "Spicy Pineapple Margarita":  (3.1, 2.9),
 "Milpa Old Fashioned":        (7.1, 5.3),
 "Loess":                      (4.6, 7.1),
}
# liquid colour only where an ingredient makes it obvious (brief): Campari red, espresso dark, cola dark
def liquid(it):
    ing = " ".join(it["ingredients"]).lower()
    if "campari" in ing: return "campari"
    if "espresso" in ing: return "espresso"
    if "cola" in ing: return "cola"
    return "neutral"

SPIRIT_GROUPS = [("Tequila · Blanco", "blanco"), ("Tequila · Reposado", "reposado"), ("Tequila · Añejo", "añejo"),
                 ("Mezcal", "mezcal"), ("Casa · House pours", "house")]
def oak(sensory):
    """oak-age mark from the manifest's own class-level sensory text: (start, end, open_end) in months, or None."""
    s = sensory.split("·")[0].strip().lower()
    if s.startswith("unaged"): return (0, 0, False)
    m = re.match(r"(\d+)–(\d+) months", s)
    if m: return (int(m[1]), int(m[2]), False)
    m = re.match(r"(\d+)–(\d+) years", s)
    if m: return (12 * int(m[1]), 12 * int(m[2]), False)
    m = re.match(r"(\d+)\+ years", s)
    if m: return (12 * int(m[1]), None, True)
    return None  # e.g. "Pit-roasted espadín": the manifest states no age

# ------------------------------------------------------------------ glass glyphs (coded family: rocks / highball / coupe + ice + garnish)
SW = 1.35
def glyph(glass, garnish, liq):
    L = LIQ[liq]; o = []
    ice = glass in ("rocks", "highball")  # served on ice; the coupe is served up
    if glass == "rocks":
        o.append(f'<path d="M-8.6,-1 L-7.9,9.6 L7.9,9.6 L8.6,-1 Z" fill="{L}"/>')
        if ice: o.append(f'<rect x="-3.6" y="-4.2" width="7" height="7" transform="rotate(9)" fill="{PAPER}" fill-opacity=".55" stroke="{INK}" stroke-width="1"/>')
        o.append(f'<path d="M-9.4,-7 L-8.2,10.4 L8.2,10.4 L9.4,-7" fill="none" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
        rim = (-9.4, 9.4, -7)
    elif glass == "highball":
        o.append(f'<path d="M-5.6,-5 L-5.6,12.2 L5.6,12.2 L5.6,-5 Z" fill="{L}"/>')
        o.append(f'<rect x="-3.4" y="-3.2" width="5.6" height="5.6" transform="rotate(-8)" fill="{PAPER}" fill-opacity=".55" stroke="{INK}" stroke-width="1"/>')
        o.append(f'<rect x="-1.8" y="3.4" width="5.6" height="5.6" transform="rotate(10)" fill="{PAPER}" fill-opacity=".55" stroke="{INK}" stroke-width="1"/>')
        o.append(f'<path d="M-6.2,-12.6 L-6.2,12.8 L6.2,12.8 L6.2,-12.6" fill="none" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
        rim = (-6.2, 6.2, -12.6)
    else:  # coupe
        o.append(f'<path d="M-10.2,-5.6 Q-9,2.2 0,2.4 Q9,2.2 10.2,-5.6 Z" fill="{L}"/>')
        o.append(f'<path d="M-11.4,-8.4 Q-10.4,3.2 0,3.4 Q10.4,3.2 11.4,-8.4 M0,3.4 L0,11.4 M-6,11.8 L6,11.8" fill="none" stroke="{INK}" stroke-width="{SW}" stroke-linecap="round"/>')
        rim = (-11.4, 11.4, -8.4)
    x0, x1, y = rim
    g = (garnish or "").lower()
    if g == "salt rim":
        o.append(f'<line x1="{x0 + .6}" y1="{y - 1.2}" x2="{x1 - .6}" y2="{y - 1.2}" stroke="{INK}" stroke-width="2" stroke-dasharray="0.01 2.4" stroke-linecap="round"/>')
    elif g == "lime wheel":
        cx, cy, r = x1 - 1, y - 1, 4.4
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{PAPER}" stroke="{INK}" stroke-width="1.1"/>'
                 + "".join(f'<line x1="{cx}" y1="{cy}" x2="{cx + r * .72 * math.cos(a)}" y2="{cy + r * .72 * math.sin(a)}" stroke="{INK}" stroke-width=".7"/>' for a in [k * math.pi / 3 for k in range(6)]))
    elif g == "lime wedge":
        cx, cy = x1 - .6, y
        o.append(f'<path d="M{cx},{cy} L{cx + 5.2},{cy - 4.2} A6,6 0 0 0 {cx - 1.8},{cy - 6.4} Z" fill="{PAPER}" stroke="{INK}" stroke-width="1.1" stroke-linejoin="round"/>')
    elif g == "lime coin":
        o.append(f'<circle cx="{x1 - 2.6}" cy="{y + .4}" r="2.6" fill="{PAPER}" stroke="{INK}" stroke-width="1.1"/>')
    elif g == "orange peel":
        o.append(f'<path d="M{x1 - 3.4},{y + 1.8} c1.6,-3.6 4.8,-3.4 4.4,-.4 c-.3,2.6 2.6,3.4 4,1.2" fill="none" stroke="{INK}" stroke-width="1.3" stroke-linecap="round"/>')
    elif g == "cocktail cherry":
        o.append(f'<path d="M2.2,-1.8 Q3.6,-7 7.4,-10.4" fill="none" stroke="{INK}" stroke-width="1" stroke-linecap="round"/><circle cx="2" cy="-1.4" r="2.6" fill="{INK}"/>')
    elif g == "candied ginger":
        o.append(f'<line x1="{x1 - 11}" y1="{y + 4}" x2="{x1 + 2}" y2="{y - 5}" stroke="{INK}" stroke-width="1"/><rect x="{x1 - 3.4}" y="{y - 5.4}" width="4.2" height="4.2" transform="rotate(-34 {x1 - 1.3} {y - 3.3})" fill="{PAPER}" stroke="{INK}" stroke-width="1.1"/>')
    return "".join(o)

# ------------------------------------------------------------------ letter grid (CSS px, 96/in; page 816 x 1056; safe area 48)
M, G = 52, 16
C = (816 - 2 * M - 11 * G) / 12
colx = lambda i: M + i * (C + G)
span = lambda n: n * C + (n - 1) * G
FX = colx(4)                 # field's left edge (the y axis)
FB = 424                     # field's bottom edge (the x axis)
X0, X1 = FX + 36, 742        # plot 0..10 on x
Y0, Y1 = FB - 32, 140        # plot 0..10 on y (clean at the bottom, smoke rises)
DR, BR, BO = 19.5, 10.5, 14.5  # disc radius, number-badge radius, badge offset

def field_svg(fx, fy0, fx1, fb, X0, X1, Y0, Y1, dr, br, bo, gid, grid=True, glyph_px=None):
    px = lambda v: X0 + (X1 - X0) * v / 10
    py = lambda v: Y0 + (Y1 - Y0) * v / 10
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in FIELD)
    s = [f'<defs><linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{px(0)}" y1="{py(0)}" x2="{px(10)}" y2="{py(10)}">{stops}</linearGradient></defs>',
         f'<rect x="{fx}" y="{fy0}" width="{fx1 - fx}" height="{fb - fy0}" fill="url(#{gid})"/>']
    if grid:  # measurement lattice: a hairline cross at every whole unit, the 5/5 midlines slightly longer
        for i in range(11):
            for j in range(11):
                a = 2.2 if (i == 5 or j == 5) else 1.4
                t = 0.95 * (i + j) / 20
                col = "#161513" if t < 0.42 else PAPER
                op = .30 if t < 0.42 else .26
                s.append(f'<path d="M{px(i) - a},{py(j)} h{2 * a} M{px(i)},{py(j) - a} v{2 * a}" stroke="{col}" stroke-opacity="{op}" stroke-width=".8"/>')
    pts = []
    for n, it in enumerate(COCKTAILS, 1):
        x, y = COORDS[it["name"]]; cx, cy = px(x), py(y)
        pts.append((n, cx, cy))
        s.append(f'<g transform="translate({cx:.2f},{cy:.2f})"><circle r="{dr}" fill="{PAPER}"/>'
                 + (f'<g transform="scale({dr / 19.5 * 1.04:.3f}) translate(0,.6)">{glyph(it["glass"], it["garnish"], liquid(it))}</g>' if glyph_px is None else
                    f'<svg x="{-glyph_px / 2:.2f}" y="{-glyph_px * 32 / 30 / 2 + .6:.2f}" width="{glyph_px}" height="{glyph_px * 32 / 30:.2f}" viewBox="-15 -16 30 32" overflow="visible">{glyph(it["glass"], it["garnish"], liquid(it))}</svg>') +
                 '</g>')
    s += [f'<circle cx="{cx - bo:.2f}" cy="{cy - bo:.2f}" r="{br}" fill="{INK}"/>' for _, cx, cy in pts]  # badges above every disc
    return "".join(s), pts

# ---------- letter front art layer
FRONT_SVG, FRONT_PTS = field_svg(FX, -9, 825, FB, X0, X1, Y0, Y1, DR, BR, BO, "fg")
# axes on paper: x axis under the field, y axis in the gutter left of the field; 11 ticks each
AX_Y = FB + 18
AXES = [f'<line x1="{X0}" y1="{AX_Y}" x2="{X1}" y2="{AX_Y}" stroke="{INK}" stroke-width=".9"/>',
        f'<path d="M{X1 + 7},{AX_Y} l-7,-3.2 v6.4 Z" fill="{INK}"/>']
AXES += [f'<line x1="{X0 + (X1 - X0) * i / 10}" y1="{AX_Y - (3 if i % 5 else 5)}" x2="{X0 + (X1 - X0) * i / 10}" y2="{AX_Y}" stroke="{INK}" stroke-width=".9"/>' for i in range(11)]
AY_X = FX - 9
AXES += [f'<line x1="{AY_X}" y1="{Y0}" x2="{AY_X}" y2="{Y1}" stroke="{INK}" stroke-width=".9"/>', f'<path d="M{AY_X},{Y1 - 7} l-3.2,7 h6.4 Z" fill="{INK}"/>']
AXES += [f'<line x1="{AY_X}" y1="{Y0 + (Y1 - Y0) * i / 10}" x2="{AY_X + (3 if i % 5 else 5)}" y2="{Y0 + (Y1 - Y0) * i / 10}" stroke="{INK}" stroke-width=".9"/>' for i in range(11)]

def ring(): return '<span class="pr" title="proposed — pending approval"></span>'
def pw(it): return f'<span class="pw">&nbsp;<span class="price tx">{price(it["price"])}</span>{ring() if PROPOSED(it) else ""}</span>'

def stack(it, n=None, cls="it"):
    """binding item stack: 1 name + price / 2 sensory / 3 ingredients in role order / 4 garnish · glass"""
    num = f'<div class="num tx">{n:02d}</div>' if n else ""
    ing = ""
    if it.get("ingredients"):
        ing = '<p class="ing tx">' + '<span class="dot"> · </span>'.join(f'<span class="i">{e(i)}</span>' for i in it["ingredients"]) + "</p>"
    gg = ""
    if it.get("glass"):
        parts = ([f'<span class="gar">{e(it["garnish"])}</span>'] if it.get("garnish") else []) + [f'<span class="gl">{e(it["glass"])}</span>']
        gg = '<p class="gg tx">' + '<span class="dot"> · </span>'.join(parts) + "</p>"
    return (f'<div class="{cls}" data-name="{e(it["name"])}" data-status="{it["status"]}">{num}'
            f'<p class="np"><span class="name tx">{e(it["name"])}</span>{pw(it)}</p>'
            f'<p class="sd tx">{e(it["sensory"])}</p>{ing}{gg}</div>')

# ---------- front: index (column-major so Classics fill columns 1-2 and House 3-4)
idx = []
for n, it in enumerate(COCKTAILS, 1):
    col, row = (n - 1) // 3 + 1, (n - 1) % 3 + 2
    idx.append(f'<div class="cell" style="grid-column:{col};grid-row:{row};order:{n if n <= 6 else n + 1}">{stack(it, n)}</div>')
subs = list(MAN["cocktails"])
INDEX = (f'<div class="index"><h3 class="tx" style="grid-column:1/3;grid-row:1">{e(subs[0])}</h3>'
         f'<h3 class="tx" style="grid-column:3/5;grid-row:1;order:7">{e(subs[1])}</h3>{"".join(idx)}</div>')
zp_name, zp = next(iter(MAN["zero_proof"].items()))
ZERO = (f'<div class="zero"><h3 class="tx">{e(zp_name)}</h3><div class="zrow">'
        + "".join(f'<div class="cell">{stack(it)}</div>' for it in zp) + "</div></div>")

# numerals on the field (HTML text over the ink badges)
BADGES = "".join(f'<div class="bn tx" style="left:{cx - BO - 12:.2f}px;top:{cy - BO - 8:.2f}px">{n:02d}</div>' for n, cx, cy in FRONT_PTS)

GLYPH_KEY = "".join(
    f'<div class="gk"><svg width="30" height="32" viewBox="-15 -16 30 32">{glyph(g, gar, "neutral")}</svg><span class="tx">{lab}</span></div>'
    for g, gar, lab in [("rocks", None, "rocks"), ("highball", None, "highball"), ("coupe", None, "coupe")])

FRONT = f"""<section class="page front">
<svg class="art fieldart" width="834" height="1074" viewBox="-9 -9 834 1074">{FRONT_SVG}{"".join(AXES)}</svg>
<header class="mast"><h1 class="wm tx">Cantina</h1><p class="venue tx">&amp; Cocktail Bar · Iowa City, Iowa</p></header>
<div class="lab ly top tx">Smoky</div><div class="lab ly bot tx">Clean</div>
<div class="lab lx l tx">Bright</div><div class="lab lx r tx">Rich</div>
{BADGES}
<aside class="legend">
 <h2 class="tx">Cócteles · Cocktails</h2>
 <p class="how tx">Each cocktail sits where its sensory notes and ingredients place it. The numbers key to the index below.</p>
 <div class="gkey">{GLYPH_KEY}</div>
 <p class="gnote tx">Cube: served on ice. Tint: shown only where an ingredient sets the colour.</p>
 <p class="key">{ring()}<span class="tx">proposed — pending approval</span></p>
 <p class="inf tx">Placement is a PHG inference from the menu text, not a tasting panel.</p>
</aside>
<div class="lower">{INDEX}{ZERO}</div>
</section>"""

# ---------- back: small multiples
AGE_MAX = 54  # months shown on the track; ticks at 0 12 24 36 48; 48+ runs to the arrow
def agebar(o, w):
    k = (w - 8) / AGE_MAX; x = lambda m: 3 + m * k; s = []
    s.append(f'<line x1="{x(0)}" y1="7" x2="{x(AGE_MAX)}" y2="7" stroke="{INK}" stroke-width=".8"/>')
    s += [f'<line x1="{x(m)}" y1="{3.5 if m % 24 == 0 else 4.5}" x2="{x(m)}" y2="7" stroke="{INK}" stroke-width=".8"/>' for m in (0, 12, 24, 36, 48)]
    if o is None: pass
    elif o[1] == 0: s.append(f'<circle cx="{x(0)}" cy="7" r="4.2" fill="{INK}"/>')
    elif o[2]: s.append(f'<rect x="{x(o[0])}" y="3" width="{x(AGE_MAX) - x(o[0]) - 1}" height="8" fill="{INK}"/><path d="M{x(AGE_MAX) - 1},1 l6,6 l-6,6 Z" fill="{INK}"/>')
    else: s.append(f'<rect x="{x(o[0])}" y="3" width="{x(o[1]) - x(o[0])}" height="8" fill="{INK}"/>')
    return f'<svg class="age" width="{w}" height="14" viewBox="0 0 {w} 14">{"".join(s)}</svg>'

CARD_W = (span(9) - 3 * G) / 4
def card(it):
    reg = it.get("region") or "—"
    return (f'<div class="card" data-name="{e(it["name"])}" data-status="{it["status"]}">'
            f'<p class="np"><span class="name tx">{e(it["name"])}</span>{pw(it)}</p>'
            f'<p class="cls tx">{e(it["cls"])}</p>{agebar(oak(it["sensory"]), CARD_W)}<p class="reg tx">{e(reg)}</p></div>')

SP = MAN["spirits"]
def group_rows():
    out = []
    for name, key in SPIRIT_GROUPS:
        items = SP[name]
        sens = []
        if key in ("blanco", "reposado", "añejo"):
            sens = [items[0]["sensory"]]
        elif key == "mezcal":
            base = items[0]["sensory"]; sens = [base] + [f'{i["name"]}: {i["sensory"]}' for i in items if i["sensory"] != base]
        else:
            sens = [f'{i["name"]}: {i["sensory"]}' for i in items if i["cls"] not in ("blanco", "añejo")]
        lab = f'<div class="glab"><h3 class="tx">{e(name)}</h3>' + "".join(f'<p class="gs tx">{e(t)}</p>' for t in sens) + "</div>"
        out.append(f'<div class="grp" data-group="{key}">{lab}<div class="cards">{"".join(card(i) for i in items)}</div></div>')
    return "".join(out)

def plain(it):
    return (f'<div class="it" data-name="{e(it["name"])}" data-status="{it["status"]}"><p class="np"><span class="name tx">{e(it["name"])}</span>'
            f'{pw(it)}</p><p class="sd tx">{e(it["sensory"])}</p></div>')
BC, WN = MAN["beer_cider"], MAN["wine"]
bk = list(BC); wk = list(WN)
BEVCOLS = [
 [(bk[0], BC[bk[0]][:2]), (bk[1], BC[bk[1]])],
 [(None, BC[bk[0]][2:]), (bk[2], BC[bk[2]])],
 [(wk[0], WN[wk[0]])],
 [(wk[1], WN[wk[1]])],
]
# phone reading order of the sub-blocks: draft, draft (cont.), cans, cider, [Vino head], by the glass, sparkling
ORD = {(n, rows[0]["name"]): k for k, (n, rows) in enumerate([BEVCOLS[0][0], BEVCOLS[1][0], BEVCOLS[0][1], BEVCOLS[1][1], BEVCOLS[2][0], BEVCOLS[3][0]], 1)}
ORD[BEVCOLS[2][0][0], BEVCOLS[2][0][1][0]["name"]] = 6; ORD[BEVCOLS[3][0][0], BEVCOLS[3][0][1][0]["name"]] = 7
BEV = ('<div class="bev"><div class="glab"><div class="bheads"><h3 class="tx">Cerveza y sidra · Beer &amp; cider</h3><h3 class="tx">Vino · Wine</h3></div><p class="key">' + ring() + '<span class="tx">proposed — pending approval</span></p>'
       '<p class="allergy tx">Please tell your server about any allergies.</p></div><div class="bgrid">'
       '<h2 class="tx ponly" style="order:0">Cerveza y sidra · Beer &amp; cider</h2><h2 class="tx ponly" style="order:5">Vino · Wine</h2>'
       + "".join(f'<div class="bcol" style="grid-column:{ci + 1};grid-row:1">' + "".join((f'<div class="bsub" style="order:{ORD[(n, rows[0]["name"])]}"><h3 class="tx">{e(n)}</h3>' if n else f'<div class="bsub cont" style="order:{ORD[(n, rows[0]["name"])]}"><h3>&nbsp;</h3>') + f'{"".join(plain(i) for i in rows)}</div>' for n, rows in col) + "</div>" for ci, col in enumerate(BEVCOLS))
       + "</div></div>")

# the key band: the cards' oak scale drawn once at poster scale (macro reading of the small multiples)
BAND_B = 152
SX0, BW = colx(3) + 3, span(9) - 8
def band_scale():
    classes = {}
    for grp in SP.values():
        for i in grp:
            o = oak(i["sensory"])
            if o is not None: classes.setdefault(o, []).append(i["cls"])
    X = lambda m: m / AGE_MAX * BW
    svg = [f'<line x1="0" y1="10" x2="{BW}" y2="10" stroke="{PAPER}" stroke-width="1"/>']
    svg += [f'<line x1="{X(m)}" y1="3" x2="{X(m)}" y2="10" stroke="{PAPER}" stroke-width="1"/>' for m in (0, 12, 24, 36, 48)]
    labs = []
    for o, cl in sorted(classes.items(), key=lambda t: t[0][0]):
        names = " · ".join(dict.fromkeys(c.replace("mezcal espadín joven", "joven") for c in cl))
        if o[1] == 0:
            svg.append(f'<circle cx="{X(0) + 6}" cy="10" r="7" fill="{PAPER}"/>'); pos, al = 0, "l"
        elif o[2]:
            svg.append(f'<rect x="{X(o[0])}" y="4" width="{X(AGE_MAX) - X(o[0]) - 2}" height="12" fill="{PAPER}"/><path d="M{X(AGE_MAX) - 2},0 l9,10 l-9,10 Z" fill="{PAPER}"/>'); pos, al = AGE_MAX, "r"
        else:
            svg.append(f'<rect x="{X(o[0]) + 1.5}" y="1" width="{X(o[1]) - X(o[0]) - 3}" height="18" fill="{PAPER}"/>'); pos, al = (o[0] + o[1]) / 2, "c in"
        labs.append(f'<span class="bcl {al} tx" style="left:{pos / AGE_MAX * 100:.3f}%">{e(names)}</span>')
    nums = "".join(f'<span class="bnum tx" style="left:{m / AGE_MAX * 100:.3f}%">{m}</span>' for m in (0, 12, 24, 36, 48))
    return (f'<div class="scale">{nums}<svg class="track" width="{BW}" height="20" viewBox="-6 0 {BW + 12} 20" preserveAspectRatio="none">{"".join(svg)}</svg>'
            f'<span class="bunit tx">months in oak</span>{"".join(labs)}</div>')

BACK = f"""<section class="page back">
<div class="band"><div class="bl"><h2 class="tx">Destilados · Spirits</h2><p class="bnote tx">1.5 oz pour</p>
<p class="lgt tx">Each card: name and price, class, months in oak, region. Empty track: age not stated.</p></div>{band_scale()}</div>
<div class="groups">{group_rows()}</div>
{BEV}
</section>"""

# ---------- phone: its own map drawing (same data, same coordinates)
PW = 390; PFH = 500; PFX = 30                      # phone field: x 30..390 (bleeds right), y 0..500; axes on paper to the left and below
PX0, PX1, PY0, PY1 = 58, 356, PFH - 30, 130
PDR, PBR, PBO, PGL = 19, 10, 14, 36                # disc radius, badge radius, badge offset, glyph box width (css px)
PH_SVG, PH_PTS = field_svg(PFX, 0, PW, PFH, PX0, PX1, PY0, PY1, PDR, PBR, PBO, "pg", grid=True, glyph_px=PGL)
PAY_X, PAX_Y = PFX - 9, PFH + 14
PH_AX = [f'<line x1="{PX0}" y1="{PAX_Y}" x2="{PX1}" y2="{PAX_Y}" stroke="{INK}" stroke-width=".9"/>', f'<path d="M{PX1 + 7},{PAX_Y} l-7,-3.2 v6.4 Z" fill="{INK}"/>',
         f'<line x1="{PAY_X}" y1="{PY0}" x2="{PAY_X}" y2="{PY1}" stroke="{INK}" stroke-width=".9"/>', f'<path d="M{PAY_X},{PY1 - 7} l-3.2,7 h6.4 Z" fill="{INK}"/>']
PH_AX += [f'<line x1="{PX0 + (PX1 - PX0) * i / 10}" y1="{PAX_Y - (3 if i % 5 else 5)}" x2="{PX0 + (PX1 - PX0) * i / 10}" y2="{PAX_Y}" stroke="{INK}" stroke-width=".9"/>' for i in range(11)]
PH_AX += [f'<line x1="{PAY_X}" y1="{PY0 + (PY1 - PY0) * i / 10}" x2="{PAY_X + (3 if i % 5 else 5)}" y2="{PY0 + (PY1 - PY0) * i / 10}" stroke="{INK}" stroke-width=".9"/>' for i in range(11)]
PH_BADGES = "".join(f'<div class="bn tx" style="left:{cx - PBO - 12:.2f}px;top:{cy - PBO - 8:.2f}px">{n:02d}</div>' for n, cx, cy in PH_PTS)
PH_LABELS = (f'<div class="plab ply tx" style="left:{PAY_X - 22}px;top:{PY1 + 2}px">Smoky</div><div class="plab ply tx" style="left:{PAY_X - 22}px;top:{PY0 - 40}px">Clean</div>'
             f'<div class="plab tx" style="left:{PX0}px;top:{PAX_Y + 5}px">Bright</div><div class="plab tx" style="right:{PW - PX1 - 7}px;top:{PAX_Y + 5}px">Rich</div>')
PHONE_MAP = f"""<div class="pmap"><svg width="{PW}" height="{PFH + 40}" viewBox="0 0 {PW} {PFH + 40}">{PH_SVG}{"".join(PH_AX)}</svg>{PH_BADGES}{PH_LABELS}</div>"""

CSS = f"""
@font-face{{font-family:'Inter Tight';src:url('fonts/intertight-normal-latin.woff2') format('woff2');font-weight:100 900;font-style:normal;font-display:block;unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}}
@font-face{{font-family:'Inter Tight';src:url('fonts/intertight-normal-latin-ext.woff2') format('woff2');font-weight:100 900;font-style:normal;font-display:block;unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}}
@font-face{{font-family:'Source Serif 4';src:url('fonts/sourceserif-normal-latin.woff2') format('woff2');font-weight:200 900;font-style:normal;font-display:block}}
@font-face{{font-family:'Source Serif 4';src:url('fonts/sourceserif-italic-latin.woff2') format('woff2');font-weight:200 900;font-style:italic;font-display:block}}
@font-face{{font-family:'Source Serif 4';src:url('fonts/sourceserif-normal-latin-ext.woff2') format('woff2');font-weight:200 900;font-style:normal;font-display:block;unicode-range:U+0100-02BA,U+1E00-1E9F}}
@font-face{{font-family:'Source Serif 4';src:url('fonts/sourceserif-italic-latin-ext.woff2') format('woff2');font-weight:200 900;font-style:italic;font-display:block;unicode-range:U+0100-02BA,U+1E00-1E9F}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:#d9d6cf}}
body{{display:flex;flex-direction:column;align-items:center;gap:24px;padding:24px 0}}
.page{{position:relative;width:816px;height:1056px;overflow:hidden;background:{PAPER};color:{INK};font-family:'Inter Tight',sans-serif;
  font-variant-numeric:lining-nums tabular-nums;-webkit-print-color-adjust:exact;print-color-adjust:exact;font-kerning:normal}}
.art{{position:absolute;left:-9px;top:-9px;pointer-events:none}}
p{{margin:0}}
.pr{{display:inline-block;width:7px;height:7px;border:1px solid {INK};border-radius:50%;margin-left:5px;vertical-align:.12em;flex:none}}
.np{{white-space:normal}}
.name{{font-weight:600}}
.pw{{white-space:nowrap}} .price{{font-weight:400;color:{INK2};margin-left:.12em}}
.sd{{font-family:'Source Serif 4',serif;font-style:italic;font-optical-sizing:auto}}
.ing{{font-family:'Source Serif 4',serif;color:{INK2};font-optical-sizing:auto}}
.gg{{color:{MUTED}}}
h3{{font-weight:600;font-size:12px;line-height:16px;letter-spacing:.08em;text-transform:uppercase}}

/* ---------- front */
.mast{{position:absolute;left:{M}px;top:{M}px;width:{span(4)}px}}
.wm{{font-weight:700;font-size:64px;line-height:72px;letter-spacing:-.035em}}
.venue{{font-weight:500;font-size:13px;line-height:18px;margin-top:0}}
.lab{{position:absolute;font-weight:600;font-size:12px;line-height:16px}}
.ly{{left:{AY_X - 21}px;writing-mode:vertical-rl;transform:rotate(180deg);letter-spacing:.02em}}
.ly.top{{top:{Y1 + 2}px}} .ly.bot{{top:{Y0 - 40}px}}
.lx{{top:{AX_Y + 5}px}} .lx.l{{left:{X0}px}} .lx.r{{right:{816 - X1 - 7}px}}
.bn{{position:absolute;width:24px;height:16px;font-weight:700;font-size:12px;line-height:16px;text-align:center;color:{PAPER};letter-spacing:-.02em}}
.legend{{position:absolute;left:{M}px;width:{span(4) - 30}px;bottom:{1056 - FB}px}}
.legend h2{{font-weight:600;font-size:17px;line-height:22px;margin-bottom:8px}}
.how{{font-family:'Source Serif 4',serif;font-size:13px;line-height:18px;color:{INK2};margin-bottom:14px}}
.gkey{{display:flex;gap:14px;margin-bottom:6px}}
.gk{{display:flex;align-items:center;gap:3px;font-size:12px;line-height:16px}}
.gnote{{font-size:12px;line-height:16px;color:{MUTED};margin-bottom:14px}}
.key{{font-size:12px;line-height:16px;display:flex;align-items:center;gap:6px}}
.key .pr{{margin-left:0}}
.inf{{font-size:12px;line-height:16px;color:{MUTED};margin-top:4px}}
.lower{{position:absolute;left:{M}px;width:{816 - 2 * M}px;top:{AX_Y + 28}px;bottom:{M - 4}px;display:flex;flex-direction:column}}
.index{{display:grid;grid-template-columns:repeat(4,{span(3)}px);column-gap:{G}px;row-gap:8px;align-items:start}}
.index h3{{border-top:1.5px solid {INK};padding-top:6px;margin-bottom:-2px}}
.num{{float:left;width:50px;font-weight:200;font-size:42px;line-height:34px;letter-spacing:-.045em;margin:0 0 0 -3px;height:34px}}
.index .it .sd{{clear:left;padding-top:2px}}
.zero{{padding-top:12px}}
.it .name,.it .price{{font-size:13.5px;line-height:17px}}
.it .sd{{font-size:13px;line-height:16px;margin-top:1px}}
.it .ing{{font-size:12.5px;line-height:15px;margin-top:1px}}
.it .gg{{font-size:12px;line-height:15px;margin-top:2px}}
.zero{{margin-top:auto}}
.zero h3{{border-top:1.5px solid {INK};padding-top:6px;margin-bottom:6px}}
.zrow{{display:grid;grid-template-columns:repeat(4,{span(3)}px);column-gap:{G}px}}

/* ---------- back */
.grp,.bev{{position:relative;display:grid;grid-template-columns:{span(3)}px {span(9)}px;column-gap:{G}px}}
.band{{position:absolute;left:-9px;top:-9px;width:834px;height:{BAND_B + 9}px;background:{INK};color:{PAPER}}}
.bl{{position:absolute;left:{M + 9}px;top:{M + 9}px;width:{span(3)}px}}
.band h2{{font-weight:600;font-size:17px;line-height:22px}}
.band .bnote{{color:#C9C3B7}} .band .lgt{{color:#DAD4C8;margin-top:8px}}
.scale{{position:absolute;left:{SX0 + 9}px;top:{M + 13}px;width:{BW}px;height:{BAND_B - M - 13}px}}
.bnum{{position:absolute;top:0;transform:translateX(-50%);font-weight:200;font-size:48px;line-height:44px;letter-spacing:-.04em}}
.bnum:first-child{{transform:translateX(-12%)}}
.track{{position:absolute;left:-6px;top:50px;width:{BW + 12}px;height:20px}}
.bunit{{position:absolute;right:0;top:0;font-size:12px;line-height:16px;font-weight:600;color:#DAD4C8;display:none}}
.bcl{{position:absolute;top:74px;font-size:12px;line-height:16px;font-weight:600;white-space:nowrap}}
.bcl.c{{transform:translateX(-50%)}} .bcl.in{{top:52px;color:{INK}}} .bcl.r{{transform:translateX(-100%)}}
.bnote{{font-size:12px;line-height:16px;color:{MUTED}}}
.lgt{{font-size:12px;line-height:16px;color:{INK2}}} .lgt b{{font-weight:600;color:{INK}}}
.groups{{position:absolute;left:{M}px;top:{BAND_B + 12}px}}
.grp{{border-top:1.5px solid {INK};padding-top:7px}}
.grp+.grp{{margin-top:6px}}
.glab h3{{margin-bottom:3px}}
.gs{{font-family:'Source Serif 4',serif;font-style:italic;font-size:12.5px;line-height:16px;color:{INK2}}}
.gs+.gs{{margin-top:3px}}
.cards{{display:grid;grid-template-columns:repeat(4,{CARD_W}px);column-gap:{G}px;row-gap:8px}}
.card{{height:80px;border-top:.75px solid {INK};padding-top:5px;display:flex;flex-direction:column}}
.card .np{{height:31px;font-size:12.5px;line-height:15.5px}}
.card .name{{font-size:12.5px}} .card .price{{font-size:12.5px}}
.card .cls{{font-family:'Source Serif 4',serif;font-style:italic;font-size:12.5px;line-height:16px;color:{INK2};margin:0 0 1px}}
.card .age{{display:block;flex:none}} .card>*{{flex:none}}
.card .reg{{font-size:12px;line-height:15px;color:{MUTED};margin-top:1px}}
.bev{{position:absolute;left:{M}px;bottom:{M - 4}px;border-top:1.5px solid {INK};padding-top:7px}}
.bev .glab{{display:flex;flex-direction:column}} .bheads{{margin-bottom:auto}} .bheads h3+h3{{margin-top:4px}}
.bev .allergy{{font-family:'Source Serif 4',serif;font-style:italic;font-size:12.5px;line-height:16px;color:{INK2};margin-top:6px}}
.bgrid{{display:grid;grid-template-columns:repeat(4,{CARD_W}px);column-gap:{G}px;row-gap:6px}}
.bgrid h2{{font-weight:600;font-size:14px;line-height:18px}}
.bsub+.bsub{{margin-top:10px}}
.bsub h3{{margin-bottom:3px}}
.bsub .it+.it{{margin-top:5px}}
.bev .it .name,.bev .it .price{{font-size:12.5px;line-height:16px}}
.bev .it .sd{{font-size:12.5px;line-height:16px;color:{INK2}}}
.pmap,.ponly{{display:none}}

/* ---------- phone: one scroll, 390 css px */
@media (max-width:600px){{
 body{{display:block;padding:0;background:{PAPER}}}
 .page{{width:100%;height:auto;overflow:visible}}
 .art,.lab,.front>.bn{{display:none}}
 .pmap{{display:block;position:relative;width:{PW}px;height:{PFH + 40}px}}
 .pmap svg{{display:block}}
 .pmap .bn{{font-size:12px}}
 .plab{{position:absolute;font-weight:600;font-size:12px;line-height:16px}} .ply{{writing-mode:vertical-rl;transform:rotate(180deg);letter-spacing:.02em}}
 .mast{{position:static;width:auto;padding:24px 20px 20px}}
 .wm{{font-size:56px;line-height:60px}} .venue{{font-size:14px;line-height:20px}}
 .legend{{position:static;width:auto;padding:20px 20px 0}}
 .how{{font-size:15px;line-height:22px}}
 .gk,.gnote,.key,.inf{{font-size:13px;line-height:18px}}
 .lower{{position:static;width:auto;padding:28px 20px 0;display:block}}
 .index{{display:flex;flex-direction:column}}
 .index h3{{margin:24px 0 12px}}
 .cell{{display:block}}
 .index .it{{display:grid;grid-template-columns:52px 1fr;padding:10px 0;border-bottom:.5px solid #b8b3a8}}
 .index .it>*{{grid-column:2}} .index .it .sd{{padding-top:0}} .index .it .num{{float:none;width:auto;height:auto;margin:0;grid-column:1;grid-row:1/6;font-size:34px;line-height:32px}} .it .ing{{clear:none}}
 .it .name,.it .price{{font-size:17px;line-height:24px}}
 .it .sd{{font-size:15.5px;line-height:22px}} .it .ing{{font-size:15px;line-height:21px}} .it .gg{{font-size:14px;line-height:20px}}
 h3{{font-size:12.5px;line-height:18px}}
 .zero{{margin-top:32px}} .zrow{{display:block}} .zrow .cell{{padding:6px 0}}
 .page.back{{padding:40px 20px 40px;border-top:1.5px solid {INK};margin-top:36px}}
 .grp,.bev{{display:block;position:static}}
 .band{{position:static;width:auto;height:auto;margin:-40px -20px 0;padding:28px 20px 24px}}
 .bl{{position:static;width:auto}} .band h2{{font-size:22px;line-height:28px}}
 .scale{{position:relative;left:auto;top:auto;width:auto;height:112px;margin:18px 10px 0 4px}}
 .bnum{{font-size:34px;line-height:36px}} .track{{top:44px;width:calc(100% + 12px)}} .bcl{{top:70px;font-size:12px}}
 .lgt{{font-size:13px;line-height:18px;margin-top:4px}}
 .groups{{position:static;margin-top:20px}}
 .grp{{margin-top:22px}} .grp+.grp{{margin-top:22px}}
 .glab{{margin-bottom:10px}}
 .gs{{font-size:14px;line-height:20px}}
 .cards{{grid-template-columns:repeat(2,1fr);column-gap:16px;row-gap:12px}}
 .card{{height:auto;padding-bottom:6px}}
 .card .np{{height:auto;min-height:44px;font-size:15px;line-height:22px}} .card .name,.card .price{{font-size:15px}}
 .card .age{{width:100%;height:auto}} .card .cls{{font-size:14px;line-height:20px}} .card .reg{{font-size:13px;line-height:18px}}
 .bev{{position:static;margin-top:32px;display:flex;flex-direction:column-reverse}}
 .bgrid{{display:flex;flex-direction:column}} .bcol{{display:contents}} .bsub.cont h3{{display:none}} .bsub.cont{{margin-top:6px}}
 .index>*{{width:100%}} .bgrid h2{{font-size:18px;line-height:24px;margin:18px 0 8px}}
 .bsub{{margin-top:14px}}
 .bev .it .name,.bev .it .price{{font-size:16px;line-height:22px}} .bev .it .sd{{font-size:15px;line-height:21px}}
 .bev .glab{{margin-top:28px}} .bheads{{display:none}} .bgrid .ponly{{display:block}} .bcl.in{{top:46px}} .bev .allergy{{font-size:14px;line-height:20px}}
}}
/* ---------- print with bleed: each page on a 9.25 x 11.75 in sheet, 9 pt bleed, crop marks */
html.bleed body{{display:block;padding:0;gap:0;background:#fff}}
html.bleed .sheet{{position:relative;width:888px;height:1128px;background:#fff;page-break-after:always;break-after:page;overflow:hidden}}
html.bleed .sheet .page{{position:absolute;left:36px;top:36px;overflow:visible;box-shadow:0 0 0 12px {PAPER}}}
html.bleed .cm{{position:absolute;background:#000}}
@page{{size:9.25in 11.75in;margin:0}}
"""
HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cantina · Mapa de sabor</title><style>{CSS}</style></head><body>
{FRONT}
{BACK}
</body></html>"""
# phone map lives inside the front page, after the masthead (hidden on letter)
HTML = HTML.replace('</header>\n<div class="lab ly top', '</header>\n' + PHONE_MAP + '\n<div class="lab ly top', 1)
(HERE / "menu.html").write_text(HTML)
print("html", len(HTML))

# ================================================================== render + measured gates
from playwright.sync_api import sync_playwright
DSF = 3.125  # 816 css px * 3.125 = 2550 px (300 dpi letter)
HIDE = "(()=>{const s=document.createElement('style');s.textContent='.tx,.tx *{color:transparent!important}';document.head.appendChild(s)})()"
COLLECT = r"""(sel) => { const root = document.querySelector(sel); const pg = root.getBoundingClientRect();
 return [...root.querySelectorAll('.tx')].map(el => { const r = document.createRange(); r.selectNodeContents(el);
   const rs = [...r.getClientRects()].filter(a => a.width > 0 && a.height > 0).map(a => [a.left - pg.left, a.top - pg.top, a.width, a.height]);
   const s = getComputedStyle(el); return {text: el.innerText.trim().replace(/\s+/g,' ').slice(0, 60), cls: el.className, color: s.color, px: parseFloat(s.fontSize), rects: rs}; })
   .filter(t => t.rects.length && t.text.length); }"""
PAIRS = r"""(sel) => [...document.querySelector(sel).querySelectorAll('.np')].map(p => { const n = p.querySelector('.name'), c = p.querySelector('.price');
  const r = document.createRange(); r.selectNodeContents(n); const nr = [...r.getClientRects()].filter(a => a.width > 0); const last = nr[nr.length - 1];
  const cr = c.getBoundingClientRect(); const em = parseFloat(getComputedStyle(n).fontSize);
  return {name: n.innerText, price: c.innerText, gap_px: cr.left - last.right, em_px: em, gap_em: (cr.left - last.right) / em, same_line: Math.abs(cr.top - last.top) < 2}; })"""
DOM = r"""() => { const q = (r, s) => r.querySelector(s); const T = x => x ? x.textContent : null;
 const items = [...document.querySelectorAll('.page .it, .page .card')].map(it => ({name: T(q(it,'.name')), price: T(q(it,'.price')), sensory: T(q(it,'.sd')),
   ingredients: [...it.querySelectorAll('.ing .i')].map(i => i.textContent), garnish: T(q(it,'.gg .gar')), glass: T(q(it,'.gg .gl')), cls: T(q(it,'.cls')), region: T(q(it,'.reg')),
   proposed_ring: !!q(it,'.np .pr'), status: it.dataset.status}));
 return {items, text: document.body.innerText}; }"""

def lum(c):
    f = lambda v: (v / 255) / 12.92 if v / 255 <= 0.04045 else (((v / 255) + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])
def cr(a, b):
    la, lb = lum(a), lum(b); return (max(la, lb) + .05) / (min(la, lb) + .05)
def rgb(s):
    v = s[s.index("(") + 1:s.index(")")].split(","); return tuple(int(float(x)) for x in v[:3])

def worst(els, full, art, S):
    diff = ImageChops.difference(full, art).convert("L").point(lambda v: 255 if v > 24 else 0)
    out = []
    for t in els:
        tc = rgb(t["color"]); w = 99; wpx = None
        for x, y, ww, hh in t["rects"]:
            bb = (max(0, int(x * S)), max(0, int(y * S)), min(full.size[0], math.ceil((x + ww) * S)), min(full.size[1], math.ceil((y + hh) * S)))
            if bb[2] <= bb[0] or bb[3] <= bb[1]: continue
            ib = diff.crop(bb).getbbox()
            if ib: bb = (max(bb[0], bb[0] + ib[0] - 2), max(bb[1], bb[1] + ib[1] - 2), min(bb[2], bb[0] + ib[2] + 2), min(bb[3], bb[1] + ib[3] + 2))
            crop = art.crop(bb)
            for _, c in crop.getcolors(crop.size[0] * crop.size[1] + 1):
                r = cr(tc, c)
                if r < w: w, wpx = r, c
        out.append({"text": t["text"], "cls": t["cls"], "px": t["px"], "pt": round(t["px"] * .75, 2), "worst": round(w, 2), "bg": wpx})
    return out

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={"width": 900, "height": 2300}, device_scale_factor=DSF)
    pg.goto((HERE / "menu.html").as_uri(), wait_until="load"); pg.evaluate("document.fonts.ready")
    fonts = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family+' '+f.style)")
    res = {"fonts_loaded": fonts}
    for side in ("front", "back"):
        sel = f".page.{side}"
        res[side] = {"text": pg.evaluate(COLLECT, sel), "pairs": pg.evaluate(PAIRS, sel)}
        pg.locator(sel).screenshot(path=str(HERE / f"preview-{side}.png"))
    res["dom"] = pg.evaluate(DOM)
    res["overlap"] = pg.evaluate("""() => { const g = document.querySelector('.back .groups').getBoundingClientRect(), b = document.querySelector('.back .bev').getBoundingClientRect(),
       k = document.querySelector('.back .band').getBoundingClientRect(), f = document.querySelector('.front .index').getBoundingClientRect(), z = document.querySelector('.front .zero h3').getBoundingClientRect();
       return {back_groups_to_bev_px: b.top - g.bottom, back_band_to_groups_px: g.top - k.bottom, front_index_to_zero_rule_px: z.top - f.bottom}; }""")
    pg.evaluate(HIDE)
    for side in ("front", "back"): pg.locator(f".page.{side}").screenshot(path=str(HERE / f"_art-{side}.png"))
    # bleed PDF: 9.25 x 11.75 in sheet, trim at 0.375 in (27 pt), 9 pt bleed, crop marks in the slug
    pb = b.new_page(viewport={"width": 888, "height": 1128})
    pb.goto((HERE / "menu.html").as_uri(), wait_until="load"); pb.evaluate("document.fonts.ready")
    pb.evaluate("""() => { document.documentElement.classList.add('bleed');
      for (const pgEl of [...document.querySelectorAll('.page')]) { const sh = document.createElement('div'); sh.className = 'sheet'; pgEl.parentNode.insertBefore(sh, pgEl); sh.appendChild(pgEl);
        const add = (l, t, w, h) => { const d = document.createElement('div'); d.className = 'cm'; Object.assign(d.style, {left: l + 'px', top: t + 'px', width: w + 'px', height: h + 'px'}); sh.appendChild(d); };
        for (const x of [36, 852]) { add(x - .33, 0, .67, 20); add(x - .33, 1108, .67, 20); }
        for (const y of [36, 1092]) { add(0, y - .33, 20, .67); add(868, y - .33, 20, .67); } } }""")
    pb.pdf(path=str(HERE / "menu-print-bleed.pdf"), width="9.25in", height="11.75in", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
    bleed_box = pb.evaluate("""() => [...document.querySelectorAll('.page')].map(pg => { const a = pg.querySelector('.art, .band'); if (!a) return null; const r = a.getBoundingClientRect(), q = pg.getBoundingClientRect();
        return {art_left: r.left - q.left, art_top: r.top - q.top, art_right: r.right - q.right, art_bottom: r.bottom - q.bottom}; })""")
    res["bleed_box"] = bleed_box
    # phone
    ph = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    ph.goto((HERE / "menu.html").as_uri(), wait_until="load"); ph.evaluate("document.fonts.ready")
    res["phone"] = {"scrollWidth": ph.evaluate("document.documentElement.scrollWidth"), "height": ph.evaluate("document.documentElement.scrollHeight"),
                    "text": ph.evaluate(COLLECT.replace("const root = document.querySelector(sel); const pg = root.getBoundingClientRect();",
                                                        "const root = document.body; const pg = {left: 0, top: -scrollY};")
                                        .replace("a.top - pg.top", "a.top + scrollY"), "body"),
                    "pairs": ph.evaluate(PAIRS, "body")}
    res["phone"]["pmap_top"] = ph.evaluate("document.querySelector('.pmap').getBoundingClientRect().top + scrollY")
    ph.screenshot(path=str(HERE / "preview-phone.png"), full_page=True)
    ph.evaluate(HIDE); ph.screenshot(path=str(HERE / "_art-phone.png"), full_page=True)
    b.close()

# ---------- gates
G = {}
S = 3.125
cont = {}
for side in ("front", "back"):
    full = Image.open(HERE / f"preview-{side}.png").convert("RGB"); art = Image.open(HERE / f"_art-{side}.png").convert("RGB")
    cont[side] = worst(res[side]["text"], full, art, S)
full = Image.open(HERE / "preview-phone.png").convert("RGB"); art = Image.open(HERE / "_art-phone.png").convert("RGB")
cont["phone"] = worst(res["phone"]["text"], full, art, 3)
G["contrast_worst_pixel"] = {k: min(v, key=lambda t: t["worst"]) for k, v in cont.items()}
G["contrast_pass_4_5"] = all(t["worst"] >= 4.5 for v in cont.values() for t in v)
G["contrast_below_4_5"] = [dict(t, side=k) for k, v in cont.items() for t in v if t["worst"] < 4.5]

# legibility: letter >= 8.5 pt (11.33 css px) for every text element; phone >= 12 css px
G["letter_min_font_pt"] = round(min(t["px"] for s in ("front", "back") for t in res[s]["text"]) * .75, 2)
G["letter_min_font_ok"] = G["letter_min_font_pt"] >= 8.5
G["phone_min_font_px"] = min(t["px"] for t in res["phone"]["text"])
G["phone_min_font_ok"] = G["phone_min_font_px"] >= 12
G["phone_png"] = list(Image.open(HERE / "preview-phone.png").size)
G["phone_no_hscroll"] = res["phone"]["scrollWidth"] <= 390
G["letter_png"] = {s: list(Image.open(HERE / f"preview-{s}.png").size) for s in ("front", "back")}

# price association
allp = res["front"]["pairs"] + res["back"]["pairs"]
G["price_max_gap_em"] = round(max(p["gap_em"] for p in allp), 3)
G["price_all_same_line_within_1em"] = all(p["same_line"] and p["gap_em"] <= 1.0 for p in allp)
G["price_phone_ok"] = all(p["same_line"] and p["gap_em"] <= 1.0 for p in res["phone"]["pairs"])
G["price_violations"] = [p for p in allp + res["phone"]["pairs"] if not (p["same_line"] and p["gap_em"] <= 1.0)]

# safe area: every text line box >= 48 px (0.5 in) inside the trim
edges = []
for s in ("front", "back"):
    for t in res[s]["text"]:
        for x, y, w, h in t["rects"]: edges.append((x, y, 816 - (x + w), 1056 - (y + h), t["text"]))
G["safe_area_min_px"] = {"left": round(min(a[0] for a in edges), 2), "top": round(min(a[1] for a in edges), 2),
                         "right": round(min(a[2] for a in edges), 2), "bottom": round(min(a[3] for a in edges), 2)}
G["safe_area_min_in"] = {k: round(v / 96, 3) for k, v in G["safe_area_min_px"].items()}
G["safe_area_ok"] = min(G["safe_area_min_px"].values()) >= 48
G["bleed"] = {"art_box_vs_trim_px": res["bleed_box"], "bleed_mm": 3.175, "sheet": "9.25 x 11.75 in, trim offset 0.375 in, crop marks in the slug",
              "front_field_bleeds_top_right": res["bleed_box"][0]["art_top"] <= -9 and res["bleed_box"][0]["art_right"] >= 9,
              "back_band_bleeds_top_left_right": res["bleed_box"][1]["art_top"] <= -9 and res["bleed_box"][1]["art_left"] <= -9 and res["bleed_box"][1]["art_right"] >= 9,
              "paper_bleed": "each page carries a 12 px (9 pt) paper box-shadow on the sheet, so the ground also runs past trim"}

# DOM text diff vs manifest (names, prices, sensory, ingredients in order, garnish, glass)
dom = {}
for it in res["dom"]["items"]: dom.setdefault(it["name"], []).append(it)
want = []
for it in COCKTAILS: want.append(("cocktail", it))
for rows in MAN["spirits"].values(): want += [("spirit", i) for i in rows]
for rows in MAN["beer_cider"].values(): want += [("beer_cider", i) for i in rows]
for rows in MAN["wine"].values(): want += [("wine", i) for i in rows]
for rows in MAN["zero_proof"].values(): want += [("zero_proof", i) for i in rows]
diffs = []
for kind, it in want:
    got = dom.get(it["name"])
    if not got: diffs.append((it["name"], "missing")); continue
    g = got[0]
    if float(g["price"]) != float(it["price"]): diffs.append((it["name"], "price", g["price"], it["price"]))
    if kind != "spirit" and g["sensory"] != it["sensory"]: diffs.append((it["name"], "sensory", g["sensory"]))
    if kind == "cocktail":
        if g["ingredients"] != it["ingredients"]: diffs.append((it["name"], "ingredients", g["ingredients"]))
        if g["garnish"] != it["garnish"]: diffs.append((it["name"], "garnish", g["garnish"]))
        if g["glass"] != it["glass"]: diffs.append((it["name"], "glass", g["glass"]))
    if kind == "spirit" and g["cls"] != it["cls"]: diffs.append((it["name"], "class", g["cls"]))
    if g["proposed_ring"] != (it["status"] != "approved_db"): diffs.append((it["name"], "proposed ring"))
extra = [n for n in dom if n not in {i["name"] for _, i in want}]
G["dom_diff"] = {"items_expected": len(want), "items_found": sum(1 for _, i in want if i["name"] in dom), "differences": diffs, "extra_items": extra,
                 "counts": {"cocktails": 12, "spirits": sum(len(v) for v in MAN["spirits"].values()), "beer_cider": sum(len(v) for v in MAN["beer_cider"].values()),
                            "wine": sum(len(v) for v in MAN["wine"].values()), "zero_proof": sum(len(v) for v in MAN["zero_proof"].values())}}
G["dom_diff_ok"] = not diffs and not extra and G["dom_diff"]["items_found"] == len(want)
# spirit sensory lines: every manifest sensory string appears in the page text
txt = res["dom"]["text"]
G["spirit_sensory_all_printed"] = all(i["sensory"] in txt for rows in MAN["spirits"].values() for i in rows)
G["ingredient_role_order_ok"] = all(dom[i["name"]][0]["ingredients"] == i["ingredients"] for i in COCKTAILS)
G["garnish_separate_ok"] = all((i["garnish"] or "") not in dom[i["name"]][0]["ingredients"] for i in COCKTAILS)
BANNED = ["beauty lives here too", "sip at your own risk", "plants, people, pours", "plants · people · pours", "adventure tastes better together",
          "good drinks", "good people", "every round takes you further in", "stranger things grow", "a more beautiful drinking world", "curiosity grows here",
          "drink deeper", "fresh ideas", "higher vibes", "a higher state of drinking", "bold flavors", "brighter tomorrows", "brighter days"]
G["banned_lines_found"] = [w for w in BANNED if w in txt.lower()]
G["no_banned_lines"] = not G["banned_lines_found"]
G["coords_phg_inference"] = {f'{n:02d} {i["name"]}': {"bright_to_rich_x": COORDS[i["name"]][0], "clean_to_smoky_y": COORDS[i["name"]][1]} for n, i in enumerate(COCKTAILS, 1)}
G["fonts_loaded"] = res["fonts_loaded"]
import numpy as np
def dark_share(img, box):
    a = np.asarray(img.convert("RGB").crop(box), dtype=np.float32) / 255
    L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    return float((L < 0.25).mean())
_lf = dark_share(Image.open(HERE / "preview-front.png"), (round(FX * 3.125), 0, 2550, round(FB * 3.125)))
_pt = res["phone"]["pmap_top"]
_pf = dark_share(Image.open(HERE / "preview-phone.png"), (PFX * 3, round(_pt * 3), PW * 3, round((_pt + PFH) * 3)))
G["map_dark_share"] = {"letter_field": round(_lf, 4), "phone_field": round(_pf, 4), "relative_diff": round(abs(_pf - _lf) / _lf, 4),
                       "method": "share of pixels with relative luminance < 0.25 inside the plotted field rectangle (letter: field x 294.7-816, y 0-424 css px at 3.125x; phone: field x 30-390, y 0-500 css px of .pmap at 3x)"}
G["map_dark_share_ok"] = G["map_dark_share"]["relative_diff"] <= 0.10
G["block_clearances_px"] = res["overlap"]; G["no_block_overlap"] = min(res["overlap"].values()) >= 6
# point spacing on the letter map (discs must not collide)
pts = FRONT_PTS
G["min_disc_center_distance_px"] = round(min(math.dist(a[1:], b_[1:]) for k, a in enumerate(pts) for b_ in pts[k + 1:]), 1)
(HERE / "gates.json").write_text(json.dumps(G, indent=1, ensure_ascii=False))
(HERE / "measure.json").write_text(json.dumps({"contrast": cont, "pairs": {k: res[k]["pairs"] for k in ("front", "back")}, "phone_pairs": res["phone"]["pairs"]}, indent=1, ensure_ascii=False))
for k in ["contrast_pass_4_5", "contrast_worst_pixel", "letter_min_font_pt", "phone_min_font_px", "price_max_gap_em", "price_all_same_line_within_1em", "price_phone_ok",
          "safe_area_min_in", "safe_area_ok", "dom_diff_ok", "spirit_sensory_all_printed", "no_banned_lines", "phone_png", "phone_no_hscroll", "letter_png", "min_disc_center_distance_px", "block_clearances_px", "map_dark_share", "map_dark_share_ok", "bleed"]:
    print(k, json.dumps(G[k], ensure_ascii=False))
if G["contrast_below_4_5"]: print("LOW", G["contrast_below_4_5"][:8])
if G["price_violations"]: print("PRICE", G["price_violations"][:6])
if G["dom_diff"]["differences"]: print("DIFF", G["dom_diff"]["differences"])
for f in ("_art-front.png", "_art-back.png", "_art-phone.png"): (HERE / f).unlink(missing_ok=True)
