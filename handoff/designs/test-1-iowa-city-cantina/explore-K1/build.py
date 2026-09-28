"""TEST-1 explore-K1 HILERAS (the field survey).

Thesis: Iowa corn and Jalisco agave are both row crops. The menu is one field seen from the air,
and every drink is planted in its row.

Everything drawn here is vector geometry computed from one terrain function:
  h(x, y) = -y + w(y) * B(x, y)
  a plane that falls down the page (so level lines far from the hills are straight rows), plus two
  knolls and a draw (B), faded out by a window w(y). The level lines of h are the contour-ploughed
  strips (Iowa); where w = 0 they are straight and become agave hileras on red Jalisco earth.
  The fine furrows inside each strip are more level lines of the same h. Relief shading is a
  quantised hillshade of B (Imhof: light from the north-west) drawn as filled vector bands.
  Below the hero the straight furrows continue as the typographic grid: every drink's name sits on a
  furrow (drawn at the measured baseline, masked under the words like a map label halo).

Outputs (this folder): menu.html, preview-front.png, preview-back.png (2550x3300), preview-phone.png
(1170 wide), menu-print-bleed.pdf (2 pages, 3.175 mm bleed + crop marks), gates.json.
Requires: numpy, contourpy, pillow, pypdf, playwright (Chromium at /opt/pw-browsers).
"""
import json, math, pathlib, hashlib, re, html
import numpy as np
import contourpy

HERE = pathlib.Path(__file__).resolve().parent
MAN_PATH = HERE.parent / "expanded-v1" / "manifest.json"
MAN = json.loads(MAN_PATH.read_text())
E = html.escape

# ------------------------------------------------------------------ palette
PAPER = "#F4EFE4"
INK = "#1C1916"
INK2 = "#4A4239"      # sensory
INK3 = "#5A5046"      # serve line, labels
RED = "#B3261E"       # survey red: prices + scale bar only
STRAW, STRAW_H = "#C2A46F", "#A68A52"          # corn stubble strip, its furrows
LOAM, LOAM_H = "#3A2F28", "#57483C"            # Iowa black loam, ploughed furrows (lighter)
SAGE, SAGE_H = "#6F8E84", "#557168"            # blue-green hay/sod strip (agave's colour, Iowa side)
EARTH, EARTH_H = "#8E4B2F", "#7A3F27"          # Jalisco red earth under the agave rows
AGV, AGV_L, AGV_D = "#6C9A96", "#8DB6B0", "#44716B"  # agave rosette, plan view

# ------------------------------------------------------------------ terrain
def smooth(a, b, t):
    u = np.clip((t - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)

def gauss(X, Y, cx, cy, sx, sy):
    return np.exp(-(((X - cx) / sx) ** 2 + ((Y - cy) / sy) ** 2))

def terrain(X, Y, P):
    B = np.zeros_like(X)
    for (a, cx, cy, sx, sy) in P["hills"]:
        B += a * gauss(X, Y, cx, cy, sx, sy)
    w = 1 - smooth(P["wa"], P["wb"], Y)
    return -Y + w * B, w * B

def ring_path(pts):
    if len(pts) < 3: return ""
    s = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
    return s + " Z"

def line_path(pts):
    if len(pts) < 2: return ""
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)

def filled(gen, lo, hi):
    polys, offs = gen.filled(lo, hi)
    out = []
    for pts, off in zip(polys, offs):
        for k in range(len(off) - 1):
            out.append(ring_path(pts[off[k]:off[k + 1]]))
    return " ".join(out)

def lines(gen, lv):
    return " ".join(line_path(seg) for seg in gen.lines(lv))

def rosette_symbol():
    """Agave in plan view (aerial): 13 narrow leaves, two tones. The one literal motif, used only as a planting pattern."""
    def star(n, ro, ri, rot=0):
        pts = []
        for k in range(2 * n):
            r = ro if k % 2 == 0 else ri
            a = rot + math.pi * k / n
            pts.append((r * math.cos(a), r * math.sin(a)))
        return ring_path(pts)
    return (f'<symbol id="ag" viewBox="-5 -5 10 10" overflow="visible">'
            f'<path d="{star(10, 4.9, 1.3)}" fill="{AGV}"/>'
            f'<path d="{star(7, 2.8, 1.0, 0.4)}" fill="{AGV_L}"/>'
            f'<circle r=".7" fill="{AGV_D}"/></symbol>')

def plant_row(x0, x1, y, pitch, phase, seed, scale=1.0):
    out = []
    x = x0 + phase
    k = 0
    while x < x1 + pitch:
        a = ((seed * 7919 + k * 104729) % 360)
        s = scale * (0.9 + 0.2 * (((seed * 31 + k * 17) % 11) / 10))
        out.append(f'<use href="#ag" x="-5" y="-5" width="10" height="10" transform="translate({x:.2f} {y:.2f}) rotate({a}) scale({s:.3f})"/>')
        x += pitch; k += 1
    return "".join(out)

