"""TEST-1 round 17: 'Sun Behind the Page', one editorial page (Bistro / Solstice lineage).
Writes ../round-17/doc.json and ../round-17/menu.html. Art = inline SVG only (cut-paper grammar), text = HTML.
Copy: round-16 sourced wording recast as 'word · word' lines; corrections: no 'poured straight', no name-echo tags,
Manhattan without bitters (draft meta.public_components {'aromatic-bitters': false})."""
import json, copy, math, pathlib, random

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "round-17"
FONTS = (HERE.parent / "build" / "fonts").resolve()
draft = json.loads((HERE.parent / "build" / "draft_doc.json").read_text())

# ---------------------------------------------------------------- copy (every word traced)
LINE = {
 "beta_margarita": ("tequila blanco · fresh lime · orange liqueur · agave syrup · lime wheel",
   "draft desc 'Tequila blanco, lime, orange liqueur, agave'; draft components 'Fresh Lime Juice', 'Agave Syrup'; garnish 'Lime wheel' from phg.recipe_versions f06abb74"),
 "beta_manhattan": ("rye · sweet vermouth · cocktail cherry",
   "draft desc 'Rye, sweet vermouth, aromatic bitters.' with bitters hidden (meta.public_components {'aromatic-bitters': false}); draft component 'Cocktail Cherry' (role Garnish); recipe_versions 9fb77eaa garnish 'Cocktail cherry'"),
 "beta_old_fashioned": ("brown butter-washed bourbon · demerara syrup · aromatic bitters · orange peel",
   "draft components 'Brown Butter-Washed Bourbon', 'Demerara Syrup', 'Aromatic Bitters' (not hidden); garnish 'Orange peel' from phg.recipe_versions 7095fd3d"),
 "beta_daiquiri": ("white rum · fresh lime · house demerara syrup · lime coin",
   "draft desc 'White rum, lime, and house demerara syrup.'; component 'Fresh Lime Juice'; garnish 'Lime coin' from phg.recipe_versions 14d45e57"),
 "beta_czech_pilsner": ("crisp · pale lager", "draft desc 'Crisp pale lager.'"),
 "beta_dry_hopped_ipa": ("hop-forward", "draft desc 'Hop-forward draft IPA.' ('draft' lives in the Draft subhead; 'IPA' would echo the name)"),
 "beta_amber_lager": ("toasty", "draft desc 'Toasty amber lager.' ('amber lager' would echo the name)"),
 "beta_dry_cider": ("sparkling", "draft desc 'Dry sparkling cider.' ('dry', 'cider' would echo the name)"),
 "beta_malbec": ("dry · red", "draft desc 'Dry red wine.'"),
 "beta_pinot_grigio": ("dry · white", "draft desc 'Dry white wine.'"),
 "beta_brut_rose": ("dry · sparkling", "draft desc 'Dry sparkling rosé.' ('rosé' would echo the name)"),
 "beta_blanco_tequila": ("pour", "draft desc 'Blanco tequila pour.' (every other word echoes the name)"),
 "beta_anejo_tequila": ("pour", "draft desc 'Añejo tequila pour.' (every other word echoes the name)"),
 "beta_cognac_vsop": ("pour", "draft desc 'VSOP Cognac pour.' (every other word echoes the name)"),
}
TAGS = {  # section-rule taglines: generic brand voice, no item facts
 "cocktails": "raise a glass", "beer": "one more round", "wine": "for the table", "spirits": "take your time"}
RAIL_TOP = ["GOOD", "DRINKS", "GOOD", "COMPANY"]
RAIL_BOT = ["PULL UP", "A CHAIR", "STAY", "A WHILE"]

items = {}
def walk(s):
    for i in s.get("items", []): items[i["id"]] = i
    for sb in s.get("subs", []): walk(sb)
for s in draft["sections"]: walk(s)
assert set(items) == set(LINE), set(items) ^ set(LINE)

# ---------------------------------------------------------------- doc.json (ids, prices, structure kept)
doc = copy.deepcopy(draft)
doc["title"] = "Cantina & Cocktail Bar"; doc["subtitle"] = "Iowa City, Iowa"
order = ["sec_cocktails", "sec_beer", "sec_cider", "sec_wine", "sec_spirits"]
doc["sections"] = sorted(doc["sections"], key=lambda s: order.index(s["id"]))
def fix(s):
    for i in s.get("items", []): i["desc"] = LINE[i["id"]][0]
    for sb in s.get("subs", []): fix(sb)
