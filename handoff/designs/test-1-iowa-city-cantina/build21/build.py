"""TEST-1 round 21: round-20b page (art, palette, wordmark, 7 pt unit) with ONE item grammar on every row:
name + price (1 em) / italic sensory line (menu_description, Newsreader italic) / ingredients by role / garnish · glass.
Writes ../round-21/doc.json and ../round-21/menu.html."""
import json, copy, math, pathlib, random

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "round-21"
FONTS = (HERE.parent / "build" / "fonts").resolve()
FONTS21 = (HERE / "fonts").resolve()   # Newsreader italic (OFL, fonts.gstatic.com latin subset): plain 'l' for every italic role
draft = json.loads((HERE.parent / "build" / "draft_doc.json").read_text())

# ---------------------------------------------------------------- copy (every word traced)
# phg.menu_items.menu_description (gateway log_id 266), verbatim minus the trailing period and minus a trailing class noun
# only where it repeats the item name (Coordinator rule, round 21)
MD = {"beta_margarita": "Tequila blanco, lime, orange liqueur, agave. Bright and citrus-forward.",
      "beta_czech_pilsner": "Crisp pale lager.", "beta_dry_hopped_ipa": "Hop-forward draft IPA.", "beta_amber_lager": "Toasty amber lager.",
      "beta_dry_cider": "Dry sparkling cider.", "beta_malbec": "Dry red wine.", "beta_pinot_grigio": "Dry white wine.", "beta_brut_rose": "Dry sparkling rosé."}
SD = {  # printed sensory line, trim note
 "beta_margarita": ("Bright and citrus-forward", "second sentence of the menu_description, verbatim; period dropped (the first sentence is the ingredient list, printed below by role)"),
 "beta_czech_pilsner": ("Crisp pale lager", "verbatim; period dropped; 'lager' kept (not in the name)"),
 "beta_dry_hopped_ipa": ("Hop-forward, draft", "trailing 'IPA' repeats the name: dropped; comma joins the remaining words (Coordinator example)"),
 "beta_amber_lager": ("Toasty", "trailing 'amber lager' repeats the name: dropped (Coordinator example)"),
 "beta_dry_cider": ("Dry, sparkling", "trailing 'cider' repeats the name: dropped; comma joins the remaining words (same pattern as the Brut Rosé example)"),
 "beta_malbec": ("Dry red wine", "verbatim; period dropped; 'wine' kept (not in the name)"),
 "beta_pinot_grigio": ("Dry white wine", "verbatim; period dropped; 'wine' kept (not in the name)"),
 "beta_brut_rose": ("Dry, sparkling", "trailing 'rosé' repeats the name: dropped; comma joins the remaining words (Coordinator example)"),
}
# phg.recipe_versions.ingredients (gateway log_id 259): (name, role) in recipe order; garnish from rv.garnish
RV = {
 "beta_margarita": ("f06abb74", [("Tequila Blanco", "Base spirit"), ("Fresh Lime Juice", "Citrus"), ("Orange Liqueur", "Liqueur"), ("Agave Syrup", "Sweetener")], "Lime wheel"),
 "beta_manhattan": ("9fb77eaa", [("Rye Whiskey", "Base spirit"), ("Sweet Vermouth", "Fortified wine"), ("Aromatic Bitters", "Bitters"), ("Cocktail Cherry", "Garnish")], "Cocktail cherry"),
 "beta_daiquiri": ("14d45e57", [("White Rum", "Base spirit"), ("Fresh Lime Juice", "Citrus"), ("Demerara Syrup", "House prep")], "Lime coin"),
 "beta_old_fashioned": ("7095fd3d", [("Brown Butter-Washed Bourbon", "House prep / base spirit"), ("Demerara Syrup", "House prep / sweetener"), ("Aromatic Bitters", "Bitters")], "Orange peel"),
}
# Coordinator override (round 21): the Daiquiri's house demerara syrup is ranked as a sweetener (prints before the lime);
# the DB role is 'House prep' -> needs_input 13 asks Rob to confirm 'House prep / sweetener'
ROLE_OVERRIDE = {("beta_daiquiri", "Demerara Syrup"): "House prep / sweetener"}
ROLE_RANK = {"base spirit": 1, "liqueur": 2, "fortified wine": 2, "vermouth": 2, "modifier": 2, "sweetener": 3, "syrup": 3,
             "citrus": 4, "acid": 4, "bitters": 5, "soda": 6, "topper": 6}