def field_svg(P, cls, css):
    """Aerial field hero. P: frame + terrain + strip plan."""
    X0, Y0, X1, Y1 = P["frame"]
    xs = np.arange(X0 - 2, X1 + 2.01, P.get("res", 1.0))
    ys = np.arange(Y0 - 2, Y1 + 2.01, P.get("res", 1.0))
    X, Y = np.meshgrid(xs, ys)
    H, Bw = terrain(X, Y, P)
    gen = contourpy.contour_generator(xs, ys, H, fill_type=contourpy.FillType.OuterOffset, line_type=contourpy.LineType.Separate)
    bounds = P["bounds"]                      # straight-row y of each strip boundary, top (small y) to bottom
    kinds = P["kinds"]                        # strip kind between bounds[i] and bounds[i+1]; kinds[0] = above bounds[0]
    cs = [-b for b in bounds]                 # level values (descending)
    top = float(H.max()) + 1
    g = []
    # strips (curved zone): band between level c_{i+1} (lower) and c_i
    levels = [top] + cs
    for i, kind in enumerate(kinds[:-1]):
        hi, lo = min(levels[i], top), levels[i + 1]
        if hi <= lo: continue
        fill = {"straw": STRAW, "loam": LOAM, "sage": SAGE, "paper": PAPER, "earth": EARTH}[kind]
        d = filled(gen, lo, hi)
        if d: g.append(f'<path d="{d}" fill="{fill}" fill-rule="evenodd"/>')
    # region below the last curved boundary is straight (w = 0): red-earth hileras
    yb = bounds[-1]
    g.append(f'<rect x="{X0}" y="{yb}" width="{X1 - X0}" height="{Y1 - yb}" fill="{kinds[-1] and {"straw": STRAW, "loam": LOAM, "sage": SAGE, "earth": EARTH}[kinds[-1]]}"/>')
    # furrows: finer level lines inside each strip, following the land
    for i, kind in enumerate(kinds[:-1]):
        hi, lo = min(levels[i], top), levels[i + 1]
        if kind in ("paper",) or hi <= lo: continue
        col = {"straw": STRAW_H, "loam": LOAM_H, "sage": SAGE_H, "earth": EARTH_H}[kind]
        n = P["furrows"].get(kind, 5)
        step = (levels[i] - lo) / n if i else (cs[0] - cs[1]) / n
        lv = lo + step
        paths = []
        while lv < min(hi, top) - 1e-6:
            paths.append(lines(gen, lv)); lv += step
        # stubble keeps going past the summit strip
        g.append(f'<path d="{" ".join(paths)}" fill="none" stroke="{col}" stroke-width="{P["fw"]}" stroke-linecap="round"/>')
    # boundaries between strips: a slightly darker edge line
    g.append('<path d="' + " ".join(lines(gen, c) for c in cs if c < top) + f'" fill="none" stroke="{INK}" stroke-opacity=".28" stroke-width=".5"/>')
    # relief shading (Imhof): hillshade of the knolls only, NW light, quantised into vector bands
    gy, gx = np.gradient(Bw * P["zx"], ys, xs)
    nx_, ny_, nz_ = -gx, -gy, np.ones_like(gx)
    nn = np.sqrt(nx_ ** 2 + ny_ ** 2 + nz_ ** 2)
    L = np.array([-1, -1, 1.2]); L = L / np.linalg.norm(L)
    sh = (nx_ * L[0] + ny_ * L[1] + nz_ * L[2]) / nn
    flat = L[2]
    sgen = contourpy.contour_generator(xs, ys, sh - flat, fill_type=contourpy.FillType.OuterOffset, line_type=contourpy.LineType.Separate)
    for lo_, hi_, fill, op in P["shade"] if P.get("relief") else []:
        d = filled(sgen, lo_, hi_)
        if d: g.append(f'<path d="{d}" fill="{fill}" fill-opacity="{op}" fill-rule="evenodd"/>')
    # agave hileras: planted along the centre level line of every earth strip, so a row that starts on the
    # contour (upper, curved) locks into a straight hilera where the window w(y) reaches 0
    rows = []
    for i, kind in enumerate(kinds[:-1]):
        if kind != "earth": continue
        mid = (levels[i] + levels[i + 1]) / 2
        for seg in gen.lines(mid):
            d = np.r_[0, np.cumsum(np.hypot(*np.diff(seg, axis=0).T))]
            if d[-1] < 10: continue
            ph = (i * 3.1) % P["pitch"]
            for k, t in enumerate(np.arange(ph, d[-1], P["pitch"])):
                x = np.interp(t, d, seg[:, 0]); y = np.interp(t, d, seg[:, 1])
                a = (i * 7919 + k * 104729) % 360
                sc = P["pscale"] * (0.9 + 0.2 * (((i * 31 + k * 17) % 11) / 10))
                rows.append(f'<use href="#ag" x="-5" y="-5" width="10" height="10" transform="translate({x:.2f} {y:.2f}) rotate({a}) scale({sc:.3f})"/>')
    for (y, pitch, phase, scale) in P["plants"]:
        rows.append(plant_row(X0 - 6, X1 + 6, y, pitch, phase, int(y * 10), scale))
    g.append("".join(rows))
    vb = f"{X0} {Y0} {X1 - X0} {Y1 - Y0}"
    return (f'<svg class="{cls}" viewBox="{vb}" style="{css}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
            + "".join(g) + "</svg>")

# ------------------------------------------------------------------ hero plans
# Letter front: frame in pt, trim 612 x 792, 9 pt bleed. Hero ends at y 252 (first menu band).
FRONT = {
    "frame": (-9, -9, 621, 206), "res": 1.0,
    "hills": [(150, 462, 6, 128, 86), (96, 70, -40, 125, 72), (-42, 292, 44, 92, 112)],
    "wa": 40, "wb": 150,
    # straight-row positions of strip boundaries (pt), top to bottom
    "bounds": [-170, -150, -130, -110, -90, -70, -50, -30, -10, 10, 30, 48, 64, 82, 96, 114, 126, 144, 154, 172, 180, 198],
    "kinds": ["sage", "straw", "loam", "straw", "sage", "loam", "straw", "loam", "sage", "straw", "loam", "straw", "earth", "straw", "earth", "loam", "earth", "straw", "earth", "straw", "earth", "straw", "loam"],
    "furrows": {"straw": 6, "loam": 5, "sage": 5, "earth": 3},
    "fw": 0.55, "zx": 1.0, "pitch": 12.5, "pscale": 1.12,
    "shade": [], "plants": [],
}
# Phone hero: px, 390 wide.
PHONE = {
    "frame": (0, 0, 390, 262), "res": 1.0,
    "hills": [(120, 300, 4, 96, 74), (80, 30, -30, 90, 60), (-36, 160, 40, 70, 96)],
    "wa": 50, "wb": 170,
    "bounds": [-160, -140, -120, -100, -80, -60, -40, -20, 0, 20, 38, 56, 70, 90, 104, 124, 136, 156, 168, 188, 198, 218, 230, 250],
    "kinds": ["sage", "straw", "loam", "straw", "sage", "loam", "straw", "loam", "sage", "straw", "loam", "straw", "earth", "straw", "earth", "loam", "earth", "straw", "earth", "straw", "earth", "straw", "earth", "straw", "loam"],
    "furrows": {"straw": 5, "loam": 4, "sage": 4, "earth": 3},
    "fw": 0.55, "zx": 1.0, "pitch": 14, "pscale": 1.3,
    "shade": [], "plants": [],
}

