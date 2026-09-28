"""TEST-1 round 20: round-17/19 'Sun Behind the Page' page, cut-paper art re-landed in Iowa (loess bluffs + contour strip
rows under the agave), one grain treatment, inline prices (no leaders), title-case names, italic/roman bilingual heads,
7 pt baseline unit, phone hero + footer of its own. Writes ../round-20/doc.json and ../round-20/menu.html."""
import json, copy, math, pathlib, random

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "round-20"
FONTS = (HERE.parent / "build" / "fonts").resolve()
draft = json.loads((HERE.parent / "build" / "draft_doc.json").read_text())

# ---------------------------------------------------------------- copy (every word traced)
# kind: "c" cocktail (name + price, then ingredient lines, glass last); "r" one row (name, draft descriptor on the tab stop, price);
#       "s" spirit (name + price only)
# cocktail tokens: list of (text, letter_break_before, phone_break_before)
C = {
 "beta_margarita": [("tequila blanco", 0, 0), ("fresh lime", 0, 0), ("orange liqueur", 0, 0), ("agave syrup", 0, 1), ("lime wheel", 1, 0), ("bright, citrus-forward", 0, 1)],
 "beta_manhattan": [("rye whiskey", 0, 0), ("sweet vermouth", 0, 0), ("cocktail cherry", 0, 0)],
 "beta_old_fashioned": [("brown butter-washed bourbon", 0, 0), ("house demerara syrup", 0, 0), ("aromatic bitters", 1, 1), ("orange peel", 0, 0)],
 "beta_daiquiri": [("white rum", 0, 0), ("fresh lime", 0, 0), ("house demerara syrup", 0, 0), ("lime coin", 1, 1)],
}
SRC = {
 "beta_margarita": "draft desc 'Tequila blanco, lime, orange liqueur, agave. Bright and citrus-forward.' (tasting note recast lower case: 'bright, citrus-forward'); components 'Fresh Lime Juice', 'Agave Syrup'; rv f06abb74 garnish 'Lime wheel'",
 "beta_manhattan": "draft component 'Rye Whiskey' (role Base spirit), 'Sweet Vermouth', 'Cocktail Cherry' (Garnish); aromatic bitters hidden per meta.public_components {'aromatic-bitters': false}; rv 9fb77eaa garnish 'Cocktail cherry'",
 "beta_old_fashioned": "draft components 'Brown Butter-Washed Bourbon' (kind prep), 'Demerara Syrup' (kind prep, role 'House prep / sweetener' -> 'house demerara syrup'), 'Aromatic Bitters'; rv 7095fd3d garnish 'Orange peel'",
 "beta_daiquiri": "draft desc 'White rum, lime, and house demerara syrup.'; component 'Demerara Syrup' (kind prep, role 'House prep', notes 'House 1:1 demerara syrup by weight.'); 'Fresh Lime Juice'; rv 14d45e57 garnish 'Lime coin'",
 "beta_czech_pilsner": "draft desc 'Crisp pale lager.'", "beta_dry_hopped_ipa": "draft desc 'Hop-forward draft IPA.' ('draft' dropped: it repeats the De Barril · Draft subhead)",
 "beta_amber_lager": "draft desc 'Toasty amber lager.'", "beta_dry_cider": "draft desc 'Dry sparkling cider.'",
 "beta_malbec": "draft desc 'Dry red wine.'", "beta_pinot_grigio": "draft desc 'Dry white wine.'", "beta_brut_rose": "draft desc 'Dry sparkling rosé.'",
 "beta_blanco_tequila": "name + price only (draft desc 'Blanco tequila pour.' only repeats the name)",
 "beta_anejo_tequila": "name + price only (draft desc 'Añejo tequila pour.' only repeats the name)",
 "beta_cognac_vsop": "name + price only (draft desc 'VSOP Cognac pour.' only repeats the name)"}
