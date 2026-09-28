#!/usr/bin/env python3
"""TEST-1 explore-D: Botanical field guide / apothecary.
Every item, price, description and component comes from ../build/draft_doc.json.
Glass / garnish / method come from phg.recipe_versions as cited in ../round-17/proposal.md.
Outputs: menu.html (proof), menu-guest.html, preview-letter.png, preview-phone.png,
preview-letter-guest.png, contrast.json.
"""
import json, os, html
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFT = json.load(open(HERE.parent / "build" / "draft_doc.json"))
FONTS = (HERE.parent / "build" / "fonts").as_uri()

IVORY, IVORY_D, SEPIA, SEPIA2, GREEN = "#F4EDDC", "#EADFC6", "#3A2716", "#5E4630", "#34502F"

# ---- recipe_versions facts (round-17 proposal citations) ---------------------------------
RV = {
    "beta_manhattan": dict(glass="Coupe", garnish="Cocktail cherry", method="Stirred", rv="9fb77eaa"),
    "beta_margarita": dict(glass="Rocks", garnish="Lime wheel", method="Shaken", rv="f06abb74"),
    "beta_daiquiri": dict(glass="Coupe", garnish="Lime coin", method="Shaken", rv="14d45e57"),
    "beta_old_fashioned": dict(glass="Rocks", garnish="Orange peel", ice="Large cube", method="Stirred", rv="7095fd3d"),
}
# Latin labels only where botanically true of the product (genus-level where species varies).
LATIN = {
    "Tequila Blanco": "Agave tequilana", "Agave Syrup": "Agave", "Rye Whiskey": "Secale cereale",
    "White Rum": "Saccharum", "Brown Butter-Washed Bourbon": "Zea mays",
    "beta_blanco_tequila": "Agave tequilana", "beta_anejo_tequila": "Agave tequilana",
    "beta_malbec": "Vitis vinifera", "beta_pinot_grigio": "Vitis vinifera", "beta_cognac_vsop": "Vitis vinifera",
    "beta_dry_hopped_ipa": "Humulus lupulus", "beta_dry_cider": "Malus",
}
MISSING = {"beer": ["Brewer", "ABV"], "cider": ["Producer", "ABV"], "wine": ["Producer", "Region", "ABV"],
           "spirits": ["Brand", "ABV", "Pour"]}

def items():
    out = []
    for s in DRAFT["sections"]:
        for sb in s["subs"]:
            for it in sb["items"]:
                out.append((s, sb, it))
        for it in s["items"]:
            out.append((s, None, it))
    return out

ALL = items()
assert len(ALL) == 14, len(ALL)
esc = html.escape
def price(it):
    v = it["prices"][0]["value"]; return str(int(v)) if float(v).is_integer() else f"{v:.2f}"
def qty(c):
    q = c["quantity"]; q = str(int(q)) if float(q).is_integer() else str(q).lstrip("0")
    u = c["unit"]; return q if u == "each" else f"{q} {u}"

# ---- engraved glass drawings (ART layer, SVG, no text) ----------------------------------
DEFS = f"""<defs>
<pattern id="h" width="3.2" height="3.2" patternUnits="userSpaceOnUse" patternTransform="rotate(40)"><line x1="0" y1="0" x2="0" y2="3.2" stroke="{SEPIA}" stroke-width=".55" opacity=".55"/></pattern>
<pattern id="hx" width="2.6" height="2.6" patternUnits="userSpaceOnUse" patternTransform="rotate(-50)"><line x1="0" y1="0" x2="0" y2="2.6" stroke="{SEPIA}" stroke-width=".5" opacity=".55"/></pattern>
<pattern id="hg" width="2.4" height="2.4" patternUnits="userSpaceOnUse" patternTransform="rotate(30)"><line x1="0" y1="0" x2="0" y2="2.4" stroke="{GREEN}" stroke-width=".6" opacity=".7"/></pattern>
</defs>"""
S = f'stroke="{SEPIA}" fill="none"'

