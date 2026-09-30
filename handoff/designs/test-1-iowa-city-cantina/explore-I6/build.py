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

GREEN, IVORY, IVORY2, IVORY3, GOLD = OPT.get("ground", "#1B1510"), "#EEE4D1", "#C4B9A6", "#A99F8E", OPT.get("accent", "#9CC3B5")
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
CUR_UID = 'l'
LOAM = OPT.get('loamc', '#120C08')
CLEAR = 23
CLEAR_ART = float(OPT.get('clear', 34))                                    # 6 mm at 96 css px / in
o = lambda k, d: float(OPT.get(k, d))
GRID = 8                                      # one baseline increment for both columns
NBSP = "\u00a0"
BLEED = 12                                    # 0.125 in = 3.2 mm art bleed past the trim, every side
SAFE = 48                                     # 0.5 in safe inset for all text

# ---- content -------------------------------------------------------------------------------
RV = {"beta_margarita": ("Lime wheel", "f06abb74"), "beta_daiquiri": ("Lime coin", "14d45e57"),
      "beta_old_fashioned": ("Orange peel", "7095fd3d"), "beta_manhattan": ("Cocktail cherry", "9fb77eaa")}
TAIL = {"beta_margarita": "Bright and citrus-forward."}


# Daiquiri: the draft desc names the syrup "house demerara syrup" (component: Demerara Syrup).
COMP_NAME = {("beta_daiquiri", "Demerara Syrup"): "house demerara syrup"}
SEP = '<span class="sep">\u00a0·</span> '            # the dot stays with the previous ingredient; breaks fall after it
SEP_BOUND = '<span class="sep">\u00a0·</span>\u00a0'  # the last two ingredients never separate (no lone garnish)


def desc(it):
    """returns (html, note_or_None)."""
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
        parts = [f'<span class="ing">{p}</span>' for p in parts]   # .ing is white-space:nowrap
        s = SEP.join(parts[:-1]) + SEP_BOUND + parts[-1] if len(parts) > 1 else parts[0]
        note = None
        if it["id"] in TAIL:
            assert TAIL[it["id"]].rstrip(".") in it["desc"]
            note = TAIL[it["id"]]
        return s, note
    return it["desc"].rstrip("."), None


def price(it):
    v = it["prices"][0]["value"]
    return f"{v:g}" if float(v).is_integer() else f"{v:.2f}"


SEC = {s["id"]: s for s in DRAFT["sections"]}
HEAD = {"sec_cocktails": "Cocktails", "sec_spirits": "Spirits", "sec_wine": "Wine", "sec_beer": "Draft Beer",
        "sec_cider": "Cider"}
SHOW_SUBS = {"sec_cocktails", "sec_spirits", "sec_wine"}
ORDER_FIRST = {"sub_cocktails_classics": ["beta_margarita", "beta_manhattan"]}
COL1, COL2 = ["sec_cocktails", "sec_spirits"], ["sec_beer", "sec_cider", "sec_wine"]


def item_html(it):
    d, note = desc(it)
    nt = f'<div class="note">{note}</div>' if note else ""
    return (f'<div class="it" data-id="{it["id"]}"><div class="row"><span class="nm">{it["name"]}</span>'
            f'<span class="pr">{price(it)}</span></div><div class="ds">{d}</div>{nt}</div>')