R = {"beta_czech_pilsner": "crisp pale lager", "beta_dry_hopped_ipa": "hop-forward IPA", "beta_amber_lager": "toasty amber lager",
     "beta_dry_cider": "dry sparkling cider", "beta_malbec": "dry red wine", "beta_pinot_grigio": "dry white wine", "beta_brut_rose": "dry sparkling rosé"}
SPIRITS = ["beta_blanco_tequila", "beta_anejo_tequila", "beta_cognac_vsop"]
KIND = {**{k: "c" for k in C}, **{k: "r" for k in R}, **{k: "s" for k in SPIRITS}}
# glassware, phg.recipe_versions (gateway log_id 248)
GLASS = {"beta_margarita": ("Rocks", "rv f06abb74 glassware 'Rocks'"), "beta_manhattan": ("Coupe", "rv 9fb77eaa glassware 'Coupe'"),
         "beta_daiquiri": ("Coupe", "rv 14d45e57 glassware 'Coupe'"), "beta_old_fashioned": ("Rocks", "rv 7095fd3d glassware 'Rocks'")}
# bilingual heads: Spanish italic, English roman, same ink and weight
H2 = {"sec_cocktails": ("Cócteles", "Cocktails"), "sec_beer": ("Cerveza y Sidra", "Beer &amp; Cider"),
      "sec_wine": ("Vino", "Wine"), "sec_spirits": ("Destilados", "Spirits")}
H3 = {"sub_cocktails_classics": ("Clásicos", "Classics"), "sub_cocktails_house_originals": ("De la Casa", "House"),
      "sub_beer_draft": ("De Barril", "Draft"), "sec_cider": ("Sidra", "Cider"), "sub_wine_by_the_glass": ("Por Copa", "By the Glass"),
      "sub_wine_sparkling": ("Espumosos", "Sparkling"), "sub_spirits_agave": ("Destilados de agave", "Agave"), "sub_spirits_brandy": ("Brandy", "Brandy")}
ALLERGY = "Please tell your server about any allergies."
plain = lambda s: s.replace("&amp;", "&")

items = {}
def walk(s):
    for i in s.get("items", []): items[i["id"]] = i
    for sb in s.get("subs", []): walk(sb)
for s in draft["sections"]: walk(s)
assert set(items) == set(KIND), set(items) ^ set(KIND)

def printed_desc(iid):
    k = KIND[iid]
    if k == "c": return " · ".join(t for t, _, _ in C[iid]) + " " + GLASS[iid][0].upper()
    if k == "r": return R[iid]
    return ""

# ---------------------------------------------------------------- doc.json (ids, prices, structure kept)
doc = copy.deepcopy(draft)
doc["title"] = "Cantina & Cocktail Bar"; doc["subtitle"] = "Iowa City, Iowa"
order = ["sec_cocktails", "sec_beer", "sec_cider", "sec_wine", "sec_spirits"]
doc["sections"] = sorted(doc["sections"], key=lambda s: order.index(s["id"]))
def fix(s):
    for i in s.get("items", []):
        i["desc"] = printed_desc(i["id"])
        if i["id"] in GLASS: i.setdefault("meta", {})["serve_glass"] = GLASS[i["id"]][0]
    for sb in s.get("subs", []):
        if sb["id"] in H3: sb["name"] = " · ".join(H3[sb["id"]])
        fix(sb)
for s in doc["sections"]:
    fix(s)
    if s["id"] in H2: s["name"] = plain(" · ".join(H2[s["id"]]))
    if s["id"] == "sec_cider": s["name"] = " · ".join(H3["sec_cider"]); s.setdefault("meta", {})["printed_under"] = "sec_beer"
    if s["id"] == "sec_cocktails":
        s["subs"][0]["items"].sort(key=lambda i: i["id"] != "beta_margarita")
        s["subs"][1]["items"].sort(key=lambda i: i["id"] != "beta_old_fashioned")
