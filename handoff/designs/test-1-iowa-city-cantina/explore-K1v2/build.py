"""TEST-1 explore-K1v2 HILERAS (the field survey), v2 after the K panel.

Thesis: Iowa corn and Jalisco agave are both row crops. The menu is one field seen from the air,
and every drink is planted in its row.

v2: the field carries the menu. ONE terrain function per page,
    h(x, y) = -y + W(y) * B(x, y)        (B = knolls + a draw + two broad swells, W fades the relief to 0 by y = 520 pt)
draws everything:
  * hero (Python, contourpy): contour strips (Iowa) and red-earth agave strips, furrows = finer level lines,
    agave rosettes (plan view, varied scale/spacing) planted along the centre level line of each earth strip;
  * reading area (the same function, evaluated in the page script after the fonts load): every hilera's furrow is
    the level line of h through the row. Each drink's name is set horizontally where the furrow passes under it,
    so rows near the top step with the land and relax into straight hileras lower down; section strips are bounded
    by level lines too. Items in a row share their serve-line baseline (grid row + margin-top:auto).
The back page has no relief (W = 0): the spirits table and the beer/wine band are straight hileras.

Outputs: menu.html, preview-front.png, preview-back.png (2550x3300), preview-phone.png (1170 wide) + preview-phone-N.png
parts, menu-print-bleed.pdf, gates.json, visual_tests.json.  Run: python3 build.py
"""
import json, math, pathlib, hashlib, html, sys, subprocess
import numpy as np
import contourpy

HERE = pathlib.Path(__file__).resolve().parent
MAN_PATH = HERE.parent / "expanded-v2" / "manifest.json"
MAN = json.loads(MAN_PATH.read_text())
E = html.escape
NB = " "

# ------------------------------------------------------------------ palette
PAPER = "#F4EFE4"
TINT = "#ECE3CF"       # the De la Casa / beer-wine strip (a paler stubble ground)
INK = "#1C1916"
INK2 = "#4A4239"
INK3 = "#5A5046"
RED = "#AD1F18"        # survey red: prices only
OAK = "#6E4A2E"        # oak bars + oak scale bar
STRAW, STRAW_H = "#C2A46F", "#A68A52"
LOAM, LOAM_H = "#3A2F28", "#57483C"
SAGE, SAGE_H = "#6F8E84", "#557168"
EARTH, EARTH_H = "#86603F", "#735236"   # Jalisco earth: browner, lower chroma, away from survey red
AGV, AGV_L, AGV_D, AGV_S = "#6F9894", "#8DB2AB", "#4A726D", "#3E2E22"
RULE = "#8C7A63"       # strip edges in the reading area
FURROW = {"straw": "#BDA571", "sage": "#8FAAA2", "loam": "#A48A73", "table": "#CDBFA6"}

# ------------------------------------------------------------------ terrain
def smooth(a, b, t):
    u = np.clip((t - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)

def terrain(X, Y, T):
    B = np.zeros_like(X, dtype=float)
    for (a, cx, cy, sx, sy) in T["hills"]:
        B += a * np.exp(-(((X - cx) / sx) ** 2 + ((Y - cy) / sy) ** 2))
    w = 1 - smooth(T["wa"], T["wb"], Y)
    return -Y + w * B

# letter front, pt. Knolls (hero) + draw + two broad swells that roll through the reading area and fade by 520 pt.
T_FRONT = {"hills": [(150, 470, 0, 130, 88), (100, 70, -40, 125, 72), (-45, 292, 44, 92, 112),
                     (15, 520, 235, 150, 170), (-13, 250, 250, 130, 170), (5, 40, 220, 80, 120)],
           "wa": 150, "wb": 520}
# phone, css px (390 wide): same family of forms, scaled to the frame
T_PHONE = {"hills": [(110, 300, 0, 90, 70), (70, 30, -30, 88, 58), (-32, 170, 34, 60, 86),
                     (17, 330, 240, 110, 170), (-14, 120, 260, 90, 170)],
           "wa": 170, "wb": 900}
T_BACK = {"hills": [], "wa": 0, "wb": 1}

def ring_path(pts):
    return ("M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z") if len(pts) >= 3 else ""

def line_path(pts):
    return ("M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)) if len(pts) >= 2 else ""

def filled(gen, lo, hi):
    polys, offs = gen.filled(lo, hi)
    return " ".join(ring_path(pts[off[k]:off[k + 1]]) for pts, off in zip(polys, offs) for k in range(len(off) - 1))

def lines(gen, lv):
    return " ".join(line_path(seg) for seg in gen.lines(lv))

# ------------------------------------------------------------------ agave, plan view (the one literal motif)
def rosette_symbols():
    """Three plan-view agave variants: lanceolate leaves in two whorls, a cast shadow to the south-east."""
    out = []
    for v, (n1, n2, rot) in enumerate([(11, 7, 0.0), (12, 8, 0.2), (10, 6, 0.45)]):
        def whorl(n, L, w, r0, col):
            s = []
            for k in range(n):
                a = r0 + 2 * math.pi * k / n
                ca, sa = math.cos(a), math.sin(a)
                # leaf: base at centre, tip at L, width w (quadratic sides)
                P = lambda px, py: (px * ca - py * sa, px * sa + py * ca)
                b1, c1, t, c2 = P(0, 0), P(L * .5, w), P(L, 0), P(L * .5, -w)
                s.append(f'M{b1[0]:.2f} {b1[1]:.2f} Q{c1[0]:.2f} {c1[1]:.2f} {t[0]:.2f} {t[1]:.2f} Q{c2[0]:.2f} {c2[1]:.2f} {b1[0]:.2f} {b1[1]:.2f}Z')
            return f'<path d="{"".join(s)}" fill="{col}"/>'
        out.append(f'<symbol id="ag{v}" viewBox="-6 -6 12 12" overflow="visible">'
                   f'<ellipse cx=".7" cy=".8" rx="4.1" ry="3.8" fill="{AGV_S}" fill-opacity=".22"/>'
                   + whorl(n1, 4.6, 1.05, rot, AGV) + whorl(n2, 2.9, .95, rot + 0.3, AGV_L)
                   + f'<circle r=".75" fill="{AGV_D}"/></symbol>')
    return "".join(out)

def rng(seed):
    return np.random.default_rng(seed)

def plant(x, y, s, a, v):
    return f'<use href="#ag{v}" x="-6" y="-6" width="12" height="12" transform="translate({x:.2f} {y:.2f}) rotate({a:.0f}) scale({s:.3f})"/>'

def plant_along(seg, pitch, scale, seed):
    """Plant along a polyline by arc length, with jittered spacing and scale (plants are not identical)."""
    r = rng(seed)
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(seg, axis=0).T))]
    out, t = [], r.uniform(0, pitch)
    while t < d[-1]:
        x, y = np.interp(t, d, seg[:, 0]), np.interp(t, d, seg[:, 1])
        s = scale * r.uniform(0.72, 1.18)
        out.append(plant(x, y + r.uniform(-.5, .5), s, r.uniform(0, 360), int(r.integers(0, 3))))
        t += pitch * r.uniform(0.82, 1.22) * (0.85 + 0.3 * s / scale)
    return "".join(out)

