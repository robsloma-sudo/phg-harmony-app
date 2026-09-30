#!/usr/bin/env python3
"""TEST-1 explore-I4 "Night Field" round 4: I2's engraved rosette agave (fleshier, cupped leaves) standing in a
restrained Iowa strip-crop field: level horizon, near-straight contour rows in alternating density bands.

Content: unchanged from I2/I3 (draft_doc.json + recipe_versions garnishes, asserted in build).
Art: one engraving, one stroke weight, drawn on a bleed canvas that runs BLEED px past the trim on every side.
Passes: (1) text only -> line boxes, header offset; (2) art, shortening any leaf within 6 mm of text; (3) render.

Usage: python3 build.py [--tag NAME] [key=value ...]
"""
import json, math, os, sys, io, re, glob, random
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFT = json.load(open(HERE.parent / "build" / "draft_doc.json"))
FONTS = (HERE / "fonts").as_uri()
TAG = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else ""
OPT = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a and not a.startswith("--"))

GREEN, IVORY, IVORY2, IVORY3, GOLD = OPT.get("ground", "#1B1510"), "#EEE4D1", "#C4B9A6", "#C4B9A6", OPT.get("accent", "#9CC3B5")
WARM = OPT.get("warm", "#D98E6A")   # loam-terracotta: H2 section heads only
# GREEN = the ground (Iowa black loam, warm near-black brown); GOLD = the one accent (agave-leaf blue-green)
STROKE = float(OPT.get("stroke", 1.25))       # the one stroke weight (css px; x3.125 at print)
HATCH = float(OPT.get("hatch", 3.0))          # target hatch pitch (css px)
WF = float(OPT.get('wf', 2.05))
WRAPS = (0.18, 0.40, 0.60) if OPT.get('wraps') == '1' else ()
CREASE = OPT.get('crease', '0') == '1'
RIBBON_EDGE = OPT.get('redge', '0') == '1'
CONE_L, CONE_W = float(OPT.get('cl', 0.98)), float(OPT.get('cw', 0.10))
PITCH_MIN = float(OPT.get('pmin', 2.7))
TEND0 = float(OPT.get('tend0', 0.8))
HEART = float(OPT.get('heart', 0.95))
CLEAR = 23                                    # 6 mm at 96 css px / in
o = lambda k, d: float(OPT.get(k, d))
GRID = 8                                      # one baseline increment for both columns
NBSP = "\u00a0"
BLEED = 12                                    # 0.125 in = 3.2 mm art bleed past the trim, every side
SAFE = 48                                     # 0.5 in safe inset for all text

# ---- content -------------------------------------------------------------------------------
RV = {"beta_margarita": ("Lime wheel", "f06abb74"), "beta_daiquiri": ("Lime coin", "14d45e57"),
      "beta_old_fashioned": ("Orange peel", "7095fd3d"), "beta_manhattan": ("Cocktail cherry", "9fb77eaa")}
TAIL = {"beta_margarita": "Bright and citrus-forward."}


SEP = '<span class="sep">\u00a0·</span> '             # the dot ends line 1 when a list wraps
SEP_BOUND = '<span class="sep">\u00a0·</span>\u00a0'   # the last two parts never separate (no lone garnish)
# Draft wording kept; "house demerara syrup" is the Daiquiri draft desc's own term.
COMP_NAME = {("beta_daiquiri", "Demerara Syrup"): "house demerara syrup"}
# Serve facts from phg.recipe_versions (gateway log 241): glassware / method. One small-caps serve label system,
# shared with the spirits' draft serve word "pour".
SERVE = {"beta_manhattan": ("coupe", "9fb77eaa glassware Coupe"),
         "beta_daiquiri": ("coupe", "14d45e57 glassware Coupe"),
         "beta_old_fashioned": ("over a large cube", "7095fd3d method 'Stir with ice and strain over a large cube'"),
         "beta_margarita": ("over fresh ice", "f06abb74 method 'Shake with ice and strain over fresh ice'")}
POUR = {"beta_blanco_tequila", "beta_anejo_tequila", "beta_cognac_vsop"}


def desc(it):
    """returns (description html, serve label or None). Serve labels sit before the price in small caps."""
    if it["id"] in POUR:
        d = it["desc"].rstrip(".")
        assert d.lower().endswith(" pour")
        return d[: -len(" pour")], "pour"
    if it["components"]:
        hidden = {k for k, v in it["meta"].get("public_components", {}).items() if v is False}
        names = [c["name"] for c in it["components"] if c["name"].lower().replace(" ", "-") not in hidden]
        g = RV.get(it["id"])
        if g and g[0].lower() not in [n.lower() for n in names]:
            names.append(g[0])
        for (iid, cn), rep in COMP_NAME.items():
            if iid == it["id"]:
                assert rep in it["desc"].lower()
                names = [rep if n == cn else n for n in names]
        parts = [n.lower() for n in names]
        parts[0] = parts[0][0].upper() + parts[0][1:]
        parts = [f'<span class="ing">{p}</span>' for p in parts]
        if it["id"] in SERVE:                     # sourced serve fact closes the list, in the serve-label style
            parts.append(f'<span class="ing sv">{SERVE[it["id"]][0]}</span>')
        s = SEP.join(parts[:-1]) + SEP_BOUND + parts[-1] if len(parts) > 1 else parts[0]
        if it["id"] in TAIL:                      # draft-supplied tasting note, same roman style, same flow
            assert TAIL[it["id"]].rstrip(".") in it["desc"]
            s += '. <span class="note">' + TAIL[it["id"]] + "</span>"
        return s, None
    return it["desc"].rstrip("."), None


def price(it):
    v = it["prices"][0]["value"]
    return f"{v:g}" if float(v).is_integer() else f"{v:.2f}"


