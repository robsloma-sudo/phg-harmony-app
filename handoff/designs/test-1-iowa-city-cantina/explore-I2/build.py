#!/usr/bin/env python3
"""TEST-1 explore-I2 "Night Field" round 2: an engraved agave rooted in contour-ploughed Iowa ground.

Content: every item, price and description comes from ../build/draft_doc.json; cocktail garnishes come from
phg.recipe_versions as cited in ../round-17/proposal.md (RV below). build.py asserts all of it.

The drawing is computed here: tapered channelled leaves with marginal teeth and terminal spines, a hatched
central cone, and furrow ribbons (the lowest leaves) whose hatch lines are the ploughed rows. One stroke weight.
Two passes: pass 1 renders the text alone and records every line box; pass 2 builds the drawing and shortens any
leaf that would come within CLEAR px (6 mm) of a text line.

Usage: python3 build.py [--tag NAME] [--opt key=value ...]
"""
import json, math, os, sys, io, re, glob, random
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFT = json.load(open(HERE.parent / "build" / "draft_doc.json"))
FONTS = (HERE / "fonts").as_uri()
TAG = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else ""
OPT = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a and not a.startswith("--"))

GREEN, IVORY, IVORY2, IVORY3, GOLD = "#10291F", "#EFE6D2", "#C9C2AF", "#A8A796", "#C8A765"
STROKE = float(OPT.get("stroke", 1.25))       # the one stroke weight (css px; x3.125 at print)
HATCH = float(OPT.get("hatch", 3.3))          # target hatch pitch (css px)
WF = float(OPT.get('wf', 1.8))
WRAPS = () if OPT.get('wraps') == '0' else (0.18, 0.40, 0.60)
CONE_L, CONE_W = float(OPT.get('cl', 0.98)), float(OPT.get('cw', 0.085))
PITCH_MIN = float(OPT.get('pmin', 2.7))
HEART = float(OPT.get('heart', 0.42))
CLEAR = 23                                    # 6 mm at 96 css px / in

# ---- content -----------------------------------------------------------------------------
RV = {  # garnish from phg.recipe_versions (round-17 proposal citations)
    "beta_margarita": ("Lime wheel", "f06abb74"), "beta_daiquiri": ("Lime coin", "14d45e57"),
    "beta_old_fashioned": ("Orange peel", "7095fd3d"), "beta_manhattan": ("Cocktail cherry", "9fb77eaa"),
}
TAIL = {"beta_margarita": "Bright and citrus-forward"}   # kept verbatim from the draft desc


def desc_lines(it):
    if it["components"]:
        hidden = {k for k, v in it["meta"].get("public_components", {}).items() if v is False}
        names = [c["name"] for c in it["components"] if c["name"].lower().replace(" ", "-") not in hidden]
        g = RV.get(it["id"])
        if g and g[0].lower() not in [n.lower() for n in names]:
            names.append(g[0])
        s = " · ".join(n.lower() for n in names)
        out = [s[0].upper() + s[1:]]
        if it["id"] in TAIL:
            assert TAIL[it["id"]] in it["desc"]
            out.append(TAIL[it["id"]])
        return out
    return [it["desc"].rstrip(".")]


def price(it):
    v = it["prices"][0]["value"]
    return f"{v:g}" if float(v).is_integer() else f"{v:.2f}"


SEC = {s["id"]: s for s in DRAFT["sections"]}
HEAD = {"sec_cocktails": "Cocktails", "sec_spirits": "Spirits", "sec_wine": "Wine", "sec_beer": "Draft Beer",
        "sec_cider": "Cider"}
SHOW_SUBS = {"sec_cocktails", "sec_spirits", "sec_wine"}
ORDER_FIRST = {"sub_cocktails_classics": ["beta_margarita", "beta_manhattan"]}
COL1, COL2 = ["sec_cocktails", "sec_spirits"], ["sec_wine", "sec_beer", "sec_cider"]


def item_html(it):
    ds = "".join(f'<div class="ds">{l}</div>' for l in desc_lines(it))
    return (f'<div class="it" data-id="{it["id"]}"><div class="row"><span class="nm">{it["name"]}</span>'
            f'<span class="pr">{price(it)}</span></div>{ds}</div>')


def section_html(sid):
    s = SEC[sid]
    out = [f"<section><h2>{HEAD[sid]}</h2>"]
    for it in s.get("items", []):
        out.append(item_html(it))
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