def field_svg(P, T, cls, css):
    X0, Y0, X1, Y1 = P["frame"]
    xs = np.arange(X0 - 2, X1 + 2.01, 1.0); ys = np.arange(Y0 - 2, Y1 + 2.01, 1.0)
    X, Y = np.meshgrid(xs, ys)
    H = terrain(X, Y, T)
    gen = contourpy.contour_generator(xs, ys, H, fill_type=contourpy.FillType.OuterOffset, line_type=contourpy.LineType.Separate)
    bounds, kinds = P["bounds"], P["kinds"]           # kinds has len(bounds)+1; last = region below the last bound
    ref_x = P.get("ref_x", X0)
    cs = [float(terrain(np.array([ref_x], dtype=float), np.array([b], dtype=float), T)[0]) for b in bounds]   # levels through (ref_x, bound)
    top = float(H.max()) + 1
    levels = [top] + cs
    col = {"straw": STRAW, "loam": LOAM, "sage": SAGE, "earth": EARTH}
    hcol = {"straw": STRAW_H, "loam": LOAM_H, "sage": SAGE_H, "earth": EARTH_H}
    g = [f'<rect x="{X0}" y="{Y0}" width="{X1 - X0}" height="{Y1 - Y0}" fill="{col[kinds[-1]]}"/>']
    for i, kind in enumerate(kinds[:-1]):
        hi, lo = min(levels[i], top), levels[i + 1]
        if hi <= lo: continue
        d = filled(gen, lo, hi)
        if d: g.append(f'<path d="{d}" fill="{col[kind]}" fill-rule="evenodd"/>')
    fur = []
    for i, kind in enumerate(kinds[:-1]):
        hi, lo = min(levels[i], top), levels[i + 1]
        if hi <= lo: continue
        n = P["furrows"][kind]
        step = ((levels[i] - lo) if i else (cs[0] - cs[1])) / n
        lv = lo + step
        paths = []
        while lv < hi - 1e-6:
            paths.append(lines(gen, lv)); lv += step
        fur.append(f'<path d="{" ".join(paths)}" fill="none" stroke="{hcol[kind]}" stroke-width="{P["fw"]}" stroke-linecap="round"/>')
    g += fur
    g.append('<path d="' + " ".join(lines(gen, c) for c in cs if c < top) + f'" fill="none" stroke="{INK}" stroke-opacity=".3" stroke-width=".5"/>')
    # agave: along the centre level line of each earth strip (curved rows ride the contour; they straighten as W -> 0)
    for i, kind in enumerate(kinds[:-1]):
        if kind != "earth": continue
        hi, lo = min(levels[i], top), levels[i + 1]
        width = hi - lo
        nrow = 2 if width > P["two_rows"] else 1
        for k in range(nrow):
            lv = lo + width * (k + 1) / (nrow + 1)
            for seg in gen.lines(lv):
                if len(seg) < 3: continue
                sc = min(1.35, 0.45 + width / (nrow * 14.0)) * P["pscale"]
                g.append(plant_along(seg, P["pitch"] * sc, sc, int(abs(lv) * 97) + k))
    vb = f"{X0} {Y0} {X1 - X0} {Y1 - Y0}"
    return (f'<svg class="{cls}" viewBox="{vb}" style="{css}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">' + "".join(g) + "</svg>")

# strips: straight-row y of each boundary at ref_x (pt), varied widths; fewer, wider strips than v1
HERO_F = {"frame": (-9, -9, 621, 162), "ref_x": 0,
          "bounds": [-150, -118, -100, -64, -44, -10, 10, 40, 58, 84, 100, 124, 142],
          "kinds": ["straw", "loam", "sage", "straw", "loam", "earth", "straw", "loam", "earth", "straw", "sage", "earth", "loam", "straw"],
          "furrows": {"straw": 7, "loam": 5, "sage": 5, "earth": 4}, "fw": .5, "pitch": 13, "pscale": 1.12, "two_rows": 30}
HERO_P = {"frame": (0, 0, 390, 250), "ref_x": 0,
          "bounds": [-150, -118, -98, -64, -42, -6, 16, 46, 64, 98, 116, 146, 170, 204, 222],
          "kinds": ["straw", "loam", "sage", "straw", "loam", "earth", "straw", "loam", "earth", "straw", "sage", "earth", "straw", "earth", "loam", "straw"],
          "furrows": {"straw": 6, "loam": 4, "sage": 4, "earth": 4}, "fw": .55, "pitch": 16, "pscale": 1.05, "two_rows": 34}

def back_field(width, height, cls, css=""):
    """Back head band: the field fully straightened, one planted block of Jalisco earth (three staggered hileras of
    plan-view agave at varied size, with gaps where plants are missing), edged by an Iowa stubble strip."""
    r = rng(1102)
    g = [f'<rect x="-2" y="0" width="{width + 4}" height="{height}" fill="{EARTH}"/>']
    edge = height - 7
    g.append(f'<rect x="-2" y="{edge:.2f}" width="{width + 4}" height="7" fill="{STRAW}"/>')
    for k in range(1, 3):
        g.append(f'<line x1="-2" x2="{width + 2}" y1="{edge + 7 * k / 3:.2f}" y2="{edge + 7 * k / 3:.2f}" stroke="{STRAW_H}" stroke-width=".5"/>')
    for k in range(4):   # earth furrows between the rows
        yy = edge * (k + .02) / 3
        g.append(f'<line x1="-2" x2="{width + 2}" y1="{yy:.2f}" y2="{yy:.2f}" stroke="{EARTH_H}" stroke-width=".5"/>')
    for k, yy in enumerate((edge * 1 / 6, edge * 3 / 6, edge * 5 / 6)):
        x = r.uniform(0, 8) + 7 * (k % 2)
        while x < width + 8:
            if r.uniform() > .07:
                s = r.uniform(.95, 1.45)
                g.append(plant(x, yy + r.uniform(-.8, .8), s, r.uniform(0, 360), int(r.integers(0, 3))))
            x += 14.5 * r.uniform(.85, 1.15)
    return (f'<svg class="{cls}" viewBox="0 0 {width} {height}" preserveAspectRatio="xMinYMin slice" style="{css}" aria-hidden="true">' + "".join(g) + "</svg>")

# ------------------------------------------------------------------ glass glyphs: hairline family (contour-line grammar)
LIQ = {"Mezcal Negroni": ("#B8352A", "Campari → red"), "Carajillo": ("#3B2A20", "fresh espresso → dark"),
       "Batanga": ("#4A2C1E", "Mexican cola → dark"), "Manhattan": ("#A86A2A", "rye whiskey + sweet vermouth → amber"),
       "Brown Butter Old Fashioned": ("#B07A34", "bourbon → amber")}