SEC = {s["id"]: s for s in DRAFT["sections"]}
# Groups (H2, English) -> list of (bilingual H3 or None, draft section id, draft sub id or None)
SUBHEAD = {"sub_cocktails_classics": "Clásicos · Classics", "sub_cocktails_house_originals": "De la Casa · House Originals",
           "sub_beer_draft": "De Barril · Draft", "sec_cider": "Sidra · Cider",
           "sub_wine_by_the_glass": "Por Copa · By the Glass", "sub_wine_sparkling": "Espumoso · Sparkling",
           "sub_spirits_agave": "Agave", "sub_spirits_brandy": "Brandy"}
GROUPS = [("Cocktails", ["sec_cocktails"]), ("Beer &amp; Cider", ["sec_beer", "sec_cider"]),
          ("Wine", ["sec_wine"]), ("Spirits", ["sec_spirits"])]
ORDER_FIRST = {"sub_cocktails_classics": ["beta_margarita", "beta_manhattan"]}
COL1, COL2 = [0, 1], [2, 3]


def item_html(it):
    d, serve = desc(it)
    sv = f'<span class="sv">{serve}</span>' if serve else ""
    return (f'<div class="it" data-id="{it["id"]}"><div class="row"><span class="nm">{it["name"]}</span>'
            f'<span class="prw">{sv}<span class="pr">{price(it)}</span></span></div><div class="ds">{d}</div></div>')


def section_html(gi, extra=0):
    head, secs = GROUPS[gi]
    out = [f"<section><h2>{head}</h2>"]
    for sid in secs:
        s = SEC[sid]
        if s.get("items"):
            out.append(f"<h3>{SUBHEAD[sid]}</h3>")
            out += [item_html(i) for i in s["items"]]
        for sub in s.get("subs", []):
            out.append(f"<h3>{SUBHEAD[sub['id']]}</h3>")
            items = sub["items"]
            if sub["id"] in ORDER_FIRST:
                items = sorted(items, key=lambda i: ORDER_FIRST[sub["id"]].index(i["id"]))
            out += [item_html(i) for i in items]
    out.append("</section>")
    return "\n".join(out)


def all_items():
    for s in DRAFT["sections"]:
        yield from s.get("items", [])
        for sub in s.get("subs", []):
            yield from sub["items"]


# ---- geometry helpers ---------------------------------------------------------------------------
def pstr(pts):
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts)


def inside(pt, poly):
    x, y = pt
    c, j = False, len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


def taper(pts, wmax):
    """engraver's line: a filled sliver that swells in from the start and tapers to a point at the end."""
    if len(pts) < 3:
        return ""
    L = len(pts) - 1
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        j0, j1 = max(0, i - 1), min(L, i + 1)
        tx, ty = pts[j1][0] - pts[j0][0], pts[j1][1] - pts[j0][1]
        m = math.hypot(tx, ty) or 1
        nx, ny = -ty / m, tx / m
        s_ = i / L
        w = wmax * min(1.0, (s_ * 10) ** 0.5) * min(1.0, (1 - s_) / 0.35) ** 0.9 / 2   # full body, tapered tip
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w))
    poly = left + right[::-1]
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in poly) + " Z"


def lvl(k):
    return (k & -k).bit_length() - 1