def section_html(sid, extra=0):
    s = SEC[sid]
    st = f' style="margin-top:{4 * GRID + extra}px"' if extra else ""
    out = [f'<section{st}><h2>{HEAD[sid]}</h2>']
    out += [item_html(i) for i in s.get("items", [])]
    for sub in s.get("subs", []):
        if sid in SHOW_SUBS:
            out.append(f"<h3>{sub['name']}</h3>")
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

    def __init__(self, bx, by, ang, L, W, droop=0.06, curl=0.0, teeth=True, ribbon=False, wave=0.0, n=220):
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

    def lines(self, pitch):
        """engraving: the channel crease plus hatch lines on the shaded half, graded so lines near the edge
        stop earlier (darker at the base, lighter toward the tip)."""
        out, n = [], self.n
        if self.ribbon:   # the furrows: evenly spaced rows across the whole strip, running off the page
            m = max(3, int(2 * self.W / pitch * 0.55))
            for k in range(1, m + 1):
                u = 1 - 2 * k / (m + 1)
                out.append([self.at(i, u) for i in range(int(n * 0.10), n + 1)])
            return out
        i0 = int(n * 0.04)
        if CREASE:
            out.append([self.at(i, 0.12 * -self.shadow) for i in range(i0, int(n * 0.9))])     # crease
        if OPT.get("cup", "1") == "1":   # the upturned far margin of a cupped leaf: its inner face shows
            out.append([self.at(i, -self.shadow * (0.62 - 0.25 * (i / n))) for i in range(int(n * 0.06), int(n * 0.86))])
        m = max(2, int(self.W / pitch))
        for k in range(1, m + 1):
            u = self.shadow * (1 - (1 - k / (m + 1)) ** o("gamma", 1.0))      # spacing swells toward the crease
            tend = TEND0 + (0.90 - TEND0) * (k / (m + 1)) ** 0.9     # longest along the shaded edge: the leaf rolls away
            out.append([self.at(i, u) for i in range(i0, min(int(n * tend), self.drop_end(k, m, tend)))])
        if HEART > 0:   # the heart of the rosette is in deep shadow: hatch the lit half too, near the base only
            for k in range(2, m + 1, 2):                                          # every second line only
                u = -self.shadow * k / (m + 1)
                tend = HEART * (1 - 0.45 * (k / (m + 1)))
                out.append([self.at(i, u) for i in range(i0, int(n * tend))])
        return out


class Cone(Leaf):
    """The central spike: tightly wrapped young leaves; dense hatch across its whole width + wrap lines."""

    def lines(self, pitch):
        out, n = [], self.n
        m = max(4, int(2 * self.W / (pitch * o("conep", 1.7))))
        for k in range(1, m + 1):
            u = 1 - 2 * k / (m + 1)
            if u * self.shadow < 0.05:                 # lit half stays open: line engraving, not a slab
                continue
            tend = 0.55 + 0.30 * abs(u)                # shading hugs the shaded edge, fades before the tip
            out.append([self.at(i, u) for i in range(int(n * 0.03), self.drop_end(k, m, tend, full_width=True))])
        for t0 in (WRAPS if 'WRAPS' in globals() else ()):   # wrapped leaf margins spiralling across the cone
            seg = []
            for j in range(0, 41):
                f = j / 40
                i = int(n * (t0 + 0.16 * f))
                seg.append(self.at(i, 1 - 2 * f))
            out.append(seg)
        return out


# ---- the agave --------------------------------------------------------------------------
def agave(bx, by, S, text_rects=None, seed=11):
    """S = scale (length of the tallest leaf). Returns svg group string + report."""
    rnd = random.Random(seed)
    j = lambda a: a * (1 + rnd.uniform(-0.07, 0.07))
    parts, report = [], {"clamped": []}
    # (angle, length factor, half-width factor, droop, curl)
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
                    X0, Y0, X1, Y1 = x0 - CLEAR_ART, y0 - CLEAR_ART, x1 + CLEAR_ART, y1 + CLEAR_ART
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
        parts.append(f'<path d="{pstr(ol)} Z" fill="{GREEN}"/>')
        if OPT.get("platetone", "1") == "1":
            parts.append(f'<path d="{pstr(ol)} Z" fill="url(#plate-{CUR_UID})" stroke="none"/>')
        ls = [l for l in lf.lines(HATCH) if len(l) > 2]
        parts.append(f'<path d="{" ".join(taper(l, o("hw", 1.8)) for l in ls)}" fill="{GOLD}" stroke="none"/>')

    for k, (a, lf_, wf, dr, cu) in enumerate(BACK):
        a2, l2 = j(a) if a else a, j(lf_)
        emit(clamp_leaf(lambda f, a2=a2, l2=l2, wf=wf, dr=dr, cu=cu:
                        Leaf(bx, by, a2, S * l2 * f, S * wf * WF * (0.8 + 0.2 * f), droop=dr, curl=cu), f"back{k}"))
    emit(clamp_leaf(lambda f: Cone(bx - 6, by, -2.5, S * CONE_L * f, S * CONE_W, droop=0.0, teeth=False), "cone"))
    for k, (a, lf_, wf, dr, cu) in enumerate(MID + FRONT):
        a2, l2 = j(a), j(lf_) * (o("low", 1.0) if a < -50 else 1.0)   # the lowest leaves leave the field visible
        emit(clamp_leaf(lambda f, a2=a2, l2=l2, wf=wf, dr=dr, cu=cu:
                        Leaf(bx, by, a2, S * l2 * f, S * wf * WF * (0.8 + 0.2 * f), droop=dr, curl=cu), f"leaf{k}"))
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