def glyph(glass, garnish, liquid):
    k, sw = INK3, ".55"
    fill = liquid or "none"
    s = []
    if glass == "coupe":
        if liquid: s.append(f'<path d="M1.6 3 H10.4 Q9.8 7.1 6 7.3 Q2.2 7.1 1.6 3Z" fill="{fill}"/>')
        s.append(f'<path d="M.8 2.2 H11.2 Q10.6 7.9 6 8.1 Q1.4 7.9 .8 2.2 M6 8.1 V12.6 M3.4 12.9 H8.6" fill="none" stroke="{k}" stroke-width="{sw}"/>')
        rim = (.8, 11.2, 2.2)
    elif glass == "highball":
        if liquid: s.append(f'<rect x="3.2" y="3.4" width="5.6" height="9.2" fill="{fill}"/>')
        s.append(f'<path d="M2.8 .9 V12.9 H9.2 V.9 M4 4.2 h2.3 v2.3 h-2.3Z M5.4 7.6 h2.3 v2.3 h-2.3Z" fill="none" stroke="{k}" stroke-width="{sw}"/>')
        rim = (2.8, 9.2, .9)
    else:
        if liquid: s.append(f'<path d="M2 6.3 H10 L9.7 12.5 H2.3Z" fill="{fill}"/>')
        s.append(f'<path d="M1.4 4.4 L1.9 12.9 H10.1 L10.6 4.4 M3 6.9 h2.6 v2.6 h-2.6Z M6.2 8.1 h2.6 v2.6 h-2.6Z" fill="none" stroke="{k}" stroke-width="{sw}"/>')
        rim = (1.4, 10.6, 4.4)
    x0, x1, yr = rim
    if garnish == "salt rim":
        s.append(f'<path d="M{x0} {yr - .5} H{x1}" stroke="{k}" stroke-width="1" stroke-dasharray=".4 .6"/>')
    elif garnish == "lime wheel":
        s.append(f'<circle cx="{x1 - .2}" cy="{yr - .3}" r="2" fill="{PAPER}" stroke="{k}" stroke-width="{sw}"/><path d="M{x1 - 2.2} {yr - .3} H{x1 + 1.8} M{x1 - .2} {yr - 2.3} V{yr + 1.7}" stroke="{k}" stroke-width=".35"/>')
    elif garnish == "lime wedge":
        s.append(f'<path d="M{x1 - 2.6} {yr} L{x1 + 1} {yr} L{x1 - .4} {yr - 2.6}Z" fill="{PAPER}" stroke="{k}" stroke-width="{sw}"/>')
    elif garnish == "lime coin":
        s.append(f'<circle cx="{x1 - 1}" cy="{yr}" r="1.2" fill="{PAPER}" stroke="{k}" stroke-width="{sw}"/>')
    elif garnish == "orange peel":
        s.append(f'<path d="M{x1 - 3.4} {yr - .6} q1.2 -1.6 2.6 -.6 q1 .8 2 -.3" fill="none" stroke="{k}" stroke-width=".8" stroke-linecap="round"/>')
    elif garnish == "cocktail cherry":
        s.append(f'<circle cx="6" cy="5.2" r="1.2" fill="{PAPER}" stroke="{k}" stroke-width="{sw}"/><path d="M6 4 q.6 -2 2.4 -2.8" stroke="{k}" stroke-width=".4" fill="none"/>')
    elif garnish == "candied ginger":
        s.append(f'<path d="M{x1 - 1} {yr - 3.2} L{x0 + 5} {yr + 3}" stroke="{k}" stroke-width=".4"/><rect x="{x1 - 2.4}" y="{yr - 3.4}" width="2" height="2" fill="{PAPER}" stroke="{k}" stroke-width=".45" transform="rotate(20 {x1 - 1.4} {yr - 2.4})"/>')
    return f'<svg class="gl" viewBox="0 0 12 13.6" aria-hidden="true">{"".join(s)}</svg>'

# ------------------------------------------------------------------ content rules (K panel + Rob, expanded-v2)
REGION_SUPPRESS = {"Tres Generaciones Añejo"}   # shares NOM 1102 with Hornitos (region null): print no region
RECIPE_FLAG = {"Spicy Pineapple Margarita"}
POURS = MAN["spirit_pour_sizes"]["sizes"]        # ["1 oz", "1.5 oz", "2 oz"]
POUR_LABEL = {"1 oz": "1 oz", "1.5 oz": "1½ oz", "2 oz": "2 oz"}

def money(p):
    assert abs(p - round(p)) < 1e-9, p      # v2: every price is a whole dollar
    return str(int(round(p)))

def price_html(it, cls=""):
    return f'<span class="pr tx {cls}">{money(it["price"])}</span>'

def proposed(it): return it["status"] != "approved_db"
def ring(on): return '<span class="ring"></span>' if on else ""
def glue(s): return s.replace(" ", NB)

def head(label, tag="h2", cls=""):
    es, en = [s.strip() for s in label.split("·", 1)] if "·" in label else (label, "")
    inner = f'<i>{E(es)}</i>' + (f'<span class="dot"> · </span>{E(en)}' if en else "")
    return f'<{tag} class="tx {cls}">{inner}</{tag}>'

def caps(label, cls=""):
    return f'<h3 class="tx {cls}">{E(label)}</h3>'

def name_row(it, prices=None):
    pr = prices if prices is not None else price_html(it)
    return (f'<p class="np">{ring(proposed(it))}<span class="nm tx">{E(it["name"])}<span class="fw"></span></span>{pr}</p>')

def ing_line(parts, flag=None):
    spans = f'{NB}· '.join(f'<span class="i">{E(glue(p))}</span>' for p in parts)
    if flag: spans += f'{NB}· <span class="flag">{E(glue(flag))}</span>'
    return f'<p class="ig tx">{spans}</p>'

def cocktail(it):
    liq = LIQ.get(it["name"], (None, ""))[0]
    serve = (f'<span class="gar">{E(glue(it["garnish"]))}</span>{NB}· ' if it.get("garnish") else "") + f'<span class="gls">{E(it["glass"])}</span>'
    return (f'<article class="item ck" data-name="{E(it["name"])}" data-status="{it["status"]}">' + name_row(it)
            + f'<p class="sd tx">{E(it["sensory"])}</p>'
            + ing_line(it["ingredients"], "recipe to confirm" if it["name"] in RECIPE_FLAG else None)
            + f'<p class="gg">{glyph(it["glass"], it.get("garnish"), liq)}<span class="tx">{serve}</span></p></article>')

def zp_item(it):
    return (f'<article class="item zp" data-name="{E(it["name"])}" data-status="{it["status"]}">' + name_row(it)
            + f'<p class="sd tx">{E(it["sensory"])}</p><p class="ig tx"><span class="flag">recipe{NB}to{NB}confirm</span></p></article>')