class Leaf:
    """A channelled agave leaf. ang: degrees from vertical (+ right). L length, W max half-width,
    droop: outward sag (fraction of L at t^2), curl: tip recurve (t^4), ribbon: furrow leaf (no taper)."""

    def __init__(self, bx, by, ang, L, W, droop=0.06, curl=0.0, teeth=(OPT.get('teeth','0')=='1'), ribbon=False, wave=0.0, n=220):
        self.__dict__.update(dict(bx=bx, by=by, ang=ang, L=L, W=W, droop=droop, curl=curl, teeth=teeth,
                                  ribbon=ribbon, wave=wave, n=n))
        self.build()

    def hw(self, t):
        if self.ribbon:   # constant width (slowly widening) once out of the rosette: a strip of field
            return self.W * min(1.0, (t / 0.12) ** 0.5) * (1 + 0.5 * t)
        p, q = o('hp', 0.24), o('hq', 0.95)     # fleshy: full shoulders, quick taper to the spine
        pk = (p / (p + q)) ** p * (q / (p + q)) ** q
        return self.W * (t ** p) * ((1 - t) ** q) / pk

    def build(self):
        a = math.radians(self.ang)
        dx, dy = math.sin(a), -math.cos(a)
        nx, ny = math.cos(a), math.sin(a)                    # right-hand normal
        sg = 1 if self.ang >= 0 else -1                       # droop goes outward-and-down
        n, L = self.n, self.L
        cen = []
        for i in range(n + 1):
            t = i / n
            off = sg * L * (self.droop * t * t + self.curl * t ** 4) + L * self.wave * math.sin(math.pi * 1.6 * t) * t
            cen.append((self.bx + dx * L * t + nx * off, self.by + dy * L * t + ny * off))
        self.cen = cen
        tan, nor = [], []
        for i in range(n + 1):
            j0, j1 = max(0, i - 1), min(n, i + 1)
            tx, ty = cen[j1][0] - cen[j0][0], cen[j1][1] - cen[j0][1]
            m = math.hypot(tx, ty) or 1
            tan.append((tx / m, ty / m)); nor.append((ty / m, -tx / m))   # nor = left-hand side
        self.tan, self.nor = tan, nor
        # shadow side: light from upper left, shade the side whose normal faces down-right
        mid = n // 2
        self.shadow = -1 if (nor[mid][0] + nor[mid][1]) > 0 else 1        # u sign of the shaded side (u=+1 is left)

    def at(self, i, u):
        """point at sample i, fraction u of half-width (+1 = left edge, -1 = right edge)."""
        t = i / self.n
        h = self.hw(t) * u
        return (self.cen[i][0] + self.nor[i][0] * h, self.cen[i][1] + self.nor[i][1] * h)

    def drop_end(self, k, m, tmax, full_width=False):
        """engraver's line dropping: line k of m stops where the local pitch falls below PITCH_MIN;
        every 2nd line runs on to half that pitch, every 4th further, so tone stays even to the tip."""
        lvl = (k & -k).bit_length() - 1          # trailing zeros of k
        span = 2.0 if full_width else 1.0
        n = self.n
        for i in range(int(n * 0.3), int(n * tmax) + 1):
            pitch = self.hw(i / n) * span / (m + 1) * (2 ** lvl)
            if pitch < PITCH_MIN * (0.8 + 0.4 * ((k * 0.618034) % 1)):   # staggered, so no bands
                return i
        return int(n * tmax) + (1 if tmax >= 1.0 else 0)

    def outline(self):
        n = self.n
        left, right = [], []
        step = max(1, round(9.0 / (self.L / n)))      # a tooth every ~9 css px of length
        for i in range(n + 1):
            t = i / n
            left.append(self.at(i, 1)); right.append(self.at(i, -1))
            if self.teeth and not self.ribbon and 0.14 < t < 0.9 and i % step == 0:
                tx, ty = self.tan[i]
                for side, arr in ((1, left), (-1, right)):
                    ex, ey = self.at(i, side)
                    ox, oy = self.nor[i][0] * side, self.nor[i][1] * side
                    arr.append((ex + ox * 2.6 + tx * 2.2, ey + oy * 2.6 + ty * 2.2))
        return left + right[::-1]

    def spine(self):
        if OPT.get('spines', '0') != '1':
            return None
        if self.ribbon:
            return None
        tx, ty = self.tan[-1]
        x, y = self.cen[-1]
        s = min(16, max(7, 0.03 * self.L))
        return [(x, y), (x + tx * s, y + ty * s)]

    def at_t(self, t, u):
        n = self.n
        x = min(n - 1e-6, max(0.0, t * n)); i = int(x); f = x - i; j = min(n, i + 1)
        cx = self.cen[i][0] * (1 - f) + self.cen[j][0] * f; cy = self.cen[i][1] * (1 - f) + self.cen[j][1] * f
        nx = self.nor[i][0] * (1 - f) + self.nor[j][0] * f; ny = self.nor[i][1] * (1 - f) + self.nor[j][1] * f
        h = self.hw(t) * u
        return (cx + nx * h, cy + ny * h)

    def lines(self, pitch):
        """returns [(points, width factor)]. Tone by spacing and swell, one grammar:
        longitudinal leaves: lines thick at the shaded edge, thinning toward the lit side; line dropping tightens
        nothing but keeps the pitch >= PITCH_MIN where the leaf narrows; the heart (base) carries every line.
        front leaves (cross=True): cross-contour arcs, packed tight at the heart and opening toward the tip,
        shortening toward the lit edge."""
        out, n = [], self.n
        sh = self.shadow
        if OPT.get("cup", "1") == "1":
            out.append(([self.at(i, -sh * (0.62 - 0.25 * (i / n))) for i in range(int(n * 0.06), int(n * 0.86))], 0.7))
        if getattr(self, "cross", False):
            t = 0.04
            k = 0
            while t < 0.9:
                k += 1
                reach = 0.95 - 1.25 * t ** 1.2                          # arcs shorten toward the tip / lit edge
                u_to = -sh * max(-0.1, reach)
                seg = []
                for q in range(25):
                    f = q / 24
                    u = sh * 1.0 + (u_to - sh * 1.0) * f
                    dt = -o("bow", 0.12) * (1 - (2 * f - 1) ** 2) * self.hw(t) / self.L
                    seg.append(self.at_t(min(0.999, max(0.0, t + dt)), u))
                out.append((seg, 1.0 - 0.45 * t))
                t += HATCH * (0.75 + o("swell", 0.6) * t ** 1.4) / self.L        # tight at the heart, open at the tip
            return out
        i0 = int(n * 0.04)
        m = max(2, int(self.W / pitch))
        for k in range(1, m + 1):
            u = sh * k / (m + 1)
            tend = TEND0 + (0.90 - TEND0) * (k / (m + 1)) ** 0.9
            pts = [self.at(i, u) for i in range(i0, min(int(n * tend), self.drop_end(k, m, tend)))]
            out.append((pts, 0.4 + 0.6 * abs(u)))                   # swell toward the shaded edge
        if HEART > 0:
            for k in range(2, m + 1, 2):
                u = -sh * k / (m + 1)
                tend = HEART * (1 - 0.55 * (k / (m + 1)))
                out.append(([self.at(i, u) for i in range(i0, int(n * tend))], 0.35 + 0.2 * (1 - abs(u))))
        return out


class Cone(Leaf):
    """The central spike: tightly wrapped young leaves; dense hatch across its whole width + wrap lines."""

    def lines(self, pitch):
        """the wrapped spike: inclined cross-contour arcs spiral round it (young leaves wrapped), tight at the base
        and opening upward; alternate arcs stop at the axis so the lit side stays lighter."""
        out, n, sh = [], self.n, self.shadow
        t, k = 0.03, 0
        while t < 0.93:
            k += 1
            u_to = -sh * (0.95 if k % 2 == 0 else 0.1)
            seg = []
            for q in range(25):
                f = q / 24
                u = sh + (u_to - sh) * f
                dt = (o("cslope", 1.3) * sh * (f - 0.5) - 0.12 * (1 - (2 * f - 1) ** 2)) * self.hw(t) / self.L
                seg.append(self.at_t(min(0.999, max(0.0, t + dt)), u))
            out.append((seg, 1.0 - 0.5 * t))
            t += HATCH * (0.8 + o("cswell", 0.8) * t ** 1.3) / self.L
        return out


