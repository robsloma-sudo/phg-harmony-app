#!/usr/bin/env python3
"""TEST-1 explore-I3 "Night Field" round 3: an engraved agave rising out of an Iowa contour-strip field.

Content: every item, price and description comes from ../build/draft_doc.json; cocktail garnishes come from
phg.recipe_versions as cited in ../round-17/proposal.md (RV). Descriptions are unchanged from I2 (content), only
set differently (non-breaking multi-word ingredients, the Margarita sentence joined into the same flow).

Art: one engraving, one stroke weight. A straight horizon; below it curved contour strips that alternate
contour rows and perspective furrows (strip cropping); an agave planted in the near strips, with swelling /
tapering contour hatch made by spacing, marginal teeth, terminal spines and a twisting cone.

Passes: (1) render text only -> line boxes, column ends, header offset; balance the columns on the 8 px grid;
(2) build the art, shortening any leaf that would come within 6 mm of a text line; (3) render + measure.

Usage: python3 build.py [--tag NAME] [key=value ...]
"""
import json, math, os, sys, io, re, glob, random
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFT = json.load(open(HERE.parent / "build" / "draft_doc.json"))
FONTS = (HERE / "fonts").as_uri()
TAG = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else ""
OPT = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a and not a.startswith("--"))
o = lambda k, d: float(OPT.get(k, d))

GREEN, IVORY, IVORY2, IVORY3, GOLD = "#10291F", "#EFE6D2", "#C9C2AF", "#B3B09E", "#C8A765"
STROKE = o("stroke", 1.25)     # the one stroke weight (css px)
PITCH = o("pitch", 3.0)        # nominal hatch pitch
PMIN = o("pmin", 1.9)          # line dropping floor
CLEAR = 23                     # 6 mm
GRID = 8                       # the shared baseline increment (css px) for both columns
NBSP = " "

# ---- content -------------------------------------------------------------------------------
RV = {"beta_margarita": ("Lime wheel", "f06abb74"), "beta_daiquiri": ("Lime coin", "14d45e57"),
      "beta_old_fashioned": ("Orange peel", "7095fd3d"), "beta_manhattan": ("Cocktail cherry", "9fb77eaa")}
TAIL = {"beta_margarita": "Bright and citrus-forward."}


def desc(it):
    if it["components"]:
        hidden = {k for k, v in it["meta"].get("public_components", {}).items() if v is False}
        names = [c["name"] for c in it["components"] if c["name"].lower().replace(" ", "-") not in hidden]
        g = RV.get(it["id"])
        if g and g[0].lower() not in [n.lower() for n in names]:
            names.append(g[0])
        parts = [n.lower().replace(" ", NBSP) for n in names]          # multi-word ingredients never break
        s = (NBSP + "· ").join(parts)                                 # breaks fall after a dot, not before
        s = s[0].upper() + s[1:]
        if it["id"] in TAIL:
            assert TAIL[it["id"]].rstrip(".") in it["desc"]
            s += ". " + TAIL[it["id"]]
        return s
    return it["desc"].rstrip(".")


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
    return (f'<div class="it" data-id="{it["id"]}"><div class="row"><span class="nm">{it["name"]}</span>'
            f'<span class="pr">{price(it)}</span></div><div class="ds">{desc(it)}</div></div>')


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


def lvl(k):
    return (k & -k).bit_length() - 1