def beer_item(it):
    r2 = (it.get("brewery_status") or "").startswith("PROPOSED") and not proposed(it)
    return (f'<article class="item bwi" data-name="{E(it["name"])}" data-status="{it["status"]}">' + name_row(it)
            + f'<p class="brw">{ring(r2)}<span class="tx">{E(it["brewery"])}</span></p>'
            + f'<p class="sd tx">{E(it["sensory"])}</p></article>')

def wine_item(it):
    r2 = (it.get("producer_status") or "").startswith("PROPOSED") and not proposed(it)
    prices = f'<span class="wp"><span class="pr tx wg">{money(it["glass"])}</span><span class="pr tx wb">{money(it["bottle"])}</span></span>'
    return (f'<article class="item bwi wn" data-name="{E(it["name"])}" data-status="{it["status"]}">' + name_row(it, prices)
            + f'<p class="brw">{ring(r2)}<span class="tx">{E(it["producer"])}</span></p>'
            + f'<p class="sd tx">{E(it["sensory"])}</p></article>')

# oak marks: NOM-006 class ranges; Cognac VSOP its own off-scale mark; mezcal with oak "not stated" is off the axis
AXS = 48.0     # oak axis in the survey table (0..36 months)
def oak_kind(it):
    c, s = it["cls"], it["sensory"]
    if "not stated" in (it.get("oak") or ""): return ("none", 0, 0)
    if c == "cognac VSOP": return ("vsop", 48, 48)
    if s.startswith("Unaged"): return ("dot", 0, 0)
    if c == "reposado": return ("bar", 2, 12)
    if c == "añejo": return ("bar", 12, 36)
    return ("none", 0, 0)

def oak_svg(it):
    k, a, b = oak_kind(it)
    u = AXS / 36
    s = [f'<path d="M1.5 7.6 H{1.5 + AXS}" stroke="{INK3}" stroke-opacity=".4" stroke-width=".45"/>'
         + "".join(f'<path d="M{1.5 + m * u:.2f} 7.6 V{5.4 if m % 36 else 4.6}" stroke="{INK3}" stroke-opacity=".55" stroke-width=".45"/>' for m in (0, 12, 24, 36))]
    if k == "dot":
        s.append(f'<circle cx="1.8" cy="5.6" r="2" fill="{OAK}"/>')
    elif k == "bar":
        s.append(f'<rect x="{1.5 + a * u:.2f}" y="4" width="{(b - a) * u:.2f}" height="3.6" fill="{OAK}"/>')
    elif k == "vsop":   # off the 0-36 scale: an open chevron beyond 36
        x = 1.5 + AXS
        s.append(f'<path d="M{x - 3:.2f} 5.8 H{x + 5:.2f} M{x + 1.8:.2f} 3.4 L{x + 5.4:.2f} 5.8 L{x + 1.8:.2f} 8.2" stroke="{OAK}" stroke-width="1.2" fill="none"/>')
    return f'<svg class="oak" viewBox="0 0 {AXS + 8} 9" aria-hidden="true" data-oak="{k}:{a}-{b}">{"".join(s)}</svg>'

def spirit_row(it):
    k = oak_kind(it)[0]
    region = None if it["name"] in REGION_SUPPRESS else it["region"]
    pours = "".join(f'<p class="s-p s{j}"><span class="pr tx {"std" if P == "1.5 oz" else ""}">{money(it["pours"][P])}</span></p>' for j, P in enumerate(POURS))
    return (f'<div class="sr" data-name="{E(it["name"])}" data-status="{it["status"]}">'
            f'<p class="s-nm">{ring(proposed(it))}<span class="nm tx">{E(it["name"])}</span></p>'
            f'<p class="s-nom">' + (f'<span class="lab">NOM{NB}</span><span class="tx nom">{E(it["nom"])}</span>' if it["nom"] else "") + '</p>'
            f'<p class="s-oak">' + (oak_svg(it) if k != "none" else "") + '</p>'
            + pours +
            f'<p class="s-sd"><span class="ssd tx">{E(it["sensory"])}</span>'
            + (f'<span class="rg tx">{NB}· {E(glue(region))}</span>' if region else "") + '<span class="fw"></span></p></div>')

def table_head():
    u = AXS / 36
    ticks = "".join('<span class="axn" style="left:%.2fpt">%d</span>' % (1.5 + m * u, m) for m in (0, 12, 24, 36))
    return ('<div class="sh"><p class="s-nm"></p><p class="s-nom"><span class="tx">NOM</span></p>'
            f'<p class="s-oak"><span class="axl tx">{ticks}</span></p>'
            + "".join(f'<p class="s-p s{j}">' + (ring(True) if j == 2 else "") + f'<span class="tx">{E(POUR_LABEL[P])}</span></p>' for j, P in enumerate(POURS))
            + '</div>')

def flight_row(f):
    return (f'<div class="sr fl" data-name="{E(f["name"])}" data-status="{f["status"]}">'
            f'<p class="s-nm fnm">{ring(True)}<span class="nm tx">{E(f["name"])}</span></p>'
            f'<p class="s-p s2"><span class="pr tx std">{money(f["price"])}</span></p>'
            f'<p class="s-sd"><span class="ssd tx">{E(f["sensory"])}</span></p>'
            f'<p class="s-it"><span class="tx">{E(" · ".join(f["items"]))}</span><span class="tx pour">{NB}· {E(f["pour"])}</span><span class="fw"></span></p></div>')

def spirits_cols():
    S = MAN["spirits"]
    def group(g):
        es, en = [x.strip() for x in g.split("·", 1)] if "·" in g else (g, "")
        return f'<div class="tg">{caps(es + (" · " + en if en else ""))}</div>' + "".join(spirit_row(it) for it in S[g])
    left = ["Casa · House pours", "Tequila · Blanco", "Tequila · Reposado"]
    right = [g for g in S if g not in left]
    fl = '<div class="flights" data-crop="table">' + '<div class="tg">' + caps("Vuelos · Flights") + '</div>' + "".join(flight_row(f) for f in MAN["flights"]) + '</div>'
    return (f'<div class="tcol">{table_head()}{"".join(group(g) for g in left)}</div>'
            f'<div class="tcol">{table_head()}{"".join(group(g) for g in right)}{fl}</div>')