MISSING = {
 "beta_margarita": [], "beta_manhattan": ["aromatic bitters display (needs_input 11)"], "beta_daiquiri": [],
 "beta_old_fashioned": ["dairy allergen confirmation (brown butter)"],
 "beta_czech_pilsner": ["brewery", "ABV", "pour size"], "beta_dry_hopped_ipa": ["brewery", "ABV", "pour size"], "beta_amber_lager": ["brewery", "ABV", "pour size"],
 "beta_dry_cider": ["producer", "ABV", "format (draft/can/bottle)"],
 "beta_malbec": ["producer", "region", "vintage", "pour size"], "beta_pinot_grigio": ["producer", "region", "vintage", "pour size"],
 "beta_brut_rose": ["producer", "region", "vintage", "price label: glass or bottle"],
 "beta_blanco_tequila": ["brand", "age statement", "pour size"], "beta_anejo_tequila": ["brand", "age statement", "pour size"], "beta_cognac_vsop": ["brand", "pour size"]}
def meta(s):
    for i in s.get("items", []): i.setdefault("meta", {})["missing"] = MISSING[i["id"]]
    for sb in s.get("subs", []): meta(sb)
for s in doc["sections"]: meta(s)
doc.setdefault("meta", {})["designer_notes"] = {"round": 20, "concept": "Sun Behind the Page, landed in Iowa",
    "copy_sources": SRC, "glass_sources": {k: v[1] for k, v in GLASS.items()}, "legal_line": ALLERGY, "taglines": "none",
    "omitted": {"Junmai Ginjo": "phg.menu_items status='retired' (gateway log_id 258); not in draft rev 3"}}