# ---- the agave ---------------------------------------------------------------------------------
class Leaf:
    """Channelled agave leaf: tapered, with marginal teeth and a terminal spine. Shading is contour hatch that
    swells toward the shaded edge by spacing (u = 1-(1-s)^GAMMA), with engraver's line dropping."""

    def __init__(self, bx, by, ang, L, W, droop=0.06, curl=0.0, teeth=True, n=220):
        self.__dict__.update(dict(bx=bx, by=by, ang=ang, L=L, W=W, droop=droop, curl=curl, teeth=teeth, n=n))
        a = math.radians(ang)
        dx, dy, nx, ny = math.sin(a), -math.cos(a), math.cos(a), math.sin(a)
        sg = 1 if ang >= 0 else -1
        self.cen = []
        for i in range(n + 1):
            t = i / n
            off = sg * L * (droop * t * t + curl * t ** 4)
            self.cen.append((bx + dx * L * t + nx * off, by + dy * L * t + ny * off))
        self.tan, self.nor = [], []
        for i in range(n + 1):
            j0, j1 = max(0, i - 1), min(n, i + 1)
            tx, ty = self.cen[j1][0] - self.cen[j0][0], self.cen[j1][1] - self.cen[j0][1]
            m = math.hypot(tx, ty) or 1
            self.tan.append((tx / m, ty / m)); self.nor.append((ty / m, -tx / m))
        mid = n // 2
        self.shadow = -1 if (self.nor[mid][0] + self.nor[mid][1]) > 0 else 1

    def hw(self, t):
        p, q = 0.28, 1.0
        pk = (p / (p + q)) ** p * (q / (p + q)) ** q
        return self.W * (t ** p) * ((1 - t) ** q) / pk

    def at(self, i, u):
        h = self.hw(i / self.n) * u
        return (self.cen[i][0] + self.nor[i][0] * h, self.cen[i][1] + self.nor[i][1] * h)

    def at_t(self, t, u):
        """continuous point at axis position t (interpolated between samples), fraction u of half-width."""
        n = self.n
        x = min(n - 1e-6, max(0.0, t * n))
        i = int(x); f = x - i
        j = min(n, i + 1)
        cx = self.cen[i][0] * (1 - f) + self.cen[j][0] * f
        cy = self.cen[i][1] * (1 - f) + self.cen[j][1] * f
        nx = self.nor[i][0] * (1 - f) + self.nor[j][0] * f
        ny = self.nor[i][1] * (1 - f) + self.nor[j][1] * f
        h = self.hw(t) * u
        return (cx + nx * h, cy + ny * h)

    def outline(self):
        n, left, right = self.n, [], []
        step = max(1, round(9.0 / (self.L / n)))
        for i in range(n + 1):
            t = i / n
            left.append(self.at(i, 1)); right.append(self.at(i, -1))
            if self.teeth and 0.14 < t < 0.9 and i % step == 0:
                tx, ty = self.tan[i]
                for side, arr in ((1, left), (-1, right)):
                    ex, ey = self.at(i, side)
                    ox, oy = self.nor[i][0] * side, self.nor[i][1] * side
                    arr.append((ex + ox * 2.6 + tx * 2.2, ey + oy * 2.6 + ty * 2.2))
        return left + right[::-1]

    def spine(self):
        tx, ty = self.tan[-1]
        x, y = self.cen[-1]
        s = min(16, max(7, 0.03 * self.L))
        return [(x, y), (x + tx * s, y + ty * s)]

    def run(self, u_of, k, du, i0, i1):
        """a hatch line at fraction u_of(t), stopped where its local spacing (with line dropping) < PMIN."""
        pts, n = [], self.n
        for i in range(i0, i1):
            t = i / n
            if t > 0.3 and self.hw(t) * du * (2 ** lvl(k)) < PMIN * (0.8 + 0.4 * ((k * 0.618034) % 1)):
                break
            u = u_of(t)
            if abs(u) > 1:
                break
            pts.append(self.at(i, u))
        return pts

    def arcs(self, t0, t1, u_from, u_to_of, bow, slope=0.0, every2_full=None):
        """cross-contour hatch: bowed arcs across the leaf. Spacing along the axis swells toward the tip
        (dense in the shaded base, open at the tip) -- tone by spacing, one stroke weight."""
        out, n = [], self.n
        t = t0
        k = 0
        while t < t1:
            k += 1
            u_to = u_to_of(t, k)
            seg = []
            for q in range(0, 25):
                f = q / 24
                u = u_from + (u_to - u_from) * f
                h = self.hw(t)
                # bow: the channel is concave, so the arc sags toward the base in the middle
                dt = (-bow * (1 - (2 * f - 1) ** 2) + slope * (2 * f - 1)) * h / self.L
                tt = min(0.999, max(0.0, t + dt))
                seg.append(self.at_t(tt, u))
            out.append(seg)
            spacing = PITCH * (0.75 + o("swell", 2.6) * t ** 1.5)          # css px along the axis
            t += spacing / self.L
        return out

    def lines(self):
        if OPT.get("hatch", "trans") == "trans":
            n = self.n
            out = [[self.at(i, 0.12 * -self.shadow) for i in range(int(n * 0.04), int(n * 0.9))]]   # crease
            sh = self.shadow
            # shaded half: arcs from the shaded edge across to the crease; near the base they cross the whole leaf
            out += self.arcs(0.05, 0.86, sh * 1.0,
                             lambda t, k: -sh * (0.9 if t < 0.28 else (0.1 if k % 2 else -0.05)), bow=o("bow", 0.12))
            return out
        return self.lines_long()

    def lines_long(self):
        out, n = [], self.n
        i0 = int(n * 0.04)
        out.append([self.at(i, 0.12 * -self.shadow) for i in range(i0, int(n * 0.9))])          # channel crease
        m = max(3, int(1.25 * self.W / PITCH))
        G = o("gamma", 1.9)
        us = [1 - (1 - k / (m + 1)) ** G for k in range(0, m + 2)]                           # dense at the edge
        for k in range(1, m + 1):
            du = us[k + 1] - us[k] if k < m else us[k] - us[k - 1]
            tend = 0.55 + 0.35 * (k / (m + 1))                                                  # longest at the edge
            u = self.shadow * us[k]
            out.append(self.run(lambda t, u=u: u, k, du, i0, int(n * tend)))
        # lit half: a few widely spaced lines near the base only (the rosette's heart is in shadow)
        for k in range(1, 4):
            u = -self.shadow * (0.35 + 0.18 * k)
            out.append([self.at(i, u) for i in range(i0, int(n * (0.42 - 0.08 * k)))])
        return out