# ---- geometry helpers ----------------------------------------------------------------------
def pstr(pts):
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts)


def inside(pt, poly):
    x, y = pt
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


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
        p, q = 0.28, 1.0
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
            if pitch < PITCH_MIN:
                return i
        return int(n * tmax) + (1 if tmax >= 1.0 else 0)

    def outline(self):
        n = self.n
        left, right = [], []
        step = max(1, round(9.0 / (self.L / n)))      # a tooth every ~9 css px of length
        for i in range(n + 1):
            t = i / n
            left.append(self.at(i, 1)); right.append(self.at(i, -1))
            if self.teeth and 0.14 < t < (0.9 if not self.ribbon else 0.3) and i % step == 0:
                tx, ty = self.tan[i]
                for side, arr in ((1, left), (-1, right)):
                    ex, ey = self.at(i, side)
                    ox, oy = self.nor[i][0] * side, self.nor[i][1] * side
                    arr.append((ex + ox * 2.6 + tx * 2.2, ey + oy * 2.6 + ty * 2.2))
        return left + right[::-1]

    def spine(self):
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
        out.append([self.at(i, 0.12 * -self.shadow) for i in range(i0, int(n * 0.9))])     # crease
        m = max(2, int(self.W / pitch))
        for k in range(1, m + 1):
            u = self.shadow * k / (m + 1)
            tend = 0.40 + 0.46 * (k / (m + 1)) ** 0.9     # longest along the shaded edge: the leaf rolls away
            out.append([self.at(i, u) for i in range(i0, min(int(n * tend), self.drop_end(k, m, tend)))])
        if HEART > 0:   # the heart of the rosette is in deep shadow: hatch the lit half too, near the base only
            for k in range(1, m + 1):
                u = -self.shadow * k / (m + 1)
                tend = HEART * (1 - 0.45 * (k / (m + 1)))
                out.append([self.at(i, u) for i in range(i0, int(n * tend))])
        return out


class Cone(Leaf):
    """The central spike: tightly wrapped young leaves; dense hatch across its whole width + wrap lines."""

    def lines(self, pitch):
        out, n = [], self.n
        m = max(4, int(2 * self.W / pitch))
        for k in range(1, m + 1):
            u = 1 - 2 * k / (m + 1)
            if u * self.shadow < -0.25 and k % 3:      # lit side stays open
                continue
            tend = 1.0 if u * self.shadow >= -0.25 else 0.80   # fixed-fraction lines meet exactly at the tip
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
    FURROWS = [(-71, 1.9, 0.040, 0.03, 0.018), (-77, 2.1, 0.050, 0.02, -0.012),
               (-83, 2.3, 0.062, 0.01, 0.010)]
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
        o = lf.outline()
        parts.append(f'<path d="{pstr(o)} Z" fill="{GREEN}"/>')
        ls = lf.lines(HATCH)
        sp = lf.spine()
        if sp:
            ls.append(sp)
        parts.append(f'<path d="{" ".join(pstr(l) for l in ls if len(l) > 1)}" fill="none"/>')

    for k, (a, lf_, wf, dr, wave) in enumerate(FURROWS):
        emit(clamp_leaf(lambda f, a=a, lf_=lf_, wf=wf, dr=dr, wave=wave:
                        Leaf(bx, by, a, S * lf_ * f, S * wf, droop=dr, ribbon=True, wave=wave, n=300), f"furrow{k}"))
    for k, (a, lf_, wf, dr, cu) in enumerate(BACK):
        a2, l2 = j(a) if a else a, j(lf_)
        emit(clamp_leaf(lambda f, a2=a2, l2=l2, wf=wf, dr=dr, cu=cu:
                        Leaf(bx, by, a2, S * l2 * f, S * wf * WF * (0.8 + 0.2 * f), droop=dr, curl=cu), f"back{k}"))
    emit(clamp_leaf(lambda f: Cone(bx - 6, by, -2.5, S * CONE_L * f, S * CONE_W, droop=0.0, teeth=False), "cone"))
    for k, (a, lf_, wf, dr, cu) in enumerate(MID + FRONT):
        a2, l2 = j(a), j(lf_)
        emit(clamp_leaf(lambda f, a2=a2, l2=l2, wf=wf, dr=dr, cu=cu:
                        Leaf(bx, by, a2, S * l2 * f, S * wf * WF * (0.8 + 0.2 * f), droop=dr, curl=cu), f"leaf{k}"))
    g = (f'<g stroke="{GOLD}" stroke-width="{STROKE}" stroke-linejoin="round" stroke-linecap="round">'
         + "".join(parts) + "</g>")
    return g, report