def hilera_strip(width, height, rows, pitch, scale, cls, css=""):
    """A straight planted strip (red earth + agave rows), used as the divider between menu bands."""
    g = [f'<rect x="0" y="0" width="{width}" height="{height}" fill="{EARTH}"/>']
    for k, y in enumerate(rows):
        g.append(plant_row(-4, width + 4, y, pitch, (pitch / 2) * (k % 2), 17 + k * 5 + int(width), scale))
    return (f'<svg class="{cls}" viewBox="0 0 {width} {height}" preserveAspectRatio="xMinYMid slice" style="{css}" aria-hidden="true">'
            + "".join(g) + "</svg>")

def back_field(width, height, cls, css=""):
    """Back page head: the field straightened into hileras (Jalisco), with stubble strips (Iowa) between."""
    g = []
    y = 0.0
    plan = [("straw", 12), ("earth", 16), ("loam", 6), ("earth", 16), ("straw", 8), ("earth", 16), ("sage", 5)]
    total = sum(h for _, h in plan)
    sc = height / total
    for kind, h in plan:
        h *= sc
        fill = {"straw": STRAW, "loam": LOAM, "sage": SAGE, "earth": EARTH}[kind]
        g.append(f'<rect x="-2" y="{y:.2f}" width="{width + 4}" height="{h + .05:.2f}" fill="{fill}"/>')
        if kind == "earth":
            g.append(plant_row(-6, width + 6, y + h / 2, 12.5, 6.25 * (int(y) % 2), int(y * 7), 1.05))
        else:
            col = {"straw": STRAW_H, "loam": LOAM_H, "sage": SAGE_H}[kind]
            n = 4
            for k in range(1, n):
                yy = y + h * k / n
                g.append(f'<line x1="-2" x2="{width + 2}" y1="{yy:.2f}" y2="{yy:.2f}" stroke="{col}" stroke-width=".55"/>')
        y += h
    return (f'<svg class="{cls}" viewBox="0 0 {width} {height}" preserveAspectRatio="xMinYMin slice" style="{css}" aria-hidden="true">'
            + "".join(g) + "</svg>")

# ------------------------------------------------------------------ glass glyphs (coded family)
LIQ = {  # only where the ingredients make the colour obvious; otherwise neutral
    "Mezcal Negroni": ("#B8352A", "Campari → red"),
    "Carajillo": ("#3B2A20", "fresh espresso → dark"),
    "Batanga": ("#4A2C1E", "Mexican cola → dark"),
    "Manhattan": ("#A86A2A", "rye whiskey + sweet vermouth → amber"),
    "Brown Butter Old Fashioned": ("#B07A34", "bourbon → amber"),
}
NEUTRAL = "#DCCDA4"

def glyph(glass, garnish, liquid):
    ink = INK3
    s = []
    if glass == "coupe":
        s.append(f'<path d="M1.2 2.6 L10.8 2.6 Q10.2 7.4 6 7.6 Q1.8 7.4 1.2 2.6 Z" fill="{liquid}"/>')
        s.append(f'<path d="M.8 2.2 L11.2 2.2 Q10.6 7.9 6 8.1 Q1.4 7.9 .8 2.2" fill="none" stroke="{ink}" stroke-width=".6"/>')
        s.append(f'<path d="M6 8.1 V12.6 M3.4 12.9 H8.6" stroke="{ink}" stroke-width=".6" fill="none"/>')
        rim = (0.8, 11.2, 2.2)
    elif glass == "highball":
        s.append(f'<rect x="3.3" y="3.2" width="5.4" height="9.3" fill="{liquid}"/>')
        s.append(f'<rect x="4.0" y="4.1" width="2.4" height="2.4" fill="#FFFFFF" fill-opacity=".75" stroke="{ink}" stroke-width=".35" transform="rotate(-8 5.2 5.3)"/>')
        s.append(f'<rect x="5.4" y="7.4" width="2.4" height="2.4" fill="#FFFFFF" fill-opacity=".75" stroke="{ink}" stroke-width=".35" transform="rotate(10 6.6 8.6)"/>')
        s.append(f'<path d="M2.8 .9 V12.9 H9.2 V.9" fill="none" stroke="{ink}" stroke-width=".6"/>')
        rim = (2.8, 9.2, 0.9)
    else:  # rocks
        s.append(f'<path d="M1.9 6.2 H10.1 L9.8 12.4 H2.2 Z" fill="{liquid}"/>')
        s.append(f'<rect x="2.9" y="6.6" width="2.7" height="2.7" fill="#FFFFFF" fill-opacity=".75" stroke="{ink}" stroke-width=".35" transform="rotate(-10 4.2 8)"/>')
        s.append(f'<rect x="6.1" y="7.9" width="2.7" height="2.7" fill="#FFFFFF" fill-opacity=".75" stroke="{ink}" stroke-width=".35" transform="rotate(12 7.4 9.2)"/>')
        s.append(f'<path d="M1.4 4.4 L1.9 12.9 H10.1 L10.6 4.4" fill="none" stroke="{ink}" stroke-width=".6"/>')
        rim = (1.4, 10.6, 4.4)
    x0, x1, yr = rim
    if garnish == "salt rim":
        s.append(f'<path d="M{x0} {yr} H{x1}" stroke="{ink}" stroke-width="1.3" stroke-dasharray=".45 .55" fill="none"/>')
    elif garnish == "lime wheel":
        s.append(f'<circle cx="{x1 - .2}" cy="{yr - .2}" r="2" fill="#A9C25A" stroke="#5E7A2A" stroke-width=".45"/>'
                 f'<path d="M{x1 - 2.2} {yr - .2} H{x1 + 1.8} M{x1 - .2} {yr - 2.2} V{yr + 1.8}" stroke="#5E7A2A" stroke-width=".3"/>')
    elif garnish == "lime wedge":
        s.append(f'<path d="M{x1 - 2.6} {yr} L{x1 + 1} {yr} L{x1 - .4} {yr - 2.6} Z" fill="#A9C25A" stroke="#5E7A2A" stroke-width=".45"/>')
    elif garnish == "lime coin":
        s.append(f'<circle cx="{x1 - 1}" cy="{yr}" r="1.2" fill="#A9C25A" stroke="#5E7A2A" stroke-width=".4"/>')
    elif garnish == "orange peel":
        s.append(f'<path d="M{x1 - 3.4} {yr - .6} q1.2 -1.6 2.6 -.6 q1 .8 2 -.3" fill="none" stroke="#D07A22" stroke-width="1.1" stroke-linecap="round"/>')
    elif garnish == "cocktail cherry":
        s.append(f'<circle cx="6" cy="5.4" r="1.25" fill="#7A1420"/><path d="M6 4.2 q.6 -2 2.4 -2.8" stroke="{ink}" stroke-width=".35" fill="none"/>')
    elif garnish == "candied ginger":
        s.append(f'<path d="M{x1 - 1} {yr - 3.2} L{x0 + 5} {yr + 3}" stroke="{ink}" stroke-width=".35"/><rect x="{x1 - 2.4}" y="{yr - 3.4}" width="2" height="2" fill="#D6A548" stroke="#9C6A1C" stroke-width=".3" transform="rotate(20 {x1 - 1.4} {yr - 2.4})"/>')
    return f'<svg class="gl" viewBox="0 0 12 13.6" aria-hidden="true">{"".join(s)}</svg>'

