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
    "beta_margarita": "Tequila blanco, fresh lime, orange liqueur, agave syrup; lime wheel. Bright and citrus-forward.",
    "beta_manhattan": "Rye whiskey, sweet vermouth; cocktail cherry. Stirred and strained into a coupe.",
    "beta_old_fashioned": "Brown butter-washed bourbon, demerara syrup, aromatic bitters; orange peel. Over a large cube.",
    "beta_daiquiri": "White rum, fresh lime, demerara syrup; lime coin. Shaken and fine-strained into a coupe.",
    "beta_blanco_tequila": "Blue agave, unaged. D.O. Tequila.",
    "beta_anejo_tequila": "Blue agave, aged at least one year in oak. D.O. Tequila.",
    "beta_cognac_vsop": "Grape brandy, aged at least four years in oak.",
    "beta_czech_pilsner": "Crisp pale lager in the Czech pils style.",
    "beta_dry_hopped_ipa": "Hop-forward India pale ale, dry-hopped. On draft.",
    "beta_amber_lager": "Toasty amber lager, on draft.",
    "beta_dry_cider": "Dry, sparkling cider.",
    "beta_malbec": "Dry red wine from the Malbec grape.",
    "beta_pinot_grigio": "Dry white wine from the Pinot Grigio grape.",
    "beta_brut_rose": "Dry sparkling rosé in the brut style.",
}
KICKER = {"sec_cocktails": "Cócteles", "sec_spirits": "Destilados", "sec_beer": "Cerveza", "sec_cider": "Sidra", "sec_wine": "Vino"}

secs = {s["id"]: s for s in draft["sections"]}
doc = copy.deepcopy(draft)
doc["title"] = "Cantina & Cocktail Bar"
doc["subtitle"] = "Iowa City, Iowa"
new_secs = [copy.deepcopy(secs[k]) for k in ["sec_cocktails", "sec_spirits", "sec_beer", "sec_cider", "sec_wine"]]
cl = new_secs[0]["subs"][0]; cl["items"] = [next(i for i in cl["items"] if i["id"] == x) for x in ["beta_margarita", "beta_manhattan"]]
ho = new_secs[0]["subs"][1]; ho["items"] = [next(i for i in ho["items"] if i["id"] == x) for x in ["beta_old_fashioned", "beta_daiquiri"]]
for s in new_secs:
    for it in s["items"] + [i for sb in s["subs"] for i in sb["items"]]:
        it["desc"] = DESC[it["id"]]
doc["sections"] = new_secs

def flat(d):
    return {i["id"]: (i["name"], json.dumps(i["prices"], sort_keys=True), json.dumps(i.get("phg"), sort_keys=True),
                      json.dumps(i.get("meta"), sort_keys=True), json.dumps(i.get("components"), sort_keys=True))
            for s in d["sections"] for i in s["items"] + [x for sb in s["subs"] for x in sb["items"]]}