def rocks(liq_y=100, garnish="", ice=""):
    g = [f'<path d="M10 70 L18 172 L92 172 L100 70" {S} stroke-width="1.3"/>',
         f'<ellipse cx="55" cy="70" rx="45" ry="7" {S} stroke-width="1.1"/>',
         f'<path d="M17 158 L93 158 L92 172 L18 172Z" fill="url(#hx)" {S} stroke-width=".8"/>',
         f'<clipPath id="rl{liq_y}{len(garnish)}"><path d="M12 {liq_y} L17 158 L93 158 L98 {liq_y}Z"/></clipPath>',
         f'<rect x="0" y="{liq_y}" width="110" height="60" fill="url(#h)" clip-path="url(#rl{liq_y}{len(garnish)})"/>',
         f'<ellipse cx="55" cy="{liq_y}" rx="43" ry="5.5" {S} stroke-width=".8"/>',
         f'<path d="M86 80 L90 150" stroke="{SEPIA}" stroke-width=".6" opacity=".6"/><path d="M22 84 L25 120" stroke="{IVORY}" stroke-width="2.2"/>',
         f'<path d="M93 76 L99 76 L93 156" fill="url(#hx)" stroke="none"/>']
    g.append(ice); g.append(garnish)
    return "".join(g)

def coupe(liq_y=70, garnish="", inner=""):
    bowl = "M8 58 C12 96 36 110 55 110 C74 110 98 96 102 58"
    g = [f'<path d="{bowl}" {S} stroke-width="1.3"/>',
         f'<ellipse cx="55" cy="58" rx="47" ry="7" {S} stroke-width="1.1"/>',
         f'<clipPath id="cl{len(garnish)}"><path d="M9 {liq_y} C14 96 36 109 55 109 C74 109 96 96 101 {liq_y}Z"/></clipPath>',
         f'<rect x="0" y="{liq_y}" width="110" height="45" fill="url(#h)" clip-path="url(#cl{len(garnish)})"/>',
         f'<ellipse cx="55" cy="{liq_y}" rx="45.5" ry="5" {S} stroke-width=".8"/>',
         inner,
         f'<path d="M51 110 C53 120 53 150 49 162 L61 162 C57 150 57 120 59 110" {S} stroke-width="1.1"/>',
         f'<path d="M57 114 L57 158" stroke="{SEPIA}" stroke-width=".5" opacity=".6"/>',
         f'<ellipse cx="55" cy="166" rx="30" ry="6" {S} stroke-width="1.1"/>',
         f'<path d="M25 166 C30 170 80 170 85 166 L85 168 C80 173 30 173 25 168Z" fill="url(#hx)"/>',
         f'<path d="M18 66 C22 86 34 98 44 102" stroke="{IVORY}" stroke-width="2"/>',
         garnish]
    return "".join(g)

def lime_wheel(cx, cy, r):
    segs = "".join(f'<line x1="{cx}" y1="{cy}" x2="{cx + r*0.82*__import__("math").cos(a*0.785398)}" y2="{cy + r*0.82*__import__("math").sin(a*0.785398)}" stroke="{GREEN}" stroke-width=".7"/>' for a in range(8))
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{IVORY}" stroke="{GREEN}" stroke-width="1.4"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r*0.84}" fill="url(#hg)" stroke="{GREEN}" stroke-width=".6"/>' + segs +
            f'<circle cx="{cx}" cy="{cy}" r="1.6" fill="{IVORY}" stroke="{GREEN}" stroke-width=".6"/>')

def cherry(cx, cy):
    return (f'<circle cx="{cx}" cy="{cy}" r="8" fill="url(#hx)" stroke="{SEPIA}" stroke-width="1.1"/>'
            f'<path d="M{cx-3} {cy-4} a3 3 0 0 1 4 -1" stroke="{IVORY}" stroke-width="1.6" fill="none"/>'
            f'<path d="M{cx+1} {cy-8} C{cx+3} {cy-20} {cx+12} {cy-28} {cx+18} {cy-32}" {S} stroke-width="1"/>')

def lime_coin(cx, cy):
    return (f'<ellipse cx="{cx}" cy="{cy}" rx="13" ry="4.5" fill="url(#hg)" stroke="{GREEN}" stroke-width="1.3"/>'
            f'<ellipse cx="{cx}" cy="{cy-0.6}" rx="9" ry="2.6" fill="none" stroke="{GREEN}" stroke-width=".5"/>')