# ---- page ---------------------------------------------------------------------------------
PW, PH = 816, 1056
M = 64
C1X, C1W, C2X, C2W = 64, 268, 362, 196


def html(svg_letter="", svg_phone=""):
    c1 = "\n".join(section_html(s) for s in COL1)
    c2 = "\n".join(section_html(s) for s in COL2)
    ff = "".join(f"@font-face{{font-family:{fam};font-weight:{w};src:url({FONTS}/{file})}}" for fam, w, file in
                 [("CG", 500, "CormorantGaramond-500.ttf"), ("SS", 400, "SourceSerif4-400.ttf"),
                  ("SS", 500, "SourceSerif4-500.ttf"), ("DM", 500, "DMSans-500.ttf"), ("DM", 600, "DMSans-600.ttf")])
    css = f"""{ff}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:{GREEN}}}
.page{{position:relative;overflow:hidden;background:{GREEN};color:{IVORY};font-family:SS;-webkit-font-smoothing:antialiased}}
body.letter .page{{width:{PW}px;height:{PH}px}}
svg.art{{position:absolute;left:0;top:0}}
svg.art-phone{{display:none}}
header{{position:absolute;left:0;right:0;top:58px;text-align:center}}
.wm{{font-family:CG;font-weight:500;font-size:82px;line-height:1;letter-spacing:.34em;padding-left:.34em;color:{GOLD}}}
.sub{{font-family:DM;font-weight:500;font-size:11.5px;letter-spacing:.34em;padding-left:.34em;text-transform:uppercase;color:{IVORY2};line-height:1}}
.sub.a{{margin-top:20px}} .sub.b{{margin-top:9px}}
.col{{position:absolute;top:246px}}
.c1{{left:{C1X}px;width:{C1W}px}} .c2{{left:{C2X}px;width:{C2W}px}}
section+section{{margin-top:34px}}
h2{{font-family:DM;font-weight:600;font-size:13.5px;letter-spacing:.3em;text-transform:uppercase;color:{GOLD};line-height:1;margin-bottom:14px}}
h3{{font-family:DM;font-weight:500;font-size:9.5px;letter-spacing:.24em;text-transform:uppercase;color:{IVORY3};line-height:1;margin:15px 0 7px}}
h2+h3{{margin-top:0}}
.it+.it{{margin-top:10px}}
.row{{font-size:16.5px;line-height:1.25}}
.nm{{font-weight:500}}
.pr{{font-weight:400;color:{IVORY2};margin-left:.9em;font-variant-numeric:tabular-nums lining-nums}}
.ds{{font-weight:400;font-size:12.5px;line-height:1.36;color:{IVORY2};margin-top:1px}}
.ds+.ds{{margin-top:0}}
body.phone .page{{width:390px}}
body.phone svg.art{{display:none}}
body.phone svg.art-phone{{display:block;margin-top:30px}}
body.phone header{{position:static;padding-top:46px}}
body.phone .wm{{font-size:48px;letter-spacing:.3em;padding-left:.3em}}
body.phone .sub{{font-size:11px}} body.phone .sub.a{{margin-top:14px}}
body.phone .col{{position:static;width:auto;padding:0 34px}}
body.phone .c1{{padding-top:42px}} body.phone .c2{{padding-top:34px}}
body.phone .row{{font-size:18px}} body.phone .ds{{font-size:13.5px}}
"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cantina &amp; Cocktail Bar, Iowa City: bar menu (explore-I2 Night Field)</title>
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
 return out; }"""