OUT.mkdir(exist_ok=True)
(OUT / "doc.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))

def P(i): return str(int(i["prices"][0]["value"])) if float(i["prices"][0]["value"]).is_integer() else str(i["prices"][0]["value"])
# ---------------------------------------------------------------- ART layer (SVG, pt units; bleed 9pt = 3.175 mm)
# One grammar (round 17): flat cut-paper planes, torn edges with a cream fibre rim, one light from top right (shadows down-left),
# no outlines. Round 20: the landscape is Iowa - rounded loess bluffs behind, contour strip-cropped field rows in front that
# bow down around the agave and frame it. One grain: the same paper-fibre overlay on every shape (the sun's speckle is gone).
PAL = dict(paper="#F2E9D6", sky0="#F1DEC2", sky1="#E7B893", sky2="#CF7F55", hill1="#B5532F", hill2="#7C3322",
           leafA="#2E5A4B", leafB="#3F7362", leafC="#244A3E", leafD="#56866F", ground="#162C25", ink="#1D1815")
ROWS = ["#27463A", "#8E4A2B", "#1D382E", "#7C3322", "#162C25", "#6A2B1C", "#10221C"]  # alternating crop (green) / soil strips

A, B, C_, D = PAL["leafA"], PAL["leafB"], PAL["leafC"], PAL["leafD"]
def leaf2(bx, by, ang, L, W, cl, cr, bend):
    """broad agave leaf, widest near the base, sharp tip; folded along the midrib (two tones)."""
    a = math.radians(ang); ux, uy = math.sin(a), -math.cos(a); px, py = -uy, ux
    P_ = lambda t, o: (bx + ux * L * t + px * (o + bend * L * t * t), by + uy * L * t + py * (o + bend * L * t * t))
    tip = P_(1, 0); q = lambda v: f"{v[0]:.1f},{v[1]:.1f}"
    l1, l2 = P_(.22, -W * .5), P_(.62, -W * .30); r1, r2 = P_(.22, W * .5), P_(.62, W * .30)
    m1, m2 = P_(.35, 0), P_(.75, 0)
    left = f"M{q(P_(0,-W*.42))} C{q(l1)} {q(l2)} {q(tip)} C{q(m2)} {q(m1)} {q(P_(0,0))} Z"
    right = f"M{q(P_(0,W*.42))} C{q(r1)} {q(r2)} {q(tip)} C{q(m2)} {q(m1)} {q(P_(0,0))} Z"
    return f'<path d="{left}" fill="{cl}"/><path d="{right}" fill="{cr}"/>'
LEAVES = [  # (base x, angle, length, width, left tone, right tone, bend) - round-17 rosette
    (40, -58, 250, 58, D, B, -.10), (118, 64, 230, 54, B, A, .10), (52, -34, 360, 66, B, A, -.08),
    (100, 38, 330, 62, D, B, .09), (62, -14, 470, 72, D, B, -.04), (86, 16, 430, 70, B, C_, .06),
    (74, 2, 360, 60, A, C_, .03), (30, -74, 170, 50, B, A, -.12), (128, 80, 170, 48, D, B, .10)]
def rosette(cx, by, k):
    return "".join(leaf2(cx + (bx - 79) * k, by, a, L * k, W * k, cl, cr, bd) for bx, a, L, W, cl, cr, bd in LEAVES)

def bluff(base, ridges, seed, x0, x1, bottom):
    """rounded loess ridgeline: sum of steep rounded crests, torn jitter; closed down to `bottom`."""
    rnd = random.Random(seed); pts = []; x = x0
    while x <= x1 + 6:
        y = base - sum(h * math.exp(-((x - c) / w) ** 2) for c, h, w in ridges) + rnd.uniform(-1.2, 1.2)
        pts.append((x, y)); x += 5
    return "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f" L{x1 + 6},{bottom} L{x0},{bottom} Z"

def row(top, A_, cx, w, seed, x0, x1, bottom, amp=1.4):
    """one contour strip: its top edge bows down at cx (bowl) and rises toward both edges."""
    rnd = random.Random(seed); pts = []; x = x0
    while x <= x1 + 6:
        pts.append((x, top - A_ * ((x - cx) / w) ** 2 + math.sin(x / 23 + seed) * amp + rnd.uniform(-amp, amp) * .5)); x += 5
    return "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f" L{x1 + 6},{bottom} L{x0},{bottom} Z"

def torn_paper_top(y, amp, seed, x0, x1, top):
    """paper sheet from `top` down to a torn edge near y (used for the phone seam and footer)."""
    rnd = random.Random(seed); pts = []; x = x1 + 6
    while x >= x0 - 6:
        pts.append((x, y + math.sin(x / 29 + seed) * amp + rnd.uniform(-amp * .5, amp * .5))); x -= 5
    return f"M{x0 - 6},{top} L{x1 + 6},{top} L" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + " Z"

def page_edge(seed=5):
    rnd = random.Random(seed); pts = []; y = -9
    while y <= 801:
        pts.append((158 + math.sin(y / 61) * 7 + math.sin(y / 17 + 2) * 2.5 + rnd.uniform(-1.6, 1.6), y)); y += 6
    return "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + " L640,801 L640,-9 Z"

def defs(p, fiber_freq=.8):
    return f'''<defs>
  <linearGradient id="{p}sky" x1="0" y1="0" x2="0" y2="1">
   <stop offset="0" stop-color="{PAL['sky0']}"/><stop offset=".30" stop-color="{PAL['sky0']}"/>
   <stop offset=".55" stop-color="{PAL['sky1']}"/><stop offset=".78" stop-color="{PAL['sky2']}"/></linearGradient>
  <radialGradient id="{p}gold" cx=".38" cy=".32" r=".8"><stop offset="0" stop-color="#E2BC62"/><stop offset=".6" stop-color="#D0A044"/><stop offset="1" stop-color="#C38F34"/></radialGradient>
  <filter id="{p}rim" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".09" numOctaves="4" seed="11"/>
   <feDisplacementMap in="SourceGraphic" scale="9"/></filter>
  <filter id="{p}cut" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="3" seed="7"/>
   <feDisplacementMap in="SourceGraphic" scale="3.2" result="d"/>
   <feDropShadow in="d" dx="-1.6" dy="2.4" stdDeviation="1.6" flood-color="#1B120C" flood-opacity=".38"/></filter>
  <filter id="{p}leaf" x="-60%" y="-10%" width="220%" height="120%"><feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="3" seed="9"/>
   <feDisplacementMap in="SourceGraphic" scale="2.6" result="d"/>
   <feDropShadow in="d" dx="-2" dy="3" stdDeviation="2" flood-color="#0C1A15" flood-opacity=".45"/></filter>
  <filter id="{p}disc" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="3" seed="13"/>
   <feDisplacementMap in="SourceGraphic" scale="2.4"/></filter>
  <filter id="{p}fiber" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="{fiber_freq}" numOctaves="3" seed="4" result="n"/>
   <feColorMatrix in="n" type="matrix" values="0 0 0 0 .22  0 0 0 0 .16  0 0 0 0 .10  0 0 0 -1.4 .95"/></filter>
  <filter id="{p}shadowL" x="-10%" y="-2%" width="120%" height="104%"><feDropShadow dx="-2" dy="2.5" stdDeviation="2.2" flood-color="#1B120C" flood-opacity=".42"/></filter>
  <filter id="{p}shadowU" x="-2%" y="-20%" width="104%" height="160%"><feDropShadow dx="-1.5" dy="2.5" stdDeviation="2" flood-color="#1B120C" flood-opacity=".35"/></filter>
 </defs>'''

def landscape(p, x0, x1, bluff_base, bluff_scale, rows_top, rows_cx, rows_w, row_step, row_A, leaves, bottom):
    """bluffs (back) -> agave -> contour rows (front), all in one cut-paper grammar."""
    s = bluff_scale
    b1 = bluff(bluff_base, [(x0 + (x1 - x0) * .10, 58 * s, 42 * s), (x0 + (x1 - x0) * .52, 74 * s, 46 * s), (x0 + (x1 - x0) * .92, 46 * s, 36 * s)], 1, x0, x1, bottom)
    b2 = bluff(bluff_base + 44 * s, [(x0 + (x1 - x0) * .0, 42 * s, 44 * s), (x0 + (x1 - x0) * .36, 52 * s, 38 * s), (x0 + (x1 - x0) * .74, 62 * s, 40 * s)], 2, x0, x1, bottom)
    out = [f'<g filter="url(#{p}cut)"><path d="{b1}" fill="{PAL["hill1"]}"/></g>',
           f'<g filter="url(#{p}rim)"><path d="{b2}" fill="{PAL["paper"]}" transform="translate(0,-2.5)"/></g>',
           f'<g filter="url(#{p}cut)"><path d="{b2}" fill="{PAL["hill2"]}"/></g>',
           f'<g filter="url(#{p}leaf)">{leaves}</g>']
    for k, col in enumerate(ROWS):
        d = row(rows_top + k * row_step, row_A * (1 - .1 * k), rows_cx, rows_w, 20 + k, x0, x1, bottom)
        out.append(f'<g filter="url(#{p}rim)"><path d="{d}" fill="{PAL["paper"]}" transform="translate(0,-2.4)"/></g>')
        out.append(f'<g filter="url(#{p}cut)"><path d="{d}" fill="{col}"/></g>')
    return "".join(out)

EDGE = page_edge()
ART = f'''
<svg class="art print" viewBox="-9 -9 630 810" preserveAspectRatio="xMinYMin slice" aria-hidden="true">
 {defs("l_")}
 <clipPath id="l_railclip"><rect x="-9" y="-9" width="200" height="810"/></clipPath>
 <g clip-path="url(#l_railclip)">
  <rect x="-9" y="-9" width="200" height="810" fill="url(#l_sky)"/>
  <circle cx="104" cy="286" r="104" fill="url(#l_gold)" filter="url(#l_disc)"/>
  {landscape("l_", -9, 191, 492, 1.0, 646, 80, 96, 23, 60, rosette(79, 740, 1.0), 801)}
  <rect x="-9" y="-9" width="200" height="810" filter="url(#l_fiber)" opacity=".55"/>
 </g>
 <g filter="url(#l_rim)"><path d="{EDGE}" fill="#FBF6EA" transform="translate(-3.2,0)"/></g>
 <path d="{EDGE}" fill="{PAL['paper']}" filter="url(#l_shadowL)"/>
 <rect x="150" y="-9" width="490" height="810" filter="url(#l_fiber)" opacity=".10"/>
</svg>'''

# phone hero, 390 x 416 css px: the full sun behind a torn seam, the rosette rising from the strips, a torn edge into the text
PHONE_HERO = f'''
<svg class="art phone hero" viewBox="0 0 390 416" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
 {defs("h_", .9)}
 <rect x="-6" y="-6" width="402" height="428" fill="url(#h_sky)"/>
 <circle cx="195" cy="150" r="100" fill="url(#h_gold)" filter="url(#h_disc)"/>
 {landscape("h_", -6, 396, 300, .78, 342, 195, 175, 15, 46, rosette(195, 470, .66), 430)}
 <rect x="-6" y="-6" width="402" height="428" filter="url(#h_fiber)" opacity=".5"/>
 <g filter="url(#h_rim)"><path d="{torn_paper_top(402, 3, 7, 0, 390, 440).replace('M-6,440 L396,440', 'M-6,440 L396,440')}" fill="#FBF6EA" transform="translate(0,-3)"/></g>
</svg>'''
PHONE_HERO = PHONE_HERO.replace("</svg>", f'<path d="{torn_paper_top(402, 3, 7, 0, 390, 440)}" fill="{PAL["paper"]}" filter="url(#h_shadowU)"/></svg>')
# phone footer, 390 x 96: the page tears open onto the contour strips
PHONE_FOOT = f'''
<svg class="art phone foot" viewBox="0 0 390 96" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
 {defs("f_", .9)}
 <rect x="-6" y="-6" width="402" height="108" fill="{ROWS[0]}"/>
 {"".join(f'<g filter="url(#f_rim)"><path d="{row(18 + k * 13, 16, 195, 190, 40 + k, -6, 396, 110, 1.1)}" fill="{PAL["paper"]}" transform="translate(0,-2.2)"/></g><g filter="url(#f_cut)"><path d="{row(18 + k * 13, 16, 195, 190, 40 + k, -6, 396, 110, 1.1)}" fill="{c}"/></g>' for k, c in enumerate(ROWS))}
 <rect x="-6" y="-6" width="402" height="108" filter="url(#f_fiber)" opacity=".5"/>
 <g filter="url(#f_rim)"><path d="{torn_paper_top(20, 3, 9, 0, 390, -10)}" fill="#FBF6EA" transform="translate(0,2.6)"/></g>
 <path d="{torn_paper_top(20, 3, 9, 0, 390, -10)}" fill="{PAL['paper']}" filter="url(#f_shadowU)"/>
</svg>'''
# ---------------------------------------------------------------- TEXT layer
nb = lambda t: t.replace(" ", "&nbsp;")
def ingredients(iid):
    out = []
    for n, (t, lb, pb) in enumerate(C[iid]):
        if n:
            if lb and pb: out.append("<br>")
            elif lb: out.append('<br class="bl"><span class="sepp">&nbsp;· </span>')
            elif pb: out.append('<span class="sepl">&nbsp;· </span><br class="bp">')
            else: out.append("&nbsp;· ")
        out.append(nb(t))
    return "".join(out) + f'<span class="glass tx">&thinsp;{GLASS[iid][0]}</span>'

def item(i):
    k = KIND[i["id"]]; nm = f'<span class="name tx">{i["name"]}</span>'; pr = f'<span class="price tx">{P(i)}</span>'
    if k == "r":
        return f'<div class="item r" data-ref="{i["id"]}"><div class="row">{nm}<span class="dl tx">{R[i["id"]]}</span>{pr}</div></div>'
    if k == "s":
        return f'<div class="item s" data-ref="{i["id"]}"><div class="row">{nm}{pr}</div></div>'
    return f'<div class="item c" data-ref="{i["id"]}"><div class="row">{nm}{pr}</div><div class="desc tx">{ingredients(i["id"])}</div></div>'

def lab(pair):
    es, en = pair
    return f'<span class="es">{es}</span><span class="sep"> · </span><span class="en">{en}</span>'
def sub(sid, its):
    return f'<div class="sub" data-id="{sid}"><h3 class="tx">{lab(H3[sid])}</h3>' + "".join(item(i) for i in its) + "</div>"
def head(sid):
    return f'<div class="hrow" data-id="{sid}"><h2 class="tx">{lab(H2[sid])}</h2></div>'

S = {s["id"]: s for s in doc["sections"]}
ck = S["sec_cocktails"]; be = S["sec_beer"]; ci = S["sec_cider"]; wi = S["sec_wine"]; sp = S["sec_spirits"]
MENU = (
 f'<section class="sec" data-id="sec_cocktails">{head("sec_cocktails")}' + "".join(sub(sb["id"], sb["items"]) for sb in ck["subs"]) + "</section>"
 + f'<section class="sec" data-id="sec_beer+sec_cider">{head("sec_beer")}' + sub(be["subs"][0]["id"], be["subs"][0]["items"]) + sub("sec_cider", ci["items"]) + "</section>"
 + f'<section class="sec" data-id="sec_wine">{head("sec_wine")}' + "".join(sub(sb["id"], sb["items"]) for sb in wi["subs"]) + "</section>"
 + f'<section class="sec" data-id="sec_spirits">{head("sec_spirits")}' + "".join(sub(sb["id"], sb["items"]) for sb in sp["subs"]) + "</section>"
 + f'<p class="legal tx">{ALLERGY}</p>')

U = 7  # letter baseline unit, pt
Y0 = 35.0; WM_TOP = 33.12; AXIS = 224.5  # tuned from the render (cap alignment, wordmark axis)
CSS = f"""
@font-face {{font-family:'Fraunces';src:url('{FONTS}/fraunces.woff2') format('woff2');font-weight:300 900;font-style:normal;font-display:block}}
@font-face {{font-family:'Fraunces';src:url('{FONTS}/fraunces-i.woff2') format('woff2');font-weight:300 900;font-style:italic;font-display:block}}
@font-face {{font-family:'DM Sans';src:url('{FONTS}/dmsans.woff2') format('woff2');font-weight:100 1000;font-style:normal;font-display:block}}
@font-face {{font-family:'DM Sans';src:url('{FONTS}/dmsans-i.woff2') format('woff2');font-weight:100 1000;font-style:italic;font-display:block}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:#fff}}
.page{{position:relative;width:612pt;height:792pt;overflow:hidden;background:{PAL['paper']};color:{PAL['ink']};
  font-family:'Fraunces',serif;font-variant-numeric:lining-nums tabular-nums;-webkit-print-color-adjust:exact}}
.art.print{{position:absolute;left:-9pt;top:-9pt;width:630pt;height:810pt}}
.art.phone{{display:none}}
.wm .big{{position:absolute;left:{AXIS}pt;top:{WM_TOP}pt;transform:translateX(-50%);writing-mode:vertical-rl;font-weight:380;font-size:96pt;line-height:74pt;letter-spacing:.075em;
  font-variation-settings:'opsz' 144, 'SOFT' 0, 'WONK' 0;color:{PAL['ink']};white-space:nowrap}}
.wm .rl{{position:absolute;left:{AXIS}pt;bottom:36pt;transform:translateX(-50%);writing-mode:vertical-rl;font:500 8pt/12pt 'DM Sans',sans-serif;letter-spacing:.42em;color:#6E2F1D;white-space:nowrap}}
.menu{{position:absolute;left:282pt;top:{Y0}pt;width:294pt;height:{103 * U}pt;display:flex;flex-direction:column}}
.sec+.sec{{margin-top:{3 * U}pt}}
.hrow{{height:{4 * U}pt;border-bottom:.75pt solid #6B5A4C;margin-bottom:{U}pt}}
h2{{font-weight:600;font-size:17pt;line-height:{3 * U}pt;white-space:nowrap;font-variation-settings:'opsz' 36}}
h2 .es,h3 .es{{font-style:italic}} h2 .sep,h3 .sep{{font-style:normal}}
h3{{font:700 9pt/{2 * U}pt 'DM Sans',sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#9A3B22;white-space:nowrap}}
.sub+.sub{{margin-top:{U}pt}}
.item+.item{{margin-top:{U}pt}}
.row{{display:flex;align-items:baseline;height:{2 * U}pt;white-space:nowrap}}
.name{{font-weight:600;font-size:11pt;line-height:{2 * U}pt;font-variation-settings:'opsz' 14}}
.item.r .name{{flex:none;width:94pt}}
.dl{{font-weight:400;font-size:10.5pt;line-height:{2 * U}pt;color:#40352D;font-variation-settings:'opsz' 12}}
.price{{font-weight:500;font-size:11pt;line-height:{2 * U}pt;color:#5A4B3F;margin-left:1em}}
.desc{{font-weight:400;font-size:10.5pt;line-height:{2 * U}pt;color:#40352D;font-variation-settings:'opsz' 12}}
.glass{{font:600 9pt/1 'DM Sans',sans-serif;letter-spacing:.1em;text-transform:uppercase;color:#40352D;white-space:nowrap}}
.bp,.sepp{{display:none}}
.legal{{margin-top:auto;font-style:italic;font-weight:400;font-size:9.5pt;line-height:{2 * U}pt;color:#4F4238}}
/* phone: one reading column on an 8 px grid; own hero and footer art */
@media (max-width:600px){{
 .page{{width:100%;height:auto;overflow:visible}}
 .art.print{{display:none}}
 .art.phone{{display:block;width:100%}}
 .art.hero{{height:416px}} .art.foot{{height:96px;margin-top:40px}}
 .wm{{padding:16px 24px 0}}
 .wm .big,.wm .rl{{position:static;transform:none;writing-mode:horizontal-tb}}
 .wm .big{{font-size:56px;line-height:64px;letter-spacing:.06em}}
 .wm .rl{{font-size:12px;line-height:16px;letter-spacing:.3em}}
 .menu{{position:static;width:auto;height:auto;display:block;padding:0 24px}}
 .sec{{margin-top:40px}} .sec+.sec{{margin-top:40px}}
 .hrow{{height:auto;padding-bottom:7px;border-bottom-width:1px;margin-bottom:16px}}
 h2{{font-size:24px;line-height:32px;white-space:normal}}
 h2 .es,h2 .en{{display:block}} h2 .sep{{display:none}}
 h3{{font-size:12px;line-height:16px;margin-bottom:8px;white-space:normal}}
 .sub+.sub{{margin-top:24px}}
 .item+.item{{margin-top:16px}}
 .row{{height:24px}}
 .name{{font-size:16px;line-height:24px}}
 .item.r .name{{width:128px}}
 .dl{{font-size:15px;line-height:24px}}
 .price{{font-size:16px;line-height:24px}}
 .desc{{font-size:15px;line-height:24px}}
 .glass{{font-size:12px}}
 .bl,.sepl{{display:none}} .bp{{display:inline}} .sepp{{display:inline}}
 .legal{{margin-top:40px;font-size:14px;line-height:24px}}
}}
"""
HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cantina &amp; Cocktail Bar · Iowa City, Iowa</title><style>{CSS}</style></head><body>
<div class="page">
{ART}
{PHONE_HERO}
<div class="wm"><div class="big tx">CANTINA</div><div class="rl tx">&amp; COCKTAIL BAR&#8195;·&#8195;IOWA CITY, IOWA</div></div>
<main class="menu">{MENU}</main>
{PHONE_FOOT}
</div></body></html>"""
(OUT / "menu.html").write_text(HTML)
print("ok", len(HTML))