def plate_uri(seed=4):
    """Plate tone: a fine grain tile in the accent colour (alpha 0-PLATE), used only inside the drawing."""
    import base64, numpy as np
    from PIL import Image
    rs = np.random.RandomState(seed)
    n = 192
    fine = rs.rand(n, n)
    coarse = np.asarray(Image.fromarray((rs.rand(12, 12) * 255).astype("uint8")).resize((n, n), Image.BICUBIC), float) / 255
    alpha = np.clip((fine * 0.85 + coarse * 0.15) ** 2.4 * o("plate", 30), 0, 255).astype("uint8")
    rgb = [int(GOLD[i:i + 2], 16) for i in (1, 3, 5)]
    im = np.zeros((n, n, 4), "uint8"); im[..., :3] = rgb; im[..., 3] = alpha
    buf = io.BytesIO(); Image.fromarray(im, "RGBA").save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


PLATE = None


def defs(uid):
    global PLATE
    PLATE = PLATE or plate_uri()
    return (f'<pattern id="plate-{uid}" patternUnits="userSpaceOnUse" width="61.44" height="61.44">'
            f'<image href="{PLATE}" width="61.44" height="61.44" preserveAspectRatio="none"/></pattern>'
            f'<filter id="ink-{uid}" x="-2%" y="-2%" width="104%" height="104%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="{o("inkf", 1.6)}" numOctaves="2" seed="3"/>'
            f'<feDisplacementMap in="SourceGraphic" scale="{o("ink", 0.9)}" xChannelSelector="R" yChannelSelector="G"/></filter>')


def strata(x0, x1, gl, bottom, scale, seed=9):
    """Loam as an engraver draws earth: short crumb strokes at varied angles, densest in the topsoil just under
    the soil line and thinning with depth; plus two faint, broken horizon strata. Same tapered-stroke grammar."""
    rnd = random.Random(seed)
    out = []
    depth = bottom - gl
    ncr = int(o("crumbs", 650) * (x1 - x0) / 840)
    for _ in range(ncr):
        f = rnd.random() ** 1.9                         # denser near the soil line
        y = gl + 4 * scale + f * depth
        x = rnd.uniform(x0, x1)
        L = rnd.uniform(3, 10) * scale * (1 + 0.6 * f)
        ang = math.radians(rnd.uniform(-35, 35) + (0 if rnd.random() < 0.7 else 90))
        pts = [(x + math.cos(ang) * L * q / 6, y + math.sin(ang) * L * q / 6) for q in range(7)]
        out.append(taper(pts, o("sw", 1.4)))
    for yy in (gl + depth * 0.42, gl + depth * 0.78):   # two strata boundaries, broken
        x = x0
        while x < x1:
            L = rnd.uniform(60, 200) * scale
            pts = [(x + L * q / 20, yy + rnd.uniform(-0.6, 0.6)) for q in range(21)]
            out.append(taper(pts[:11][::-1], 1.3)); out.append(taper(pts[10:], 1.3))
            x += L + rnd.uniform(30, 90) * scale
    return out