# ---- the agave --------------------------------------------------------------------------
def agave(bx, by, S, text_rects=None, seed=11):
    """S = scale (length of the tallest leaf). Returns svg group string + report."""
    rnd = random.Random(seed)
    j = lambda a: a * (1 + rnd.uniform(-0.07, 0.07))
    parts, report = [], {"clamped": []}
    # (angle, length factor, half-width factor, droop, curl)
    # I5's rosette table (read as an agave in round 5): one base point, three tall back leaves, the rest radiating
    BACK = [(-6, 0.90, .050, .02, 0), (6, 0.94, .052, .03, .01), (-15, 0.80, .052, .05, .02), (15, 0.86, .055, .05, 0)]
    MID = [(-24, 0.64, .060, .06, .02), (-33, 0.60, .060, .09, .03), (24, 0.74, .062, .08, .02),
           (-44, 0.62, .062, .12, .04), (36, 0.66, .064, .10, .03), (-56, 0.66, .064, .14, .05)]
    FRONT = [(-66, 0.72, .068, .12, .08), (-12, 0.46, .070, .05, .02), (8, 0.50, .072, .06, .03),
             (-76, 0.78, .066, .10, .10), (-40, 0.44, .074, .10, .04), (30, 0.48, .074, .10, .05),
             (-24, 0.36, .080, .08, .03), (16, 0.34, .080, .07, .03)]

    def clamp_leaf(mk, name):
        f = 1.0
        while True:
            lf = mk(f)
            poly = lf.outline()
            sp = lf.spine()
            pts = poly + (sp or [])
            bad = False
            if text_rects:
                for (x0, y0, x1, y1) in text_rects:
                    X0, Y0, X1, Y1 = x0 - CLEAR, y0 - CLEAR, x1 + CLEAR, y1 + CLEAR
                    if any(X0 <= x <= X1 and Y0 <= y <= Y1 for x, y in pts) or \
                            any(inside(c, poly) for c in ((X0, Y0), (X1, Y0), (X0, Y1), (X1, Y1))):
                        bad = True
                        break
            if not bad or f < 0.3:
                if f < 1.0:
                    report["clamped"].append((name, round(f, 2)))
                return lf
            f -= 0.03

    def emit(lf):
        ol = lf.outline()
        parts.append(f'<path d="{pstr(ol)} Z" fill="{GREEN}"' + (' stroke="none"' if (lf.ribbon and not RIBBON_EDGE) else '') + '/>')
        ls = [(l, w) for l, w in lf.lines(HATCH) if len(l) > 2]
        parts.append(f'<path d="{" ".join(taper(l, o("hw", 1.9) * w) for l, w in ls)}" fill="{GOLD}" stroke="none"/>')

    for k, (a, lf_, wf, dr, cu) in enumerate(BACK):
        a2, l2 = j(a) if a else a, j(lf_)
        emit(clamp_leaf(lambda f, a2=a2, l2=l2, wf=wf, dr=dr, cu=cu:
                        Leaf(bx, by, a2, S * l2 * f, S * wf * WF * (0.8 + 0.2 * f), droop=dr, curl=cu), f"back{k}"))
    emit(clamp_leaf(lambda f: Cone(bx - 6, by, -2.5, S * CONE_L * f, S * CONE_W, droop=0.0, teeth=False), "cone"))
    for k, (a, lf_, wf, dr, cu) in enumerate(MID + FRONT):
        a2, l2 = j(a), j(lf_)
        lf = clamp_leaf(lambda f, a2=a2, l2=l2, wf=wf, dr=dr, cu=cu:
                        Leaf(bx, by, a2, S * l2 * f, S * wf * WF * (0.8 + 0.2 * f), droop=dr, curl=cu), f"leaf{k}")
        lf.cross = (k >= len(MID)) and OPT.get("cross", "0") == "1"      # front leaves: cross-contour hatch
        emit(lf)
    g = (f'<g stroke="{GOLD}" stroke-width="{STROKE}" stroke-linejoin="round" stroke-linecap="round">'
         + "".join(parts) + "</g>")
    return g, report



# ---- the field ---------------------------------------------------------------------------------
def field(x0, x1, horizon, bottom, scale=1.0):
    """Restrained strip-crop field: a level horizon and near-straight contour rows. Bands alternate dense and
    open rows (strip cropping); band depth and row pitch grow toward the viewer (perspective). No boundary
    lines, no rays, no waves: every row is a very flat arc (a gentle rise), all bowing the same way."""
    rows, y, k = [], horizon, 0
    depth = bottom - horizon
    band_top = horizon
    xs = [x0 + (x1 - x0) * i / 80 for i in range(81)]
    while band_top < bottom:
        p = (band_top - horizon) / depth
        bh = (o("band0", 7) + o("bandk", 46) * p ** 1.3) * scale        # band depth grows toward the viewer
        dense = (k % 2 == 0)
        y = band_top + (0.0 if k else 0.0)
        while y < band_top + bh and y < bottom:
            q = (y - horizon) / depth
            pitch = (o("rp", 2.6) * (1 + 2.2 * q)) * scale * (1.0 if dense else o("sparse", 2.6))
            rise = o("rise", 14) * scale * q ** 1.2                       # one broad, low rise (contour ploughing)
            cx, wdt = x0 + (x1 - x0) * o("risex", 0.3), (x1 - x0) * 0.42
            rows.append([(x, y - rise * math.exp(-((x - cx) / wdt) ** 2)) for x in xs])
            y += pitch
        band_top += bh
        k += 1
    return "".join(f'<path d="{pstr(r)}" fill="none"/>' for r in rows)


def field_patch(x0, x1, horizon, bottom, scale=1.0, seed=3):
    """Patchwork of field plots: bands in perspective, each split into parcels. Inside a parcel the rows are
    straight and parallel (no convergence), at a small angle and a dense or open pitch that differs from the
    neighbours. No boundary lines: the parcels exist only where the rows change."""
    rnd = random.Random(seed)
    out = []
    depth = bottom - horizon
    band_top, k = horizon, 0
    while band_top < bottom:
        p = (band_top - horizon) / depth
        bh = (o("band0", 6) + o("bandk", 50) * p ** 1.25) * scale
        x = x0 - rnd.uniform(0, 80) * scale
        j = 0
        while x < x1:
            pw = (70 + 260 * p + rnd.uniform(0, 120) * (0.4 + p)) * scale     # parcels widen toward the viewer
            dense = (j + k) % 2 == 0
            ang = math.radians(rnd.choice([-7, -3, 0, 4, 8]) * (0.35 + p))       # flattened by perspective
            pitch = o("rp", 2.6) * (1 + 2.0 * p) * scale * (1.0 if dense else o("sparse", 2.4))
            # rows: lines y = c + tan(ang)*(X - x), clipped to the parcel [x, x+pw] x [band_top, band_top+bh]
            ta = math.tan(ang)
            c = band_top - abs(ta) * pw - pitch
            while c < band_top + bh + abs(ta) * pw:
                seg = []
                for q in range(0, 21):
                    X = x + pw * q / 20
                    Y = c + ta * (X - x)
                    if band_top + 0.8 <= Y <= band_top + bh - 0.8:
                        seg.append((X, Y))
                if len(seg) > 1:
                    out.append(seg)
                c += pitch / max(0.3, math.cos(ang))
            x += pw
            j += 1
        band_top += bh
        k += 1
    return "".join(f'<path d="{pstr(r)}" fill="none"/>' for r in out)