def orange_peel():
    return (f'<path d="M26 72 C18 58 30 46 42 50 C52 53 50 40 60 36 L64 42 C56 46 58 58 46 58 C36 57 30 64 33 73Z" '
            f'fill="url(#hx)" stroke="{SEPIA}" stroke-width="1.1"/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r=".7" fill="{SEPIA}"/>' for x, y in [(30,60),(38,54),(46,55),(55,45),(34,66)]))

def cubes_small():
    return "".join(f'<rect x="{x}" y="{y}" width="20" height="18" rx="2" transform="rotate({r} {x+10} {y+9})" fill="{IVORY}" fill-opacity=".55" {S} stroke-width=".8"/>'
                   for x, y, r in [(22, 104, -8), (48, 112, 6), (66, 100, 14), (34, 128, 4), (60, 132, -10)])

def cube_large():
    return (f'<path d="M26 90 L78 86 L84 140 L30 146Z" fill="{IVORY}" fill-opacity=".6" {S} stroke-width="1"/>'
            f'<path d="M26 90 L36 80 L86 76 L78 86 M86 76 L92 128 L84 140" {S} stroke-width=".9"/>'
            f'<path d="M78 86 L86 76 L92 128 L84 140Z" fill="url(#hx)"/>')

DRAW = {
    "beta_margarita": (lambda: rocks(96, lime_wheel(90, 60, 16), cubes_small()), {"garnish": (84, 50)}),
    "beta_old_fashioned": (lambda: rocks(92, orange_peel(), cube_large()), {"garnish": (58, 40), "liq": (70, 150), "top": (90, 94)}),
    "beta_manhattan": (lambda: coupe(70, "", cherry(50, 90)), {"garnish": (56, 86)}),
    "beta_daiquiri": (lambda: coupe(68, lime_coin(74, 67)), {"garnish": (84, 66)}),
}

# ---- cocktail plates (TEXT layer in HTML; leaders in SVG) -----------------------------
ROMAN = ["I", "II", "III", "IV"]
LBL_X = 160  # label column start (px within plate body)