PROBE_JS = """() => {
 const pg=document.querySelector('.page').getBoundingClientRect(); const out=[];
 document.querySelectorAll('.wm,.sub,h2,h3,.nm,.pr,.ds').forEach(e=>{
   const r=document.createRange(); r.selectNodeContents(e); const b=r.getBoundingClientRect(); const cs=getComputedStyle(e);
   out.push({t:e.textContent.trim().slice(0,48),cls:e.className||e.tagName,c:cs.color,fs:cs.fontSize,
     x:b.left-pg.left,y:b.top-pg.top,w:b.width,h:b.height});});
 const rows=[...document.querySelectorAll('.row')].map(e=>{const n=e.querySelector('.nm'),p=e.querySelector('.pr');
   const col=e.closest('.col').getBoundingClientRect(); const rn=document.createRange(); rn.selectNodeContents(n);
   const nb=rn.getBoundingClientRect(), pb=p.getBoundingClientRect();
   return {name:n.textContent, price:p.textContent, gap_px:Math.round(pb.left-nb.right),
     travel_pct:Math.round(100*(pb.left-nb.right)/(col.width - (parseFloat(getComputedStyle(e.closest('.col')).paddingLeft)||0)*2)), same_line:Math.abs(pb.top-nb.top)<2}});
 const box=s=>[...document.querySelectorAll(s)].map(e=>{const b=e.getBoundingClientRect();return [Math.round(b.left-pg.left),Math.round(b.top-pg.top),Math.round(b.right-pg.left),Math.round(b.bottom-pg.top)]});
 return {boxes:out, rows, geometry:{page:[pg.width,pg.height],header:box('header')[0],wordmark:box('.wm')[0],cols:box('.col'),sections:box('section'),art_phone:box('svg.art-phone')[0]}};
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
        rows.append({"text": b["t"], "role": b["cls"], "font_px_css": b["fs"], "min_contrast": round(worst, 2),
                     "box_css": [round(b["x"]), round(b["y"]), round(b["x"] + b["w"]), round(b["y"] + b["h"])]})
    return rows


def svg_wrap(g, w, h, cls):
    return f'<svg class="{cls}" viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">{g}</svg>'


def silhouette_share(g, w, h):
    """share of the page covered by the drawing's filled silhouette (leaf outlines) - rendered by chromium later."""
    return None


def main():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    doc0 = html()
    for it in all_items():
        assert f'data-id="{it["id"]}"' in doc0 and f'<span class="pr">{price(it)}</span>' in doc0, it["id"]
    exe = next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))
    BX, BY, S = float(OPT.get("bx", 772)), float(OPT.get("by", 1150)), float(OPT.get("S", 860))
    report = {"tag": TAG, "opt": OPT}
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=exe)

        def load(doc, cls, w, h, dsf):
            pg = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            tmp = HERE / f".render-{cls}.html"
            tmp.write_text(doc.replace("{BODYCLASS}", cls))
            pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(500)
            return pg

        # pass 1: text only -> line boxes
        pg = load(doc0, "letter", PW, PH, 1)
        rects = pg.evaluate(LINES_JS)
        pg.close()
        g, rep = agave(BX, BY, S, rects)
        report["letter_clamped_leaves"] = rep["clamped"]
        gp, repp = agave(float(OPT.get("pbx", 352)), float(OPT.get("pby", 610)), float(OPT.get("pS", 470)), None)
        doc = html(svg_wrap(g, PW, PH, "art"), svg_wrap(gp, 390, 540, "art-phone"))
        if not TAG:
            (HERE / "menu.html").write_text(doc.replace("{BODYCLASS}", "letter"))
        jobs = [(f"preview-letter{TAG}.png", "letter", PW, PH, 3.125)]
        if not TAG:
            jobs.append(("preview-phone.png", "phone", 390, 800, 3))
        for name, cls, w, h, dsf in jobs:
            pg = load(doc, cls, w, h, dsf)
            pg.screenshot(path=str(HERE / name), full_page=(cls == "phone"))
            data = pg.evaluate(PROBE_JS)
            # drawing footprint: share of page inside the leaf silhouettes (fills only, strokes hidden)
            if cls == "letter":
                from PIL import Image
                pg.add_style_tag(content=f"svg.art path{{fill:#fff!important;stroke:#fff!important}} .col,header{{visibility:hidden}}")
                im = Image.open(io.BytesIO(pg.screenshot())).convert("L").resize((204, 264))
                import numpy as np
                a = np.asarray(im) > 128
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
    print("clamped:", report["letter_clamped_leaves"])
    for k, v in report.items():
        if isinstance(v, dict) and "text" in v:
            print(k, v["geometry_css_px"])
            print("  worst contrast", sorted((r["min_contrast"], r["text"]) for r in v["text"])[:2])
            print("  max travel %", max(r["travel_pct"] for r in v["price_rows"]), "all same line", all(r["same_line"] for r in v["price_rows"]))


if __name__ == "__main__":
    main()
