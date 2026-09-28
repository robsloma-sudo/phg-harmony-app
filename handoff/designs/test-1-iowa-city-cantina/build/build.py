"""TEST-1 round 2: build doc.json + menu.html from the verbatim draft doc.
Grid: every slot height and every gap is a multiple of 12pt. Baseline shifts per text class come from shifts.json
(written by render.py after a measuring pass) so that every baseline lands on the same 12pt grid line phase."""
import json, copy, html, pathlib, base64, math

HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path("/home/user/phg-harmony-app/handoff/designs/test-1-iowa-city-cantina")
draft = json.loads((HERE / "draft_doc.json").read_text())
shifts = json.loads((HERE / "shifts.json").read_text()) if (HERE / "shifts.json").exists() else {}

# ---------------------------------------------------------------- copy (every word traced in proposal.md)
DESC = {
    "beta_margarita": "Blanco tequila, fresh lime, orange liqueur, agave syrup; lime wheel. Shaken, served on the rocks over fresh ice.",
    "beta_manhattan": "Rye whiskey, sweet vermouth; cocktail cherry. Stirred, served up in a coupe.",
    "beta_old_fashioned": "Brown butter-washed bourbon, demerara syrup, aromatic bitters; orange peel. Stirred, served over a large cube.",
    "beta_daiquiri": "White rum, fresh lime, house demerara syrup; lime coin. Shaken, served up in a coupe.",
    "beta_blanco_tequila": "Blue agave. D.O. Tequila.",
    "beta_anejo_tequila": "Blue agave, aged at least one year in oak. D.O. Tequila.",
    "beta_cognac_vsop": "Grape brandy, aged at least four years in oak.",
    "beta_czech_pilsner": "Crisp pale lager.",
    "beta_dry_hopped_ipa": "Hop-forward India pale ale.",
    "beta_amber_lager": "Toasty amber lager.",
    "beta_dry_cider": "Sparkling.",
    "beta_malbec": "Dry red wine.",
    "beta_pinot_grigio": "Dry white wine.",
    "beta_brut_rose": "Dry and sparkling.",
}
MISSING = {
    "beta_margarita": [], "beta_manhattan": [], "beta_old_fashioned": ["allergen confirmation (brown butter: dairy)"], "beta_daiquiri": [],
    "beta_blanco_tequila": ["brand", "pour size", "100% agave confirmation"], "beta_anejo_tequila": ["brand", "pour size", "100% agave confirmation"],
    "beta_cognac_vsop": ["brand", "pour size"],
    "beta_czech_pilsner": ["brewery", "ABV", "pour size"], "beta_dry_hopped_ipa": ["brewery", "ABV", "pour size"], "beta_amber_lager": ["brewery", "ABV", "pour size"],
    "beta_dry_cider": ["producer", "fruit", "ABV", "format (draft or can)"],
    "beta_malbec": ["producer", "region or country", "vintage"], "beta_pinot_grigio": ["producer", "region or country", "vintage"],
    "beta_brut_rose": ["producer", "grapes", "region", "glass or bottle price (label empty)"],
}
KICKER = {"sec_cocktails": "Cócteles", "sec_spirits": "Destilados", "sec_beer": "Cerveza", "sec_wine": "Vino"}

secs = {s["id"]: s for s in draft["sections"]}
doc = copy.deepcopy(draft)
doc["title"] = "Cantina & Cocktail Bar"
doc["subtitle"] = "Iowa City, Iowa"
new_secs = [copy.deepcopy(secs[k]) for k in ["sec_cocktails", "sec_spirits", "sec_beer", "sec_wine"]]
new_secs[2]["subs"].append({"id": "sub_beer_cider", "name": "Cider", "items": [copy.deepcopy(i) for i in secs["sec_cider"]["items"]]})
cl = new_secs[0]["subs"][0]; cl["items"] = [next(i for i in cl["items"] if i["id"] == x) for x in ["beta_margarita", "beta_manhattan"]]
ho = new_secs[0]["subs"][1]; ho["items"] = [next(i for i in ho["items"] if i["id"] == x) for x in ["beta_old_fashioned", "beta_daiquiri"]]
for s in new_secs:
    for it in s["items"] + [i for sb in s["subs"] for i in sb["items"]]:
        it["desc"] = DESC[it["id"]]; it["missing_ingredients"] = MISSING[it["id"]]