def roots(bx, gl, bottom, scale, seed=7):
    """Fibrous agave roots in the loam below the soil line: tapered slivers, seeded, cropped by the page edge."""
    rnd = random.Random(seed)
    out = []
    n = int(o("nroots", 4))
    for r in range(n):
        f = (r + 0.5) / n
        ang = math.radians(-50 + 100 * f + rnd.uniform(-8, 8))          # fan downward, from left to right
        L = (o("rootlen", 80) * (0.65 + 0.5 * rnd.random()) * (1.25 - 0.6 * abs(f - 0.5))) * scale
        x, y = bx + (f - 0.5) * 40 * scale, gl + 1
        pts = [(x, y)]
        wig = rnd.uniform(-1, 1)
        for q in range(1, 41):
            t = q / 40
            dx, dy = math.sin(ang), math.cos(ang)
            bend = wig * 18 * scale * math.sin(math.pi * t * 1.3)
            pts.append((x + dx * L * t + dy * bend, y + dy * L * t * (0.7 + 0.3 * t) - dx * bend * 0.3))
        out.append(taper(pts, o("rootw", 2.1)))
        for c in range(rnd.choice([1, 2]) if OPT.get("rootlets", "0") == "1" else 0):   # a rootlet or two
            t0 = rnd.uniform(0.3, 0.6)
            i0 = int(40 * t0)
            px, py = pts[i0]
            ca = ang + rnd.choice([-1, 1]) * math.radians(rnd.uniform(25, 45))
            cl = L * rnd.uniform(0.25, 0.4)
            sub = [(px + math.sin(ca) * cl * q / 16, py + math.cos(ca) * cl * q / 16) for q in range(17)]
            out.append(taper(sub, o("rootw", 2.1) * 0.6))
    return out


def art(x0, x1, gl, bottom, bx, by, S, rects, uid="l"):
    """One engraving: the rosette above the soil line; below it a warmer, darker loam band with strata and a
    few short roots, cropped by the page edge. Plate tone + ink spread on the art only."""
    global CUR_UID
    CUR_UID = uid
    sc = (x1 - x0) / 840
    ag, rep = agave(bx, by, S, rects)
    rt = "".join(roots(bx, gl, bottom, sc))
    st = "".join(strata(x0, x1, gl, bottom, sc)) if OPT.get("strata", "1") == "1" else ""
    loam = (f'<rect x="{x0}" y="{gl:.2f}" width="{x1 - x0}" height="{bottom - gl + 60:.2f}" fill="{LOAM}"/>'
            f'<rect x="{x0}" y="{gl:.2f}" width="{x1 - x0}" height="{bottom - gl + 60:.2f}" fill="url(#plate-{uid})"/>'
            if OPT.get("loam", "1") == "1" else "")
    g = (f'<defs>{defs(uid)}<clipPath id="above-{uid}"><rect x="{x0}" y="{-200}" width="{x1 - x0}" height="{gl + 200:.2f}"/></clipPath>'
         f'<clipPath id="below-{uid}"><rect x="{x0}" y="{gl:.2f}" width="{x1 - x0}" height="{bottom - gl + 50:.2f}"/></clipPath></defs>'
         f'<g filter="url(#ink-{uid})">{loam}'
         f'<g clip-path="url(#below-{uid})"><path d="{st} {rt}" fill="{GOLD}" stroke="none"/></g>'
         f'<g clip-path="url(#above-{uid})">{ag}</g>'
         f'<path d="M{x0},{gl:.2f} L{x1},{gl:.2f}" fill="none" stroke="{GOLD}" stroke-width="{STROKE}"/></g>')
    return g, rep


# ---- page --------------------------------------------------------------------------------------
PW, PH = 816, 1056
SUBGAP = o('subgap', 20)
COLTOP = o('coltop', 240)
M = 64
C1X, C1W, C2X, C2W = 64, 328, 0, 328
C2X = C1X + C1W + 32   # 424; right margin 816-752 = 64