def plate(n, sec, sub, it):
    iid = it["id"]; rv = RV[iid]
    hidden = {k for k, v in it["meta"].get("public_components", {}).items() if v is False}
    comps = [c for c in it["components"] if c["name"].lower().replace(" ", "-") not in hidden]
    show_qty = it["meta"]["public_visibility"].get("house_recipe", True)
    garn = [c for c in comps if c["role"] == "Garnish"]
    meas = [c for c in comps if c["role"] != "Garnish"]
    body_h = 176
    art, anchors = DRAW[iid]
    svg = [f'<svg class="art" width="{LBL_X}" height="{body_h}" viewBox="0 0 {LBL_X} {body_h}">{DEFS}<g transform="translate(0,2)">{art()}</g>']
    labels = []
    # garnish label (top row). Garnish name: component if present, else recipe_versions.
    gname = garn[0]["name"] if garn else rv["garnish"]
    gsrc = "garnish" + ("" if garn else "")
    gy = 16
    ax, ay = anchors["garnish"]; ay += 2
    svg.append(f'<polyline points="{ax},{ay} {ax+8},{gy} {LBL_X-4},{gy}" fill="none" stroke="{GREEN}" stroke-width=".8"/>'
               f'<circle cx="{ax}" cy="{ay}" r="1.8" fill="{GREEN}"/>')
    gq = qty(garn[0]) + " · " if (garn and show_qty) else ""
    labels.append((gy, f'<b class="q">{esc(gq)}</b>{esc(gname)}', "garnish"))
    # measured components: graduated scale when quantities are public
    ys = [52 + i * ((body_h - 64) / max(1, len(meas) - 1) if len(meas) > 1 else 0) for i in range(len(meas))]
    order = list(reversed(meas))  # top of scale first
    if show_qty:
        SX, B, PPO = 118, 170, 29.0
        svg.append(f'<line x1="{SX}" y1="{B}" x2="{SX}" y2="{B-4*PPO}" stroke="{SEPIA}" stroke-width=".8"/>')
        for k in range(0, 9):
            y = B - k * PPO / 2
            svg.append(f'<line x1="{SX-(5 if k%2==0 else 3)}" y1="{y}" x2="{SX}" y2="{y}" stroke="{SEPIA}" stroke-width=".7"/>')
        cum = 0; mids = {}
        for c in meas:
            h = c["quantity"] * PPO if c["unit"] == "oz" else 0
            top = B - cum - h
            if h:
                fill = "url(#hg)" if c["role"] in ("Citrus",) else ("url(#hx)" if cum == 0 else "url(#h)")
                svg.append(f'<rect x="{SX+1}" y="{top:.1f}" width="9" height="{h:.1f}" fill="{fill}" stroke="{SEPIA}" stroke-width=".7"/>')
            mids[c["name"]] = (SX + 10, top + h / 2 if h else top)
            cum += h
        for i, c in enumerate(order):
            mx, my = mids[c["name"]]
            ly = ys[i]
            svg.append(f'<polyline points="{mx},{my:.1f} {mx+10},{my:.1f} {LBL_X-12},{ly:.1f} {LBL_X-4},{ly:.1f}" fill="none" stroke="{SEPIA}" stroke-width=".7"/>'
                       f'<circle cx="{mx}" cy="{my:.1f}" r="1.5" fill="{SEPIA}"/>')
    else:
        pts = [anchors["top"], (60, 118), anchors["liq"]]
        for i, c in enumerate(order):
            px, py = pts[i % 3]; py += 2
            ly = ys[i]
            svg.append(f'<polyline points="{px},{py} {px+14},{py} {LBL_X-12},{ly:.1f} {LBL_X-4},{ly:.1f}" fill="none" stroke="{SEPIA}" stroke-width=".7"/>'
                       f'<circle cx="{px}" cy="{py}" r="1.6" fill="{SEPIA}"/>')
    for i, c in enumerate(order):
        role = c["role"].lower()
        lat = LATIN.get(c["name"])
        note = " · 1:1 by weight" if c.get("notes", "").startswith("House 1:1 demerara") else ""
        sub2 = esc(role) + esc(note) + (f' · <i>{esc(lat)}</i>' if lat else "")
        q = f'<b class="q">{esc(qty(c))}</b> ' if show_qty else ""
        labels.append((ys[i], f'{q}{esc(c["name"])}<span class="role">{sub2}</span>', "meas"))
    svg.append("</svg>")
    lab_html = "".join(f'<div class="lab {cls}" style="top:{y+2:.1f}px">{t}</div>' for y, t, cls in labels)
    gl = f'<span class="role">garnish · per recipe</span>'
    cols = [("Glass", rv["glass"]), ("Garnish", rv["garnish"])]
    if "ice" in rv: cols.append(("Ice", rv["ice"]))
    cols.append(("Method", rv["method"]))
    table = "<table class='dt'><tr>" + "".join(f"<th>{k}</th>" for k, _ in cols) + "</tr><tr>" + "".join(f"<td>{esc(v)}</td>" for _, v in cols) + "</tr></table>"
    note = ""
    if iid == "beta_margarita":
        note = '<div class="fn">Field note: bright and citrus-forward.</div>'
    serve = f'<div class="fn">Serve: {esc(it["meta"]["serve_format"].lower())}.</div>'
    return f"""<section class="plate" data-item="{iid}">
  <div class="ph"><span class="pno">Plate {ROMAN[n]} · No. {n+1:02d}</span><span class="psub">{esc(sub['name'])}</span></div>
  <div class="row"><span class="nm">{esc(it['name'])}</span><span class="ld"></span><span class="pr">{price(it)}</span></div>
  <div class="body">{''.join(svg)}{lab_html}</div>
  {table}{note}{serve}
</section>"""

def register_entry(no, sec, it, proof):
    lat = LATIN.get(it["id"])
    key = sec["name"].lower()
    fields = ""
    if proof:
        fields = '<div class="miss">' + "".join(f'<span><em>{f}</em><u>—</u></span>' for f in MISSING[key]) + "</div>"
    return f"""<div class="re" data-item="{it['id']}">
  <div class="row"><span class="no">{no:02d}</span><span class="nm2">{esc(it['name'])}</span><span class="ld"></span><span class="pr2">{price(it)}</span></div>
  <div class="ds">{esc(it['desc'])}{f' <i class="lat">{esc(lat)}</i>' if lat else ''}</div>{fields}
</div>"""