# ------------------------------------------------------------------ content helpers
def price_txt(p):
    return f"{p:.2f}" if abs(p - round(p)) > 1e-9 else str(int(round(p)))

def proposed(it):
    return it["status"] != "approved_db"

def head(label, tag="h2", cls=""):
    es, en = [s.strip() for s in label.split("·", 1)] if "·" in label else (label, "")
    inner = f'<i>{E(es)}</i>' + (f'<span class="dot"> · </span>{E(en)}' if en else "")
    return f'<{tag} class="tx {cls}" data-label="{E(label)}">{inner}</{tag}>'

def name_row(it, cls="np"):
    ring = '<span class="ring" title="proposed — pending approval"></span>' if proposed(it) else ""
    return (f'<p class="{cls}">{ring}<span class="nm tx">{E(it["name"])}</span><span class="fw"></span>'
            f'<span class="pr tx">{price_txt(it["price"])}</span></p>')

def cocktail(it):
    ing = " · ".join(it["ingredients"])
    serve = " · ".join([x for x in (it.get("garnish"), it["glass"]) if x])
    liq = LIQ.get(it["name"], (NEUTRAL, ""))[0]
    return (f'<article class="item ck" data-name="{E(it["name"])}" data-status="{it["status"]}">'
            + name_row(it)
            + f'<p class="sd tx">{E(it["sensory"])}</p>'
            + f'<p class="ig tx">{E(ing)}</p>'
            + f'<p class="gg">{glyph(it["glass"], it.get("garnish"), liq)}<span class="tx">'
            + (f'<span class="gar">{E(it["garnish"])}</span> · ' if it.get("garnish") else "")
            + f'<span class="gls">{E(it["glass"])}</span></span></p>'
            + "</article>")

def simple(it):
    return (f'<article class="item sm" data-name="{E(it["name"])}" data-status="{it["status"]}">'
            + name_row(it) + f'<p class="sd tx">{E(it["sensory"])}</p></article>')

# oak months by class (NOM-006 age classes, as the manifest sensory lines state them)
def oak(it):
    c, s = it["cls"], it["sensory"]
    if s.startswith("Unaged"): return ("dot", 0, 0)
    if c == "reposado": return ("bar", 2, 12)
    if c == "añejo": return ("bar", 12, 36)
    if c == "cognac VSOP": return ("over", 48, 48)
    return ("ns", 0, 0)  # age not stated (mezcal espadín, "Pit-roasted")

AXW = 108.0   # oak axis width in pt (0..36 months)
def oak_svg(it):
    k, a, b = oak(it)
    u = AXW / 36
    s = []
    if k == "dot":
        s.append(f'<circle cx="2.2" cy="5.9" r="2" fill="{EARTH_H}"/>')
    elif k == "bar":
        s.append(f'<rect x="{2.2 + a * u:.2f}" y="4.4" width="{(b - a) * u:.2f}" height="3.6" fill="{EARTH_H}"/>')
    elif k == "over":
        s.append(f'<path d="M{2.2 + 36 * u - 7:.2f} 5.8 H{2.2 + 36 * u + 4:.2f} M{2.2 + 36 * u + 1:.2f} 3.6 L{2.2 + 36 * u + 4.4:.2f} 5.8 L{2.2 + 36 * u + 1:.2f} 8" stroke="{EARTH_H}" stroke-width="1.4" fill="none"/>')
    else:
        s.append(f'<path d="M.6 3.6 H4.6" stroke="{INK3}" stroke-width=".8"/>')
    return f'<svg class="oak" viewBox="0 0 {AXW + 10} 8" aria-hidden="true" data-oak="{k}:{a}-{b}">{"".join(s)}</svg>'