def rank(role):
    return min(ROLE_RANK.get(r.strip().lower(), 7) for r in role.split("/"))
SHOW = {"Tequila Blanco": "tequila blanco", "Fresh Lime Juice": "fresh lime", "Orange Liqueur": "orange liqueur", "Agave Syrup": "agave syrup",
        "Rye Whiskey": "rye whiskey", "Sweet Vermouth": "sweet vermouth", "Aromatic Bitters": "aromatic bitters", "White Rum": "white rum",
        "Demerara Syrup": "house demerara syrup", "Brown Butter-Washed Bourbon": "brown butter-washed bourbon"}
HIDDEN = {"beta_manhattan": {"Aromatic Bitters"}}
# line breaks (letter, phone): a break keeps its "·" at the end of the line
BREAKS = {"beta_margarita": (set(), {"agave syrup"}), "beta_manhattan": (set(), set()),
          "beta_old_fashioned": ({"house demerara syrup"}, {"house demerara syrup"}), "beta_daiquiri": (set(), set())}
def ordered(iid):
    rows = [(n, ROLE_OVERRIDE.get((iid, n), r)) for n, r in RV[iid][1] if r.lower() != "garnish" and n not in HIDDEN.get(iid, set())]
    return [SHOW[n] for n, r in sorted(rows, key=lambda t: rank(t[1]))]
C = {k: [(t, t in BREAKS[k][0], t in BREAKS[k][1]) for t in ordered(k)] for k in RV}
GARNISH = {k: v[2] for k, v in RV.items()}
GLASS = {"beta_margarita": ("Rocks", "rv f06abb74 glassware 'Rocks'"), "beta_manhattan": ("Coupe", "rv 9fb77eaa glassware 'Coupe'"),
         "beta_daiquiri": ("Coupe", "rv 14d45e57 glassware 'Coupe'"), "beta_old_fashioned": ("Rocks", "rv 7095fd3d glassware 'Rocks'")}
SPIRITS = ["beta_blanco_tequila", "beta_anejo_tequila", "beta_cognac_vsop"]
KIND = {**{k: "c" for k in RV}, **{k: "r" for k in SD if k not in RV}, **{k: "s" for k in SPIRITS}}
SRC = {**{k: f"sensory line: {SD[k][1]}" for k in SD if k not in RV},
       "beta_margarita": "sensory line: " + SD["beta_margarita"][1] + "; ingredients: rv f06abb74 roles (log 259); garnish 'Lime wheel', glass 'Rocks'",
       "beta_manhattan": "rv 9fb77eaa roles (Base spirit, Fortified wine); bitters hidden (public_components); 'Cocktail Cherry' role Garnish -> serve line; glass 'Coupe'",
       "beta_old_fashioned": "rv 7095fd3d roles ('House prep / base spirit', 'House prep / sweetener', 'Bitters'); garnish 'Orange peel', glass 'Rocks'",
       "beta_daiquiri": "rv 14d45e57 roles (Base spirit, Citrus, 'House prep' ranked as sweetener by Coordinator override, needs_input 13); garnish 'Lime coin', glass 'Coupe'",
       **{k: "name + price only (menu_description '... pour.' only repeats the name)" for k in SPIRITS}}
# bilingual heads (Spanish sentence case; H3 duplicates removed)
H2 = {"sec_cocktails": ("Cócteles", "Cocktails"), "sec_beer": ("Cerveza y sidra", "Beer &amp; Cider"),
      "sec_wine": ("Vino", "Wine"), "sec_spirits": ("Destilados", "Spirits")}
H3 = {"sub_cocktails_classics": ("Clásicos", "Classics"), "sub_cocktails_house_originals": ("De la casa", "House"),
      "sub_beer_draft": ("De barril", "Draft"), "sec_cider": ("Sidra", "Cider"), "sub_wine_by_the_glass": ("Por copa", "By the Glass"),
      "sub_wine_sparkling": ("Espumosos", "Sparkling"), "sub_spirits_agave": ("De agave", "Agave"), "sub_spirits_brandy": (None, "Brandy")}
ALLERGY = "Please tell your server about any allergies."
plain = lambda s: s.replace("&amp;", "&")
def lab_plain(p): return " · ".join(x for x in p if x)