def build(proof=True):
    cock = [(s, sb, it) for s, sb, it in ALL if s["id"] == "sec_cocktails"]
    rest = [(s, sb, it) for s, sb, it in ALL if s["id"] != "sec_cocktails"]
    plates = "".join(plate(i, s, sb, it) for i, (s, sb, it) in enumerate(cock))
    # register columns: Beer + Cider | Wine | Spirits
    colmap = {"sec_beer": 0, "sec_cider": 0, "sec_wine": 1, "sec_spirits": 2}
    cols = [[], [], []]; no = 5; last = [None, None, None]; lastsub = [None, None, None]
    for s, sb, it in rest:
        c = colmap[s["id"]]
        if last[c] != s["id"]:
            cols[c].append(f'<h3>{esc(s["name"])}</h3>'); last[c] = s["id"]
        if sb and lastsub[c] != sb["id"] and s["id"] in ("sec_wine", "sec_spirits"):
            cols[c].append(f'<h4>{esc(sb["name"])}</h4>'); lastsub[c] = sb["id"]
        cols[c].append(register_entry(no, s, it, proof)); no += 1
    reg = "".join(f'<div class="rc">{"".join(c)}</div>' for c in cols)
    proofbar = ('<div class="proofnote">PROOF · ruled fields marked “—” are facts not yet supplied (ABV, producer, region, brand, pour); they print only on this proof.</div>' if proof else "")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Fr;font-weight:600;src:url({FONTS}/Fraunces-600-normal.ttf)}}
@font-face{{font-family:Fr;font-weight:700;src:url({FONTS}/Fraunces-700-normal.ttf)}}
@font-face{{font-family:Fr;font-weight:600;font-style:italic;src:url({FONTS}/Fraunces-600-italic.ttf)}}
@font-face{{font-family:Dm;font-weight:400;src:url({FONTS}/DMSans-400-normal.ttf)}}
@font-face{{font-family:Dm;font-weight:500;src:url({FONTS}/DMSans-500-normal.ttf)}}
@font-face{{font-family:Dm;font-weight:700;src:url({FONTS}/DMSans-700-normal.ttf)}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{IVORY}}}
.page{{width:816px;height:1056px;position:relative;overflow:hidden;color:{SEPIA};font-family:Fr;
 background:radial-gradient(ellipse at 50% 45%, {IVORY} 60%, {IVORY_D} 100%);padding:48px 52px}}