def spirit_row(it, own_sd):
    ring = '<span class="ring"></span>' if proposed(it) else ""
    fwm = "" if own_sd else '<span class="fw"></span>'
    sd = f'<p class="ssd"><span class="tx">{E(it["sensory"])}</span><span class="fw"></span></p>' if own_sd else ""
    return (f'<div class="tr" data-name="{E(it["name"])}" data-status="{it["status"]}">'
            f'<p class="c-nm">{ring}<span class="nm tx">{E(it["name"])}</span>{fwm}</p>'
            f'<p class="c-cl"><span class="tx">{E(it["cls"])}</span></p>'
            f'<p class="c-nom"><span class="tx">{E(it["nom"]) if it["nom"] else "—"}</span></p>'
            f'<p class="c-rg"><span class="tx">{E(it["region"]) if it["region"] else "—"}</span></p>'
            f'<p class="c-oak">{oak_svg(it)}</p>'
            f'<p class="c-pr"><span class="pr tx">{price_txt(it["price"])}</span></p>'
            f'{sd}</div>')

def spirits_table():
    out = []
    for g, items in MAN["spirits"].items():
        sds = [i["sensory"] for i in items]
        common = max(set(sds), key=sds.count)
        shared = sds.count(common) >= 2
        out.append(f'<div class="tg">{head(g, "h3")}' + (f'<span class="gsd tx">{E(common)}</span>' if shared else "") + '</div>')
        for it in items:
            out.append(spirit_row(it, (not shared) or it["sensory"] != common))
    return "".join(out)

def legend_front():
    sw_iowa = (f'<svg class="sw" viewBox="0 0 26 10"><rect width="26" height="10" fill="{STRAW}"/>'
               + "".join(f'<path d="M0 {y} Q13 {y - 3} 26 {y}" stroke="{STRAW_H}" stroke-width=".6" fill="none"/>' for y in (3, 5.5, 8))
               + f'<path d="M0 10 Q13 7 26 10 V10 H0Z" fill="{LOAM}"/></svg>')
    sw_ag = (f'<svg class="sw" viewBox="0 0 26 10"><rect width="26" height="10" fill="{EARTH}"/>'
             + "".join(f'<use href="#ag" x="-5" y="-5" width="10" height="10" transform="translate({x} 5) scale(.85)"/>' for x in (4.5, 13, 21.5)) + '</svg>')
    return ('<footer class="legend lg-f">'
            + north() +
            f'<span class="li">{sw_iowa}<span class="tx">Contour strips · Iowa</span></span>'
            f'<span class="li">{sw_ag}<span class="tx">Agave hileras · Jalisco</span></span>'
            '<span class="li"><span class="ring k"></span><span class="tx">proposed — pending approval</span></span>'
            '</footer>')

def north():
    return (f'<svg class="na" viewBox="0 0 12 22" aria-hidden="true"><path d="M6 1 L10 13 L6 10.6 L2 13 Z" fill="{INK}"/>'
            f'<path d="M6 1 L6 10.6 L2 13 Z" fill="{PAPER}" stroke="{INK}" stroke-width=".5"/>'
            f'<path d="M3.6 21 V15.2 L8.4 21 V15.2" stroke="{INK}" stroke-width=".9" fill="none"/></svg>')

def legend_back():
    u = AXW / 36
    ticks = "".join(f'<path d="M{2.2 + m * u:.2f} 0 V{7 if m % 12 == 0 else 4}" stroke="{RED}" stroke-width=".6"/>' for m in range(0, 37, 6))
    bar = (f'<svg class="scale" viewBox="0 0 {AXW + 6} 8" aria-hidden="true">'
           f'<rect x="2.2" y="2.2" width="{12 * u:.2f}" height="2.6" fill="{RED}"/><rect x="{2.2 + 24 * u:.2f}" y="2.2" width="{12 * u:.2f}" height="2.6" fill="{RED}"/>'
           f'<rect x="2.2" y="2.2" width="{AXW:.2f}" height="2.6" fill="none" stroke="{RED}" stroke-width=".6"/>{ticks}</svg>')
    scl = "".join('<span class="tx" style="left:%.2f%%">%d</span>' % ((2.2 + m * u) * 100 / (AXW + 6), m) for m in (0, 12, 24, 36))
    return ('<footer class="legend lg-b">' + north() +
            f'<span class="li sc"><span class="scwrap">{bar}<span class="scl">{scl}</span></span>'
            '<span class="tx">months in oak (NOM class)</span></span>'
            f'<span class="li"><svg class="sw2" viewBox="0 0 8 8"><circle cx="4" cy="4" r="2" fill="{EARTH_H}"/></svg><span class="tx">unaged</span></span>'
            f'<span class="li"><svg class="sw2" viewBox="0 0 8 8"><path d="M1.8 4 H6.2" stroke="{INK3}" stroke-width=".8"/></svg><span class="tx">age not stated</span></span>'
            '<span class="li"><span class="ring k"></span><span class="tx">proposed — pending approval</span></span>'
            '</footer>')

# ------------------------------------------------------------------ page assembly
def band(label, crop, inner, divider=True, cls=""):
    div = hilera_strip(630, 13, [6.5], 12.5, 1.0, "strip") if divider else ""
    return (f'<section class="band {cls}" data-crop="{crop}">{div}{head(label)}{inner}</section>')

def hileras(items, per, fn):
    rows = [items[i:i + per] for i in range(0, len(items), per)]
    return "".join(f'<div class="hl n{per}">' + "".join(fn(it) for it in r) + "</div>" for r in rows)