def key_back():
    u = 108 / 36
    ticks = "".join(f'<path d="M{2.2 + m * u:.2f} 0 V{7 if m % 12 == 0 else 4}" stroke="{OAK}" stroke-width=".6"/>' for m in range(0, 37, 6))
    bar = (f'<svg class="scale" viewBox="0 0 114 8" aria-hidden="true"><rect x="2.2" y="2.2" width="{12 * u:.2f}" height="2.6" fill="{OAK}"/>'
           f'<rect x="{2.2 + 24 * u:.2f}" y="2.2" width="{12 * u:.2f}" height="2.6" fill="{OAK}"/><rect x="2.2" y="2.2" width="108" height="2.6" fill="none" stroke="{OAK}" stroke-width=".6"/>{ticks}</svg>')
    scl = "".join('<span class="tx" style="left:%.2f%%">%d</span>' % ((2.2 + m * u) * 100 / 114, m) for m in (0, 12, 24, 36))
    k1 = (f'<div class="key kb1"><p class="li sc"><span class="scwrap">{bar}<span class="scl">{scl}</span></span></p>'
          f'<p class="li"><span class="tx">months in oak (class range)</span></p>'
          f'<p class="li"><svg class="sw2" viewBox="0 0 8 8"><circle cx="4" cy="4" r="2" fill="{OAK}"/></svg><span class="tx">unaged</span></p></div>')
    k2 = ('<div class="key kb2"><p class="li"><span class="ring k"></span><span class="tx">proposed — pending approval</span></p>'
          '<p class="li"><span class="tx">beer ABV to confirm</span></p></div>')
    return k1, k2

def key_block(back=False):
    return ('<div class="key kf"><p class="li"><span class="ring k"></span><span class="tx">proposed — pending approval</span></p></div>')

# ------------------------------------------------------------------ assembly
def build_html():
    ck, zp = MAN["cocktails"], MAN["zero_proof"]
    c1, c2 = list(ck)
    rows = lambda items, fn: "".join('<div class="hl">' + "".join(fn(it) for it in items[i:i + 3]) + "</div>" for i in range(0, len(items), 3))
    zitems = zp[list(zp)[0]]
    zp_html = ('<div class="hl">' + "".join(zp_item(it) for it in zitems[:3]) + '</div>'
               '<div class="hl">' + zp_item(zitems[3]) + f'<div class="slot2">{key_block()}</div></div>')
    front = (f'<section class="band" data-crop="straw" data-bg="paper">{head(c1)}{rows(ck[c1], cocktail)}</section>'
             f'<section class="band tint" data-crop="sage" data-bg="tint">{head(c2)}{rows(ck[c2], cocktail)}</section>'
             f'<section class="band" data-crop="loam" data-bg="paper">{head(list(zp)[0])}{zp_html}</section>')
    # beer / cider / wine band on the 3-column grid: draft | cans + cider | wine + key; 5 hileras
    B, Wn = MAN["beer_cider"], MAN["wine"]
    draft, cans, cider = B["De barril · Draft"], B["En lata · Cans"], B["Sidra · Cider"]
    wines = [it for g in Wn.values() for it in g]
    k1, k2 = key_back()
    c1 = [beer_item(it) for it in draft]
    c2 = [beer_item(it) for it in cans] + [f'<div class="cellh">{caps("Sidra · Cider")}{beer_item(cider[0])}</div>']
    c3 = [wine_item(it) for it in wines] + [k1, k2]
    heads = (f'<div class="bwh">{caps("De barril · Draft")}{caps("En lata · Cans")}'
             f'<div class="wh">{caps("Vino · Wine")}<span class="wph tx"><span>copa</span><span>botella</span></span></div></div>')
    bw_html = heads + "".join(f'<div class="hl">{c1[i]}{c2[i]}{c3[i]}</div>' for i in range(5))
    back = (f'<section class="band spirits" data-crop="table" data-bg="paper">{head("Destilados · Spirits")}<div class="tcols">{spirits_cols()}</div></section>'
            f'<section class="band tint bw" data-crop="straw" data-bg="tint">{head("Cerveza, sidra y vino · Beer, cider & wine")}{bw_html}</section>')
    fonts_css = (HERE / "fonts" / "fonts.css").read_text().replace("url(", "url(fonts/")
    css = CSS
    for k, v in {"PAPER": PAPER, "TINT": TINT, "INK": INK, "INK2": INK2, "INK3": INK3, "RED": RED, "OAK": OAK, "RULE": RULE}.items():
        css = css.replace(f"%{k}%", v)
    for k, v in FURROW.items(): css = css.replace(f"%F_{k}%", v)
    terr = json.dumps({"front": T_FRONT, "phone": T_PHONE, "back": T_BACK})
    defs = f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{rosette_symbols()}</defs></svg>'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cantina Hileras Menu</title>
<style>{fonts_css}
{css}</style></head>
<body>{defs}
<div class="page front" data-terrain="front">
 {field_svg(HERO_F, T_FRONT, "field lt", "position:absolute;left:-9pt;top:-9pt;width:630pt;height:171pt")}
 {field_svg(HERO_P, T_PHONE, "field ph", "")}
 <div class="hl wmrow" data-crop="loam"><header class="wm"><h1 class="tx big">Cantina<span class="fw"></span></h1><p class="tx sub">&amp; Cocktail Bar · Iowa City, Iowa</p></header></div>
 <div class="ph-key">{key_block()}</div>
 <main class="menu">{front}</main>
</div>
<div class="page back" data-terrain="back">
 {back_field(630, 21, "bfield", "")}
 <main class="menu">{back}</main>