def mix(c1, c2, f):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * (1 - f) + y * f):02X}" for x, y in zip(a, b))


SOIL = {"gl": 900.0, "top": 760.0, "xa": 600.0, "xb": 760.0}


def ysoil(x):
    """the soil surface: level under the list, rising in one smooth low mound under the rosette (a rolling Iowa
    rise), so the loam holds the right third of the art."""
    t = min(1.0, max(0.0, (x - SOIL["xa"]) / (SOIL["xb"] - SOIL["xa"])))
    s_ = t * t * (3 - 2 * t)
    return SOIL["gl"] - (SOIL["gl"] - SOIL["top"]) * s_


def loam(x0, x1, gl, bottom, bx, scale, seed=9):
    """Iowa soil profile, all level: A horizon of dense short horizontal dashes, B of sparser dashes + stipple
    with a few clod ovals, C of sparse stipple and pebbles. Returns [(pts, width factor)]."""
    rnd = random.Random(seed)
    out = []
    depth = bottom - gl
    def dash(x, y, L, w):
        pts = [(x + L * q / 6, y) for q in range(7)]
        out.append((pts[:4][::-1], w)); out.append((pts[3:], w))
    def dot(x, y, r):
        pts = [(x - r, y), (x, y), (x + r, y)]
        out.append((pts, 1.3))
    def oval(cx, cy, rx, ry):
        pts = [(cx + rx * math.cos(2 * math.pi * q / 24), cy + ry * math.sin(2 * math.pi * q / 24)) for q in range(25)]
        out.append((pts, 0.55))
    # A horizon: 0-35 %
    y = gl + 4 * scale
    while y < gl + depth * 0.35:
        x = x0 + rnd.uniform(0, 8)
        while x < x1:
            L = rnd.uniform(5, 14) * scale
            dash(x, y + rnd.uniform(-0.5, 0.5), L, 0.8)
            x += L + rnd.uniform(3, 9) * scale
        y += rnd.uniform(3.4, 4.2) * scale
    # boundary (broken straight line)
    for yb in (gl + depth * 0.38, gl + depth * 0.74):
        x = x0
        while x < x1:
            L = rnd.uniform(30, 90) * scale
            dash(x, yb, L, 0.7)
            x += L + rnd.uniform(6, 20) * scale
    # B horizon: 40-72 %
    for _ in range(int(900 * (x1 - x0) / 840)):
        x, yy = rnd.uniform(x0, x1), gl + depth * rnd.uniform(0.41, 0.72)
        if rnd.random() < 0.55:
            dash(x, yy, rnd.uniform(3, 8) * scale, 0.7)
        else:
            dot(x, yy, 0.9 * scale)
    for _ in range(int(14 * (x1 - x0) / 840)):
        oval(rnd.uniform(x0, x1), gl + depth * rnd.uniform(0.45, 0.68), rnd.uniform(4, 9) * scale, rnd.uniform(2, 4) * scale)
    # C horizon: 76 %+
    for _ in range(int(500 * (x1 - x0) / 840)):
        dot(rnd.uniform(x0, x1), gl + depth * rnd.uniform(0.77, 1.02), 0.9 * scale)
    for _ in range(int(9 * (x1 - x0) / 840)):
        oval(rnd.uniform(x0, x1), gl + depth * rnd.uniform(0.8, 0.98), rnd.uniform(5, 11) * scale, rnd.uniform(3, 6) * scale)
    return out


def roots(bx, gl, bottom, scale, seed=7):
    """A few roots going straight down from the base, tapering."""
    rnd = random.Random(seed)
    out = []
    for r in range(int(o("nroots", 5))):
        x = bx + (r - 2) * 14 * scale + rnd.uniform(-4, 4)
        L = (bottom - gl) * rnd.uniform(0.35, 0.7)
        pts = [(x + rnd.uniform(-0.4, 0.4) * q / 10, gl + L * q / 40) for q in range(41)]
        out.append((pts, 1.1))
    return out


def art(x0, x1, gl, bottom, bx, by, S, rects, uid="l", horizon=None, hx0=None):
    """One engraving: rosette above the soil line; engraved loam below (lower contrast); the soil line; and,
    on letter, a horizon at the wordmark's baseline that the tallest leaves rise to."""
    sc = (x1 - x0) / 840
    ag, rep = agave(bx, by, S, rects)
    ink2 = mix(GOLD, GREEN, o("loamfade", 0.55))                 # loam engraved at lower contrast than the rosette
    lm = "".join(taper(p, o("hw", 1.9) * w) for p, w in loam(x0, x1, gl, bottom, bx, sc))
    rt = "".join(taper(p, o("hw", 1.9) * w) for p, w in roots(bx, gl, bottom, sc))
    top = horizon if horizon is not None else -200
    xs = [x0 + (x1 - x0) * i / 120 for i in range(121)]
    surf = " L".join(f"{x:.2f},{ysoil(x):.2f}" for x in xs)
    above = f"M{x0},{top:.2f} L{x1},{top:.2f} L{surf[::-1][:0]}" if False else None
    above_d = f"M{x0},{top:.2f} L{x1},{top:.2f} " + " ".join(f"L{x:.2f},{ysoil(x):.2f}" for x in xs[::-1]) + " Z"
    below_d = f"M{x0},{bottom + 50:.2f} L{x1},{bottom + 50:.2f} " + " ".join(f"L{x:.2f},{ysoil(x):.2f}" for x in xs[::-1]) + " Z"
    g = (f'<defs><clipPath id="above-{uid}"><path d="{above_d}"/></clipPath>'
         f'<clipPath id="below-{uid}"><path d="{below_d}"/></clipPath></defs>'
         f'<g clip-path="url(#below-{uid})"><path d="{lm}" fill="{ink2}"/><path d="{rt}" fill="{ink2}"/></g>'
         f'<g clip-path="url(#above-{uid})">{ag}</g>'
         f'<path d="M{surf}" fill="none" stroke="{GOLD}" stroke-width="{STROKE}"/>')
    if horizon is not None:
        g += f'<path d="M{hx0:.2f},{horizon:.2f} L{x1},{horizon:.2f}" fill="none" stroke="{GOLD}" stroke-width="{STROKE}"/>'
    return g, rep