.page:before{{content:"";position:absolute;inset:0;pointer-events:none;opacity:.06;
 background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/><feColorMatrix values='0 0 0 0 .35 0 0 0 0 .25 0 0 0 0 .12 0 0 0 1 0'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>")}}
.frame{{position:absolute;inset:40px;border:1px solid {SEPIA};pointer-events:none}}
.frame:after{{content:"";position:absolute;inset:3px;border:.5px solid {SEPIA2}}}
header{{position:relative;display:grid;grid-template-columns:1fr auto;align-items:end;border-bottom:1.5px solid {SEPIA};padding:8px 6px 8px}}
.kick{{font-family:Dm;font-weight:700;font-size:10px;letter-spacing:.32em;color:{GREEN};text-transform:uppercase}}
h1{{font-weight:700;font-size:46px;letter-spacing:.34em;line-height:1.05;text-transform:uppercase;margin-top:4px}}
.sub{{font-style:italic;font-size:13px;color:{SEPIA2};margin-top:2px}}
.key{{font-family:Dm;font-size:9.5px;line-height:1.45;color:{SEPIA2};text-align:right;border-left:1px solid {SEPIA2};padding-left:12px}}
.key b{{color:{SEPIA};letter-spacing:.2em;font-weight:700}}
.sect{{display:flex;align-items:center;gap:10px;margin:10px 6px 6px;font-family:Dm;font-weight:700;font-size:10.5px;letter-spacing:.3em;text-transform:uppercase}}
.sect:after,.sect:before{{content:"";flex:1;height:0;border-top:.8px solid {SEPIA}}}
.sect:before{{flex:0 0 18px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px 14px;padding:0 6px}}
.plate{{border:1px solid {SEPIA};outline:.5px solid {SEPIA2};outline-offset:-4px;padding:9px 14px 8px;background:rgba(244,237,220,.9)}}
.ph{{display:flex;justify-content:space-between;font-family:Dm;font-weight:700;font-size:9px;letter-spacing:.24em;text-transform:uppercase;color:{GREEN}}}
.row{{display:flex;align-items:baseline;gap:6px}}
.nm{{font-weight:700;font-size:16.5px;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap}}
.ld{{flex:1;border-bottom:1.2px dotted {SEPIA2};transform:translateY(-4px);min-width:14px}}
.pr{{font-weight:700;font-size:19px}}
.body{{position:relative;height:178px;margin-top:2px}}
.art{{position:absolute;left:0;top:0}}
.lab{{position:absolute;left:{LBL_X}px;right:0;transform:translateY(-50%);font-size:12.5px;line-height:1.12}}
.lab.garnish{{color:{GREEN}}}
.q{{font-family:Dm;font-weight:700;font-size:11px;letter-spacing:.03em}}
.role{{display:block;font-family:Dm;font-size:9.5px;color:{SEPIA2};letter-spacing:.02em}}
.role i{{font-family:Fr;font-style:italic;font-size:10.5px;color:{GREEN}}}
.dt{{width:100%;border-collapse:collapse;margin-top:4px;font-family:Dm}}
.dt th{{font-size:8px;letter-spacing:.2em;text-transform:uppercase;font-weight:700;color:{SEPIA2};text-align:left;border-top:.8px solid {SEPIA};border-bottom:.5px solid {SEPIA2};padding:2px 4px 1px}}
.dt td{{font-size:11px;padding:2px 4px;border-bottom:.8px solid {SEPIA}}}
.dt th+th,.dt td+td{{border-left:.5px solid {SEPIA2}}}
.fn{{font-style:italic;font-size:11px;color:{SEPIA2};margin-top:3px}}
.reg{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0 16px;padding:0 6px}}
.rc+.rc{{border-left:.5px solid {SEPIA2};padding-left:14px}}
h3{{font-family:Dm;font-weight:700;font-size:10px;letter-spacing:.3em;text-transform:uppercase;color:{GREEN};border-bottom:.8px solid {SEPIA};padding-bottom:2px;margin:2px 0 4px}}
h4{{font-family:Dm;font-weight:500;font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:{SEPIA2};margin:4px 0 1px}}
.re{{margin-bottom:5px}}
.no{{font-family:Dm;font-weight:700;font-size:9px;color:{GREEN};width:16px}}
.nm2{{font-weight:700;font-size:13.5px;letter-spacing:.12em;text-transform:uppercase;white-space:nowrap}}
.pr2{{font-weight:700;font-size:15px}}
.ds{{font-style:italic;font-size:12px;padding-left:22px;color:{SEPIA}}}
.lat{{color:{GREEN};font-size:11px}}
.miss{{display:flex;gap:8px;padding-left:22px;margin-top:1px;font-family:Dm;font-size:8.5px;color:{SEPIA2}}}
.miss span{{display:flex;gap:3px;align-items:baseline}}
.miss em{{font-style:normal;letter-spacing:.14em;text-transform:uppercase}}
.miss u{{text-decoration:none;border-bottom:.6px solid {SEPIA2};min-width:26px;text-align:center}}
footer{{position:absolute;left:58px;right:58px;bottom:50px;display:flex;justify-content:space-between;font-family:Dm;font-size:9px;letter-spacing:.24em;text-transform:uppercase;color:{SEPIA2};border-top:.8px solid {SEPIA};padding-top:4px}}
.proofnote{{position:absolute;left:58px;right:58px;bottom:66px;font-family:Dm;font-size:8.5px;color:{SEPIA2};text-align:center}}
/* phone */
body.phone .page{{width:390px;height:auto;padding:22px 16px 60px}}
body.phone .frame{{inset:10px}}
body.phone header{{grid-template-columns:1fr}}
body.phone .key{{text-align:left;border-left:0;padding:6px 0 0;border-top:.5px solid {SEPIA2};margin-top:6px}}
body.phone h1{{font-size:34px;letter-spacing:.22em}}
body.phone .grid,body.phone .reg{{grid-template-columns:1fr}}
body.phone .rc+.rc{{border-left:0;padding-left:0;margin-top:6px}}
body.phone .nm{{font-size:15px}}
body.phone .lab{{font-size:12px}}
body.phone footer,body.phone .proofnote{{position:static;margin:10px 4px 0}}
body.phone footer{{flex-direction:column;gap:3px}}
</style></head><body class="{{BODYCLASS}}"><div class="page"><div class="frame"></div>
<header><div><div class="kick">Cantina &amp; Cocktail Bar · Iowa City</div><h1>{esc(DRAFT['title'])}</h1>
<div class="sub">A field guide: four cocktail plates, then the register of pours.</div></div>
<div class="key"><b>KEY</b><br>scale · 1 tick = ½ oz, measures per house spec<br>green leader · garnish<br>No. · specimen number</div></header>
<div class="sect">{esc(DRAFT['sections'][0]['name'])} · Plates I–IV</div>
<div class="grid">{plates}</div>
<div class="sect">The register · No. 05–14</div>
<div class="reg">{reg}</div>
{proofbar}
<footer><span>Good drinks · good company</span><span>{esc(DRAFT.get('subtitle',''))}</span></footer>
</div></body></html>"""

CONTRAST_JS = """() => {
  const out=[]; const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  let n; while(n=walker.nextNode()){ if(!n.textContent.trim()) continue; const el=n.parentElement;
    const r=document.createRange(); r.selectNodeContents(n); for(const b of r.getClientRects()){
      if(b.width<1) continue; out.push({t:n.textContent.trim().slice(0,40),c:getComputedStyle(el).color,
      role:el.className||el.tagName,x:b.x,y:b.y,w:b.width,h:b.height});}}
  return out;}"""

def lum(c):
    def ch(v):
        v /= 255; return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])

def contrast_check(page, scale, tag):
    from PIL import Image
    import io, re
    boxes = page.evaluate(CONTRAST_JS)
    page.add_style_tag(content="*{color:transparent !important;text-decoration-color:transparent!important} .ld{border-color:transparent!important}")
    img = Image.open(io.BytesIO(page.screenshot(full_page=True))).convert("RGB")
    res = []
    for b in boxes:
        rgb = tuple(int(float(v)) for v in re.findall(r"[\d.]+", b["c"])[:3])
        L1 = lum(rgb)
        x0, y0 = max(0, int((b["x"] - 2) * scale)), max(0, int((b["y"] - 2) * scale))
        x1, y1 = min(img.width, int((b["x"] + b["w"] + 2) * scale)), min(img.height, int((b["y"] + b["h"] + 2) * scale))
        crop = img.crop((x0, y0, x1, y1)).resize((max(1, (x1 - x0) // 2), max(1, (y1 - y0) // 2)), Image.NEAREST)
        worst = 99
        for px in set(crop.getdata()):
            L2 = lum(px); cr = (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05); worst = min(worst, cr)
        res.append({"text": b["t"], "role": b["role"], "min": round(worst, 2)})
    res.sort(key=lambda r: r["min"])
    return res

def main():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    proof = build(True); guest = build(False)
    (HERE / "menu.html").write_text(proof.replace("{BODYCLASS}", "letter"))
    (HERE / "menu-guest.html").write_text(guest.replace("{BODYCLASS}", "letter"))
    report = {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=next(__import__("glob").iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")))
        for name, doc, cls, w, h, dsf in [("preview-letter.png", proof, "letter", 816, 1056, 3.125),
                                          ("preview-letter-guest.png", guest, "letter", 816, 1056, 3.125),
                                          ("preview-phone.png", proof, "phone", 390, 800, 3)]:
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            pg.set_content(doc.replace("{BODYCLASS}", cls)); pg.wait_for_timeout(400)
            ov = pg.evaluate("() => { const p=document.querySelector('.page'); const r=[];"
                             "document.querySelectorAll('.plate,.reg,header,footer,.proofnote').forEach(e=>{const b=e.getBoundingClientRect(); r.push([e.className||e.tagName,b.top,b.bottom,b.left,b.right])}); return {h:p.scrollHeight, r} }")
            report[name + ":geometry"] = ov
            pg.screenshot(path=str(HERE / name), full_page=(cls == "phone"))
            report[name] = contrast_check(pg, dsf, name)[:6]
            pg.close()
        b.close()
    (HERE / "contrast.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    for k, v in report.items():
        print(k, v if "geometry" in k else v[:3])

if __name__ == "__main__":
    main()
