#!/usr/bin/env python3
"""TEST-1 explore-K2 "EL RELOJ" (the sun clock).

Thesis: a cantina runs on the sun. The menu is one evening, 5 pm to 2 am, and every drink sits at its hour.

Front: the rim of one great circle (centre off the left trim). Outside the rim is the dusk field; its colour is the
colour of the hour (gold at 5 pm, indigo at 2 am). The rim is graduated in 5-minute ticks, with hour numerals in the
field. Cocktail clusters are set on their hour line, and each block is pushed against the rim, so the blocks step
along the arc and the reading path is the evening.
Back: the night. 25 pours on a logarithmic ruler of months in oak (0 at dusk, 48 at the bottom). Every class sits on
the rung at its NOM-006 age; star size = Iowa accounts pouring the brand (manifest iowa_accounts).

Writes menu.html, preview-front.png, preview-back.png, preview-phone.png, menu-print-bleed.pdf, gates.json.
All text is live HTML; the art is inline SVG built from the data. No raster art.
"""
import json, math, pathlib, re, hashlib, html as H

HERE = pathlib.Path(__file__).resolve().parent
MAN_P = HERE.parent / "expanded-v1" / "manifest.json"
MAN = json.loads(MAN_P.read_text())
FONTS = HERE / "fonts"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
esc = lambda s: H.escape(s, quote=False)

# ------------------------------------------------------------------ palette
PAPER = "#F4EDDF"
INK = "#1B1C30"        # names, wordmark
INK2 = "#34303D"       # ingredients
MUTED = "#5A4F45"      # sensory (italic)
MUTED2 = "#665B51"     # garnish · glass, notes
GOLD_D = "#7E5410"     # prices + hour marks on paper (gold, darkened for 4.5:1)
NIGHT_TXT = "#F2E9D8"
NIGHT_MUTED = "#B9B3CB"
GOLD = "#E8B552"       # gold on the night (prices, ruler, stars)

# ------------------------------------------------------------------ colour maths (OKLab interpolation for the dusk)
def _lin(c): c /= 255; return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def _gam(c): c = c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055; return max(0, min(255, round(c * 255)))
def hex2rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def rgb2hex(c): return "#%02X%02X%02X" % c
def to_oklab(h):
    r, g, b = (_lin(v) for v in hex2rgb(h))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s, 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)