doc["sections"] = new_secs

def flat(d):
    return {i["id"]: (i["name"], json.dumps(i["prices"], sort_keys=True), json.dumps(i.get("phg"), sort_keys=True),
                      json.dumps(i.get("meta"), sort_keys=True), json.dumps(i.get("components"), sort_keys=True))
            for s in d["sections"] for i in s["items"] + [x for sb in s["subs"] for x in sb["items"]]}
assert flat(doc) == flat(draft) and len(flat(doc)) == 14, "item/price/meta drift"
(OUT / "doc.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2))

# ---------------------------------------------------------------- palette
P = dict(cream="#F6EEDF", ink="#231B16", terra="#A63C1A", flag_terra="#A63C1A", agave="#2F5D50", mari="#E3A018", muted="#5A4A3F")

# ---------------------------------------------------------------- bespoke papel picado (9 flags, 9 different cut-outs)
def agave_cut(cx, cy, r, cr):
    """agave rosette seen side-on: 7 pointed leaves, cut out of the flag"""
    out = ""
    for j, (ang, ln) in enumerate(zip((-70, -45, -22, 0, 22, 45, 70), (0.7, 0.85, 0.95, 1.0, 0.95, 0.85, 0.7))):
        t = math.radians(ang); L = r * ln
        tx, ty = cx + L * math.sin(t), cy - L * math.cos(t)
        nx, ny = math.cos(t) * r * 0.16, math.sin(t) * r * 0.16
        out += f'<path d="M{cx-nx:.2f} {cy-ny:.2f} Q{(cx+tx)/2-nx*0.7:.2f} {(cy+ty)/2-ny*0.7:.2f} {tx:.2f} {ty:.2f} Q{(cx+tx)/2+nx*0.7:.2f} {(cy+ty)/2+ny*0.7:.2f} {cx+nx:.2f} {cy+ny:.2f} Z" fill="{cr}"/>'
    return out

def rosette_cut(cx, cy, r, c, cr):
    """agave seen from above: 8 leaves radiating, with a solid heart (pina) left in paper"""
    out = f'<circle cx="{cx}" cy="{cy}" r="{r:.2f}" fill="{cr}"/>'
    for j in range(8):
        t = j * math.pi / 4
        out += (f'<path d="M{cx:.2f} {cy:.2f} L{cx+r*0.92*math.cos(t-0.2):.2f} {cy+r*0.92*math.sin(t-0.2):.2f} '
                f'L{cx+r*0.55*math.cos(t+0.39):.2f} {cy+r*0.55*math.sin(t+0.39):.2f} Z" fill="{c}"/>')
    return out + f'<circle cx="{cx}" cy="{cy}" r="{r*0.3:.2f}" fill="{c}"/><circle cx="{cx}" cy="{cy}" r="{r*0.12:.2f}" fill="{cr}"/>'

def dia(cx, cy, w, h, f):
    return f'<path d="M{cx:.2f} {cy-h:.2f} L{cx+w:.2f} {cy:.2f} L{cx:.2f} {cy+h:.2f} L{cx-w:.2f} {cy:.2f} Z" fill="{f}"/>'

def flag(x, fw, top, hem, c, cr, k):
    """one cut-paper flag: scalloped hem, lace border of diamond cuts, agave-derived centre motif"""
    n = 6; sw = fw / n
    d = f"M{x:.2f} {top} L{x+fw:.2f} {top} L{x+fw:.2f} {hem}"
    for j in range(n):
        x1 = x + fw - (j + 1) * sw
        d += f" A{sw/2:.2f} {sw/2*0.9:.2f} 0 0 1 {x1:.2f} {hem}"
    out = f'<path d="{d} Z" fill="{c}"/>'
    # lace: top row of small diamonds, row of pierced dots above hem, dot in each scallop
    out += "".join(dia(x + sw / 2 + j * sw, top + 5.2, 1.6, 2.2, cr) for j in range(n))
    out += f'<rect x="{x+3:.2f}" y="{top+8.6:.2f}" width="{fw-6:.2f}" height="0.6" fill="{cr}"/>'
    out += f'<rect x="{x+3:.2f}" y="{hem-5.4:.2f}" width="{fw-6:.2f}" height="0.6" fill="{cr}"/>'
    out += "".join(f'<circle cx="{x + sw/2 + j*sw:.2f}" cy="{hem+1.4:.2f}" r="1.1" fill="{cr}"/>' for j in range(n))
    cx = x + fw / 2; cy = (top + 9 + hem - 5.4) / 2
    r = min(fw * 0.3, (hem - top) * 0.3)
    if k % 3 == 0:
        out += agave_cut(cx, cy + r * 0.55, r * 1.25, cr) + dia(cx - r * 1.35, cy, 1.8, 2.8, cr) + dia(cx + r * 1.35, cy, 1.8, 2.8, cr)
    elif k % 3 == 1:
        out += rosette_cut(cx, cy, r * 0.95, c, cr)
    else:  # diamond lattice (agave-leaf points) with small agave inside
        out += dia(cx, cy, r * 1.05, r * 1.05, cr) + dia(cx, cy, r * 0.8, r * 0.8, c) + agave_cut(cx, cy + r * 0.4, r * 0.62, cr)
        out += dia(cx - r * 1.5, cy, 2, 3, cr) + dia(cx + r * 1.5, cy, 2, 3, cr)
    return out

def papel_picado(n=9, cls="banner", W=540, H=48, dims='width="540pt" height="48pt"'):
    cell = W / n; fw = cell - (8 if n > 6 else 10)
    cols = [P["flag_terra"], P["mari"], P["agave"]]
    out = [f'<svg class="{cls}" viewBox="0 0 {W} {H}" {dims} xmlns="http://www.w3.org/2000/svg" aria-hidden="true">',
           f'<path d="M1 0.4 Q{W/2} 4.4 {W-1} 0.4" stroke="{P["ink"]}" stroke-width="0.8" fill="none"/>']
    for k in range(n):
        x = k * cell + (cell - fw) / 2
        out.append(flag(x, fw, 3.4, H - 5, cols[k % 3], P["cream"], k))
    out.append("</svg>")
    return "".join(out)

def title_rule():
    W = 540; cx = W / 2
    g = [f'<svg class="mastrule" viewBox="0 0 {W} 12" width="540pt" height="12pt" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">',
         f'<rect x="0" y="5.75" width="{cx-30}" height="0.5" fill="{P["ink"]}"/><rect x="{cx+30}" y="5.75" width="{cx-30}" height="0.5" fill="{P["ink"]}"/>',
         dia(cx - 22, 6, 2.2, 2.2, P["mari"]), dia(cx + 22, 6, 2.2, 2.2, P["mari"]), dia(cx - 14, 6, 1.4, 1.4, P["terra"]), dia(cx + 14, 6, 1.4, 1.4, P["terra"])]
    g.append(f'<g fill="{P["agave"]}"><path d="M{cx} 12 L{cx-1.2} 1.5 L{cx} 0 L{cx+1.2} 1.5 Z"/><path d="M{cx-0.6} 12 L{cx-5} 3.5 L{cx-5.4} 1.6 L{cx-3.4} 3.6 Z"/>'
             f'<path d="M{cx+0.6} 12 L{cx+5} 3.5 L{cx+5.4} 1.6 L{cx+3.4} 3.6 Z"/><path d="M{cx-1} 12 L{cx-8.4} 7.4 L{cx-9.6} 6 L{cx-6.8} 6.8 Z"/>'
             f'<path d="M{cx+1} 12 L{cx+8.4} 7.4 L{cx+9.6} 6 L{cx+6.8} 6.8 Z"/></g></svg>')
    return "".join(g)

AGAVE = (f'<svg class="agave" viewBox="0 0 40 24" width="40pt" height="24pt" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
         f'<g fill="{P["agave"]}"><path d="M20 24 L18 4 L20 0 L22 4 Z"/><path d="M19 24 L10 7 L9 2 L13 6 Z"/><path d="M21 24 L30 7 L31 2 L27 6 Z"/>'
         f'<path d="M18 24 L4 14 L0 11 L6 12 Z"/><path d="M22 24 L36 14 L40 11 L34 12 Z"/></g></svg>')
DIAMOND = f'<svg class="dia" viewBox="0 0 8 8" width="5pt" height="5pt" aria-hidden="true"><path d="M4 0 L8 4 L4 8 L0 4 Z" fill="{P["mari"]}"/></svg>'

def nb(t):
    t = html.escape(t).replace("D.O. Tequila", "D.O.&nbsp;Tequila")
    i = t.rfind(" ")
    return t[:i] + "&nbsp;" + t[i+1:] if i > 0 else t

def item_html(it):
    return (f'<div class="item" data-ref="{it["id"]}"><div class="row"><span class="name">{html.escape(it["name"])}</span>'
            f'<span class="price">{it["prices"][0]["value"]:g}</span></div><p class="desc">{nb(it["desc"])}</p></div>')

def sec_html(s):
    h = [f'<section class="sec" data-id="{s["id"]}"><div class="hrow"><h2>{html.escape(s["name"])}</h2>'
         f'<div class="kicker">{DIAMOND}<span>{KICKER[s["id"]]}</span></div></div>']
    if s["items"]:
        h.append('<div class="items">' + "".join(item_html(i) for i in s["items"]) + "</div>")
    for sb in s["subs"]:
        h.append(f'<div class="sub" data-id="{sb["id"]}"><h3>{html.escape(sb["name"])}</h3><span class="subrule"></span></div>')
        h.append('<div class="items">' + "".join(item_html(i) for i in sb["items"]) + "</div>")
    return "".join(h) + "</section>"

left = "".join(sec_html(s) for s in doc["sections"][:2])
right = "".join(sec_html(s) for s in doc["sections"][2:])
ENDMARK = (f'<div class="endmark" aria-hidden="true"><span class="er"></span>'
           f'<svg viewBox="0 0 8 8" width="6pt" height="6pt"><path d="M4 0 L8 4 L4 8 L0 4 Z" fill="{P["mari"]}"/></svg>'
           f'<svg viewBox="0 0 8 8" width="6pt" height="6pt"><path d="M4 0 L8 4 L4 8 L0 4 Z" fill="{P["terra"]}"/></svg>'
           f'<svg viewBox="0 0 8 8" width="6pt" height="6pt"><path d="M4 0 L8 4 L4 8 L0 4 Z" fill="{P["agave"]}"/></svg><span class="er"></span></div>')

FONTS = "".join(
    "@font-face {{ font-family:'{}'; font-style:{}; font-weight:{}; font-display:block; src:url(data:font/ttf;base64,{}) format('truetype'); }}\n".format(
        f.stem.split('-')[0].replace('DMSans', 'DM Sans'), f.stem.split('-')[2], f.stem.split('-')[1], base64.b64encode(f.read_bytes()).decode())
    for f in sorted((HERE / "fonts").glob("*.ttf")))

def sh(k): return f"{shifts.get(k, 0):.3f}pt"
SHIFT_CSS = f"""
@media (min-width: 601px) {{
  .title {{ position:relative; top:{sh('title')}; }}
  .loc {{ position:relative; top:{sh('loc')}; }}
  .hrow h2 {{ position:relative; top:{sh('h2')}; }}
  .kicker {{ position:relative; top:{sh('h2')}; }}
  h3 {{ position:relative; top:{sh('h3')}; }}
  .name, .price {{ position:relative; top:{sh('name')}; }}
  .desc {{ position:relative; top:{sh('desc')}; }}
}}"""

CSS = FONTS + f"""
@page {{ size: 8.5in 11in; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin:0; padding:0; background:#d9d2c6; }}
body {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; font-family:'DM Sans', sans-serif; color:{P['ink']}; }}
.page {{ width:612pt; height:792pt; padding:36pt; background:{P['cream']}; display:flex; flex-direction:column; margin:0 auto; }}
/* masthead: 48 banner | 24 | 48 title | 12 loc | 12 | 12 rule | 24 -> columns start at 216pt */
.banner {{ display:block; width:540pt; height:48pt; flex:none; }}
.title {{ font-family:'Fraunces', serif; font-weight:700; font-size:40pt; line-height:48pt; height:48pt; letter-spacing:-0.4pt; text-align:center; margin:24pt 0 0; white-space:nowrap; }}
.title .amp {{ color:{P['terra']}; font-style:italic; font-weight:600; }}
.loc {{ text-align:center; font-size:9pt; line-height:12pt; height:12pt; letter-spacing:3.2pt; text-transform:uppercase; color:{P['muted']}; font-weight:500; margin:0; }}
.mastrule {{ display:block; width:540pt; height:12pt; margin-top:12pt; }}
.banner-m {{ display:none; }}
.cols {{ display:grid; grid-template-columns:258pt 24pt 258pt; margin-top:24pt; align-items:stretch; }}
.divider {{ justify-self:center; width:0; border-left:0.75pt dotted {P['mari']}; }}
/* 12pt grid: all heights/gaps below are multiples of 12 */
.sec + .sec {{ margin-top:36pt; }}
.hrow {{ display:flex; justify-content:space-between; align-items:baseline; height:24pt; }}
h2 {{ font-family:'Fraunces', serif; font-weight:700; font-size:24pt; line-height:24pt; margin:0; color:{P['ink']}; }}
.kicker {{ display:flex; align-items:baseline; gap:5pt; font-size:9pt; line-height:12pt; letter-spacing:2.2pt; text-transform:uppercase; color:{P['terra']}; font-weight:700; }}
.kicker .dia {{ flex:none; align-self:center; }}
.hrow + .items, .hrow + .sub {{ margin-top:12pt; }}        /* 12pt below every section header, whatever follows */
.items + .sub {{ margin-top:24pt; }}
.sub {{ display:flex; align-items:center; gap:8pt; height:12pt; }}
.sub + .items {{ margin-top:12pt; }}
h3 {{ margin:0; font-size:9pt; line-height:12pt; letter-spacing:2pt; text-transform:uppercase; color:{P['agave']}; font-weight:700; white-space:nowrap; }}
.subrule {{ flex:1; height:0; border-top:0.5pt solid {P['agave']}; opacity:.55; }}
.item + .item {{ margin-top:12pt; }}
.row {{ display:flex; justify-content:space-between; align-items:baseline; height:12pt; }}
.name {{ font-family:'Fraunces', serif; font-size:13pt; line-height:12pt; font-weight:600; }}
.price {{ font-family:'Fraunces', serif; font-size:12pt; line-height:12pt; font-weight:500; color:{P['terra']};
          font-variant-numeric:lining-nums tabular-nums; font-feature-settings:'lnum' 1, 'tnum' 1; margin-left:12pt; }}
.desc {{ margin:0; padding-right:6pt; font-size:9pt; line-height:12pt; color:{P['muted']}; }}
.endmark {{ display:flex; align-items:center; justify-content:center; gap:6pt; height:12pt; margin-top:12pt; }}
.endmark .er {{ width:42pt; border-top:0.5pt solid {P['agave']}; opacity:.55; }}
.foot {{ display:flex; align-items:center; gap:10pt; height:24pt; margin-top:auto; }}
.foot .fr {{ flex:1; border-top:0.5pt solid {P['ink']}; opacity:.5; }}
.foot .salud {{ font-family:'Fraunces', serif; font-style:italic; font-size:11pt; line-height:24pt; color:{P['terra']}; font-weight:600; }}
.agave {{ display:block; }}
{SHIFT_CSS}
@media screen and (max-width: 600px) {{
  html, body {{ background:{P['cream']}; }}
  .page {{ width:auto; height:auto; padding:20px 20px 24px; }}
  .banner {{ display:none; }}
  .banner-m {{ display:block; width:100%; height:auto; }}
  .mastrule {{ width:100%; height:auto; margin-top:14px; }}
  .title {{ font-size:36px; line-height:40px; height:auto; margin-top:16px; white-space:normal; text-wrap:balance; }}
  .loc {{ font-size:11px; line-height:16px; height:auto; margin-top:6px; letter-spacing:3px; }}
  .cols {{ grid-template-columns:1fr; margin-top:20px; }}
  .divider, .endmark {{ display:none; }}
  .col + .divider + .col {{ margin-top:36px; }}
  .sec + .sec {{ margin-top:36px; }}
  .hrow {{ height:38px; }}
  h2 {{ font-size:30px; line-height:38px; }}
  .kicker {{ font-size:12px; line-height:16px; align-items:baseline; }}
  .hrow {{ align-items:baseline; }}
  .hrow + .items, .hrow + .sub, .sub + .items {{ margin-top:14px; }}
  .items + .sub {{ margin-top:22px; }}
  .sub {{ height:20px; }}
  h3 {{ font-size:11.5px; line-height:20px; }}
  .row {{ height:26px; }}
  .name {{ font-size:18px; line-height:26px; }}
  .price {{ font-size:16px; line-height:26px; }}
  .desc {{ font-size:14px; line-height:20px; padding-right:20px; }}
  .item + .item {{ margin-top:16px; }}
  .foot {{ margin-top:36px; height:28px; }}
  .foot .salud {{ font-size:16px; }}
}}
"""

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cantina &amp; Cocktail Bar · Iowa City, Iowa</title>
<style>{CSS}</style></head>
<body><div class="page">
<header class="mast">{papel_picado()}{papel_picado(5, "banner-m", 340, 64, 'width="100%"')}
<h1 class="title">Cantina <span class="amp">&amp;</span> Cocktail Bar</h1>
<p class="loc">Iowa City, Iowa</p>{title_rule()}</header>
<main class="cols"><div class="col">{left}</div><div class="divider" aria-hidden="true"></div><div class="col">{right}</div></main>
<footer class="foot"><span class="fr"></span>{AGAVE}<span class="salud">¡Salud!</span>{AGAVE}<span class="fr"></span></footer>
</div>
<script>
(function(){{
  if (window.innerWidth <= 600) return;
  const q = s => document.querySelector(s);
  const pairs = [['[data-id="sec_spirits"]','[data-id="sec_wine"]'],['[data-id="sub_spirits_agave"]','[data-id="sub_wine_by_the_glass"]'],['[data-id="sub_spirits_brandy"]','[data-id="sub_wine_sparkling"]']];
  for (const [a,b] of pairs) {{
    const A=q(a), B=q(b); const d=A.getBoundingClientRect().top-B.getBoundingClientRect().top;
    const T = d>0 ? B : A; T.style.marginTop = (parseFloat(getComputedStyle(T).marginTop)+Math.abs(d))+'px';
  }}
}})();
</script></body></html>
"""
(OUT / "menu.html").write_text(HTML)
print("built; shifts =", shifts)