items = {}
def walk(s):
    for i in s.get("items", []): items[i["id"]] = i
    for sb in s.get("subs", []): walk(sb)
for s in draft["sections"]: walk(s)
assert set(items) == set(KIND), set(items) ^ set(KIND)

def printed_desc(iid):
    k = KIND[iid]; sd = SD[iid][0] if iid in SD else ""
    if k == "c": return (sd + ". " if sd else "") + " · ".join(t for t, _, _ in C[iid]) + ". " + GARNISH[iid].lower() + " · " + GLASS[iid][0].lower()
    return sd

# ---------------------------------------------------------------- doc.json (ids, prices, structure kept)
doc = copy.deepcopy(draft)
doc["title"] = "Cantina & Cocktail Bar"; doc["subtitle"] = "Iowa City, Iowa"
order = ["sec_cocktails", "sec_beer", "sec_cider", "sec_wine", "sec_spirits"]
doc["sections"] = sorted(doc["sections"], key=lambda s: order.index(s["id"]))
def fix(s):
    for i in s.get("items", []):
        i["desc"] = printed_desc(i["id"])
        if i["id"] in GLASS: i.setdefault("meta", {})["serve_glass"] = GLASS[i["id"]][0]; i["meta"]["serve_garnish"] = GARNISH[i["id"]]
    for sb in s.get("subs", []):
        if sb["id"] in H3: sb["name"] = lab_plain(H3[sb["id"]])
        fix(sb)
for s in doc["sections"]:
    fix(s)
    if s["id"] in H2: s["name"] = plain(" · ".join(H2[s["id"]]))
    if s["id"] == "sec_cider": s["name"] = lab_plain(H3["sec_cider"]); s.setdefault("meta", {})["printed_under"] = "sec_beer"
    if s["id"] == "sec_cocktails":
        s["subs"][0]["items"].sort(key=lambda i: i["id"] != "beta_margarita")
        s["subs"][1]["items"].sort(key=lambda i: i["id"] != "beta_old_fashioned")