</div>
<script>
const TERRAIN = {terr};
{JS}
</script>
</body></html>"""

JS = r"""
function mk(tag, attrs) { const e = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; }
function terrainFor(pg) { const phone = innerWidth <= 600; const t = pg.dataset.terrain; return phone && t === 'front' ? TERRAIN.phone : TERRAIN[t]; }
function Bf(T, x, y) { let s = 0; for (const [a, cx, cy, sx, sy] of T.hills) { const dx = (x - cx) / sx, dy = (y - cy) / sy; s += a * Math.exp(-(dx * dx + dy * dy)); } return s; }
function Wf(T, y) { let u = Math.min(1, Math.max(0, (y - T.wa) / (T.wb - T.wa))); return 1 - u * u * (3 - 2 * u); }
function Hf(T, x, y) { return -y + Wf(T, y) * Bf(T, x, y); }
function levelY(T, x, c, y0) { let y = y0; for (let i = 0; i < 12; i++) y = Wf(T, y) * Bf(T, x, y) - c; return y; }
function layout() {
  const phone = innerWidth <= 600;
  document.querySelectorAll('.ov').forEach(e => e.remove());
  document.querySelectorAll('.page .item, .page .wm, .page .slot2').forEach(e => e.style.paddingTop = '');
  document.querySelectorAll('.page').forEach(pg => {
    const T = terrainFor(pg), K = phone ? 1 : 0.75;  // terrain units per css px (pt on letter, px on phone)
    const P = () => pg.getBoundingClientRect();
    const rows = [];
    // 1) plant each hilera: names sit where the furrow (a level line of h) passes under them
    pg.querySelectorAll('.hl').forEach(hl => {
      if (!hl.offsetParent) return;
      const units = phone ? [...hl.querySelectorAll('.item, .wm')].map(it => [it]) : [[...hl.querySelectorAll('.item, .wm')]];
      for (const items of units) {
        if (!items.length) continue;
        const pr = P();
        const pts = items.map(it => { const nm = it.querySelector('.nm, .big'); const r = document.createRange(); r.selectNodeContents(nm.firstChild);
          const a = r.getBoundingClientRect(); const fw = it.querySelector('.fw').getBoundingClientRect();
          return {it, x: ((a.left + a.right) / 2 - pr.left) * K, y: (fw.bottom - pr.top) * K}; });
        const y0 = Math.min(...pts.map(p => p.y));
        const c = Math.max(...pts.map(p => Hf(T, p.x, y0)));
        for (const p of pts) { const yj = levelY(T, p.x, c, y0); const pad = Math.max(0, (yj - y0) / K); if (pad > 0.05) p.it.style.paddingTop = pad + 'px'; }
        const slot = hl.querySelector('.slot2'); if (slot && !phone) { const yj = levelY(T, 400, c, y0); }
        const band = hl.closest('[data-crop]');
        rows.push({c, y0, items, band, hl});
      }
    });
    // 2) draw: section strips (level lines through each band top) and the furrows
    const pr = P(), Wp = pr.width * K, Hp = pr.height * K, bl = phone ? 0 : 9;
    const svg = mk('svg', {class: 'ov', viewBox: `${-bl} ${0} ${Wp + 2 * bl} ${Hp + bl}`, preserveAspectRatio: 'none'});
    svg.style.cssText = `position:absolute;left:${-bl / K}px;top:0;width:${(Wp + 2 * bl) / K}px;height:${(Hp + bl) / K}px;z-index:0;pointer-events:none;overflow:visible`;
    const xs = []; for (let x = -bl; x <= Wp + bl + 0.01; x += 3) xs.push(x);
    const lineAt = (c, y0, x0, x1) => { const pts = xs.filter(x => x >= x0 - 1e-6 && x <= x1 + 1e-6); return pts.map((x, i) => (i ? 'L' : 'M') + x.toFixed(2) + ' ' + levelY(T, x, c, y0).toFixed(2)).join(' '); };
    const bands = [...pg.querySelectorAll('.band')].filter(b => b.offsetParent);
    const tops = bands.map(b => { const r = b.getBoundingClientRect(); const y = (r.top - pr.top) * K; return {b, c: Hf(T, 0, y), y}; });
    tops.sort((a, b) => a.y - b.y);
    tops.forEach((t, i) => {
      const next = tops[i + 1];
      const top = xs.map(x => [x, levelY(T, x, t.c, t.y)]);
      const bot = next ? xs.map(x => [x, levelY(T, x, next.c, next.y)]) : xs.map(x => [x, Hp + bl]);
      if (t.b.classList.contains('tint')) {
        const d = 'M' + top.map(p => p[0].toFixed(2) + ' ' + p[1].toFixed(2)).join(' L') + ' L' + bot.reverse().map(p => p[0].toFixed(2) + ' ' + p[1].toFixed(2)).join(' L') + ' Z';
        svg.appendChild(mk('path', {d, fill: getComputedStyle(document.documentElement).getPropertyValue('--tint').trim()}));
      }
      if (i > 0 || pg.dataset.terrain === 'back') svg.appendChild(mk('path', {d: lineAt(t.c, t.y, -bl, Wp + bl), fill: 'none', stroke: getComputedStyle(document.documentElement).getPropertyValue('--rule').trim(), 'stroke-width': phone ? 1 : .7}));
    });
    for (const r of rows) {
      const col = getComputedStyle(r.band).getPropertyValue('--furrow').trim() || '#A48A73';
      // segments: one per item (its column), the first from the left bleed, the last to the right bleed;
      // each ends at its column edge, so a rule never runs on into the next drink's ring
      const wm = r.items[0].classList.contains('wm');
      if (wm) {  // a set lock-up: the furrow runs flat under the words, and leaves on the land's level lines either side
        const b = r.items[0].getBoundingClientRect(); const xl = (b.left - pr.left) * K - 6, xr = (b.left - pr.left) * K + [...r.items[0].children].reduce((m, e) => Math.max(m, (e.getBoundingClientRect().right - b.left) * K), 0) + 6;
        const cl = Hf(T, xl, r.y0), cr = Hf(T, xr, r.y0);
        const d = lineAt(cl, r.y0, -bl, xl) + ` L${xr.toFixed(2)} ${r.y0.toFixed(2)} ` + lineAt(cr, r.y0, xr, Wp + bl).replace(/^M/, 'L');
        svg.appendChild(mk('path', {d, fill: 'none', stroke: col, 'stroke-width': phone ? 1.2 : .8}));
      } else svg.appendChild(mk('path', {d: lineAt(r.c, r.y0, -bl, Wp + bl), fill: 'none', stroke: col, 'stroke-width': phone ? 1 : .6}));
    }
    // survey-table rows (straight hileras): one furrow under each row, within its table column
    pg.querySelectorAll('.sr .fw').forEach(m => { if (!m.offsetParent) return;
      const row = m.closest('.sr'), tc = m.closest('.tcol');
      const y = phone ? (row.getBoundingClientRect().bottom - pr.top - 5) : (m.getBoundingClientRect().bottom - pr.top) * K + .3;
      const cr = tc.getBoundingClientRect(), first = !tc.previousElementSibling, last = !tc.nextElementSibling;
      const x0 = phone || first ? -bl : (cr.left - pr.left) * K - 12, x1 = phone || last ? Wp + bl : (cr.right - pr.left) * K + 4;
      svg.appendChild(mk('path', {d: `M${x0.toFixed(2)} ${y.toFixed(2)} H${x1.toFixed(2)}`, stroke: getComputedStyle(row.closest('[data-crop]')).getPropertyValue('--furrow').trim(), 'stroke-width': phone ? 1 : .55})); });
    pg.insertBefore(svg, pg.firstChild.nextSibling);
  });
  document.documentElement.dataset.laid = '1';
}
document.fonts.ready.then(() => requestAnimationFrame(layout));
let rz; window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(layout, 50); });
"""

CSS = r"""
:root{--paper:%PAPER%;--tint:%TINT%;--ink:%INK%;--ink2:%INK2%;--ink3:%INK3%;--red:%RED%;--oak:%OAK%;--rule:%RULE%;--bg:var(--paper)}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#d9d4c8}
body{font-family:'Newsreader',serif;color:var(--ink);-webkit-font-smoothing:antialiased;font-kerning:normal;text-rendering:geometricPrecision}
.page{position:relative;width:612pt;height:792pt;background:var(--paper);overflow:hidden;margin:0 auto}
.field.ph,.ph-key,.ph-axis,.lab{display:none}
.tx{position:relative;z-index:2}
.ig,.gg,h3,.key,.sub,.c-cl,.c-nom,.c-rg,.c-pr,.th,.pr,.flag,.vs{font-family:'IBM Plex Sans Condensed',sans-serif}
[data-bg=tint]{--bg:var(--tint)}
.band{position:relative;--furrow:%F_straw%}
.band[data-crop=sage]{--furrow:%F_sage%}
.band[data-crop=loam],.wmrow{--furrow:%F_loam%}
.band[data-crop=table]{--furrow:%F_table%}
/* grid: 3 equal columns of 166.33 pt, 20 pt gutters, from x = 36.5 pt */
.menu{position:absolute;left:37pt;width:538pt;z-index:1}
.front .menu{top:228pt}
.hl{display:grid;grid-template-columns:repeat(3,1fr);column-gap:20pt;padding:0 0 10pt;position:relative;z-index:1}
/* wordmark lock-up: sits on the first furrow */
.wmrow{position:absolute;left:37pt;top:166pt;width:538pt;display:block;padding:0;z-index:3}
.wm{display:flex;align-items:baseline;gap:12pt}
.wm .big{font-weight:420;font-size:62pt;line-height:62pt;letter-spacing:-.018em;font-variation-settings:'opsz' 72;background:var(--paper);padding:0 7pt;margin-left:-7pt}
.wm .sub{font-size:10.5pt;font-weight:500;letter-spacing:.035em;background:var(--paper);padding:0 4pt;margin-left:-4pt}
.fw{display:inline-block;width:0;height:0;vertical-align:baseline}
/* heads: level 1 = 20 pt serif (1.67x names); level 2 = tracked caps <= 3 words */
h2{font-weight:500;font-size:20pt;line-height:24pt;padding:6pt 0 5pt;letter-spacing:-.005em;position:relative;z-index:2}
h2 i{font-weight:500}
h2 .dot{color:var(--ink3)}
h3{font-size:8.5pt;line-height:11pt;font-weight:600;letter-spacing:.12em;text-transform:uppercase}
/* item stack */
.item{position:relative;display:flex;flex-direction:column}
.np{font-size:12pt;line-height:15pt;position:relative;white-space:nowrap}
.nm{font-weight:600;background:var(--bg);padding:0 3pt;margin-left:-3pt;font-variation-settings:'opsz' 14;letter-spacing:-.006em}
.pr{color:var(--red);font-weight:500;font-size:11pt;font-variant-numeric:tabular-nums lining-nums;background:var(--bg);padding:0 3pt 0 3.5pt}
.pr.tbc{color:var(--ink3);letter-spacing:.06em;font-size:9.5pt}
.sq{display:inline-block;width:5pt;height:5pt;border:.6pt solid var(--ink3);margin-left:1pt;vertical-align:.5pt;background:var(--bg);position:relative;z-index:2}
.ring{position:absolute;left:-10pt;top:6.2pt;width:5.6pt;height:5.6pt;border:.6pt solid var(--ink3);border-radius:50%;background:var(--bg);z-index:2;box-shadow:0 0 0 2.5pt var(--bg)}
.sd{font-style:italic;font-size:10.5pt;line-height:13pt;color:var(--ink2);margin-top:1.5pt;font-variation-settings:'opsz' 11;text-wrap:pretty}
.ig{font-size:9.5pt;line-height:12pt;margin-top:1.5pt;text-wrap:pretty}
.i{white-space:nowrap}
.flag{font-style:italic;color:var(--ink3);white-space:nowrap}
.gg{font-size:9pt;line-height:12pt;color:var(--ink3);margin-top:auto;padding-top:2pt;position:relative}
.gg .gl{position:absolute;left:-14pt;bottom:1.2pt;width:10.5pt;height:11.9pt}
.gg .tx span{white-space:nowrap}
.sv{color:var(--ink3)}
.slot2{grid-column:2 / 4;display:flex;align-items:flex-end}
.zp .ig{margin-top:auto;padding-top:2pt}
.key{font-size:8.5pt;line-height:12pt;color:var(--ink3)}
.kf{display:flex;flex-direction:column;gap:1pt;padding-left:0}
.kf .li{display:flex;align-items:center;gap:6pt}
.kf .fl{font-style:italic}
.ring.k{position:relative;left:0;top:0;display:inline-block;box-shadow:none;background:transparent}
.sq.k{margin:0}
/* back */
.bfield{position:absolute;left:-9pt;top:-9pt;width:630pt;height:21pt}
.back .menu{top:14pt}
.spirits>h2{padding:3pt 0 0}
.tcols{display:grid;grid-template-columns:1fr 1fr;column-gap:20pt;position:relative}
.tcol{position:relative}
.sh,.sr{display:grid;grid-template-columns:1fr 20pt 54pt 21pt 24pt 21pt;align-items:start}
.sh{font-family:'IBM Plex Sans Condensed',sans-serif;font-size:8pt;line-height:10pt;color:var(--ink3);letter-spacing:.04em;padding:0 0 1pt}
.sh .s-oak{position:relative;height:10pt}
.axl{position:absolute;left:0;top:0;width:100%;height:10pt}
.axn{position:absolute;top:0;transform:translateX(-50%);letter-spacing:0}
.sh .s-p{position:relative;white-space:nowrap}
.sh .ring{left:auto;right:-8.5pt;top:2.3pt;width:5pt;height:5pt}
.tg{padding:4pt 0 0;position:relative;z-index:2}
.sr{position:relative}
.s-nm{font-size:9.5pt;line-height:10.5pt;white-space:nowrap;position:relative;letter-spacing:-.008em}
.sr .nm{font-weight:500;font-variation-settings:'opsz' 11;background:none;padding:0;margin:0}
.sr .ring{top:2.8pt}
.s-nom{font-family:'IBM Plex Sans Condensed',sans-serif;font-size:8.5pt;line-height:10.5pt;color:var(--ink2);font-variant-numeric:tabular-nums;text-align:right;margin-top:-.75pt}
.s-oak{position:relative;white-space:nowrap}
.s-oak .oak{display:inline-block;width:56pt;height:9pt;vertical-align:-1.4pt}
.vs{position:absolute;left:34pt;top:-7.5pt;font-family:'IBM Plex Sans Condensed',sans-serif;font-size:7.5pt;color:var(--ink3);background:var(--paper);padding:0 1pt}
.s-p{text-align:right;line-height:10.5pt;margin-top:-1.5pt}
.s-oak{line-height:10.5pt}
.sr .pr{font-size:9.5pt;padding:0;background:none;font-weight:400}
.sr .pr.std{font-weight:600}
.s-sd{grid-column:1 / -1;font-size:8.5pt;line-height:9pt;padding:0 0 1.2pt}
.ssd{font-style:italic;color:var(--ink2);font-variation-settings:'opsz' 9}
.rg{font-family:'IBM Plex Sans Condensed',sans-serif;color:var(--ink3)}
.s-sd .fw,.s-it .fw{vertical-align:-2.6pt}
.fl .fnm{grid-column:1 / 6}
.s-it{grid-column:1 / -1;font-family:'IBM Plex Sans Condensed',sans-serif;font-size:8.5pt;line-height:10pt;padding:0 0 2.5pt}
.flights{margin-top:3pt}
.bw>h2{padding-top:4pt;padding-bottom:1pt}
.bwh{display:grid;grid-template-columns:repeat(3,1fr);column-gap:20pt;padding:0 0 3pt}
.wh{display:flex;justify-content:space-between;align-items:baseline}
.wph{display:flex;font-family:'IBM Plex Sans Condensed',sans-serif;font-size:8pt;letter-spacing:.1em;text-transform:uppercase;color:var(--ink3)}
.wph span{width:36pt;text-align:right}
.bw .hl{padding-bottom:4.5pt}
.bwi .np{font-size:11pt;line-height:13pt}
.bwi .pr{font-size:10.5pt}
.brw{font-family:'IBM Plex Sans Condensed',sans-serif;font-size:8.5pt;line-height:10pt;color:var(--ink3);position:relative;margin-top:.5pt}
.brw .ring{left:-10pt;top:2.2pt;width:5pt;height:5pt}
.bwi .sd{font-size:9.5pt;line-height:11pt;margin-top:auto}
.wn .np{display:flex;align-items:baseline}
.wp{margin-left:auto;display:flex}
.wp .pr{width:36pt;text-align:right;padding:0 0 0 3pt;background:var(--bg)}
.wp .wb{font-weight:400}
.cellh h3{margin:-12pt 0 1pt}
.cellh{display:flex;flex-direction:column}
.cellh .item{flex:1}
.key{font-family:'IBM Plex Sans Condensed',sans-serif;font-size:8.5pt;line-height:11pt;color:var(--ink3);position:relative;z-index:2}
.key .tx{background:var(--bg);padding:0 2pt;margin-left:-2pt}
.kb1,.kb2{display:flex;flex-direction:column;justify-content:flex-end;gap:1pt}
.key .li{display:flex;align-items:center;gap:5pt}
.scwrap{display:inline-flex;flex-direction:column;align-items:flex-start;gap:1pt;position:relative;background:var(--bg)}
.key .scale{width:114pt;height:8pt}
.scl{position:relative;display:block;width:114pt;height:10pt;color:var(--oak)}
.scl span{position:absolute;top:0;transform:translateX(-50%)}
.sw2{width:8pt;height:8pt}