def build_html():
    ck = MAN["cocktails"]
    zp = MAN["zero_proof"]
    front_menu = (band(list(ck)[0], "straw", hileras(ck[list(ck)[0]], 3, cocktail), divider=False, cls="b1")
                  + band(list(ck)[1], "sage", hileras(ck[list(ck)[1]], 3, cocktail), cls="b2")
                  + band(list(zp)[0], "loam", hileras(zp[list(zp)[0]], 4, simple), cls="b3"))
    bc, wn = MAN["beer_cider"], MAN["wine"]
    bw = []
    cols = [[("beer_cider", "De barril · Draft")], [("beer_cider", "En lata · Cans"), ("beer_cider", "Sidra · Cider")],
            [("wine", "Por copa · By the glass"), ("wine", "Espumosos · Sparkling")]]
    for c in cols:
        ph = {0: head("Cerveza y sidra · Beer & cider", cls="ph-h"), 2: head("Vino · Wine", cls="ph-h")}.get(cols.index(c), "")
        bw.append('<div class="bwc">' + ph + "".join(
            f'<div class="bwg">{head(g, "h3")}' + "".join(simple(it) for it in MAN[src][g]) + "</div>" for src, g in c) + "</div>")
    u = AXW / 36
    axis = (f'<svg class="oak axis" viewBox="0 0 {AXW + 10} 8" aria-hidden="true">'
            + "".join(f'<path d="M{2.2 + m * u:.2f} 3 V8" stroke="{INK3}" stroke-width=".5"/>' for m in (0, 12, 24, 36)) + "</svg>")
    axn = "".join('<span class="axn tx" style="left:%.2fpt">%d</span>' % (2.2 + m * u, m) for m in (0, 12, 24, 36))
    grid = "".join('<i class="grid" style="left:%.2fpt"></i>' % (346 + 2.2 + m * u) for m in (12, 24, 36))
    back_main = (
        f'<section class="band spirits" data-crop="table">'
        f'<div class="th"><div class="c-nm">{head("Destilados · Spirits")}</div><p class="c-cl"><span class="tx">class</span></p><p class="c-nom"><span class="tx">NOM</span></p>'
        f'<p class="c-rg"><span class="tx">region</span></p><p class="c-oak">{axn}<span class="axu tx" style="left:{2.2 + 36 * u + 9:.2f}pt">mo oak</span>&nbsp;</p><p class="c-pr"><span class="tx">$</span></p></div>'
        f'<div class="tbody">{grid}{spirits_table()}</div></section>'
        + f'<section class="band bw" data-crop="loam">'
        + f'<div class="bwh">{head("Cerveza y sidra · Beer & cider", cls="h-b")}{head("Vino · Wine", cls="h-w")}</div>'
        + f'<div class="bwrow">{"".join(bw)}</div></section>')
    fonts_css = (HERE / "fonts" / "fonts.css").read_text().replace("url(", "url(fonts/")
    css = CSS.replace("%PAPER%", PAPER).replace("%INK%", INK).replace("%INK2%", INK2).replace("%INK3%", INK3).replace("%RED%", RED) \
             .replace("%STRAW_H%", STRAW_H).replace("%SAGE_H%", SAGE_H).replace("%LOAM_H%", LOAM_H).replace("%EARTH_H%", EARTH_H)
    defs = f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{rosette_symbol()}</defs></svg>'
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cantina Hileras Menu</title>
<style>{fonts_css}
{css}</style></head>
<body>{defs}
<div class="page front">
 {field_svg(FRONT, "field lt", "position:absolute;left:-9pt;top:-9pt;width:630pt;height:215pt")}
 {field_svg(PHONE, "field ph", "")}
 <header class="wm" data-crop="straw"><h1 class="tx big">Cantina<span class="fw"></span></h1><p class="tx sub">&amp; Cocktail Bar · Iowa City, Iowa</p></header>
 <main class="menu">{front_menu}</main>
 {legend_front()}
</div>
<div class="page back">
 {back_field(630, 80, "bfield", "")}
 <main class="menu">{back_main}</main>
 {legend_back()}