def html(svg_letter="", svg_phone="", hdr_top=64, extra1=(), extra2=()):
    c1 = "\n".join(section_html(s, dict(extra1).get(i, 0)) for i, s in enumerate(COL1))
    c2 = "\n".join(section_html(s, dict(extra2).get(i, 0)) for i, s in enumerate(COL2))
    ff = "".join(f"@font-face{{font-family:{fam};font-weight:{w};src:url({FONTS}/{file})}}" for fam, w, file in
                 [("CG", 500, "CormorantGaramond-500.ttf"), ("SS", 400, "SourceSerif4-400.ttf"),
                  ("SS", 500, "SourceSerif4-500.ttf"), ("SSI", 400, "SourceSerif4-400i.ttf"), ("DM", 500, "DMSans-500.ttf"), ("DM", 600, "DMSans-600.ttf")])
    G = GRID
    css = f"""{ff}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:{GREEN}}}
.page{{position:relative;overflow:hidden;background:{GREEN};color:{IVORY};font-family:SS;-webkit-font-smoothing:antialiased}}
body.letter .page{{width:{PW}px;height:{PH}px}}
svg.art{{position:absolute;left:-{BLEED}px;top:-{BLEED}px}}
body.bleed{{padding:{BLEED}px}} body.bleed .page{{overflow:visible;width:{PW}px;height:{PH}px}}
svg.art-phone{{display:none}}
header{{position:absolute;left:0;right:0;top:{hdr_top}px;text-align:center}}
.wm{{font-family:CG;font-weight:500;font-size:82px;line-height:1;letter-spacing:.34em;padding-left:.34em;color:{GOLD}}}
.sub{{font-family:DM;font-weight:500;font-size:11.5px;letter-spacing:.34em;padding-left:.34em;text-transform:uppercase;color:{IVORY2};line-height:1}}
.sub.a{{margin-top:{SUBGAP}px}} .sub.b{{margin-top:9px}}
.col{{position:absolute;top:{COLTOP}px}}
.c1{{left:{C1X}px;width:{C1W}px}} .c2{{left:{C2X}px;width:{C2W}px}}
section+section{{margin-top:{4 * G}px}}
h2{{font-family:DM;font-weight:600;font-size:13.5px;letter-spacing:.3em;text-transform:uppercase;color:{GOLD};line-height:{2 * G}px;margin-bottom:{G}px}}
h3{{font-family:DM;font-weight:500;font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:{IVORY3};line-height:{2 * G}px;margin:{2 * G}px 0 0}}
h2+h3{{margin-top:0}}
.it{{margin-top:{G}px}}
h2+.it,h3+.it{{margin-top:0}}
.row{{font-size:16.5px;line-height:{3 * G}px}}
.nm{{font-weight:500}}
.pr{{font-weight:400;color:{IVORY2};margin-left:.9em;font-variant-numeric:tabular-nums lining-nums}}
.nw{{white-space:nowrap}}
.ing{{white-space:nowrap}}
.note{{font-family:SSI;font-style:italic;font-size:12.5px;line-height:{2 * G}px;color:{IVORY2}}}
.ds{{font-weight:400;font-size:12.5px;line-height:{2 * G}px;color:{IVORY2}}}
body.phone .page{{width:390px}}
body.phone svg.art{{display:none}}
body.phone svg.art-phone{{display:block;margin-top:{3 * G}px}}
body.phone header{{position:static;padding-top:46px}}
body.phone .wm{{font-size:48px;letter-spacing:.3em;padding-left:.3em}}
body.phone .sub{{font-size:11px}} body.phone .sub.a{{margin-top:14px}}
body.phone .col{{position:static;width:auto;padding:0 34px}}
body.phone .c1{{padding-top:{5 * G}px}} body.phone .c2{{padding-top:{4 * G}px}}
body.phone section{{margin-top:{4 * G}px !important}} body.phone .col>section:first-child{{margin-top:0 !important}}
body.phone .row{{font-size:18px}} body.phone .ds{{font-size:13.5px;line-height:{2.25 * G}px}}
"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cantina &amp; Cocktail Bar, Iowa City: bar menu (explore-I3 Night Field)</title>
<style>{css}</style></head>
<body class="{{BODYCLASS}}"><div class="page">
{svg_letter}
<header><div class="wm">CANTINA</div><div class="sub a">&amp; Cocktail Bar</div><div class="sub b">Iowa City, Iowa</div></header>
<div class="col c1">
{c1}
</div><div class="col c2">
{c2}
</div>
{svg_phone}
</div>
</body></html>"""