/* ---------------------------------------------------------------- phone */
@media (max-width:600px){
 html,body{background:var(--paper)}
 .page{width:100%;height:auto;overflow:hidden;padding:0 24px 8px}
 .field.lt{display:none}
 .field.ph{display:block;width:calc(100% + 48px);height:250px;margin:0 -24px}
 .wmrow{position:static;width:auto;padding:30px 0 0}
 .wm{flex-direction:column;align-items:flex-start;gap:6px}
 .wm .big{font-size:64px;line-height:60px;margin-left:-5px;padding:0 5px}
 .wm .sub{font-size:14px}
 .ph-key{display:block;padding:14px 0 0}
 .key{font-size:13px;line-height:18px}
 .kf .li{gap:8px}
 .ring{left:-15px;top:8px;width:8px;height:8px;border-width:1px}
 .sq{width:8px;height:8px;border-width:1px}
 .menu{position:static;width:auto}
 .hl,.bw .hl{display:block;padding:0}
 .slot2{display:none}
 h2{font-size:28px;line-height:32px;padding:26px 0 12px}
 .item{padding:0 0 20px}
 .np{font-size:18px;line-height:24px;white-space:normal}
 .pr{font-size:17px}
 .pr.tbc{font-size:14px}
 .sd{font-size:16px;line-height:21px}
 .ig{font-size:15px;line-height:20px}
 .gg{font-size:14px;line-height:19px;padding-top:3px}
 .gg .gl{left:-20px;width:15px;height:17px;bottom:1px}
 .back{padding-top:0}
 .back .menu{display:flex;flex-direction:column}
 .band.bw{order:-1}
 .bfield{position:static;display:block;width:calc(100% + 48px);height:90px;margin:0 -24px}
 .tcols{display:block}
 .tcol+.tcol .sh{display:none}
 .sh{grid-template-columns:1fr 34px 34px 34px;font-size:12px;line-height:16px;padding:6px 0 4px}
 .sh .s-nom,.sh .s-oak{display:none}
 .sh .ring{left:-14px;top:4px;width:8px;height:8px}
 .sr{grid-template-columns:1fr 34px 34px 34px;padding:0 0 10px}
 .s-nm{grid-column:1;grid-row:1;font-size:16px;line-height:22px}
 .sr .s0{grid-column:2;grid-row:1}.sr .s1{grid-column:3;grid-row:1}.sr .s2{grid-column:4;grid-row:1}
 .s-sd{grid-column:1 / -1;grid-row:2;font-size:14px;line-height:19px;padding:0}
 .s-nom{grid-column:1;grid-row:3;font-size:13px}
 .lab{display:inline}
 .s-oak{grid-column:2 / 5;grid-row:3;justify-self:end}
 .s-oak .oak{width:86px;height:13px;vertical-align:-2px}
 .vs{position:static;font-size:11px;margin-left:3px;background:none}
 .sr .pr{font-size:15px}
 .sr .ring{top:7px}
 .fl .fnm{grid-column:1 / 4;white-space:normal}
 .s-it{grid-row:3;font-size:13px;line-height:18px}
 .tg{padding:20px 0 6px}
 h3{font-size:13px;line-height:17px}
 .bwh{display:none}
 .cellh h3{margin:0 0 8px}
 .bwi .np{font-size:18px;line-height:24px}
 .bwi .pr{font-size:17px}
 .brw{font-size:14px;line-height:19px}
 .brw .ring{left:-15px;top:5px;width:8px;height:8px}
 .bwi .sd{font-size:15px;line-height:20px}
 .wp .pr{width:48px}
 .kb1,.kb2{padding:6px 0}
 .key{font-size:13px;line-height:18px}
 .key .scale,.scl{width:124px}
 .scl{height:17px}
}
"""

if __name__ == "__main__":
    (HERE / "menu.html").write_text(build_html())
    print("menu.html", len((HERE / "menu.html").read_text()) // 1024, "KB; manifest sha256", hashlib.sha256(MAN_PATH.read_bytes()).hexdigest()[:16])
    if "--html-only" not in sys.argv:
        subprocess.run([sys.executable, str(HERE / "render.py")], check=True, cwd=HERE)
        subprocess.run([sys.executable, str(HERE / "finalize.py")], check=True, cwd=HERE)
        vt = subprocess.run([sys.executable, str(HERE.parent.parent / "tools" / "visual_tests.py"), "preview-front.png", "preview-back.png"], check=True, cwd=HERE, capture_output=True, text=True)
        (HERE / "visual_tests.json").write_text(vt.stdout)
        for r in json.loads(vt.stdout)["results"]:
            print(r["file"], "primary", r["primary_area_pct"], "p:s", r["primary_to_secondary"], "accent", r["accent_area_pct"], "regions", r["squint_salient_regions"])