# ---- page --------------------------------------------------------------------------------------
PW, PH = 816, 1056
SUBGAP = o('subgap', 8)
COLTOP = 240
PHONE_H = 2000
M = 64
C1X, C1W, C2X, C2W = 64, int(o("c1w", 344)), 0, int(o("c2w", 200))
C2X = C1X + C1W + 32


def html(svg_letter="", svg_phone="", hdr_top=64, extra1=(), extra2=()):
    c1 = "\n".join(section_html(s, dict(extra1).get(i, 0)) for i, s in enumerate(COL1))
    c2 = "\n".join(section_html(s, dict(extra2).get(i, 0)) for i, s in enumerate(COL2))
    ff = "".join(f"@font-face{{font-family:{fam};font-weight:{w};src:url({FONTS}/{file})}}" for fam, w, file in
                 [("CG", 500, "CormorantGaramond-500.ttf"), ("SS", 400, "SourceSerif4-400.ttf"),
                  ("SS", 500, "SourceSerif4-500.ttf"), ("SSI", 400, "SourceSerif4-400i.ttf"), ("DM", 500, "DMSans-500.ttf"), ("DM", 600, "DMSans-600.ttf"), ("DM", 700, "DMSans-700.ttf")])
    G = GRID
    css = f"""{ff}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:{GREEN}}}
.page{{position:relative;overflow:hidden;background:{GREEN};color:{IVORY};font-family:SS;-webkit-font-smoothing:antialiased}}
body.letter .page{{width:{PW}px;height:{PH}px}}
svg.art{{position:absolute;left:-{BLEED}px;top:-{BLEED}px}}
body.bleed{{padding:{BLEED}px}} body.bleed .page{{overflow:visible;width:{PW}px;height:{PH}px}}
svg.art-phone{{display:none}}
header{{position:absolute;left:{M}px;right:{M}px;top:{hdr_top}px;text-align:left}}
.wm{{font-family:CG;font-weight:500;font-size:82px;line-height:1;letter-spacing:.26em;color:{GOLD};margin-left:-.02em}}
.sub{{font-family:SSI;font-style:italic;font-size:15px;line-height:{3 * G}px;color:{IVORY2};margin-top:{SUBGAP}px}}
.col{{position:absolute;top:{COLTOP}px}}
.c1{{left:{C1X}px;width:{C1W}px}} .c2{{left:{C2X}px;width:{C2W}px}}
section+section{{margin-top:{4 * G}px}}
h2{{font-family:DM;font-weight:700;font-size:14.5px;letter-spacing:.24em;text-transform:uppercase;color:{WARM};line-height:{2 * G}px;margin-bottom:{G}px}}
h3{{font-family:DM;font-weight:500;font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;color:{IVORY3};line-height:{2 * G}px;margin:{2 * G}px 0 {G}px}}
h2+h3{{margin-top:0}}
.it{{margin-top:{G}px}}
h2+.it,h3+.it{{margin-top:0}}
.row{{font-size:16.5px;line-height:{3 * G}px}}
.nm{{font-weight:500}}
.prw{{margin-left:.9em;white-space:nowrap}}
.sv{{font-family:DM;font-weight:500;font-size:10px;line-height:1;letter-spacing:.12em;text-transform:uppercase;color:{IVORY2};vertical-align:baseline}}
.prw .sv{{margin-right:.55em}}
.pr{{font-weight:400;color:{IVORY2};font-variant-numeric:tabular-nums lining-nums}}
.ing{{white-space:nowrap}}
.ds .sv{{line-height:1}}
.note{{white-space:nowrap}}
.ds{{font-weight:400;font-size:12.5px;line-height:{2 * G}px;color:{IVORY2}}}
body.phone .page{{width:390px;height:{PHONE_H}px}}
body.phone svg.art{{display:none}}
body.phone svg.art-phone{{display:block;position:absolute;left:0;top:0}}
body.phone header{{position:static;padding:{5 * G}px 34px 0}}
body.phone .wm{{font-size:48px;letter-spacing:.24em}}
body.phone .sub{{font-size:14px;margin-top:{G}px}}
body.phone .col{{position:static;width:auto;padding:0 34px}}
body.phone .c1{{padding-top:{5 * G}px}} body.phone .c2{{padding-top:{4 * G}px}}
body.phone .row{{font-size:18px}} body.phone .ds{{font-size:13.5px;line-height:{2.25 * G}px}}
"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cantina &amp; cocktail bar, Iowa City: bar menu</title>
<style>{css}</style></head>
<body class="{{BODYCLASS}}"><div class="page">
{svg_letter}
{svg_phone}
<header><div class="wm">CANTINA</div><div class="sub">Cantina &amp; cocktail bar · Iowa City, Iowa</div></header>
<div class="col c1">
{c1}
</div><div class="col c2">
{c2}
</div>
</div></body></html>"""