class Cone(Leaf):
    """The wrapped central spike. Hatch lines twist around it (the young leaves are wrapped), dense on the
    shaded side and opening toward the light, so no vertical barcode."""

    def lines(self):
        if OPT.get("hatch", "trans") == "trans":
            sh = self.shadow
            # wrapped young leaves: inclined arcs spiral round the spike; every arc covers the shaded side,
            # every second one runs on across the lit side, so tone falls off toward the light
            return self.arcs(0.03, 0.97, sh * 1.0, lambda t, k: -sh * (1.0 if k % 2 == 0 else 0.2),
                             bow=0.15, slope=o("slope", 1.4) * sh)
        out, n = [], self.n
        m = max(6, int(2.2 * self.W / PITCH))
        twist = o("twist", 0.9) * self.shadow
        G = 0.62
        for k in range(1, m + 1):
            s = k / (m + 1)
            u0 = self.shadow * (2 * s ** G - 1) - twist * 0.55
            du = 2 * ((s + 1 / (m + 1)) ** G - s ** G)
            out.append(self.run(lambda t, u0=u0: u0 + twist * t, k, du, int(n * 0.03), n + 1))
        return out


def agave(bx, by, S, text_rects=None, seed=5):
    rnd = random.Random(seed)
    jit = lambda a: a * (1 + rnd.uniform(-0.07, 0.07))
    report = {"clamped": []}
    WF = o("wf", 1.8)
    # (angle, length, half-width, droop, curl) -- tall rosette: the plant rises; low leaves stay short so the
    # field reads as field
    BACK = [(-4, 0.93, .050, .02, 0), (9, 0.90, .052, .03, .01), (-15, 0.74, .052, .05, .02), (21, 0.84, .055, .05, 0)]
    MID = [(-26, 0.46, .060, .07, .02), (30, 0.70, .062, .08, .02), (-9, 0.66, .058, .04, .01), (40, 0.60, .064, .06, .02),
           (-38, 0.38, .062, .10, .04)]
    FRONT = [(-52, 0.33, .068, .10, .04), (-64, 0.31, .066, .10, .05), (-76, 0.30, .064, .08, .06),
             (-20, 0.42, .072, .05, .02), (14, 0.46, .072, .05, .02), (52, 0.46, .070, .06, .02)]

    def clamp(mk, name):
        f = 1.0
        while True:
            lf = mk(f)
            poly = lf.outline()
            pts = poly + lf.spine()
            bad = False
            for (x0, y0, x1, y1) in (text_rects or []):
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

    parts = []

    def emit(lf):
        parts.append(f'<path d="{pstr(lf.outline())} Z" fill="{GREEN}"/>')
        ls = lf.lines() + [lf.spine()]
        parts.append(f'<path d="{" ".join(pstr(l) for l in ls if len(l) > 1)}" fill="none"/>')

    for k, (a, lf_, wf, dr, cu) in enumerate(BACK):
        a2, l2 = jit(a), jit(lf_)
        emit(clamp(lambda f, a2=a2, l2=l2, wf=wf, dr=dr, cu=cu:
                   Leaf(bx, by, a2, S * l2 * f, S * wf * WF * (0.8 + 0.2 * f), dr, cu), f"back{k}"))
    emit(clamp(lambda f: Cone(bx - 6, by, -2.0, S * o("cl", 1.0) * f, S * o("cw", 0.095), 0.0, 0.0, teeth=False), "cone"))
    for k, (a, lf_, wf, dr, cu) in enumerate(MID + FRONT):
        a2, l2 = jit(a), jit(lf_)
        emit(clamp(lambda f, a2=a2, l2=l2, wf=wf, dr=dr, cu=cu:
                   Leaf(bx, by, a2, S * l2 * f, S * wf * WF * (0.8 + 0.2 * f), dr, cu), f"leaf{k}"))
    return "".join(parts), report