</div>
<script>
function furrows(){{
  document.querySelectorAll('.fwl').forEach(e => e.remove());
  document.querySelectorAll('.page').forEach(pg => {{
    const pr = pg.getBoundingClientRect(), seen = new Map();
    pg.querySelectorAll('.fw').forEach(m => {{
      if (!m.offsetParent) return;
      const y = m.getBoundingClientRect().bottom - pr.top;
      const b = m.closest('[data-crop]');
      const col = b ? getComputedStyle(b).getPropertyValue('--furrow').trim() : '#999';
      const key = Math.round(y * 4) / 4;
      const c = m.closest('.bwc');
      if (c && getComputedStyle(c.parentElement).display === 'grid') {{   // column-local furrow (columns do not share baselines)
        const cr = c.getBoundingClientRect(), cols = [...c.parentElement.children], i = cols.indexOf(c);
        const L = i === 0 ? -12 : cr.left - pr.left + 2, Rr = i === cols.length - 1 ? pr.width + 12 : cr.right - pr.left + 4;
        const d = document.createElement('div'); d.className = 'fwl'; Object.assign(d.style, {{top: y + 'px', left: L + 'px', right: 'auto', width: (Rr - L) + 'px', background: col}}); pg.appendChild(d);
        return;
      }}
      if (![...seen.keys()].some(k => Math.abs(k - key) < 1.5)) seen.set(key, col);
    }});
    for (const [y, col] of seen) {{ const d = document.createElement('div'); d.className = 'fwl'; d.style.top = y + 'px'; d.style.background = col; pg.appendChild(d); }}
  }});
  document.documentElement.dataset.laid = '1';
}}
document.fonts.ready.then(furrows);
window.addEventListener('resize', furrows);
</script>
</body></html>"""
    return doc

CSS = r"""
:root{--paper:%PAPER%;--ink:%INK%;--ink2:%INK2%;--ink3:%INK3%;--red:%RED%}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#d9d4c8}
body{font-family:'Newsreader',serif;color:var(--ink);-webkit-font-smoothing:antialiased;font-kerning:normal;text-rendering:geometricPrecision}
.page{position:relative;width:612pt;height:792pt;background:var(--paper);overflow:hidden;margin:0 auto}
.field.ph,.ph-only,.ph-h{display:none}
.fwl{position:absolute;left:-12px;right:-12px;height:.6pt;z-index:0;margin-top:.35pt;pointer-events:none}
.tx{position:relative;z-index:2}
.sans,.ig,.gg,h3,.legend,.sub,.c-cl,.c-nom,.c-rg,.c-pr,.th,.pr{font-family:'IBM Plex Sans Condensed',sans-serif}
/* wordmark: sits in the fallow strip of the field, baseline on the strip's lower furrow */
.wm{--furrow:#A48A73;position:absolute;left:37pt;top:214pt;z-index:3;display:flex;align-items:baseline;gap:14pt}
.wm .big{background:var(--paper);padding:0 6pt;margin-left:-6pt;font-weight:380;font-size:64pt;line-height:52pt;letter-spacing:-.012em;font-variation-settings:'opsz' 72;color:var(--ink)}
.wm .sub{font-size:10pt;font-weight:500;letter-spacing:.06em;color:var(--ink);background:var(--paper);padding:0 3pt}
/* menu */
.menu{position:absolute;left:37pt;top:266pt;width:539pt;z-index:1}
.band{position:relative;--furrow:#C4AB6E}
.band[data-crop=sage]{--furrow:#86A69D}
.band[data-crop=loam]{--furrow:#A48A73}
.band[data-crop=table]{--furrow:#CDBFA6}
.strip{display:block;width:630pt;height:13pt;margin-left:-45pt}
h2{font-weight:500;font-size:13pt;line-height:16pt;padding:9pt 0 4pt;color:var(--ink);letter-spacing:.005em}
h2 i{font-style:italic;font-weight:500}
h2 .dot,h3 .dot{color:var(--ink3)}
.hl{display:grid;grid-template-columns:1.17fr 1fr 1fr;column-gap:18pt;padding:0 0 10pt}
.hl.n4{grid-template-columns:repeat(4,1fr);column-gap:16pt}
.item{position:relative}
.np{font-size:12pt;line-height:15pt;position:relative}
.nm{font-weight:600;background:var(--paper);padding:0 2.5pt;margin-left:-2.5pt;font-variation-settings:'opsz' 14}
.pr{color:var(--red);font-weight:500;font-size:11pt;font-variant-numeric:tabular-nums lining-nums;background:var(--paper);padding:0 3pt 0 3.5pt}
.fw{display:inline-block;width:0;height:0;vertical-align:baseline}
.ring{position:absolute;left:-9.5pt;top:6.2pt;width:5.6pt;height:5.6pt;border:.6pt solid var(--ink3);border-radius:50%;background:var(--paper);z-index:2}
.sd{font-style:italic;font-size:10.5pt;line-height:13pt;color:var(--ink2);margin-top:1.5pt;font-variation-settings:'opsz' 11}
.ig{font-size:9.5pt;line-height:12pt;color:var(--ink);margin-top:1pt}
.gg{font-size:9pt;line-height:12pt;color:var(--ink3);margin-top:1pt;display:flex;align-items:flex-end;gap:3pt}
.gl{width:10.5pt;height:11.9pt;flex:none;margin-bottom:.6pt}
.sm .sd{font-size:10.5pt}
.b3 .hl{padding-bottom:0}
/* legend */
.legend{position:absolute;left:37pt;right:36pt;bottom:37pt;display:flex;align-items:flex-end;gap:16pt;font-size:8.5pt;line-height:10pt;color:var(--ink3);z-index:2}
.legend .li{display:flex;align-items:center;gap:5pt}
.legend .na{width:7pt;height:13pt;margin-right:2pt}
.legend .sw{width:22pt;height:8.5pt}
.legend .sw2{width:8pt;height:8pt}
.ring.k{position:relative;left:0;top:0;display:inline-block}
.lg-f .li:last-child,.lg-b .li:last-child{margin-left:auto}
/* back */
.bfield{position:absolute;left:-9pt;top:-9pt;width:630pt;height:80pt}
.back .menu{top:72pt}
.th,.tr{display:grid;grid-template-columns:150pt 84pt 36pt 76pt 118pt 1fr;column-gap:0;align-items:baseline}
.th{font-size:8.5pt;line-height:11pt;color:var(--ink3);padding:0 0 2pt;letter-spacing:.02em}
.th h2{font-family:'Newsreader',serif;font-size:13pt;color:var(--ink);letter-spacing:.005em;padding:9pt 0 2pt;white-space:nowrap}
.th .c-oak,.th .c-pr,.th .c-cl,.th .c-nom,.th .c-rg{align-self:end;padding-bottom:3pt}
.th .c-pr{text-align:right}
.th .c-oak{position:relative}
.axn{position:absolute;bottom:3pt;transform:translateX(-50%)}
.axu{position:absolute;bottom:3pt;white-space:nowrap}
.tbody{position:relative}
.grid{position:absolute;top:0;bottom:0;width:.5pt;background:#E0D6C4;z-index:0}
.tg{display:flex;align-items:baseline;gap:8pt;padding:6pt 0 1pt;position:relative;z-index:2}
h3{font-size:8.5pt;line-height:11pt;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--ink)}
h3 i{font-style:normal}
.gsd{font-style:italic;font-size:9.5pt;color:var(--ink2);font-variation-settings:'opsz' 10}
.tr{font-size:9pt;line-height:12.8pt;position:relative}
.tr .nm{font-size:10.5pt;font-weight:500;font-variation-settings:'opsz' 12;background:none}
.tr .c-nm{position:relative;font-family:'Newsreader',serif;font-size:10.5pt}
.tr{align-items:start}
.tr>p{line-height:12.8pt}
.tr>.c-cl,.tr>.c-nom,.tr>.c-rg,.tr>.c-pr{margin-top:-1.5pt}
.tr .ring{top:4.4pt}
.tr .fw{vertical-align:-3.3pt}
.c-cl,.c-rg{color:var(--ink2)}
.c-nom{font-variant-numeric:tabular-nums;color:var(--ink2)}
.c-pr{text-align:right}
.tr .pr{font-size:10.5pt;padding:0;background:none}
.tr .oak{display:inline-block;vertical-align:-3.3pt;width:118pt;height:8pt;position:relative;z-index:1}
.ssd .fw{vertical-align:-3.3pt}
.ssd{grid-column:1 / -1;font-style:italic;font-size:9.5pt;line-height:11pt;color:var(--ink2);padding:0 0 3pt;font-variation-settings:'opsz' 10;position:relative;z-index:2}
.bw .bwh{display:grid;grid-template-columns:1.3fr .85fr 1fr;column-gap:18pt}
.bw .bwh .h-b{grid-column:1 / 3}
.bw .bwh h2{padding:9pt 0 1pt}
.bwrow{display:grid;grid-template-columns:1.3fr .85fr 1fr;column-gap:18pt}
.bwg{margin-bottom:2pt}
.bwg h3{padding:1pt 0 1pt}
.bw .item{margin-bottom:1.5pt}
.bw .np{font-size:11pt;line-height:14pt}
.bw .pr{font-size:10.5pt}
.bw .sd{font-size:10pt;line-height:12pt;margin-top:0}
.scwrap{display:inline-flex;flex-direction:column;align-items:flex-start;gap:1pt;position:relative}
.legend .scale{width:114pt;height:8pt}
.scl{position:relative;display:block;width:114pt;height:10pt;color:var(--red)}
.scl span{position:absolute;top:0;transform:translateX(-50%)}
.lg-b{align-items:flex-end}
/* ---------------------------------------------------------------- phone */
@media (max-width:600px){
 html,body{background:var(--paper)}
 .page{width:100%;height:auto;overflow:hidden;padding:0 24px}
 .field.lt{display:none}
 .field.ph{display:block;width:calc(100% + 48px);height:318px;margin:0 -24px}
 .wm{position:static;flex-direction:column;align-items:flex-start;gap:6px;padding:26px 0 4px}
 .wm .big{font-size:64px;line-height:56px;margin-left:-4px;padding:0 4px}
 .wm .sub{display:none}
 .front .wm .sub{display:block;font-size:13px;margin-left:-3px}
 .menu{position:static;width:auto;padding-top:0}
 .fwl{left:0;right:0;height:1px;margin-top:.5px}
 .strip{width:calc(100% + 48px);height:20px;margin-left:-24px}
 h2{font-size:20px;line-height:24px;padding:20px 0 10px}
 .hl,.hl.n4{display:block;padding:0}
 .item{padding:0 0 18px}
 .np{font-size:18px;line-height:24px}
 .pr{font-size:17px}
 .sd{font-size:16px;line-height:21px}
 .ig{font-size:15px;line-height:20px}
 .gg{font-size:14px;line-height:19px;gap:5px}
 .gl{width:15px;height:17px}
 .ring{left:-14px;top:8px;width:8px;height:8px;border-width:1px}
 .legend{position:static;flex-wrap:wrap;gap:10px 16px;font-size:13px;line-height:17px;padding:8px 0 28px}
 .legend .na{width:10px;height:18px}
 .legend .sw{width:30px;height:12px}
 .legend .sw2{width:12px;height:12px}
 .lg-f .li:last-child,.lg-b .li:last-child{margin-left:0}
 .back{padding-top:0}
 .bfield{position:static;display:block;width:calc(100% + 48px);height:96px;margin:0 -24px}
 .th,.grid{display:none}
 .tg{flex-direction:column;gap:2px;padding:18px 0 6px}
 h3{font-size:13px;line-height:17px}
 .gsd{font-size:15px;line-height:19px}
 .tr{display:flex;flex-wrap:wrap;align-items:baseline;font-size:14px;line-height:19px;padding:0 0 10px}
 .tr .c-nm{order:1;width:calc(100% - 64px);line-height:24px}
 .tr .c-pr{order:2;width:64px;line-height:24px}
 .tr .c-cl{order:3;margin-right:10px}
 .tr .c-nom{order:4;margin-right:10px}
 .tr .c-rg{order:5}
 .tr .c-oak{order:6;margin-left:auto;width:124px}
 .tr .ssd{order:7;width:100%}
 .tr .nm{font-size:17px}
 .tr .pr{font-size:16px}
 .tr .ring{top:8px}
 .tr .oak{width:124px;height:9px;vertical-align:-4px}
 .ssd{font-size:15px;line-height:19px}
 .bw .bwh{display:none}
 .ph-h{display:block}
 .bwrow{display:block}
 .bwg h3{padding:14px 0 8px}
 .bw .np{font-size:18px;line-height:24px}
 .bw .pr{font-size:17px}
 .bw .sd{font-size:16px;line-height:21px}
 .scale,.legend .scale{width:120px;height:9px}
 .scl{width:120px;height:17px;font-size:13px}
 .page.back .menu{padding-top:0}
}
"""

if __name__ == "__main__":
    import sys, subprocess
    (HERE / "menu.html").write_text(build_html())
    print("menu.html", len((HERE / "menu.html").read_text()) // 1024, "KB; manifest sha256", hashlib.sha256(MAN_PATH.read_bytes()).hexdigest()[:16])
    if "--html-only" not in sys.argv:   # render (render.py), gates (finalize.py), KB visual tests
        subprocess.run([sys.executable, str(HERE / "render.py")], check=True, cwd=HERE)
        subprocess.run([sys.executable, str(HERE / "finalize.py")], check=True, cwd=HERE)
        vt = subprocess.run([sys.executable, str(HERE.parent.parent / "tools" / "visual_tests.py"), "preview-front.png", "preview-back.png"], check=True, cwd=HERE, capture_output=True, text=True)
        (HERE / "visual_tests.json").write_text(vt.stdout)
        for r in json.loads(vt.stdout)["results"]:
            print(r["file"], "primary", r["primary_area_pct"], "p:s", r["primary_to_secondary"], "accent", r["accent_area_pct"], "regions", r["squint_salient_regions"])