assert flat(doc) == flat(draft) and len(flat(doc)) == 14, "item/price/meta drift"
(OUT / "doc.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2))

# ---------------------------------------------------------------- palette
P = dict(cream="#F6EEDF", ink="#231B16", terra="#A63C1A", flag_terra="#B4441F", agave="#2F5D50", mari="#E3A018", muted="#5A4A3F")

# ---------------------------------------------------------------- bespoke papel picado (9 flags, 9 different cut-outs)
def motif(k, cx, cy, c, cr):
    if k == 0:   # agave
        return "".join(f'<path d="M{cx} {cy+9} L{cx+dx*0.35:.2f} {cy-6+abs(dx)*0.5:.2f} L{cx+dx:.2f} {cy-9+abs(dx)*0.7:.2f} L{cx+dx*0.2:.2f} {cy+9} Z" fill="{cr}"/>' for dx in (-10, -5, 0.01, 5, 10))
    if k == 1:   # lime wheel
        s = f'<circle cx="{cx}" cy="{cy}" r="10" fill="{cr}"/><circle cx="{cx}" cy="{cy}" r="8" fill="{c}"/>'
        for j in range(8):
            a0, a1 = j * math.pi / 4 + 0.12, (j + 1) * math.pi / 4 - 0.12
            s += (f'<path d="M{cx} {cy} L{cx+7*math.cos(a0):.2f} {cy+7*math.sin(a0):.2f} A7 7 0 0 1 {cx+7*math.cos(a1):.2f} {cy+7*math.sin(a1):.2f} Z" fill="{cr}"/>')
        return s + f'<circle cx="{cx}" cy="{cy}" r="1.6" fill="{c}"/>'
    if k == 2:   # five-point star
        pts = " ".join(f"{cx+(10 if j%2==0 else 4.2)*math.sin(j*math.pi/5):.2f},{cy-(10 if j%2==0 else 4.2)*math.cos(j*math.pi/5):.2f}" for j in range(10))
        return f'<polygon points="{pts}" fill="{cr}"/>'
    if k == 3:   # nested diamond
        return (f'<path d="M{cx} {cy-11} L{cx+9} {cy} L{cx} {cy+11} L{cx-9} {cy} Z" fill="{cr}"/>'
                f'<path d="M{cx} {cy-6} L{cx+5} {cy} L{cx} {cy+6} L{cx-5} {cy} Z" fill="{c}"/><circle cx="{cx}" cy="{cy}" r="1.8" fill="{cr}"/>')
    if k == 4:   # sun
        s = f'<circle cx="{cx}" cy="{cy}" r="5" fill="{cr}"/>'
        for j in range(12):
            a = j * math.pi / 6; w = 0.22
            s += (f'<path d="M{cx+6.5*math.cos(a-w):.2f} {cy+6.5*math.sin(a-w):.2f} L{cx+11*math.cos(a):.2f} {cy+11*math.sin(a):.2f} '
                  f'L{cx+6.5*math.cos(a+w):.2f} {cy+6.5*math.sin(a+w):.2f} Z" fill="{cr}"/>')
        return s
    if k == 5:   # marigold flower
        s = "".join(f'<ellipse cx="{cx+6*math.cos(j*math.pi/3):.2f}" cy="{cy+6*math.sin(j*math.pi/3):.2f}" rx="4.2" ry="2.6" '
                    f'transform="rotate({j*60} {cx+6*math.cos(j*math.pi/3):.2f} {cy+6*math.sin(j*math.pi/3):.2f})" fill="{cr}"/>' for j in range(6))
        return s + f'<circle cx="{cx}" cy="{cy}" r="2.6" fill="{c}"/>'
    if k == 6:   # cactus
        return (f'<rect x="{cx-2.4}" y="{cy-11}" width="4.8" height="21" rx="2.4" fill="{cr}"/>'
                f'<path d="M{cx-2.4} {cy+2} h-4 a2 2 0 0 1 -2 -2 v-6 a1.8 1.8 0 0 1 3.6 0 v4.4 h2.4 Z" fill="{cr}"/>'
                f'<path d="M{cx+2.4} {cy-1} h4 a2 2 0 0 0 2 -2 v-5 a1.8 1.8 0 0 0 -3.6 0 v3.4 h-2.4 Z" fill="{cr}"/>'
                f'<rect x="{cx-7}" y="{cy+10}" width="14" height="1.4" fill="{cr}"/>')
    if k == 7:   # heart (corazón)
        return (f'<path d="M{cx} {cy+9} C{cx-14} {cy-1} {cx-7} {cy-12} {cx} {cy-4} C{cx+7} {cy-12} {cx+14} {cy-1} {cx} {cy+9} Z" fill="{cr}"/>'
                f'<path d="M{cx} {cy+3.5} C{cx-6} {cy-1} {cx-3} {cy-6} {cx} {cy-2} C{cx+3} {cy-6} {cx+6} {cy-1} {cx} {cy+3.5} Z" fill="{c}"/>')
    # crescent moon + star
    return (f'<circle cx="{cx-1}" cy="{cy}" r="9" fill="{cr}"/><circle cx="{cx+3}" cy="{cy-2}" r="8" fill="{c}"/>'
            f'<circle cx="{cx+6}" cy="{cy+4}" r="1.6" fill="{cr}"/>')

def papel_picado():
    W, H, n = 540, 48, 9
    cell = W / n; fw = cell - 8
    cols = [P["flag_terra"], P["mari"], P["agave"]]
    out = [f'<svg class="banner" viewBox="0 0 {W} {H}" width="540pt" height="48pt" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">',
           f'<path d="M1 0.4 Q{W/2} 4.4 {W-1} 0.4" stroke="{P["ink"]}" stroke-width="0.8" stroke-linecap="butt" fill="none"/>']
    for k in range(n):
        x = k * cell + 4; c = cols[k % 3]; cx = round(x + fw / 2, 2); cr = P["cream"]
        zig = " ".join(f"L{x + fw - j * fw / 6:.2f} {41 if j % 2 == 0 else 47.6}" for j in range(7))
        out.append(f'<path d="M{x:.2f} 3.4 L{x+fw:.2f} 3.4 L{x+fw:.2f} 41 {zig} Z" fill="{c}"/>')
        out.append(f'<rect x="{x:.2f}" y="6.4" width="{fw:.2f}" height="0.8" fill="{cr}" opacity=".85"/>')
        out.append(motif(k, cx, 21.5, c, cr))
        out.append("".join(f'<circle cx="{x + 5 + j * (fw - 10) / 6:.2f}" cy="36.4" r="1.2" fill="{cr}"/>' for j in range(7)))
    out.append("</svg>")
    return "".join(out)

AGAVE = (f'<svg class="agave" viewBox="0 0 40 24" width="40pt" height="24pt" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
         f'<g fill="{P["agave"]}"><path d="M20 24 L18 4 L20 0 L22 4 Z"/><path d="M19 24 L10 7 L9 2 L13 6 Z"/><path d="M21 24 L30 7 L31 2 L27 6 Z"/>'
         f'<path d="M18 24 L4 14 L0 11 L6 12 Z"/><path d="M22 24 L36 14 L40 11 L34 12 Z"/></g></svg>')
DIAMOND = f'<svg class="dia" viewBox="0 0 8 8" width="5pt" height="5pt" aria-hidden="true"><path d="M4 0 L8 4 L4 8 L0 4 Z" fill="{P["mari"]}"/></svg>'

def item_html(it):
    return (f'<div class="item" data-ref="{it["id"]}"><div class="row"><span class="name">{html.escape(it["name"])}</span>'
            f'<span class="price">{it["prices"][0]["value"]:g}</span></div><p class="desc">{html.escape(it["desc"]).replace("D.O. Tequila", "D.O.&nbsp;Tequila")}</p></div>')

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
.mastrule {{ height:12pt; margin-top:12pt; position:relative; }}
.mastrule::before {{ content:''; position:absolute; left:0; right:0; top:4pt; border-top:1.5pt solid {P['ink']}; }}
.mastrule::after {{ content:''; position:absolute; left:0; right:0; top:7pt; border-top:0.5pt solid {P['ink']}; }}
.cols {{ display:grid; grid-template-columns:258pt 24pt 258pt; margin-top:24pt; align-items:stretch; }}
.divider {{ justify-self:center; width:0; border-left:0.75pt dotted {P['mari']}; }}
/* 12pt grid: all heights/gaps below are multiples of 12 */
.sec + .sec {{ margin-top:36pt; }}
.hrow {{ display:flex; justify-content:space-between; align-items:baseline; height:24pt; }}
h2 {{ font-family:'Fraunces', serif; font-weight:700; font-size:24pt; line-height:24pt; margin:0; color:{P['ink']}; }}
.kicker {{ display:flex; align-items:baseline; gap:5pt; font-size:8pt; line-height:12pt; letter-spacing:2.4pt; text-transform:uppercase; color:{P['terra']}; font-weight:700; }}
.kicker .dia {{ flex:none; align-self:center; }}
.hrow + .items, .hrow + .sub {{ margin-top:12pt; }}        /* 12pt below every section header, whatever follows */
.items + .sub {{ margin-top:24pt; }}
.sub {{ display:flex; align-items:center; gap:8pt; height:12pt; }}
.sub + .items {{ margin-top:12pt; }}
h3 {{ margin:0; font-size:8.5pt; line-height:12pt; letter-spacing:2pt; text-transform:uppercase; color:{P['agave']}; font-weight:700; white-space:nowrap; }}
.subrule {{ flex:1; height:0; border-top:0.5pt solid {P['agave']}; opacity:.55; }}
.item + .item {{ margin-top:12pt; }}
.row {{ display:flex; justify-content:space-between; align-items:baseline; height:12pt; }}
.name {{ font-family:'Fraunces', serif; font-size:13pt; line-height:12pt; font-weight:600; }}
.price {{ font-family:'Fraunces', serif; font-size:13pt; line-height:12pt; font-weight:600; color:{P['terra']};
          font-variant-numeric:lining-nums tabular-nums; font-feature-settings:'lnum' 1, 'tnum' 1; margin-left:12pt; }}
.desc {{ margin:0; padding-right:30pt; font-size:9pt; line-height:12pt; color:{P['muted']}; }}
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
  .banner {{ width:100%; height:auto; }}
  .title {{ font-size:36px; line-height:40px; height:auto; margin-top:16px; white-space:normal; text-wrap:balance; }}
  .loc {{ font-size:11px; line-height:16px; height:auto; margin-top:6px; letter-spacing:3px; }}
  .cols {{ grid-template-columns:1fr; margin-top:20px; }}
  .divider, .endmark {{ display:none; }}
  .col + .divider + .col {{ margin-top:36px; }}
  .sec + .sec {{ margin-top:36px; }}
  .hrow {{ height:38px; }}
  h2 {{ font-size:30px; line-height:38px; }}
  .kicker {{ font-size:11px; line-height:16px; }}
  .hrow + .items, .hrow + .sub, .sub + .items {{ margin-top:14px; }}
  .items + .sub {{ margin-top:22px; }}
  .sub {{ height:20px; }}
  h3 {{ font-size:11.5px; line-height:20px; }}
  .row {{ height:26px; }}
  .name {{ font-size:18px; line-height:26px; }}
  .price {{ font-size:18px; line-height:26px; }}
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
<header class="mast">{papel_picado()}
<h1 class="title">Cantina <span class="amp">&amp;</span> Cocktail Bar</h1>
<p class="loc">Iowa City, Iowa</p><div class="mastrule"></div></header>
<main class="cols"><div class="col">{left}</div><div class="divider" aria-hidden="true"></div><div class="col">{right}{ENDMARK}</div></main>
<footer class="foot"><span class="fr"></span>{AGAVE}<span class="salud">¡Salud!</span>{AGAVE}<span class="fr"></span></footer>
</div></body></html>
"""
(OUT / "menu.html").write_text(HTML)
print("built; shifts =", shifts)