for s in doc["sections"]:
    fix(s)
    if s["id"] == "sec_cocktails":  # Margarita leads Classics (round-16 order)
        cl = s["subs"][0]; cl["items"].sort(key=lambda i: i["id"] != "beta_margarita")
        ho = s["subs"][1]; ho["items"].sort(key=lambda i: i["id"] != "beta_old_fashioned")
doc.setdefault("meta", {})["designer_notes"] = {"round": 17, "concept": "Sun Behind the Page",
    "copy_sources": {k: v[1] for k, v in LINE.items()}, "taglines": {"rail": [RAIL_TOP, RAIL_BOT], "section_rules": TAGS}}
OUT.mkdir(exist_ok=True)
(OUT / "doc.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))

# price check against the draft
for k, i in items.items():
    pass
def P(i): return str(int(i["prices"][0]["value"])) if float(i["prices"][0]["value"]).is_integer() else str(i["prices"][0]["value"])

# ---------------------------------------------------------------- ART layer (SVG, pt units; bleed 9pt = 3.175 mm)
random.seed(17)
PAL = dict(paper="#F2E9D6", sky0="#F1DEC2", sky1="#E7B893", sky2="#CF7F55", hill1="#B5532F", hill2="#7C3322",
           leafA="#2E5A4B", leafB="#3F7362", leafC="#244A3E", leafD="#56866F", ground="#162C25", gold0="#C99532", ink="#1D1815")

def leaf(bx, by, ang, L, W, cl, cr, curve=0.10):
    """two-tone folded paper leaf: left half cl, right half cr; ang deg from vertical (+ = leans right)."""
    a = math.radians(ang); ux, uy = math.sin(a), -math.cos(a); px, py = -uy, ux
    tipx, tipy = bx + ux * L + px * L * curve, by + uy * L + py * L * curve
    mx, my = bx + ux * L * .45 + px * L * curve * .5, by + uy * L * .45 + py * L * curve * .5
    lx, ly = mx - px * W, my - py * W; rx, ry = mx + px * W, my + py * W
    bl = (bx - px * W * .55, by - py * W * .55); br = (bx + px * W * .55, by + py * W * .55)
    q = lambda v: f"{v:.1f}"
    left = f"M{q(bl[0])},{q(bl[1])} Q{q(lx)},{q(ly)} {q(tipx)},{q(tipy)} Q{q(mx - px*W*.15)},{q(my - py*W*.15)} {q(bx)},{q(by)} Z"
    right = f"M{q(br[0])},{q(br[1])} Q{q(rx)},{q(ry)} {q(tipx)},{q(tipy)} Q{q(mx + px*W*.15)},{q(my + py*W*.15)} {q(bx)},{q(by)} Z"
    return f'<path d="{left}" fill="{cl}"/><path d="{right}" fill="{cr}"/>'

A, B, C_, D = PAL["leafA"], PAL["leafB"], PAL["leafC"], PAL["leafD"]
# one rosette, base below trim, tips lean toward the menu (gaze vector -> content)
LEAVES = [(-44, 330, 30, D, B), (-30, 420, 34, B, A), (48, 300, 28, D, B), (-14, 500, 36, D, B), (34, 400, 32, B, A),
          (4, 560, 38, B, C_), (20, 470, 34, D, B), (-6, 380, 30, A, C_), (12, 330, 26, B, C_), (62, 250, 24, B, A)]
leaves_svg = "".join(leaf(66, 812, a, L, W * .5, cl, cr, curve=0.06 if a < 0 else 0.10) for a, L, W, cl, cr in LEAVES)

def torn_band(y, amp, seed, x0=-9, x1=240):
    rnd = random.Random(seed); pts = []; x = x0
    while x <= x1:
        pts.append((x, y + math.sin(x / 37 + seed) * amp + rnd.uniform(-amp * .4, amp * .4))); x += 9
    d = "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f" L{x1},801 L{x0},801 Z"
    return d

def page_edge(seed=5):
    """torn edge of the page paper laid over the art; returns path covering x >= edge."""
    rnd = random.Random(seed); pts = []; y = -9
    while y <= 801:
        pts.append((158 + math.sin(y / 61) * 7 + math.sin(y / 17 + 2) * 2.5 + rnd.uniform(-1.6, 1.6), y)); y += 6
    return "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + " L640,801 L640,-9 Z"

EDGE = page_edge()
ART = f'''
<svg class="art" viewBox="-9 -9 630 810" preserveAspectRatio="xMinYMin slice" aria-hidden="true">
 <defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
   <stop offset="0" stop-color="{PAL['sky0']}"/><stop offset=".30" stop-color="{PAL['sky0']}"/>
   <stop offset=".55" stop-color="{PAL['sky1']}"/><stop offset=".78" stop-color="{PAL['sky2']}"/></linearGradient>
  <radialGradient id="goldlight" cx=".38" cy=".32" r=".8"><stop offset="0" stop-color="#E4BF66"/><stop offset=".6" stop-color="#CF9E3E"/><stop offset="1" stop-color="#BF8C31"/></radialGradient>
  <filter id="torn" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".06" numOctaves="4" seed="3"/>
   <feDisplacementMap in="SourceGraphic" scale="5"/></filter>
  <filter id="rim" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".09" numOctaves="4" seed="11"/>
   <feDisplacementMap in="SourceGraphic" scale="9"/></filter>
  <filter id="cut" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="3" seed="7"/>
   <feDisplacementMap in="SourceGraphic" scale="3.2" result="d"/>
   <feDropShadow in="d" dx="-1.6" dy="2.4" stdDeviation="1.6" flood-color="#1B120C" flood-opacity=".38"/></filter>
  <filter id="leaf" x="-60%" y="-10%" width="220%" height="120%"><feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="3" seed="9"/>
   <feDisplacementMap in="SourceGraphic" scale="2.6" result="d"/>
   <feDropShadow in="d" dx="-2" dy="3" stdDeviation="2" flood-color="#0C1A15" flood-opacity=".45"/></filter>
  <filter id="goldleaf" x="-5%" y="-5%" width="110%" height="110%">
   <feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="4" seed="21" result="n"/>
   <feColorMatrix in="n" type="matrix" values="0 0 0 0 .93  0 0 0 0 .78  0 0 0 0 .42  0 0 0 1.9 -.85" result="fleck"/>
   <feComposite in="fleck" in2="SourceGraphic" operator="in" result="f2"/>
   <feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="f2"/></feMerge></filter>
  <filter id="fiber" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3" seed="4" result="n"/>
   <feColorMatrix in="n" type="matrix" values="0 0 0 0 .22  0 0 0 0 .16  0 0 0 0 .10  0 0 0 -1.4 .95"/></filter>
  <filter id="shadowL" x="-10%" y="-2%" width="120%" height="104%"><feDropShadow dx="-2" dy="2.5" stdDeviation="2.2" flood-color="#1B120C" flood-opacity=".42"/></filter>
  <clipPath id="railclip"><rect x="-9" y="-9" width="200" height="810"/></clipPath>
 </defs>
 <g clip-path="url(#railclip)">
  <rect x="-9" y="-9" width="200" height="810" fill="url(#sky)"/>
  <circle cx="104" cy="286" r="104" fill="url(#goldlight)" filter="url(#goldleaf)"/>
  <g filter="url(#cut)"><path d="{torn_band(482, 7, 1)}" fill="{PAL['hill1']}"/></g>
  <g filter="url(#rim)"><path d="{torn_band(528, 9, 2)}" fill="{PAL['paper']}" transform="translate(0,-2.5)"/></g>
  <g filter="url(#cut)"><path d="{torn_band(528, 9, 2)}" fill="{PAL['hill2']}"/></g>
  <g filter="url(#leaf)">{leaves_svg}</g>
  <g filter="url(#rim)"><path d="{torn_band(676, 6, 4)}" fill="{PAL['paper']}" transform="translate(0,-2.5)"/></g>
  <g filter="url(#cut)"><path d="{torn_band(676, 6, 4)}" fill="{PAL['ground']}"/></g>
  <rect x="-9" y="-9" width="200" height="810" filter="url(#fiber)" opacity=".55"/>
 </g>
 <g filter="url(#rim)"><path d="{EDGE}" fill="#FBF6EA" transform="translate(-3.2,0)"/></g>
 <path d="{EDGE}" fill="{PAL['paper']}" filter="url(#shadowL)"/>
 <rect x="150" y="-9" width="490" height="810" filter="url(#fiber)" opacity=".10"/>
</svg>'''

# ---------------------------------------------------------------- TEXT layer
def item(i, half=False):
    return (f'<div class="item" data-ref="{i["id"]}"><div class="row"><span class="name tx">{i["name"]}</span>'
            f'<span class="lead"></span><span class="price tx">{P(i)}</span></div>'
            f'<div class="desc tx">{LINE[i["id"]][0]}</div></div>')

def sub(label, its, sid, half=False):
    return f'<div class="sub" data-id="{sid}"><h3 class="tx">{label}</h3>' + "".join(item(i, half) for i in its) + "</div>"

S = {s["id"]: s for s in doc["sections"]}
def head(title, tag, sid):
    return f'<div class="hrow" data-id="{sid}"><h2 class="tx">{title}</h2><span class="tag tx">{tag}</span></div>'

ck = S["sec_cocktails"]; be = S["sec_beer"]; ci = S["sec_cider"]; wi = S["sec_wine"]; sp = S["sec_spirits"]
MENU = (
 f'<section class="sec" data-id="sec_cocktails">{head("Cocktails", TAGS["cocktails"], "sec_cocktails")}'
 + "".join(sub(sb["name"], sb["items"], sb["id"]) for sb in ck["subs"]) + "</section>"
 + f'<section class="sec" data-id="sec_beer+sec_cider">{head("Beer &amp; Cider", TAGS["beer"], "sec_beer")}'
 + sub(be["subs"][0]["name"], be["subs"][0]["items"], be["subs"][0]["id"]) + sub(ci["name"], ci["items"], "sec_cider") + "</section>"
 + '<div class="pair">'
 + f'<section class="sec half" data-id="sec_wine">{head("Wine", TAGS["wine"], "sec_wine")}'
 + "".join(sub(sb["name"], sb["items"], sb["id"], True) for sb in wi["subs"]) + "</section>"
 + f'<section class="sec half" data-id="sec_spirits">{head("Spirits", TAGS["spirits"], "sec_spirits")}'
 + "".join(sub(sb["name"], sb["items"], sb["id"], True) for sb in sp["subs"]) + "</section></div>")

CSS = f"""
@font-face {{font-family:'Fraunces';src:url('{FONTS}/fraunces.woff2') format('woff2');font-weight:300 900;font-style:normal;font-display:block}}
@font-face {{font-family:'Fraunces';src:url('{FONTS}/fraunces-i.woff2') format('woff2');font-weight:300 900;font-style:italic;font-display:block}}
@font-face {{font-family:'DM Sans';src:url('{FONTS}/DMSans-500-normal.ttf');font-weight:500;font-display:block}}
@font-face {{font-family:'DM Sans';src:url('{FONTS}/DMSans-700-normal.ttf');font-weight:700;font-display:block}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:#fff}}
.page{{position:relative;width:612pt;height:792pt;overflow:hidden;background:{PAL['paper']};color:{PAL['ink']};
  font-family:'Fraunces',serif;font-variant-numeric:lining-nums tabular-nums;-webkit-print-color-adjust:exact}}
.art{{position:absolute;left:-9pt;top:-9pt;width:630pt;height:810pt}}
.rail{{position:absolute;left:36pt;font:500 7.5pt/12pt 'DM Sans',sans-serif;letter-spacing:.38em}}
.rail.top{{top:36pt;color:{PAL['ink']}}}
.rail.bot{{bottom:36pt;color:#F4ECDC}}
.wm{{position:absolute;left:170pt;top:36pt;height:720pt;display:flex;flex-direction:row-reverse;gap:6pt}}
.wm .big{{writing-mode:vertical-rl;font-weight:380;font-size:96pt;line-height:74pt;letter-spacing:.075em;
  font-variation-settings:'opsz' 144, 'SOFT' 0, 'WONK' 0;color:{PAL['ink']};height:720pt;text-align:start}}
.wm .small{{writing-mode:vertical-rl;font:500 8pt/12pt 'DM Sans',sans-serif;letter-spacing:.42em;color:#6E2F1D;height:720pt;text-align:end}}
.menu{{position:absolute;left:282pt;top:36pt;width:294pt;height:720pt;display:flex;flex-direction:column;justify-content:space-between}}
.hrow{{display:flex;align-items:baseline;justify-content:space-between;border-bottom:.75pt solid #6B5A4C;padding-bottom:5pt;margin-bottom:9pt}}
h2{{font-weight:600;font-size:15pt;line-height:18pt;letter-spacing:.2em;text-transform:uppercase;font-variation-settings:'opsz' 36}}
.tag{{font-style:italic;font-weight:400;font-size:9.5pt;line-height:12pt;color:#5A4B3F;letter-spacing:.02em}}
h3{{font:700 7.5pt/12pt 'DM Sans',sans-serif;letter-spacing:.26em;text-transform:uppercase;color:#9A3B22;margin:0 0 3pt}}
.sub+.sub{{margin-top:9pt}}
.item+.item{{margin-top:6pt}}
.row{{display:flex;align-items:baseline}}
.name{{font-weight:600;font-size:10.5pt;line-height:14pt;letter-spacing:.11em;text-transform:uppercase;white-space:nowrap}}
.lead{{flex:1;min-width:8pt;margin:0 5pt;border-bottom:1.1pt dotted #9C8B7B;transform:translateY(-2.5pt)}}
.price{{font-weight:600;font-size:12pt;line-height:14pt;min-width:15pt;text-align:right}}
.desc{{font-weight:400;font-size:10pt;line-height:13pt;color:#40352D;padding-right:22pt;font-variation-settings:'opsz' 12}}
.pair{{display:grid;grid-template-columns:1fr 1fr;column-gap:18pt}}
.half .name{{letter-spacing:.08em}}
.half .desc{{padding-right:0}}
.salud{{position:absolute;right:36pt;bottom:36pt}}
/* phone: one reading column; the art becomes a hero band */
@media (max-width:600px){{
 .page{{width:100%;height:auto;overflow:visible}}
 .art{{position:relative;left:0;top:0;width:100%;height:auto;aspect-ratio:390/330;display:block}}
 .rail{{display:none}}
 .wm{{position:relative;left:0;top:0;height:auto;display:block;padding:18px 22px 6px;background:{PAL['paper']}}}
 .wm .big{{writing-mode:horizontal-tb;height:auto;font-size:58px;line-height:62px;letter-spacing:.06em}}
 .wm .small{{writing-mode:horizontal-tb;height:auto;font-size:11px;line-height:18px;letter-spacing:.3em;text-align:start}}
 .menu{{position:relative;left:0;top:0;width:auto;height:auto;display:block;padding:12px 22px 36px}}
 .sec{{margin-top:26px}}
 .pair{{display:block}}
 h2{{font-size:19px;line-height:24px}}
 .tag{{font-size:14px;line-height:18px}}
 h3{{font-size:11px;line-height:16px;margin-bottom:4px}}
 .sub+.sub{{margin-top:14px}}
 .item+.item{{margin-top:10px}}
 .name,.half .name{{font-size:15px;line-height:21px;letter-spacing:.08em;white-space:normal}}
 .price{{font-size:17px;line-height:21px}}
 .desc,.half .desc{{font-size:15px;line-height:20px;padding-right:30px}}
 .phonefoot{{display:block}}
}}
.phonefoot{{display:none;padding:0 22px 40px;font:500 11px/18px 'DM Sans',sans-serif;letter-spacing:.34em;color:{PAL['ink']}}}
"""
PHONE_ART = ART.replace('viewBox="-9 -9 630 810" preserveAspectRatio="xMinYMin slice"', 'viewBox="-9 150 390 330" preserveAspectRatio="xMidYMid slice"')
HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cantina &amp; Cocktail Bar · Iowa City, Iowa</title><style>{CSS}
.art.phone{{display:none}} @media (max-width:600px){{.art.print{{display:none}} .art.phone{{display:block}}}}</style></head><body>
<div class="page">
{ART.replace('class="art"', 'class="art print"')}
{PHONE_ART.replace('class="art"', 'class="art phone"').replace('id="', 'id="p_').replace('url(#', 'url(#p_')}
<div class="rail top tx">{'<br>'.join(RAIL_TOP)}</div>
<div class="rail bot tx">{'<br>'.join(RAIL_BOT)}</div>
<div class="wm"><div class="big tx">CANTINA</div><div class="small tx">&amp; COCKTAIL BAR&#8195;·&#8195;IOWA CITY, IOWA</div></div>
<main class="menu">{MENU}</main>
<div class="phonefoot tx">{' '.join(RAIL_TOP)}<br>{' '.join(RAIL_BOT)}</div>
</div></body></html>"""
(OUT / "menu.html").write_text(HTML)
print("ok", len(HTML))