LINES_JS = """() => {
 const pg=document.querySelector('.page').getBoundingClientRect(); const out=[];
 document.querySelectorAll('.wm,.sub,h2,h3,.nm,.pr,.sv,.ds').forEach(e=>{
   const r=document.createRange(); r.selectNodeContents(e);
   for (const b of r.getClientRects()) out.push([b.left-pg.left,b.top-pg.top,b.right-pg.left,b.bottom-pg.top]);});
 const colEnd=[...document.querySelectorAll('.col')].map(c=>{let m=0; c.querySelectorAll('.ds,.nm').forEach(e=>{const r=document.createRange(); r.selectNodeContents(e);
   for (const b of r.getClientRects()) m=Math.max(m,b.bottom-pg.top)}); return m});
 const w=document.querySelector('.wm'); const r=document.createRange(); r.selectNodeContents(w);
 return {rects:out, colEnd, wmTop:r.getBoundingClientRect().top-pg.top}; }"""

PROBE_JS = """() => {
 const pg=document.querySelector('.page').getBoundingClientRect(); const out=[];
 document.querySelectorAll('.wm,.sub,h2,h3,.nm,.pr,.sv,.ds').forEach(e=>{
   const r=document.createRange(); r.selectNodeContents(e); const b=r.getBoundingClientRect(); const cs=getComputedStyle(e);
   out.push({t:e.textContent.trim().slice(0,48),cls:e.className||e.tagName,c:cs.color,fs:cs.fontSize,
     x:b.left-pg.left,y:b.top-pg.top,w:b.width,h:b.height,lines:new Set([...r.getClientRects()].map(b=>Math.round(b.top))).size});});
 const rows=[...document.querySelectorAll('.row')].map(e=>{const n=e.querySelector('.nm'),p=e.querySelector('.pr');
   const col=e.closest('.col'); const cw=col.getBoundingClientRect().width-2*(parseFloat(getComputedStyle(col).paddingLeft)||0);
   const rn=document.createRange(); rn.selectNodeContents(n); const nb=rn.getBoundingClientRect(), pb=p.getBoundingClientRect();
   const ds=e.parentElement.querySelector('.ds'); const rd=document.createRange(); rd.selectNodeContents(ds);
   return {name:n.textContent, price:p.textContent, top:Math.round(nb.top-pg.top), gap_px:Math.round(pb.left-nb.right),
     travel_pct:Math.round(100*(pb.left-nb.right)/cw), same_line:Math.abs(pb.top-nb.top)<2, desc_lines:new Set([...rd.getClientRects()].map(b=>Math.round(b.top))).size,
     col:col.classList.contains('c1')?1:2, row_top_mod8:Math.round(e.getBoundingClientRect().top-pg.top)%8}});
 const box=s=>[...document.querySelectorAll(s)].map(e=>{const b=e.getBoundingClientRect();return [Math.round(b.left-pg.left),Math.round(b.top-pg.top),Math.round(b.right-pg.left),Math.round(b.bottom-pg.top)]});
 const colEnd=[...document.querySelectorAll('.col')].map(c=>{let m=0; c.querySelectorAll('.ds,.nm').forEach(e=>{const r=document.createRange(); r.selectNodeContents(e);
   for (const b of r.getClientRects()) m=Math.max(m,b.bottom-pg.top)}); return Math.round(m*10)/10});
 return {boxes:out, rows, geometry:{page:[pg.width,pg.height],header:box('header')[0],cols:box('.col'),col_text_end:colEnd,sections:box('section'),art_phone:box('svg.art-phone')[0]}};
}"""


def rl(c):
    c = [v / 255 for v in c]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(pg, scale, boxes):
    from PIL import Image
    pg.add_style_tag(content="*{color:transparent!important}")
    img = Image.open(io.BytesIO(pg.screenshot(full_page=True))).convert("RGB")
    rows = []
    for b in boxes:
        L1 = rl(tuple(int(float(v)) for v in re.findall(r"[\d.]+", b["c"])[:3]))
        x0, y0 = max(0, int(b["x"] * scale)), max(0, int(b["y"] * scale))
        x1, y1 = min(img.width, int((b["x"] + b["w"]) * scale)), min(img.height, int((b["y"] + b["h"]) * scale))
        worst = 99
        for px in set(img.crop((x0, y0, x1, y1)).get_flattened_data()):
            L2 = rl(px)
            worst = min(worst, (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05))
        rows.append({"text": b["t"], "role": b["cls"], "font_px_css": b["fs"], "lines": b["lines"],
                     "min_contrast": round(worst, 2),
                     "box_css": [round(b["x"]), round(b["y"]), round(b["x"] + b["w"]), round(b["y"] + b["h"])]})
    return rows


def svg_wrap(g, w, h, cls):
    return f'<svg class="{cls}" viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">{g}</svg>'


def cap_top(png_bytes, W):
    """first row (css px, dsf 1) with wordmark gold in the header zone: the real top margin of the type."""
    from PIL import Image
    import numpy as np
    a = np.asarray(Image.open(io.BytesIO(png_bytes)).convert("RGB"), dtype=int)[:240, 100:W - 100]
    ar, ag_, ab = (int(GOLD[i:i + 2], 16) for i in (1, 3, 5))
    gold = (abs(a[..., 0] - ar) < 40) & (abs(a[..., 1] - ag_) < 40) & (abs(a[..., 2] - ab) < 40)
    rows = np.nonzero(gold.sum(1) > 3)[0]
    return int(rows[0]) if len(rows) else None


def wm_rows(png_bytes):
    """(cap top, baseline) of CANTINA by pixel scan (accent-coloured rows in the header zone)."""
    from PIL import Image
    import numpy as np
    a = np.asarray(Image.open(io.BytesIO(png_bytes)).convert("RGB"), dtype=int)[:200, 60:760]
    ar = [int(GOLD[i:i + 2], 16) for i in (1, 3, 5)]
    m = (np.abs(a - np.array(ar)).sum(-1) < 90).sum(1) > 3
    rows = np.nonzero(m)[0]
    top = int(rows[0]); bot = top
    for r in rows[1:]:
        if r > bot + 1:
            break
        bot = int(r)
    return top, bot + 1