# ---- the field ---------------------------------------------------------------------------------
def field(W, horizon, bottom, vpx, ground_x, ground_y, scale=1.0):
    """Contour strips below a straight horizon. Returns (far_svg, near_svg, horizon_svg): far strips are behind
    the agave, near strips are in front of its base (it grows out of the field)."""
    J = int(o("strips", 8))
    X0, X1 = -12, W + 12
    xs = [X0 + (X1 - X0) * i / 160 for i in range(161)]
    depth = bottom - horizon

    def hill(x):
        f = x / W
        return 0.55 * math.sin(2 * math.pi * (0.85 * f + 0.10)) + 0.45 * math.sin(2 * math.pi * (1.6 * f + 0.55))

    def bnd(j, x):   # boundary j (0 = horizon); spacing and curvature grow toward the viewer (perspective)
        if j == 0:
            return horizon
        p = j / J
        return horizon + depth * 1.18 * p ** 1.75 + o("amp", 60) * scale * p ** 1.3 * hill(x) * (1 - 0.15 * p)

    strips = []
    for j in range(J):
        top = [(x, bnd(j, x)) for x in xs]
        bot = [(x, bnd(j + 1, x)) for x in xs]
        # enforce order (a nearer boundary never rises above a farther one)
        bot = [(x, max(yb, yt + 1.5)) for (x, yt), (_, yb) in zip(top, bot)]
        strips.append((j, top, bot))

    def contour_rows(top, bot):
        th = sum(b[1] - t[1] for t, b in zip(top, bot)) / len(top)
        m = max(1, int(th / (o("rowpitch", 4.2) * scale)))
        rows = []
        for k in range(1, m + 1):
            f = k / (m + 1)
            rows.append([(t[0], t[1] + (b[1] - t[1]) * f) for t, b in zip(top, bot)])
        return rows

    def furrows(top, bot, j):
        """rays to a vanishing point on the horizon, evenly spaced along the page bottom; rays are dropped
        (engraver's line dropping) where perspective would pack them tighter than PMIN."""
        vy = horizon - 1.5 * scale
        fp = o("furpitch", 8.0) * scale
        ymid = sum((t[1] + b[1]) / 2 for t, b in zip(top, bot)) / len(top)
        local = fp * (ymid - vy) / (bottom - vy)
        rows = []
        nray = int(3 * W / fp)
        for r in range(0, nray + 1):
            xb = -W + 3 * W * r / nray
            sin_t = (bottom - vy) / math.hypot(bottom - vy, xb - vpx)      # perpendicular spacing factor
            step = 1
            while local * sin_t * step < PMIN * 1.7:
                step *= 2
            if r % step:
                continue
            seg = []
            ylo, yhi = min(t[1] for t in top) - 1, max(b[1] for b in bot) + 1
            for q in range(0, 241):
                yy = ylo + (yhi - ylo) * q / 240
                if yy <= vy:
                    continue
                x = vpx + (xb - vpx) * (yy - vy) / (bottom - vy)
                if not (X0 <= x <= X1):
                    continue
                i = min(160, max(0, int(round((x - X0) / (X1 - X0) * 160))))
                if top[i][1] <= yy <= bot[i][1]:
                    seg.append((x, yy))
            if len(seg) > 1:
                rows.append(seg)
        return rows

    far, near = [], []
    for j, top, bot in strips:
        poly = top + bot[::-1]
        body = contour_rows(top, bot) if j % 2 == 0 else furrows(top, bot, j)
        edge = [top]
        s = (f'<path d="{pstr(poly)} Z" fill="{GREEN}" stroke="none"/>'
             f'<path d="{" ".join(pstr(l) for l in edge + body if len(l) > 1)}" fill="none"/>')
        i = min(160, max(0, int((ground_x - X0) / (X1 - X0) * 160)))
        (far if bot[i][1] <= ground_y else near).append(s)
    hz = f'<path d="M{X0},{horizon:.2f} L{X1},{horizon:.2f}" fill="none"/>'
    return "".join(far), "".join(near), hz