MISSING = {
 "beta_margarita": [], "beta_manhattan": ["aromatic bitters display (needs_input 11)"],
 "beta_daiquiri": ["demerara syrup role: confirm 'House prep / sweetener' (needs_input 13; prints before the lime by Coordinator override)"],
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
doc.setdefault("meta", {})["designer_notes"] = {"round": 21, "concept": "Sun Behind the Page, landed in Iowa",
    "copy_sources": SRC, "sensory_trims": {k: {"menu_description": MD[k], "printed": v[0], "rule": v[1]} for k, v in SD.items()},
    "ingredient_order": {"role_rank": ROLE_RANK, "other": 7, "garnish": "serve line", "override": {"beta_daiquiri/Demerara Syrup": "ranked as sweetener (Coordinator, needs_input 13)"}, "source": "phg.recipe_versions.ingredients, gateway log_id 259"},
    "glass_sources": {k: v[1] for k, v in GLASS.items()}, "legal_line": ALLERGY, "taglines": "none",
    "omitted": {"Junmai Ginjo": "phg.menu_items status='retired' (gateway log_id 258, re-read log_id 266)"}}
OUT.mkdir(exist_ok=True)
(OUT / "doc.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))

def P(i): return str(int(i["prices"][0]["value"])) if float(i["prices"][0]["value"]).is_integer() else str(i["prices"][0]["value"])

# ---------------------------------------------------------------- ART layer (SVG, pt units; bleed 9pt = 3.175 mm)
# One grammar (round 17): flat cut-paper planes, torn edges with a cream fibre rim, one light from top right (shadows down-left),
# no outlines. Round 20: the landscape is Iowa - rounded loess bluffs behind, contour strip-cropped field rows in front that
# bow down around the agave and frame it. One grain: the same paper-fibre overlay on every shape (the sun's speckle is gone).
PAL = dict(paper="#F2E9D6", sky0="#F1DEC2", sky1="#E7B893", sky2="#CF7F55", hill1="#B5532F", hill2="#7C3322",
           leafA="#2E5A4B", leafB="#3F7362", leafC="#244A3E", leafD="#56866F", ground="#162C25", ink="#1D1815")
ROWS = ["#27463A", "#5E4636", "#1D382E", "#4A372B", "#132720"]  # alternating crop (green) / Iowa loam (desaturated brown) strips

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
  {landscape("l_", -9, 191, 500, .85, 646, 80, 96, 31, 60, rosette(79, 740, 1.0), 801)}
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
 {landscape("h_", -6, 396, 300, .78, 342, 195, 175, 20, 46, rosette(195, 452, .8), 430)}
 <rect x="-6" y="-6" width="402" height="428" filter="url(#h_fiber)" opacity=".5"/>
 <g filter="url(#h_rim)"><path d="{torn_paper_top(402, 3, 7, 0, 390, 440).replace('M-6,440 L396,440', 'M-6,440 L396,440')}" fill="#FBF6EA" transform="translate(0,-3)"/></g>
</svg>'''
PHONE_HERO = PHONE_HERO.replace("</svg>", f'<path d="{torn_paper_top(402, 3, 7, 0, 390, 440)}" fill="{PAL["paper"]}" filter="url(#h_shadowU)"/></svg>')
# phone footer, 390 x 96: the page tears open onto the contour strips
PHONE_FOOT = f'''
<svg class="art phone foot" viewBox="0 0 390 96" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
 {defs("f_", .9)}
 <rect x="-6" y="-6" width="402" height="108" fill="{ROWS[0]}"/>
 {"".join(f'<g filter="url(#f_rim)"><path d="{row(18 + k * 17, 16, 195, 190, 40 + k, -6, 396, 110, 1.1)}" fill="{PAL["paper"]}" transform="translate(0,-2.2)"/></g><g filter="url(#f_cut)"><path d="{row(18 + k * 17, 16, 195, 190, 40 + k, -6, 396, 110, 1.1)}" fill="{c}"/></g>' for k, c in enumerate(ROWS))}
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
            if lb and pb: out.append("&nbsp;·<br>")
            elif lb: out.append('&nbsp;·<br class="bl"><span class="sepp"> </span>')
            elif pb: out.append('&nbsp;·<br class="bp"><span class="sepl"> </span>')
            else: out.append("&nbsp;· ")
        out.append(nb(t))
    return "".join(out)

def item(i):
    iid = i["id"]; k = KIND[iid]
    row = f'<div class="row"><span class="name tx">{i["name"]}</span><span class="price tx">{P(i)}</span></div>'
    sd = f'<div class="sd tx">{SD[iid][0]}</div>' if iid in SD else ""
    if k == "c":
        body = (f'<div class="desc tx">{ingredients(iid)}</div>'
                f'<div class="slot tx"><span class="gar">{GARNISH[iid]}</span> · <span class="glass">{GLASS[iid][0]}</span></div>')
        return f'<div class="item c" data-ref="{iid}">{row}{sd}{body}</div>'
    return f'<div class="item {k}" data-ref="{iid}">{row}{sd}</div>'

def lab(pair):
    es, en = pair
    return (f'<span class="es">{es}</span><span class="sep"> · </span>' if es else "") + f'<span class="en">{en}</span>'
def sub(sid, its):
    return f'<div class="sub" data-id="{sid}"><h3 class="tx">{lab(H3[sid])}</h3>' + "".join(item(i) for i in its) + "</div>"
def head(sid):
    return f'<div class="hrow" data-id="{sid}"><h2 class="tx">{lab(H2[sid])}</h2></div>'

S = {s["id"]: s for s in doc["sections"]}
ck = S["sec_cocktails"]; be = S["sec_beer"]; ci = S["sec_cider"]; wi = S["sec_wine"]; sp = S["sec_spirits"]
MENU = (
 f'<section class="sec" data-id="sec_cocktails">{head("sec_cocktails")}' + "".join(sub(sb["id"], sb["items"]) for sb in ck["subs"]) + "</section>"
 + f'<section class="sec" data-id="sec_beer+sec_cider">{head("sec_beer")}<div class="pair in"><div class="half" data-id="sec_beer_l">' + sub(be["subs"][0]["id"], be["subs"][0]["items"]) + '</div><div class="half" data-id="sec_beer_r">' + sub("sec_cider", ci["items"]) + "</div></div></section>"
 + '<div class="pair">'
 + f'<section class="sec half" data-id="sec_wine">{head("sec_wine")}' + "".join(sub(sb["id"], sb["items"]) for sb in wi["subs"]) + "</section>"
 + f'<section class="sec half" data-id="sec_spirits">{head("sec_spirits")}' + "".join(sub(sb["id"], sb["items"]) for sb in sp["subs"]) + "</section>"
 + "</div>"
 + f'<p class="legal tx">{ALLERGY}</p>')

U = 7
Y0 = 31.88; WM_TOP = 33.12; AXIS = 224.5
GREEN = "#27463A"
CSS = f"""
@font-face {{font-family:'Fraunces';src:url('{FONTS}/fraunces.woff2') format('woff2');font-weight:300 900;font-style:normal;font-display:block}}
@font-face {{font-family:'NewsIt';src:url('{FONTS21}/Newsreader-italic-latin.woff2') format('woff2');font-weight:200 800;font-style:italic;font-display:block}}
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
.menu{{position:absolute;left:282pt;top:{Y0}pt;width:294pt;height:{104 * U}pt;display:flex;flex-direction:column}}
.menu>.sec+.sec,.menu>.pair{{margin-top:{5 * U}pt}}
.pair{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);column-gap:18pt}}
.hrow{{height:{4 * U}pt;border-bottom:.75pt solid #6B5A4C;margin-bottom:{U}pt}}
h2{{font-weight:600;font-size:16.5pt;line-height:{3 * U}pt;white-space:nowrap;font-variation-settings:'opsz' 36}}
h2 .es{{font-family:'NewsIt',serif;font-style:italic;font-weight:600}}
h3{{font:700 9pt/{2 * U}pt 'DM Sans',sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#9A3B22;white-space:nowrap}}
h3 .es{{font-style:italic}}
.sub+.sub{{margin-top:{U}pt}}
.item+.item{{margin-top:{U}pt}}
.item.c+.item.c{{margin-top:{2 * U}pt}}
.row{{display:flex;align-items:baseline;height:{2 * U}pt;white-space:nowrap}}
.name{{font-weight:600;font-size:11pt;line-height:{2 * U}pt;font-variation-settings:'opsz' 14}}
.price{{font-weight:600;font-size:11pt;line-height:{2 * U}pt;color:{GREEN};margin-left:1em}}
.sd{{font-family:'NewsIt',serif;font-style:italic;font-weight:400;font-size:11pt;line-height:{2 * U - 1.5}pt;padding-top:1.5pt;color:#5A4B3F}}
.desc{{font-weight:400;font-size:10.5pt;line-height:{2 * U}pt;color:#40352D;font-variation-settings:'opsz' 12}}
.slot{{font-weight:500;font-size:9pt;line-height:{2 * U}pt;letter-spacing:.06em;text-transform:uppercase;color:#40352D;font-variation-settings:'opsz' 9;line-height:{2 * U - .75}pt;padding-top:.75pt}}
.bp,.sepp{{display:none}}
.legal{{margin-top:auto;position:relative;top:-1.7pt;font-family:'NewsIt',serif;font-style:italic;font-weight:400;font-size:10pt;line-height:{2 * U}pt;color:#4F4238}}
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
 .sec,.menu>.sec+.sec,.menu>.pair,.pair .sec+.sec{{margin-top:40px}}
 .pair{{display:block}} .pair.in .half+.half{{margin-top:24px}}
 .hrow{{height:auto;padding-bottom:7px;border-bottom-width:1px;margin-bottom:16px}}
 h2{{font-size:24px;line-height:32px;white-space:normal}}
 h2 .es,h2 .en{{display:block}} h2 .sep{{display:none}}
 h3{{font-size:12px;line-height:16px;margin-bottom:8px;white-space:normal}}
 .sub+.sub{{margin-top:24px}}
 .item+.item{{margin-top:16px}} .item.c+.item.c{{margin-top:24px}}
 .row{{height:24px}}
 .name{{font-size:16px;line-height:24px}}
 .price{{font-size:16px;line-height:24px}}
 .sd{{font-size:16px;line-height:22px;padding-top:2px}}
 .desc{{font-size:15px;line-height:24px}}
 .slot{{font-size:12px;line-height:23px;padding-top:1px}}
 .bl,.sepl{{display:none}} .bp{{display:inline}} .sepp{{display:inline}}
 .legal{{margin-top:40px;top:0;font-size:15px;line-height:24px}}
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