def main():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    exe = next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))
    report = {"tag": TAG, "opt": OPT, "trim_in": [8.5, 11], "bleed_px_css": BLEED, "bleed_mm": round(BLEED * 25.4 / 96, 2),
              "safe_inset_px_css": SAFE}
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=exe)

        def load(doc, cls, w, h, dsf, name):
            pg = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            tmp = HERE / f".render-{name}.html"
            tmp.write_text(doc.replace("{BODYCLASS}", cls))
            pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
            return pg

        global PHONE_H
        # pass 1 (letter, no art): wordmark cap top at 64 = the left margin; measure baseline + text boxes
        hdr = 64.0
        for _ in range(4):
            pg = load(html(hdr_top=hdr), "letter", PW, PH, 1, "p1")
            d = pg.evaluate(LINES_JS); shot = pg.screenshot(); pg.close()
            ct, base = wm_rows(shot)
            if abs(ct - M) < 1:
                break
            hdr += M - ct
        report["pass1"] = {"header_top": hdr, "cap_top": ct, "baseline": base, "col_ends": d["colEnd"]}
        rects = d["rects"]
        GL = GRID * math.ceil((d["colEnd"][0] + CLEAR + o("glpad", 8)) / GRID)
        SOIL.update(gl=GL, top=GL, xa=0, xb=1)            # flat, level soil surface
        by = GL + o("bdepth", 6)                           # the rosette base sits on the soil line
        S = o("S", 660)
        g, rep = art(-BLEED, PW + BLEED, GL, PH + BLEED, o("bx", 745), by, S, rects, "l",
                     horizon=base + 0.5, hx0=M)
        report["soil_line_y"] = GL
        report["loam_share_of_art_height"] = {"at_rosette": round((PH - SOIL["top"]) / (PH - base), 3), "at_list": round((PH - GL) / (PH - base), 3)}
        report["soil"] = dict(SOIL)
        report["letter_clamped_leaves"] = rep["clamped"]
        # phone pass (no art): text boxes, then the rosette rises beside Wine/Spirits, 6 mm clear
        PHONE_H = 4000
        pg = load(html(), "phone", 390, 800, 1, "p2")
        dp = pg.evaluate(LINES_JS); pg.close()
        pend = max(r[3] for r in dp["rects"])
        GLp = GRID * math.ceil((pend + 32) / GRID)
        PHONE_H = int(GLp + o("ploam", 190))
        SOIL.update(gl=GLp, top=GLp, xa=0, xb=1)
        gph, repp = art(0, 390, GLp, PHONE_H, o("pbx", 330), GLp + 14, o("pS", 470), dp["rects"], "p")
        report["phone"] = {"text_end": pend, "soil_line": GLp, "page_h": PHONE_H, "clamped": repp["clamped"]}
        svg_l = (f'<svg class="art" viewBox="{-BLEED} {-BLEED} {PW + 2 * BLEED} {PH + 2 * BLEED}" width="{PW + 2 * BLEED}" '
                 f'height="{PH + 2 * BLEED}" xmlns="http://www.w3.org/2000/svg">{g}</svg>')
        doc = html(svg_l, svg_wrap(gph, 390, PHONE_H, "art-phone"), hdr)
        for it in all_items():
            assert f'data-id="{it["id"]}"' in doc and f'<span class="pr">{price(it)}</span>' in doc, it["id"]
        if not TAG:
            (HERE / "menu.html").write_text(doc.replace("{BODYCLASS}", "letter"))
            (HERE / "menu-bleed.html").write_text(doc.replace("{BODYCLASS}", "bleed"))
        jobs = [(f"preview-letter{TAG}.png", "letter", PW, PH, 3.125)]
        if not TAG:
            jobs += [("preview-phone.png", "phone", 390, 800, 3), ("preview-letter-bleed.png", "bleed", PW + 2 * BLEED, PH + 2 * BLEED, 3.125)]
        for name, cls, w, h, dsf in jobs:
            pg = load(doc, cls, w, h, dsf, cls)
            pg.screenshot(path=str(HERE / name), full_page=(cls == "phone"))
            if cls == "bleed":
                pg.close(); continue
            data = pg.evaluate(PROBE_JS)
            if cls == "letter":
                from PIL import Image
                import numpy as np
                pg.add_style_tag(content="svg.art path{fill:#fff!important;stroke:#fff!important} .col,header{visibility:hidden}")
                a = np.asarray(Image.open(io.BytesIO(pg.screenshot())).convert("L").resize((204, 264))) > 128
                data["geometry"]["art_silhouette_pct_of_page"] = round(100 * float(a.mean()), 1)
                ys, xs = np.nonzero(a)
                data["geometry"]["art_bbox_css"] = [int(xs.min() * 4), int(ys.min() * 4), PW, PH]
                pg.reload(); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
            rows = contrast(pg, dsf, data["boxes"])
            report[name] = {"geometry_css_px": data["geometry"], "price_rows": data["rows"], "text": rows}
            pg.close()
        br.close()
    for t in HERE.glob(".render-*.html"):
        t.unlink()
    (HERE / f"render_report{TAG}.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print("pass1:", report["pass1"], "phone", report["phone"], "loam share", report["loam_share_of_art_height"], "soil line", report["soil_line_y"], "clamped:", report["letter_clamped_leaves"])
    for k, v in report.items():
        if isinstance(v, dict) and "text" in v:
            gm = v["geometry_css_px"]
            pr = v["price_rows"]
            print(k, "cols", gm["cols"], "text_end", gm["col_text_end"], "sil", gm.get("art_silhouette_pct_of_page"))
            print("  worst contrast", sorted((r["min_contrast"], r["text"]) for r in v["text"])[:2])
            print("  max travel %", max(r["travel_pct"] for r in pr),
                  "col1 max desc lines", max(r["desc_lines"] for r in pr if r["col"] == 1),
                  "row tops mod 8", sorted(set(r["row_top_mod8"] for r in pr)))


if __name__ == "__main__":
    main()