def art(W, H, horizon, bottom, bx, by, S, ground, rects, vpx):
    far, near, hz = field(W, horizon, bottom, vpx, ground[0], ground[1], scale=W / 816)
    ag, rep = agave(bx, by, S, rects)
    g = (f'<g stroke="{GOLD}" stroke-width="{STROKE}" stroke-linejoin="round" stroke-linecap="round">'
         f'{hz}{far}{ag}{near}</g>')
    return g, rep


# ---- page --------------------------------------------------------------------------------------
PW, PH = 816, 1056
M = 64
C1X, C1W, C2X, C2W = 64, int(o("c1w", 336)), 0, 170
C2X = C1X + C1W + 32


def html(svg_letter="", svg_phone="", hdr_top=64, extra1=(), extra2=()):
    c1 = "\n".join(section_html(s, dict(extra1).get(i, 0)) for i, s in enumerate(COL1))
    c2 = "\n".join(section_html(s, dict(extra2).get(i, 0)) for i, s in enumerate(COL2))
    ff = "".join(f"@font-face{{font-family:{fam};font-weight:{w};src:url({FONTS}/{file})}}" for fam, w, file in
                 [("CG", 500, "CormorantGaramond-500.ttf"), ("SS", 400, "SourceSerif4-400.ttf"),
                  ("SS", 500, "SourceSerif4-500.ttf"), ("DM", 500, "DMSans-500.ttf"), ("DM", 600, "DMSans-600.ttf")])
    G = GRID
    css = f"""{ff}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:{GREEN}}}
.page{{position:relative;overflow:hidden;background:{GREEN};color:{IVORY};font-family:SS;-webkit-font-smoothing:antialiased}}
body.letter .page{{width:{PW}px;height:{PH}px}}
svg.art{{position:absolute;left:0;top:0}}
svg.art-phone{{display:none}}
header{{position:absolute;left:0;right:0;top:{hdr_top}px;text-align:center}}
.wm{{font-family:CG;font-weight:500;font-size:82px;line-height:1;letter-spacing:.34em;padding-left:.34em;color:{GOLD}}}
.sub{{font-family:DM;font-weight:500;font-size:11.5px;letter-spacing:.34em;padding-left:.34em;text-transform:uppercase;color:{IVORY2};line-height:1}}
.sub.a{{margin-top:20px}} .sub.b{{margin-top:9px}}
.col{{position:absolute;top:{30 * G}px}}
.c1{{left:{C1X}px;width:{C1W}px}} .c2{{left:{C2X}px;width:{C2W}px}}
section+section{{margin-top:{4 * G}px}}
h2{{font-family:DM;font-weight:600;font-size:13.5px;letter-spacing:.3em;text-transform:uppercase;color:{GOLD};line-height:{2 * G}px;margin-bottom:{G}px}}
h3{{font-family:DM;font-weight:500;font-size:10.5px;letter-spacing:.22em;text-transform:uppercase;color:{IVORY3};line-height:{2 * G}px;margin:{2 * G}px 0 0}}
h2+h3{{margin-top:0}}
.it{{margin-top:{G}px}}
h2+.it,h3+.it{{margin-top:0}}
.row{{font-size:16.5px;line-height:{3 * G}px}}
.nm{{font-weight:500}}
.pr{{font-weight:400;color:{IVORY};margin-left:.9em;font-variant-numeric:tabular-nums lining-nums}}
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
</div></body></html>"""


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
     x:b.left-pg.left,y:b.top-pg.top,w:b.width,h:b.height,lines:r.getClientRects().length});});
 const rows=[...document.querySelectorAll('.row')].map(e=>{const n=e.querySelector('.nm'),p=e.querySelector('.pr');
   const col=e.closest('.col'); const cw=col.getBoundingClientRect().width-2*(parseFloat(getComputedStyle(col).paddingLeft)||0);
   const rn=document.createRange(); rn.selectNodeContents(n); const nb=rn.getBoundingClientRect(), pb=p.getBoundingClientRect();
   const ds=e.parentElement.querySelector('.ds'); const rd=document.createRange(); rd.selectNodeContents(ds);
   return {name:n.textContent, price:p.textContent, top:Math.round(nb.top-pg.top), gap_px:Math.round(pb.left-nb.right),
     travel_pct:Math.round(100*(pb.left-nb.right)/cw), same_line:Math.abs(pb.top-nb.top)<2, desc_lines:rd.getClientRects().length,
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


def main():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    exe = next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))
    report = {"tag": TAG, "opt": OPT}
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=exe)

        def load(doc, cls, w, h, dsf, name):
            pg = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            tmp = HERE / f".render-{name}.html"
            tmp.write_text(doc.replace("{BODYCLASS}", cls))
            pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
            return pg

        # pass 1: header offset (top margin = 64) and column balance on the grid
        hdr, ex1, ex2 = 64, {}, {}
        for _ in range(3):
            pg = load(html(hdr_top=hdr, extra1=ex1, extra2=ex2), "letter", PW, PH, 1, "p1")
            d = pg.evaluate(LINES_JS); pg.close()
            hdr = round(hdr + (M - d["wmTop"]), 1)
            e1, e2 = d["colEnd"]
            diff = e1 - e2
            if abs(diff) < 3.8:        # within 1 mm
                break
            base1 = e1 - sum(ex1.values()); base2 = e2 - sum(ex2.values())
            best = None
            for g1 in range(0, 6 * GRID, GRID):
                for g2 in range(0, 6 * GRID, GRID):
                    dd = (base1 + g1 * (len(COL1) - 1)) - (base2 + g2 * (len(COL2) - 1))
                    key = (abs(dd), abs(g1 - g2), g1 + g2)
                    if best is None or key < best[0]:
                        best = (key, g1, g2)
            _, g1, g2 = best
            ex1 = {i: g1 for i in range(1, len(COL1))} if g1 else {}
            ex2 = {i: g2 for i in range(1, len(COL2))} if g2 else {}
        report["pass1"] = {"header_top": hdr, "col_ends": d["colEnd"], "extra_col1": ex1, "extra_col2": ex2}
        rects = d["rects"]
        text_end = max(d["colEnd"])
        H0 = round(max(text_end + CLEAR + o("hgap", 16), o("horizon", 0)))
        g, rep = art(PW, PH, H0, PH, o("bx", 770), o("by", 1000), o("S", 880), (o("gx", 760), o("gy", 945)),
                     rects, o("vpx", 408))
        report["horizon_y"] = H0
        report["letter_clamped_leaves"] = rep["clamped"]
        PHW, PHH = 390, 600
        gph, _ = art(PHW, PHH, 330, PHH, 330, 560, 520, (322, 520), None, 120)
        doc = html(svg_wrap(g, PW, PH, "art"), svg_wrap(gph, PHW, PHH, "art-phone"), hdr, ex1, ex2)
        for it in all_items():
            assert f'data-id="{it["id"]}"' in doc and f'<span class="pr">{price(it)}</span>' in doc, it["id"]
        if not TAG:
            (HERE / "menu.html").write_text(doc.replace("{BODYCLASS}", "letter"))
        jobs = [(f"preview-letter{TAG}.png", "letter", PW, PH, 3.125)]
        if not TAG:
            jobs.append(("preview-phone.png", "phone", 390, 800, 3))
        for name, cls, w, h, dsf in jobs:
            pg = load(doc, cls, w, h, dsf, cls)
            pg.screenshot(path=str(HERE / name), full_page=(cls == "phone"))
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
    print("pass1:", report["pass1"], "horizon", report["horizon_y"], "clamped:", report["letter_clamped_leaves"])
    for k, v in report.items():
        if isinstance(v, dict) and "text" in v:
            gm = v["geometry_css_px"]
            print(k, "cols", gm["cols"], "text_end", gm["col_text_end"], "sil", gm.get("art_silhouette_pct_of_page"))
            print("  worst contrast", sorted((r["min_contrast"], r["text"]) for r in v["text"])[:2])
            print("  max travel %", max(r["travel_pct"] for r in v["price_rows"]),
                  "col1 max desc lines", max(r["desc_lines"] for r in v["price_rows"] if r["col"] == 1),
                  "row tops mod 8", sorted(set(r["row_top_mod8"] for r in v["price_rows"])))


if __name__ == "__main__":
    main()