def from_oklab(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3; m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return rgb2hex((_gam(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s), _gam(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
                    _gam(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)))
def ramp(stops, t):
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            f = 0 if t1 == t0 else max(0, (t - t0) / (t1 - t0)); A, B = to_oklab(c0), to_oklab(c1)
            return from_oklab(*[A[i] + (B[i] - A[i]) * f for i in range(3)])
    return stops[-1][1]
def lum(c):
    f = lambda v: (v / 255) / 12.92 if v / 255 <= 0.04045 else (((v / 255) + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])
def cr(a, b): la, lb = lum(a), lum(b); return (max(la, lb) + .05) / (min(la, lb) + .05)

# ------------------------------------------------------------------ content (manifest only)
COCK = {i["name"]: i for rows in MAN["cocktails"].values() for i in rows}
ZERO = [i for rows in MAN["zero_proof"].values() for i in rows]
SPIRITS = {i["name"]: i for rows in MAN["spirits"].values() for i in rows}
PROPOSED = lambda i: i["status"] != "approved_db"
def money(p): return ("%.2f" % p) if p != int(p) else str(int(p))

# PHG-inferred service suggestion: the hour each cocktail suits best (justified in proposal.md). Index 0 = 5 pm.
HOURS = [(0, ["Ranch Water", "Paloma"]), (1, ["Batanga", "House Daiquiri"]), (2, ["Margarita", "Spicy Pineapple Margarita"]),
         (3, ["Mezcal Negroni", "Loess"]), (4, ["Manhattan"]), (5, ["Milpa Old Fashioned", "Brown Butter Old Fashioned"]), (6, ["Carajillo"])]
assert sorted(n for _, ns in HOURS for n in ns) == sorted(COCK), "every cocktail placed once"
HLABEL = ["5", "6", "7", "8", "9", "10", "11", "12", "1", "2"]
HSUF = ["pm", "", "", "", "", "", "", "am", "", "am"]

# liquid tint only where an ingredient makes it obvious (brief): Campari red, espresso dark, cola dark
def liquid(i):
    ing = " ".join(i["ingredients"]).lower()
    if "campari" in ing: return "#B3342B"
    if "espresso" in ing: return "#3B2A21"
    if "cola" in ing: return "#4E2C1E"
    return "#D5C6A8"

def glyph(i, size_pt=None):
    """Mini glass glyph from the manifest glass + garnish fields. 12 x 16 units; ice cue for rocks/highball."""
    g, gar, liq = i["glass"], (i["garnish"] or ""), liquid(i)
    s = []
    if g == "rocks":
        s.append(f'<path d="M2.2 6.2 L2.8 15.2 H9.2 L9.8 6.2 Z" fill="{liq}"/>')
        s.append('<rect x="3.7" y="7.6" width="2.4" height="2.4" fill="none" stroke="#FFF8EC" stroke-width=".6"/><rect x="6.2" y="10.6" width="2.3" height="2.3" fill="none" stroke="#FFF8EC" stroke-width=".6"/>')
        s.append(f'<path d="M1.6 4.4 L2.6 15.6 H9.4 L10.4 4.4" fill="none" stroke="{INK}" stroke-width=".7" stroke-linejoin="round"/>')
        rim = (1.6, 10.4, 4.4)
    elif g == "highball":
        s.append(f'<path d="M3.3 4 L3.7 15.2 H8.3 L8.7 4 Z" fill="{liq}"/>')
        s.append('<rect x="4.4" y="5.4" width="2.2" height="2.2" fill="none" stroke="#FFF8EC" stroke-width=".55"/><rect x="5.5" y="8.6" width="2.2" height="2.2" fill="none" stroke="#FFF8EC" stroke-width=".55"/><rect x="4.4" y="11.8" width="2.2" height="2.2" fill="none" stroke="#FFF8EC" stroke-width=".55"/>')
        s.append(f'<path d="M2.9 1.6 L3.5 15.6 H8.5 L9.1 1.6" fill="none" stroke="{INK}" stroke-width=".7" stroke-linejoin="round"/>')
        rim = (2.9, 9.1, 1.6)
    else:  # coupe (served up: no ice cue)
        s.append(f'<path d="M1.9 6.2 Q6 11.3 10.1 6.2 Z" fill="{liq}"/>')
        s.append(f'<path d="M1 4.6 Q6 12.6 11 4.6 M6 9.4 V15.2 M3.4 15.4 H8.6" fill="none" stroke="{INK}" stroke-width=".7" stroke-linecap="round"/>')
        rim = (1, 11, 4.6)
    x0, x1, y = rim
    if gar == "lime wheel":
        s.append(f'<circle cx="{x1}" cy="{y}" r="2.1" fill="{PAPER}" stroke="{INK}" stroke-width=".55"/><path d="M{x1-1.5} {y} H{x1+1.5} M{x1} {y-1.5} V{y+1.5}" stroke="{INK}" stroke-width=".35"/>')
    elif gar == "lime wedge":
        s.append(f'<path d="M{x1-1.6} {y} L{x1+1.8} {y} L{x1+0.4} {y-2.6} Z" fill="{PAPER}" stroke="{INK}" stroke-width=".55" stroke-linejoin="round"/>')
    elif gar == "salt rim":
        s.append("".join(f'<circle cx="{x0 + k * (x1 - x0) / 5:.2f}" cy="{y - 0.7}" r=".5" fill="{INK}"/>' for k in range(6)))
    elif gar == "orange peel":
        s.append(f'<path d="M{x1-1.2} {y-0.2} q1.6 -1.6 2.6 0.4 q0.6 1.4 -0.4 2.6" fill="none" stroke="{INK}" stroke-width=".7" stroke-linecap="round"/>')
    elif gar == "cocktail cherry":
        s.append(f'<circle cx="6" cy="7.4" r="1.3" fill="{INK}"/>')
    elif gar == "lime coin":
        s.append(f'<ellipse cx="7.4" cy="6.4" rx="1.6" ry=".7" fill="{PAPER}" stroke="{INK}" stroke-width=".5"/>')
    elif gar == "candied ginger":
        s.append(f'<path d="M{x1-0.6} {y+1.2} L{x1+1.2} {y-3.4}" stroke="{INK}" stroke-width=".45"/><rect x="{x1+0.1}" y="{y-3.6}" width="1.9" height="1.9" fill="{PAPER}" stroke="{INK}" stroke-width=".5" transform="rotate(12 {x1+1} {y-2.6})"/>')
    return '<svg class="gl" viewBox="0 0 12 16" aria-hidden="true">' + "".join(s) + "</svg>"

# ------------------------------------------------------------------ FRONT geometry (pt, page 612 x 792)
Y5, STEP = 166.0, 62.0                      # 5 pm hour line; one hour of the evening = 63 pt of page
YH = [Y5 + h * STEP for h in range(10)]     # 5 pm ... 2 am
CY = (YH[0] + YH[-1]) / 2
R = 590.0                                    # the rim of the great circle
COLW, CG, GAP = 176.0, 14.0, 28.0            # item column, gutter between the two items of an hour, text-to-rim gap
W = 2 * COLW + CG
def arc_x(y): return CX + math.sqrt(max(0.0, R * R - (y - CY) ** 2))
CX = 0.0
CX = 36 + W + GAP - (0 + math.sqrt(R * R - (YH[0] - 10 - CY) ** 2))   # 5 pm block starts on the 36 pt margin
def block_left(y, h_pt): return min(arc_x(yy) for yy in (y - 10, y + h_pt * 0.5, y + h_pt)) - GAP - W

FIELD = [(-9, "#EEE2C9"), (80, "#EDD49E"), (Y5, "#E2A947"), (YH[2], "#D27D3C"), (YH[3] - 14, "#9A4945"), (YH[4], "#87404A"), (YH[6], "#553561"),
         (YH[7], "#2F2D5E"), (YH[9], "#1A1C42"), (801, "#12142F")]
def field_at(y): return ramp(FIELD, y)

def front_svg():
    stops = "".join(f'<stop offset="{(y + 9) / 810:.4f}" stop-color="{field_at(y)}"/>' for y in range(-9, 802, 9))
    circ = f"M {CX - R:.2f} {CY:.2f} a {R} {R} 0 1 0 {2 * R:.2f} 0 a {R} {R} 0 1 0 {-2 * R:.2f} 0 Z"
    s = [f'<defs><linearGradient id="dusk" gradientUnits="userSpaceOnUse" x1="0" y1="-9" x2="0" y2="801">{stops}</linearGradient></defs>',
         f'<rect x="-9" y="-9" width="630" height="810" fill="{PAPER}"/>',
         f'<path d="M -9 -9 H 621 V 801 H -9 Z {circ}" fill="url(#dusk)" fill-rule="evenodd"/>',
         f'<circle cx="{CX:.2f}" cy="{CY:.2f}" r="{R}" fill="none" stroke="{INK}" stroke-width=".6"/>',
         f'<circle cx="{CX:.2f}" cy="{CY:.2f}" r="{R + 19}" fill="none" stroke="#FFF6E6" stroke-opacity=".38" stroke-width=".45"/>']
    # graduation: every 5 minutes from 5 pm to 2 am, radial to the centre
    for k in range(9 * 12 + 1):
        y = Y5 + k * STEP / 12
        px = arc_x(y); ux, uy = (px - CX) / R, (y - CY) / R
        hour = k % 12 == 0; q = k % 3 == 0
        r0, r1 = R + 1.2, R + (19 if hour else 11 if q else 6.5)
        op = .95 if hour else .62 if q else .45
        wdt = .9 if hour else .55 if q else .42
        s.append(f'<line x1="{CX + ux * r0:.2f}" y1="{CY + uy * r0:.2f}" x2="{CX + ux * r1:.2f}" y2="{CY + uy * r1:.2f}" stroke="#FFF6E6" stroke-opacity="{op}" stroke-width="{wdt}"/>')
        if hour:  # the hour line continues inside the rim, toward the cluster, in gold
            a0, a1 = R - 16, R - 1.2
            s.append(f'<line x1="{CX + ux * a0:.2f}" y1="{CY + uy * a0:.2f}" x2="{CX + ux * a1:.2f}" y2="{CY + uy * a1:.2f}" stroke="{GOLD_D}" stroke-width=".9"/>')
    return f'<svg class="art" viewBox="-9 -9 630 810" aria-hidden="true">{"".join(s)}</svg>'

# ------------------------------------------------------------------ item markup
def ring(i): return '<i class="prop" title="proposed"></i>' if PROPOSED(i) else ""
def cocktail(i, cls=""):
    ings = '<span class="sep"> · </span>'.join(f'<span class="ig">{esc(x)}</span>' for x in i["ingredients"])
    gg = ((f'<span class="gar">{esc(i["garnish"])}</span><span class="sep"> · </span>') if i["garnish"] else "") + f'<span class="gls">{esc(i["glass"])}</span>'
    return (f'<div class="item {cls}" data-kind="cocktail" data-name="{esc(i["name"])}" data-status="{i["status"]}">{glyph(i)}'
            f'<div class="row"><span class="name tx">{esc(i["name"])}</span><span class="price tx">{money(i["price"])}</span>{ring(i)}</div>'
            f'<div class="sd tx">{esc(i["sensory"])}</div>'
            f'<div class="ing tx">{ings}<span class="gg">{gg}</span></div></div>')
def simple(i, kind, cls=""):
    return (f'<div class="item {cls}" data-kind="{kind}" data-name="{esc(i["name"])}" data-status="{i["status"]}">'
            f'<div class="row"><span class="name tx">{esc(i["name"])}</span><span class="price tx">{money(i["price"])}</span>{ring(i)}</div>'
            f'<div class="sd tx">{esc(i["sensory"])}</div></div>')

def front_html():
    out = [front_svg()]
    out.append('<div class="wm tx" style="left:36pt;top:36pt">Cantina</div>')
    out.append('<div class="venue tx" style="left:36pt;top:103pt">Cantina &amp; Cocktail Bar · Iowa City, Iowa</div>')
    out.append(f'<h2 class="tx" style="left:36pt;top:{Y5 - 40:.2f}pt"><span class="es">Cócteles</span> · Cocktails</h2>')
    # hour numerals in the field, on the hour line, just outside the graduation
    for h, y in enumerate(YH):
        px = arc_x(y); ux, uy = (px - CX) / R, (y - CY) / R
        nx, ny = CX + ux * (R + 25), CY + uy * (R + 25)
        c = field_at(ny)
        col = INK if cr(hex2rgb(c), hex2rgb(INK)) >= cr(hex2rgb(c), hex2rgb(PAPER)) else PAPER
        suf = f'<span class="ap">{HSUF[h]}</span>' if HSUF[h] else ""
        out.append(f'<div class="hr tx" data-h="{h}" style="left:{nx:.2f}pt;top:{ny - 13:.2f}pt;color:{col}">{HLABEL[h]}{suf}</div>')
    # cocktail clusters: the block is pushed against the rim at its hour, so blocks step along the arc
    for h, names in HOURS:
        y = YH[h]; left = block_left(y, 50)
        for k, n in enumerate(names):
            out.append(f'<div class="slot" data-h="{h}" style="left:{left + k * (COLW + CG):.2f}pt;top:{y - 8.5:.2f}pt;width:{COLW if len(names) > 1 else W}pt">{cocktail(COCK[n])}</div>')
    # zero proof: after the last cocktail, at the turn of midnight
    y = YH[7]; left = block_left(y, 64)
    out.append(f'<h3 class="tx" style="left:{left + 16:.2f}pt;top:{y - 27:.2f}pt"><span class="es">Sin alcohol</span> · Zero proof</h3>')
    for k, i in enumerate(ZERO):
        r, c = divmod(k, 2); yy = y + r * 34; lft = left
        out.append(f'<div class="slot z" style="left:{lft + c * (COLW + CG):.2f}pt;top:{yy - 8.5:.2f}pt;width:{COLW}pt">{simple(i, "zero")}</div>')
    y = YH[9]; left = block_left(y - 20, 20)
    out.append(f'<div class="key tx" style="left:{left + 16:.2f}pt;top:{y - 16:.2f}pt"><i class="prop"></i> proposed — pending approval</div>')
    out.append(f'<div class="note tx" style="left:{left + 16:.2f}pt;top:{y - 3:.2f}pt">Each drink is set at the hour it suits: a suggestion, not a schedule.</div>')
    return "".join(out)

# ------------------------------------------------------------------ BACK geometry: the night, a log ruler of months in oak
Y0, HH = 128.0, 440.0
LN49 = math.log(49)
def ym(m): return Y0 + HH * math.log(1 + m) / LN49
RX = 76.0                       # ruler axis
BX = 96.0                      # blocks start
BCW, BCG = 148.0, 6.0           # block column width / gutter
def bcol(c): return BX + c * (BCW + BCG)
ROWH = 21.5
IA_MAX = 1288
def star_r(n): return 1.3 + 3.9 * math.sqrt(n / IA_MAX)

CLASSES = [  # (label_es, label_en, months, [names], column span start, sensory source name)
    ("Blanco", "tequila", 0, ["Blanco Tequila", "Espolòn Blanco", "Olmeca Altos Plata", "Milagro Silver", "Patrón Silver", "Siete Leguas Blanco", "Casamigos Blanco", "Don Julio Blanco"], 0, 2),
    ("Mezcal", "espadín", 0, ["Del Maguey Vida", "Montelobos Espadín", "Ilegal Joven", "400 Conejos Espadín"], 2, 1),
    ("Reposado", "tequila", 2, ["Hornitos Reposado", "Cazadores Reposado", "Teremana Reposado", "Corralejo Reposado", "Casa Noble Reposado", "Herradura Reposado", "Fortaleza Reposado", "Clase Azul Reposado"], 0, 3),
    ("Añejo", "tequila", 12, ["Añejo Tequila", "Tres Generaciones Añejo", "Don Julio 1942", "El Tesoro Añejo"], 0, 3),
    ("Cognac", "VSOP", 48, ["Cognac VSOP"], 0, 1),
]
assert sorted(n for c in CLASSES for n in c[3]) == sorted(SPIRITS), "every pour placed once"
OWN_CLASS_SENS = {n: SPIRITS[c[3][-1]]["sensory"] for c in CLASSES for n in c[3]}  # class line printed once in the head

def back_svg():
    s = ['<defs><linearGradient id="night" gradientUnits="userSpaceOnUse" x1="0" y1="-9" x2="0" y2="801">'
         '<stop offset="0" stop-color="#2B2B57"/><stop offset=".45" stop-color="#1B1C40"/><stop offset="1" stop-color="#0D0F24"/></linearGradient></defs>',
         '<rect x="-9" y="-9" width="630" height="810" fill="url(#night)"/>']
    # ruler: every month 0..48, log spaced; long ticks at the labelled months
    s.append(f'<line x1="{RX}" y1="{ym(0) - 8:.2f}" x2="{RX}" y2="{ym(48) + 8:.2f}" stroke="{GOLD}" stroke-width=".7"/>')
    for m in range(49):
        y = ym(m); L = 9 if m in (0, 1, 2, 3, 6, 12, 24, 36, 48) else 4.5
        s.append(f'<line x1="{RX - L:.2f}" y1="{y:.2f}" x2="{RX}" y2="{y:.2f}" stroke="{GOLD}" stroke-width="{.7 if L > 5 else .45}"/>')
    # class ranges from the manifest sensory lines: blanco unaged (0), reposado 2-12, anejo 12-36, VSOP 48+
    s.append(f'<circle cx="{RX + 6}" cy="{ym(0):.2f}" r="3.2" fill="{GOLD}"/>')
    s.append(f'<rect x="{RX + 4}" y="{ym(2) + .8:.2f}" width="4" height="{ym(12) - ym(2) - 1.6:.2f}" fill="{GOLD}"/>')
    s.append(f'<rect x="{RX + 4}" y="{ym(12) + .8:.2f}" width="4" height="{ym(36) - ym(12) - 1.6:.2f}" fill="{GOLD}" fill-opacity=".78"/>')
    s.append(f'<rect x="{RX + 4}" y="{ym(48) + .8:.2f}" width="4" height="22" fill="{GOLD}" fill-opacity=".55"/>')
    # rungs: the class sits on its month line
    for m in (0, 2, 12, 48):
        s.append(f'<line x1="{RX}" y1="{ym(m):.2f}" x2="576" y2="{ym(m):.2f}" stroke="{GOLD}" stroke-opacity=".55" stroke-width=".5"/>')
    return s

def pour_row(n):
    i = SPIRITS[n]; acc = i["iowa_accounts"]
    meta = []
    if i["nom"]: meta.append(f'NOM {i["nom"]}')
    if i["region"]: meta.append(i["region"])
    if not meta and n in ("Blanco Tequila", "Añejo Tequila", "Cognac VSOP"): meta.append("casa · house pour")
    return acc, (f'<div class="item pour" data-kind="spirit" data-name="{esc(n)}" data-status="{i["status"]}" data-ia="{acc if acc else ""}">'
                 f'<div class="row"><span class="name tx">{esc(n)}</span><span class="price tx">{money(i["price"])}</span>{ring(i)}</div>'
                 f'<div class="meta tx">{esc(" · ".join(meta)) if meta else "&nbsp;"}</div>'
                 + (f'<div class="sd tx">{esc(i["sensory"])}</div>' if i["sensory"] != OWN_CLASS_SENS.get(n, i["sensory"]) else "") + '</div>')

def back_html():
    svg = back_svg(); out = []
    out.append(f'<h2 class="tx" style="left:36pt;top:37pt"><span class="es">Destilados</span> · Spirits</h2>')
    out.append(f'<div class="cap tx" style="left:36pt;top:64pt">Twenty-five pours, set by months in oak</div>')
    out.append(f'<div class="axl tx" style="left:36pt;top:{ym(0) - 36:.2f}pt">Months<br>in oak</div>')
    for m in (0, 1, 2, 3, 6, 12, 24, 36, 48):
        out.append(f'<div class="mo tx" style="left:36pt;width:{RX - 12 - 36}pt;top:{ym(m) - 6:.2f}pt">{m}</div>')
    # legend (top right)
    lx = 336.0
    out.append(f'<div class="lg tx" style="left:{lx}pt;top:36pt;width:240pt;white-space:normal">Star size: Iowa accounts pouring the brand (PHG brand graph)</div>')
    for k, (n, lab) in enumerate([(100, "100"), (500, "500"), (1000, "1,000")]):
        x = lx + 6 + k * 50
        svg.append(f'<circle cx="{x:.2f}" cy="72" r="{star_r(n):.2f}" fill="{GOLD}"/>')
        out.append(f'<div class="lg tx" style="left:{x + 8:.2f}pt;top:66pt">{lab}</div>')
    svg.append(f'<path d="M{lx + 156:.2f} 72 h6 M{lx + 159:.2f} 69 v6" stroke="{NIGHT_MUTED}" stroke-width=".7"/>')
    out.append(f'<div class="lg tx" style="left:{lx + 166:.2f}pt;top:66pt">no data</div>')
    out.append(f'<div class="key tx" style="left:{lx}pt;top:84pt"><i class="prop"></i> proposed — pending approval</div>')
    for es, en, m, names, c0, span in CLASSES:
        y = ym(m); x = bcol(c0)
        sens = SPIRITS[names[-1]]["sensory"]
        out.append(f'<h3 class="tx" style="left:{x:.2f}pt;top:{y - 16:.2f}pt"><span class="es">{es}</span> {en}</h3>')
        out.append(f'<div class="csd tx" style="left:{x:.2f}pt;top:{y + 2.5:.2f}pt;width:{span * BCW + (span - 1) * BCG:.2f}pt">{esc(sens)}</div>')
        per = math.ceil(len(names) / span); extra = {}
        for k, n in enumerate(names):
            col, row = divmod(k, per)
            xx, yy = bcol(c0 + col), y + 17 + row * ROWH + extra.get(col, 0)
            if SPIRITS[n]["sensory"] != sens: extra[col] = extra.get(col, 0) + 11
            acc, htm = pour_row(n)
            if acc: svg.append(f'<circle cx="{xx + 3.5:.2f}" cy="{yy + 6.2:.2f}" r="{star_r(acc):.2f}" fill="{GOLD}"/>')
            elif n not in ("Blanco Tequila", "Añejo Tequila", "Cognac VSOP"):
                svg.append(f'<path d="M{xx + 0.5:.2f} {yy + 6.2:.2f} h6 M{xx + 3.5:.2f} {yy + 3.2:.2f} v6" stroke="{NIGHT_MUTED}" stroke-width=".7"/>')
            else:
                svg.append(f'<rect x="{xx + 1.5:.2f}" y="{yy + 4.2:.2f}" width="4" height="4" fill="none" stroke="{GOLD}" stroke-width=".7"/>')
            out.append(f'<div class="slot" style="left:{xx + 12:.2f}pt;top:{yy - 1:.2f}pt;width:{BCW - 12}pt">{htm}</div>')
    # Ilegal Joven's own sensory differs from the other three espadín pours: print it under its row
    # (placed by CSS order: see .ilegal)
    # beer, cider, wine under the chart
    yb = 646.0
    cols = [("De barril", "Draft", MAN["beer_cider"]["De barril · Draft"], 0),
            ("En lata", "Cans", MAN["beer_cider"]["En lata · Cans"], 1), ("Sidra", "Cider", MAN["beer_cider"]["Sidra · Cider"], 1),
            ("Por copa", "By the glass", MAN["wine"]["Por copa · By the glass"], 2), ("Espumosos", "Sparkling", MAN["wine"]["Espumosos · Sparkling"], 2)]
    out.append(f'<h2 class="tx small" style="left:36pt;top:{yb - 34:.2f}pt"><span class="es">Cerveza, sidra y vino</span> · Beer, cider &amp; wine</h2>')
    svg.append(f'<line x1="36" y1="{yb - 8:.2f}" x2="576" y2="{yb - 8:.2f}" stroke="{GOLD}" stroke-opacity=".55" stroke-width=".5"/>')
    ycur = {0: yb, 1: yb, 2: yb}
    colx = {0: 36.0, 1: 250.0, 2: 416.0}
    for es, en, rows, c in cols:
        out.append(f'<h3 class="tx" style="left:{colx[c]:.2f}pt;top:{ycur[c]:.2f}pt"><span class="es">{es}</span> · {en}</h3>')
        ycur[c] += 16
        for i in rows:
            out.append(f'<div class="slot bw" style="left:{colx[c]:.2f}pt;top:{ycur[c]:.2f}pt;width:{206 if c == 0 else 160}pt">{simple(i, "beer" if c < 2 else "wine")}</div>')
            ycur[c] += 23.5
        ycur[c] += 6
    return f'<svg class="art" viewBox="-9 -9 630 810" aria-hidden="true">{"".join(svg)}</svg>' + "".join(out)

# ------------------------------------------------------------------ PHONE (390 css px, one scroll)
def phone_html():
    o = ['<section class="ph-front">']
    # hero: the same rim, cropped to a 390 x 300 window (arc drawn in phone px)
    pr, pcx, pcy = 520.0, -40.0, 470.0
    stops = "".join(f'<stop offset="{k / 20:.3f}" stop-color="{field_at(Y5 - 40 + k * (YH[9] - Y5 + 40) / 20)}"/>' for k in range(21))
    arc = f"M {pcx - pr} {pcy} a {pr} {pr} 0 1 0 {2 * pr} 0 a {pr} {pr} 0 1 0 {-2 * pr} 0 Z"
    ticks = []
    for k in range(0, 9 * 12 + 1):
        a0, a1 = math.atan2(-470, 222), math.atan2(-292, 430)
        a = a0 + (a1 - a0) * k / 108; ux, uy = math.cos(a), math.sin(a)
        L = 16 if k % 12 == 0 else 9 if k % 3 == 0 else 5
        ticks.append(f'<line x1="{pcx + ux * (pr + 1):.1f}" y1="{pcy + uy * (pr + 1):.1f}" x2="{pcx + ux * (pr + L):.1f}" y2="{pcy + uy * (pr + L):.1f}" stroke="#FFF6E6" stroke-opacity="{.9 if L == 16 else .55}" stroke-width="{1 if L == 16 else .6}"/>')
    o.append(f'<svg class="ph-hero" viewBox="0 0 390 196" aria-hidden="true"><defs><linearGradient id="pdusk" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="190">{stops}</linearGradient></defs>'
             f'<rect width="390" height="196" fill="{PAPER}"/><path d="M0 -300 H390 V600 H0 Z {arc}" fill="url(#pdusk)" fill-rule="evenodd"/>'
             f'<circle cx="{pcx}" cy="{pcy}" r="{pr}" fill="none" stroke="{INK}" stroke-width=".8"/>{"".join(ticks)}</svg>')
    o.append('<div class="ph-wm tx">Cantina</div><div class="ph-venue tx">Cantina &amp; Cocktail Bar · Iowa City, Iowa</div>')
    o.append('<h2 class="tx"><span class="es">Cócteles</span> · Cocktails</h2>')
    o.append('<div class="note tx">Each drink is set at the hour it suits: a suggestion, not a schedule.</div>')
    o.append('<div class="ph-evening">')
    for h, names in HOURS:
        c0, c1 = field_at(YH[h] - 10), field_at(YH[h] + STEP - 10)
        num = field_at(YH[h] + 4)
        col = INK if cr(hex2rgb(num), hex2rgb(INK)) >= cr(hex2rgb(num), hex2rgb(PAPER)) else PAPER
        o.append(f'<div class="ph-hour"><div class="ph-rail" style="background:linear-gradient(in oklab,{c0},{c1})"><span class="hr tx" style="color:{col}">{HLABEL[h]}<span class="ap">{HSUF[h]}</span></span></div><div class="ph-items">')
        o.extend(cocktail(COCK[n]) for n in names)
        o.append('</div></div>')
    c0, c1 = field_at(YH[7] - 10), field_at(YH[9] + 20)
    num = field_at(YH[7] + 4); col = INK if cr(hex2rgb(num), hex2rgb(INK)) >= cr(hex2rgb(num), hex2rgb(PAPER)) else PAPER
    o.append(f'<div class="ph-hour"><div class="ph-rail" style="background:linear-gradient(in oklab,{c0},{c1})"><span class="hr tx" style="color:{col}">12<span class="ap">am</span></span></div><div class="ph-items">'
             '<h3 class="tx"><span class="es">Sin alcohol</span> · Zero proof</h3>' + "".join(simple(i, "zero") for i in ZERO) + '</div></div>')
    o.append('</div><div class="key tx"><i class="prop"></i> proposed — pending approval</div></section>')
    # the night
    o.append('<section class="ph-back"><h2 class="tx"><span class="es">Destilados</span> · Spirits</h2><div class="cap tx">Twenty-five pours, set by months in oak</div>')
    o.append('<div class="lg tx">Star size: Iowa accounts pouring the brand (PHG brand graph). + no data.</div>')
    rng = {0: "0 months", 2: "2–12 months", 12: "12–36 months", 48: "48+ months"}
    for es, en, m, names, c0, span in CLASSES:
        o.append(f'<div class="ph-class"><div class="ph-mo tx">{rng[m]}</div><h3 class="tx"><span class="es">{es}</span> {en}</h3>'
                 f'<div class="csd tx">{esc(SPIRITS[names[-1]]["sensory"])}</div>')
        for n in names:
            acc, htm = pour_row(n)
            if acc: st = f'<svg class="st" viewBox="-6 -6 12 12"><circle r="{star_r(acc) * 1.2:.2f}" fill="{GOLD}"/></svg>'
            elif n in ("Blanco Tequila", "Añejo Tequila", "Cognac VSOP"): st = f'<svg class="st" viewBox="-6 -6 12 12"><rect x="-2.4" y="-2.4" width="4.8" height="4.8" fill="none" stroke="{GOLD}" stroke-width=".8"/></svg>'
            else: st = f'<svg class="st" viewBox="-6 -6 12 12"><path d="M-3.5 0 h7 M0 -3.5 v7" stroke="{NIGHT_MUTED}" stroke-width=".8"/></svg>'
            o.append(f'<div class="ph-pour">{st}{htm}</div>')
        o.append('</div>')
    o.append('<h2 class="tx bwh"><span class="es">Cerveza, sidra y vino</span> · Beer, cider &amp; wine</h2>')
    for es, en, rows in [("De barril", "Draft", MAN["beer_cider"]["De barril · Draft"]), ("En lata", "Cans", MAN["beer_cider"]["En lata · Cans"]),
                         ("Sidra", "Cider", MAN["beer_cider"]["Sidra · Cider"]), ("Por copa", "By the glass", MAN["wine"]["Por copa · By the glass"]),
                         ("Espumosos", "Sparkling", MAN["wine"]["Espumosos · Sparkling"])]:
        o.append(f'<h3 class="tx"><span class="es">{es}</span> · {en}</h3>' + "".join(simple(i, "beer" if es in ("De barril", "En lata", "Sidra") else "wine") for i in rows))
    o.append('<div class="key tx"><i class="prop"></i> proposed — pending approval</div></section>')
    return "".join(o)

# ------------------------------------------------------------------ CSS
CSS = """
@font-face{font-family:'Newsreader';src:url('fonts/Newsreader.woff2') format('woff2');font-weight:200 800;font-style:normal;font-display:block}
@font-face{font-family:'Newsreader';src:url('fonts/Newsreader-i.woff2') format('woff2');font-weight:200 800;font-style:italic;font-display:block}
@font-face{font-family:'Instrument Sans';src:url('fonts/InstrumentSans.woff2') format('woff2');font-weight:400 700;font-stretch:75%% 100%%;font-style:normal;font-display:block}
*{margin:0;padding:0;box-sizing:border-box}
html{background:#8A8578}
body{font-family:'Newsreader',serif;font-variant-numeric:lining-nums tabular-nums;-webkit-print-color-adjust:exact;print-color-adjust:exact;color:%(INK)s}
.phone{display:none}
.page{position:relative;width:612pt;height:792pt;overflow:hidden;background:%(PAPER)s;margin:0 auto 24pt}
.page.back{background:#1B1C40;color:%(NIGHT_TXT)s}
.art{position:absolute;left:-9pt;top:-9pt;width:630pt;height:810pt}
.page>.tx,.page>.slot,.page>h2,.page>h3{position:absolute;white-space:nowrap}
.page>.slot{white-space:normal}
.wm{font-weight:330;font-size:60pt;line-height:64pt;letter-spacing:-.012em;font-variation-settings:'opsz' 72}
.venue{font:400 9pt/12pt 'Instrument Sans',sans-serif;letter-spacing:.01em;color:%(MUTED2)s}
h2{font-weight:500;font-size:14pt;line-height:18pt;font-variation-settings:'opsz' 24}
h2.small{font-size:12.5pt}
h2 .es,h3 .es{font-style:italic}
h3{font-weight:500;font-size:11pt;line-height:14pt;font-variation-settings:'opsz' 16}
.hr{font-weight:360;font-size:23pt;line-height:26pt;font-variation-settings:'opsz' 60;letter-spacing:-.01em}
.hr .ap{font:500 8.5pt/1 'Instrument Sans',sans-serif;letter-spacing:.04em;margin-left:2pt;vertical-align:.55em}
.slot{white-space:normal}
.item{position:relative;padding-left:17pt}
.item .gl{position:absolute;left:0;top:1pt;width:11.5pt;height:15.3pt}
.z .item,.bw .item,.pour{padding-left:0}
.row{font-size:11pt;line-height:13pt;white-space:nowrap}
.name{font-weight:560;font-variation-settings:'opsz' 14}
.price{font-weight:500;color:%(GOLD_D)s;margin-left:.42em;font-variation-settings:'opsz' 14}
.prop{display:inline-block;width:4.6pt;height:4.6pt;border:.6pt solid currentColor;border-radius:50%%;margin-left:4pt;vertical-align:.18em;opacity:.8}
.sd{font-style:italic;font-weight:400;font-size:9.5pt;line-height:11.5pt;color:%(MUTED)s;font-variation-settings:'opsz' 10}
.ing{font:400 8.75pt/11pt 'Instrument Sans',sans-serif;color:%(INK2)s;margin-top:.5pt}
.ing .sep{color:%(MUTED2)s}
.gg{white-space:nowrap;color:%(MUTED2)s;font-style:italic;margin-left:.7em}
.gg .sep{color:%(MUTED2)s}
.key{font:400 8.5pt/11pt 'Instrument Sans',sans-serif;color:%(MUTED2)s}
.key .prop{margin:0 2pt 0 0;vertical-align:.05em}
.note{font-style:italic;font-size:9pt;line-height:11pt;color:%(MUTED2)s}
.back h2{color:%(NIGHT_TXT)s}
.back h3{color:%(NIGHT_TXT)s}
.back h3 .es{font-weight:500}
.cap,.lg,.axl{font:400 8.5pt/11pt 'Instrument Sans',sans-serif;color:%(NIGHT_MUTED)s}
.axl{letter-spacing:.02em}
.mo{font:500 8.5pt/12pt 'Instrument Sans',sans-serif;color:%(GOLD)s;text-align:right}
.csd{font-style:italic;font-size:9pt;line-height:11pt;color:%(NIGHT_MUTED)s;font-variation-settings:'opsz' 10;white-space:nowrap}
.back .row{font-size:10pt;line-height:12pt}
.back .name{font-weight:500;color:%(NIGHT_TXT)s}
.back .price{color:%(GOLD)s}
.meta{font:400 8.5pt/9.5pt 'Instrument Sans',sans-serif;color:%(NIGHT_MUTED)s;white-space:nowrap}
.back .sd{color:%(NIGHT_MUTED)s;font-size:9pt;line-height:11pt}
.back .key{color:%(NIGHT_MUTED)s}
.bw .row{font-size:10.5pt;line-height:12.5pt}
.bw .sd{white-space:nowrap}
.pour .sd{font-size:8.75pt;line-height:11pt;white-space:nowrap}
@media print{html{background:none}.page{margin:0;page-break-after:always}}
@media screen and (max-width:600px){
 html{background:%(PAPER)s}
 .page{display:none}
 .phone{display:block;width:390px;overflow:hidden}
 .ph-front{background:%(PAPER)s;padding:0 0 40px;position:relative}
 .ph-hero{display:block;width:390px;height:196px}
 .ph-wm{position:absolute;left:22px;top:28px;font-weight:330;font-size:54px;line-height:60px;letter-spacing:-.012em;font-variation-settings:'opsz' 72}
 .ph-venue{position:absolute;left:24px;top:92px;font:400 13px/18px 'Instrument Sans',sans-serif;color:%(MUTED2)s;width:200px}
 .phone h2{font-size:22px;line-height:28px;margin:0 24px 4px}
 .phone .note{font-size:14px;line-height:20px;margin:0 24px 24px}
 .ph-evening{margin:0}
 .ph-hour{display:flex;align-items:stretch;margin:0 0 0 0}
 .ph-rail{flex:0 0 72px;position:relative;border-top:1px solid rgba(255,246,230,.75)}
 .ph-rail .hr{position:absolute;left:10px;top:8px;font-size:30px;line-height:32px}
 .ph-rail .hr .ap{font-size:12px}
 .ph-items{flex:1;padding:12px 22px 22px 18px}
 .phone .item{padding-left:24px;margin:0 0 18px}
 .phone .item .gl{width:16px;height:21px;top:3px}
 .phone .row{font-size:17px;line-height:24px;white-space:normal}
 .phone .sd{font-size:15px;line-height:21px}
 .phone .ing{font-size:14px;line-height:20px}
 .phone .prop{width:7px;height:7px;border-width:1px;margin-left:6px}
 .phone h3{font-size:16px;line-height:22px;margin:0 0 10px}
 .phone .z .item,.ph-front h3+.item{padding-left:0}
 .ph-items h3~.item{padding-left:0}
 .phone .key{font-size:13px;line-height:18px;margin:8px 24px 0}
 .ph-back{background:linear-gradient(#2B2B57,#1B1C40 45%%,#0D0F24);color:%(NIGHT_TXT)s;padding:40px 24px 48px}
 .ph-back h2{margin:0 0 4px;color:%(NIGHT_TXT)s}
 .ph-back .cap,.ph-back .lg{font-size:13px;line-height:18px;margin:0 0 6px}
 .ph-class{border-top:1px solid rgba(232,181,82,.55);margin:22px 0 0;padding:10px 0 0 0;position:relative}
 .ph-mo{font:500 13px/18px 'Instrument Sans',sans-serif;color:%(GOLD)s;margin:0 0 2px}
 .ph-back h3{color:%(NIGHT_TXT)s;margin:0 0 2px}
 .ph-back .csd{font-size:14px;line-height:20px;white-space:normal;margin:0 0 10px}
 .ph-pour{display:flex;align-items:flex-start;margin:0 0 8px}
 .ph-pour .st{flex:0 0 16px;width:16px;height:16px;margin:4px 8px 0 0}
 .ph-back .row{font-size:16px;line-height:22px}
 .ph-back .price{color:%(GOLD)s}
 .ph-back .name{color:%(NIGHT_TXT)s}
 .ph-back .meta{font-size:12px;line-height:16px}
 .ph-back .item{padding-left:0;margin:0}
 .ph-back .bwh{margin:36px 0 10px;border-top:1px solid rgba(232,181,82,.55);padding-top:14px}
 .ph-back h3{margin-top:14px}
 .ph-back .item[data-kind=beer],.ph-back .item[data-kind=wine]{margin:0 0 10px}
 .ph-back .sd{font-size:14px;line-height:20px;color:%(NIGHT_MUTED)s}
 .ph-back .key{margin:28px 0 0;color:%(NIGHT_MUTED)s}
}
""" % dict(INK=INK, PAPER=PAPER, MUTED=MUTED, MUTED2=MUTED2, INK2=INK2, GOLD_D=GOLD_D, NIGHT_TXT=NIGHT_TXT, NIGHT_MUTED=NIGHT_MUTED, GOLD=GOLD)

def page_html():
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Cantina · El Reloj</title><style>' + CSS + '</style></head><body>'
            f'<div class="page front">{front_html()}</div><div class="page back">{back_html()}</div>'
            f'<div class="phone">{phone_html()}</div></body></html>')

# ------------------------------------------------------------------ render + measure
MEASURE = r"""(sel) => {
 const pg = document.querySelector(sel), P = pg.getBoundingClientRect(), K = 0.75;   // css px -> pt
 const rects = el => { const r = document.createRange(); r.selectNodeContents(el); return [...r.getClientRects()].filter(a => a.width > .5 && a.height > .5); };
 const tx = [...pg.querySelectorAll('.tx')].filter(e => e.offsetParent !== null).map(e => ({cls: e.className, text: e.innerText.trim().replace(/\s+/g,' ').slice(0,60),
   color: getComputedStyle(e).color, size_pt: parseFloat(getComputedStyle(e).fontSize) * K,
   rects: rects(e).map(a => [(a.left - P.left) * K, (a.top - P.top) * K, a.width * K, a.height * K])}));
 const items = [...pg.querySelectorAll('.item')].map(it => { const n = it.querySelector('.name'), p = it.querySelector('.price');
   const nr = rects(n), pr = rects(p), ln = nr[nr.length - 1], lp = pr[0];
   return {name: n.innerText.trim(), price: p.innerText.trim(), kind: it.dataset.kind, status: it.dataset.status,
     ingredients: [...it.querySelectorAll('.ig')].map(e => e.innerText.trim()), garnish: (it.querySelector('.gar') || {}).innerText || null,
     glass: (it.querySelector('.gls') || {}).innerText || null, sensory: (it.querySelector('.sd') || {}).innerText || null,
     ring: !!it.querySelector('.prop'), gap_pt: (lp.left - ln.right) * K, em_pt: parseFloat(getComputedStyle(p).fontSize) * K,
     same_line: Math.abs(lp.top - ln.top) < 2 && Math.abs(lp.bottom - ln.bottom) < 2}; });
 return {w: P.width * K, h: P.height * K, tx, items, text: pg.innerText};
}"""
HIDE = "const st=document.createElement('style');st.textContent='.tx,.tx *{color:transparent!important}';st.id='hide';document.head.appendChild(st);"
SHOW = "document.getElementById('hide').remove();"

def rgb(s): v = s[s.index("(") + 1:s.index(")")].split(","); return tuple(int(float(x)) for x in v[:3])

def worst_contrast(full, art, tx, S, pad=2):
    from PIL import ImageChops
    diff = ImageChops.difference(full, art).convert("L").point(lambda v: 255 if v > 24 else 0)
    res = []
    for e in tx:
        tc = rgb(e["color"]); worst, wpx = 99.0, None
        for x, y, w, h in e["rects"]:
            bb = (max(0, int(x * S)), max(0, int(y * S)), min(full.size[0], int(math.ceil((x + w) * S))), min(full.size[1], int(math.ceil((y + h) * S))))
            if bb[2] <= bb[0] or bb[3] <= bb[1]: continue
            ib = diff.crop(bb).getbbox()
            if not ib: continue
            bb2 = (max(bb[0], bb[0] + ib[0] - pad), max(bb[1], bb[1] + ib[1] - pad), min(bb[2], bb[0] + ib[2] + pad), min(bb[3], bb[1] + ib[3] + pad))
            crop = art.crop(bb2)
            for n, c in crop.getcolors(crop.size[0] * crop.size[1] + 1):
                r = cr(tc, c)
                if r < worst: worst, wpx = r, c
        res.append({"text": e["text"], "cls": e["cls"], "size_pt": round(e["size_pt"], 2), "text_rgb": tc, "worst_bg": wpx, "worst_ratio": round(worst, 2)})
    return res

def render():
    from playwright.sync_api import sync_playwright
    from PIL import Image
    url = (HERE / "menu.html").as_uri(); res = {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME)
        pg = b.new_page(viewport={"width": 900, "height": 1100}, device_scale_factor=3.125)
        pg.goto(url, wait_until="load"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        res["fonts_loaded"] = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family+' '+f.style)")
        for side in ("front", "back"):
            res[side] = pg.evaluate(MEASURE, f".page.{side}")
            pg.locator(f".page.{side}").screenshot(path=str(HERE / f"preview-{side}.png"))
            pg.evaluate(HIDE); pg.locator(f".page.{side}").screenshot(path=str(HERE / f"_art-{side}.png")); pg.evaluate(SHOW)
        # print PDF with 3.175 mm (9 pt) bleed + crop marks, two sheets
        pg2 = b.new_page(viewport={"width": 900, "height": 1200})
        pg2.goto(url, wait_until="load"); pg2.evaluate("document.fonts.ready"); pg2.wait_for_timeout(300)
        pg2.evaluate("""() => { const s = document.createElement('style'); s.textContent = `
          @page{size:666pt 846pt;margin:0} html,body{background:#fff!important;margin:0}
          .sheet{position:relative;width:666pt;height:846pt;page-break-after:always;overflow:hidden}
          .sheet .page{position:absolute;left:27pt;top:27pt;margin:0;overflow:visible!important}
          .cm{position:absolute;background:#000}`; document.head.appendChild(s);
          for (const pgEl of [...document.querySelectorAll('.page')]) { const sh = document.createElement('div'); sh.className = 'sheet'; pgEl.parentNode.insertBefore(sh, pgEl); sh.appendChild(pgEl);
            const add = (l, t, w, h) => { const d = document.createElement('div'); d.className = 'cm'; Object.assign(d.style, {left: l + 'pt', top: t + 'pt', width: w + 'pt', height: h + 'pt'}); sh.appendChild(d); };
            for (const x of [27, 639]) { add(x - .25, 0, .5, 15); add(x - .25, 831, .5, 15); }
            for (const y of [27, 819]) { add(0, y - .25, 15, .5); add(651, y - .25, 15, .5); } } }""")
        pg2.pdf(path=str(HERE / "menu-print-bleed.pdf"), width="9.25in", height="11.75in", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        ph = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
        ph.goto(url, wait_until="load"); ph.evaluate("document.fonts.ready"); ph.wait_for_timeout(300)
        res["phone"] = ph.evaluate(MEASURE, ".phone")
        res["phone"]["scrollWidth"] = ph.evaluate("document.documentElement.scrollWidth")
        res["phone"]["min_font_px"] = ph.evaluate("Math.min(...[...document.querySelectorAll('.phone .tx, .phone .tx *')].filter(e=>e.offsetParent!==null && e.innerText.trim()).map(e=>parseFloat(getComputedStyle(e).fontSize)))")
        ph.screenshot(path=str(HERE / "preview-phone.png"), full_page=True)
        ph.evaluate(HIDE); ph.screenshot(path=str(HERE / "_art-phone.png"), full_page=True)
        b.close()
    S = 2550 / 612
    for side in ("front", "back"):
        full = Image.open(HERE / f"preview-{side}.png").convert("RGB"); art = Image.open(HERE / f"_art-{side}.png").convert("RGB")
        res[side]["png"] = list(full.size); res[side]["contrast"] = worst_contrast(full, art, res[side]["tx"], S)
    full = Image.open(HERE / "preview-phone.png").convert("RGB"); art = Image.open(HERE / "_art-phone.png").convert("RGB")
    # phone rects are relative to .phone, which starts at the document origin; px -> pt factor 0.75 was applied, undo: 1 pt = 4 device px at DSF 3
    res["phone"]["png"] = list(full.size); res["phone"]["contrast"] = worst_contrast(full, art, res["phone"]["tx"], 4.0)
    return res

def gates(res):
    G = {"manifest_sha256_16": hashlib.sha256(MAN_P.read_bytes()).hexdigest()[:16]}
    want = {}
    for i in COCK.values(): want[i["name"]] = ("cocktail", i)
    for i in ZERO: want[i["name"]] = ("zero", i)
    for i in SPIRITS.values(): want[i["name"]] = ("spirit", i)
    for rows in MAN["beer_cider"].values():
        for i in rows: want[i["name"]] = ("beer", i)
    for rows in MAN["wine"].values():
        for i in rows: want[i["name"]] = ("wine", i)
    for surf in ("letter", "phone"):
        items = (res["front"]["items"] + res["back"]["items"]) if surf == "letter" else res["phone"]["items"]
        errs = []; seen = {}
        for it in items:
            seen[it["name"]] = seen.get(it["name"], 0) + 1
            if it["name"] not in want: errs.append(("unknown name", it["name"])); continue
            k, m = want[it["name"]]
            if float(it["price"]) != float(m["price"]): errs.append(("price", it["name"], it["price"], m["price"]))
            if k == "cocktail":
                if it["ingredients"] != m["ingredients"]: errs.append(("ingredients", it["name"], it["ingredients"]))
                if (it["garnish"] or None) != m["garnish"]: errs.append(("garnish", it["name"]))
                if it["glass"] != m["glass"]: errs.append(("glass", it["name"]))
            if k in ("cocktail", "zero", "beer", "wine") and it["sensory"] != m["sensory"]: errs.append(("sensory", it["name"]))
            if it["ring"] != (m["status"] != "approved_db"): errs.append(("proposed mark", it["name"]))
        missing = [n for n in want if n not in seen]; dup = [n for n, c in seen.items() if c > 1]
        G[f"{surf}_dom_diff"] = {"items_found": len(items), "items_expected": len(want), "errors": errs, "missing": missing, "duplicates": dup,
                                 "pass": not errs and not missing and not dup}
        G[f"{surf}_price_pairs"] = {"max_gap_em": round(max(it["gap_pt"] / it["em_pt"] for it in items), 3), "all_same_line": all(it["same_line"] for it in items),
                                    "pass": all(it["same_line"] and it["gap_pt"] <= it["em_pt"] for it in items)}
    counts = {"cocktails": len(COCK), "spirits": len(SPIRITS), "beer_cider": sum(len(r) for r in MAN["beer_cider"].values()),
              "wine": sum(len(r) for r in MAN["wine"].values()), "zero_proof": len(ZERO)}
    G["content_counts"] = counts; G["content_counts_ok"] = counts == {"cocktails": 12, "spirits": 25, "beer_cider": 6, "wine": 3, "zero_proof": 4}
    # class-level spirit sensory: every distinct manifest spirit sensory string is printed
    txt = res["front"]["text"] + "\n" + res["back"]["text"]
    G["spirit_sensory_printed"] = sorted({i["sensory"] for i in SPIRITS.values() if i["sensory"] not in txt}) or "all"
    # contrast
    for surf, cs in (("front", res["front"]["contrast"]), ("back", res["back"]["contrast"]), ("phone", res["phone"]["contrast"])):
        w = min(cs, key=lambda c: c["worst_ratio"])
        G[f"contrast_{surf}"] = {"min": w["worst_ratio"], "at": w["text"], "below_4_5": [c for c in cs if c["worst_ratio"] < 4.5], "pass": w["worst_ratio"] >= 4.5}
    # legibility
    mins = {s: round(min(e["size_pt"] for e in res[s]["tx"]), 2) for s in ("front", "back")}
    G["legibility_letter_min_pt"] = mins; G["legibility_letter_pass"] = min(mins.values()) >= 8.5
    G["legibility_phone_min_px"] = res["phone"]["min_font_px"]; G["legibility_phone_pass"] = res["phone"]["min_font_px"] >= 12
    # safe area (0.5 in = 36 pt) on the text line boxes
    for s in ("front", "back"):
        R_ = [r for e in res[s]["tx"] for r in e["rects"]]
        box = {"min_x": round(min(r[0] for r in R_), 2), "min_y": round(min(r[1] for r in R_), 2), "max_x": round(max(r[0] + r[2] for r in R_), 2), "max_y": round(max(r[1] + r[3] for r in R_), 2)}
        G[f"safe_area_{s}"] = dict(box, pass_=box["min_x"] >= 36 - .01 and box["min_y"] >= 36 - .01 and box["max_x"] <= 576.01 and box["max_y"] <= 756.01)
    # banned lines / taglines
    BANNED = ["beauty lives here too", "sip at your own risk", "plants, people, pours", "plants · people · pours", "adventure tastes better together",
              "good drinks", "good people", "every round takes you further in", "stranger things grow", "a more beautiful drinking world", "curiosity grows here",
              "drink deeper", "fresh ideas", "higher vibes", "a higher state of drinking", "bold flavors", "brighter tomorrows", "brighter days"]
    alltxt = (txt + res["phone"]["text"]).lower()
    G["banned_lines_found"] = [w for w in BANNED if w in alltxt]; G["no_banned_lines"] = not G["banned_lines_found"]
    G["ingredient_role_order_ok"] = G["letter_dom_diff"]["pass"]  # printed lists equal the manifest's role-ordered lists
    G["garnish_separate_ok"] = all((COCK[n]["garnish"] or "") not in COCK[n]["ingredients"] for n in COCK)
    G["png"] = {"front": res["front"]["png"], "back": res["back"]["png"], "phone": res["phone"]["png"]}
    G["phone_no_hscroll"] = res["phone"]["scrollWidth"] <= 390
    G["fonts_loaded"] = res["fonts_loaded"]
    # overlap check: no two text line boxes intersect (letter)
    ov = []
    for s in ("front", "back"):
        R_ = [(e["text"][:24], r) for e in res[s]["tx"] for r in e["rects"]]
        for a in range(len(R_)):
            for b_ in range(a + 1, len(R_)):
                (ta, (x1, y1, w1, h1)), (tb, (x2, y2, w2, h2)) = R_[a], R_[b_]
                if x1 < x2 + w2 - .5 and x2 < x1 + w1 - .5 and y1 < y2 + h2 - 1.5 and y2 < y1 + h1 - 1.5 and ta != tb:
                    ov.append((s, ta, tb))
    G["text_overlaps"] = ov[:20]
    # text never enters the dusk field except the hour numerals (front)
    intr = []
    for e in res["front"]["tx"]:
        if e["cls"].startswith("hr"): continue
        for x, y, w, h in e["rects"]:
            for yy in (y, y + h):
                if x + w > arc_x(yy) - 6: intr.append((e["text"][:30], round(x + w - arc_x(yy), 1)))
    G["front_text_clear_of_rim"] = intr or "ok"
    G["hours_phg_inferred"] = {HLABEL[h] + (" pm" if h < 7 else " am"): ns for h, ns in HOURS}
    return G

if __name__ == "__main__":
    import sys
    (HERE / "menu.html").write_text(page_html())
    if "--html" in sys.argv: sys.exit()
    res = render()
    (HERE / "_measure.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    G = gates(res)
    (HERE / "gates.json").write_text(json.dumps(G, ensure_ascii=False, indent=1))
    short = {k: (v.get("pass", v.get("pass_")) if isinstance(v, dict) and ("pass" in v or "pass_" in v) else v) for k, v in G.items() if k not in ("fonts_loaded", "hours_phg_inferred")}
    print(json.dumps(short, ensure_ascii=False, indent=0))
    for k in ("contrast_front", "contrast_back", "contrast_phone"): print(k, G[k]["min"], G[k]["at"])