LINES_JS = """() => {
 const pg=document.querySelector('.page').getBoundingClientRect(); const out=[];
 document.querySelectorAll('.wm,.sub,h2,h3,.nm,.pr,.ds').forEach(e=>{
   const r=document.createRange(); r.selectNodeContents(e);
   for (const b of r.getClientRects()) out.push([b.left-pg.left,b.top-pg.top,b.right-pg.left,b.bottom-pg.top]);});
 const colEnd=[...document.querySelectorAll('.col')].map(c=>{let m=0; c.querySelectorAll('.ds,.nm').forEach(e=>{const r=document.createRange(); r.selectNodeContents(e);
   for (const b of r.getClientRects()) m=Math.max(m,b.bottom-pg.top)}); return m});
 const w=document.querySelector('.wm'); const r=document.createRange(); r.selectNodeContents(w);
 return {rects:out, colEnd, wmTop:r.getBoundingClientRect().top-pg.top}; }"""

PROBE_JS = """() => {
 const pg=document.querySelector('.page').getBoundingClientRect(); const out=[];
 document.querySelectorAll('.wm,.sub,h2,h3,.nm,.pr,.ds').forEach(e=>{
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


def lockup(png_bytes, W):
    """(wordmark cap top, wordmark baseline, sub-line cap top) in css px, by pixel scan at dsf 1."""
    from PIL import Image
    import numpy as np
    a = np.asarray(Image.open(io.BytesIO(png_bytes)).convert("RGB"), dtype=int)[:260, 150:W - 150]
    g = np.array([int(GREEN[i:i + 2], 16) for i in (1, 3, 5)])
    ink = (np.abs(a - g).sum(-1) > 60).sum(1) > 2
    rows = np.nonzero(ink)[0]
    runs, start = [], rows[0]
    for p, q in zip(rows, rows[1:]):
        if q != p + 1:
            runs.append((start, p)); start = q
    runs.append((start, rows[-1]))
    return int(runs[0][0]), int(runs[0][1]), int(runs[1][0])


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

        # pass 1: the wordmark's cap tops sit exactly at the 64 px margin (same as the left margin)
        hdr = 64.0
        for _ in range(3):
            pg = load(html(hdr_top=hdr), "letter", PW, PH, 1, "p1")
            d = pg.evaluate(LINES_JS); ct = cap_top(pg.screenshot(), PW); pg.close()
            if ct is None or abs(ct - M) < 1:
                break
            hdr += M - ct
        # lock-up: baseline of CANTINA to cap top of the sub-line = 32 px; the recovered depth goes to the list
        global SUBGAP, COLTOP
        pg = load(html(hdr_top=hdr), "letter", PW, PH, 1, "p1")
        c0, base0, sub0 = lockup(pg.screenshot(), PW); pg.close()
        gap0 = sub0 - base0
        if "subgap" not in OPT:
            SUBGAP = SUBGAP - (gap0 - 32)
            COLTOP = COLTOP - GRID * int((gap0 - 32) // GRID)
        pg = load(html(hdr_top=hdr), "letter", PW, PH, 1, "p1")
        d = pg.evaluate(LINES_JS); c1_, base1, sub1 = lockup(pg.screenshot(), PW); pg.close()
        report["lockup"] = {"before_gap": gap0, "after_gap": sub1 - base1, "subgap_css": SUBGAP, "col_top": COLTOP,
                            "cap_top": c1_, "baseline": base1}
        report["pass1"] = {"header_top": hdr, "cap_top": ct, "col_ends": d["colEnd"]}
        rects = d["rects"]
        GL = round(o("gl", 972))
        assert GL >= max(d["colEnd"]) + CLEAR
        g, rep = art(-BLEED, PW + BLEED, GL, PH + BLEED, o("bx", 740), GL + o("bdepth", 16), o("S", 750), rects, "l")
        report["soil_line_y"] = GL
        report["letter_clamped_leaves"] = rep["clamped"]
        PHW, PHH = 390, 560
        gph, _ = art(0, PHW, 470, PHH, 300, 486, 420, None, "p")
        svg_l = (f'<svg class="art" viewBox="{-BLEED} {-BLEED} {PW + 2 * BLEED} {PH + 2 * BLEED}" width="{PW + 2 * BLEED}" '
                 f'height="{PH + 2 * BLEED}" xmlns="http://www.w3.org/2000/svg">{g}</svg>')
        doc = html(svg_l, svg_wrap(gph, PHW, PHH, "art-phone"), hdr)
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
    print("lockup:", report["lockup"]); print("pass1:", report["pass1"], "soil line", report["soil_line_y"], "clamped:", report["letter_clamped_leaves"])
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
