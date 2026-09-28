"""TEST-1 round 18: 'Where Agave Country Meets the Iowa Prairie at Dusk'.
One cut-paper grammar: a torn Iowa horizon (prairie hills, corn rows) and a Jalisco agave field share one perspective
and meet at a torn seam under a setting sun; CANTINA is cut from the same red paper with the sun behind its first A.
The menu then descends through torn paper strata from dusk light (Cocktails) to night (the closing ground band).
Writes ../round-18/doc.json and ../round-18/menu.html. Art = inline SVG (text-free); text = HTML + one SVG wordmark.
Pass 1 uses default strata positions; pass 2 reads measure.json (section boxes) so the torn strata sit in the gaps."""
import json, copy, math, pathlib, random

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "round-18"
FONTS = (HERE.parent / "build" / "fonts").resolve()
draft = json.loads((HERE.parent / "build" / "draft_doc.json").read_text())

# ---------------------------------------------------------------- copy (every word traced to the draft)
# (ingredient list, italic note, source). Spirits print NO description line (a 'per pour' label sits by the header).
LINE = {
 "beta_margarita": (["tequila blanco", "fresh lime", "orange liqueur", "agave syrup", "lime wheel"], "bright and citrus-forward",
   "draft desc 'Tequila blanco, lime, orange liqueur, agave. Bright and citrus-forward.'; components 'Fresh Lime Juice', 'Agave Syrup'; garnish 'Lime wheel' phg.recipe_versions f06abb74"),
 "beta_manhattan": (["rye", "sweet vermouth", "cocktail cherry"], None,
   "draft desc 'Rye, sweet vermouth, aromatic bitters.' with bitters hidden (meta.public_components {'aromatic-bitters': false}); component 'Cocktail Cherry' (Garnish); recipe_versions 9fb77eaa"),
 "beta_old_fashioned": (["brown butter-washed bourbon", "house demerara syrup", "aromatic bitters", "orange peel"], None,
   "draft components 'Brown Butter-Washed Bourbon' (prep), 'Demerara Syrup' (kind prep = house-made), 'Aromatic Bitters'; garnish 'Orange peel' phg.recipe_versions 7095fd3d"),
 "beta_daiquiri": (["white rum", "fresh lime", "house demerara syrup", "lime coin"], None,
   "draft desc 'White rum, lime, and house demerara syrup.'; component 'Fresh Lime Juice'; garnish 'Lime coin' phg.recipe_versions 14d45e57"),
 "beta_czech_pilsner": (["crisp pale lager"], None, "draft desc 'Crisp pale lager.'"),
 "beta_dry_hopped_ipa": (["hop-forward IPA"], None, "draft desc 'Hop-forward draft IPA.' ('draft' is carried by the De Barril / Draft subhead)"),
 "beta_amber_lager": (["toasty amber lager"], None, "draft desc 'Toasty amber lager.'"),
 "beta_dry_cider": (["dry sparkling cider"], None, "draft desc 'Dry sparkling cider.'"),
 "beta_malbec": (["dry red"], None, "draft desc 'Dry red wine.'"),
 "beta_pinot_grigio": (["dry white"], None, "draft desc 'Dry white wine.'"),
 "beta_brut_rose": (["dry sparkling rosé"], None, "draft desc 'Dry sparkling rosé.'"),
 "beta_blanco_tequila": ([], None, "no description line: draft desc 'Blanco tequila pour.' only repeats the name; brand, age and pour size requested"),
 "beta_anejo_tequila": ([], None, "no description line: draft desc 'Añejo tequila pour.' only repeats the name; brand, age and pour size requested"),
 "beta_cognac_vsop": ([], None, "no description line: draft desc 'VSOP Cognac pour.' only repeats the name; brand, age and pour size requested"),
}
MISSING = {"beta_czech_pilsner": ["abv", "producer"], "beta_dry_hopped_ipa": ["abv", "producer"], "beta_amber_lager": ["abv", "producer"],
           "beta_dry_cider": ["abv", "producer"], "beta_malbec": ["region", "producer", "pour_size"], "beta_pinot_grigio": ["region", "producer", "pour_size"],
           "beta_brut_rose": ["region", "producer", "pour_size", "price_label"], "beta_blanco_tequila": ["brand", "age", "pour_size"],
           "beta_anejo_tequila": ["brand", "age", "pour_size"], "beta_cognac_vsop": ["brand", "age", "pour_size"]}
# small set of Spanish display subheads (one idea each, correct accents); doc keeps the draft names
LABEL = {"sub_cocktails_house_originals": "De la Casa", "sub_cocktails_classics": "Clásicos", "sub_beer_draft": "De Barril", "sub_spirits_agave": "Agave"}
TAG = "¡salud!"   # the only italic tagline (generic toast, no item fact)

items = {}
def walk(s):
    for i in s.get("items", []): items[i["id"]] = i
    for sb in s.get("subs", []): walk(sb)
for s in draft["sections"]: walk(s)
assert set(items) == set(LINE), set(items) ^ set(LINE)

def desc_text(k):
    ing, note, _ = LINE[k]
    t = " · ".join(ing)
    return t + (f". {note[0].upper() + note[1:]}." if note else "")

# ---------------------------------------------------------------- doc.json (ids, prices, names kept)
doc = copy.deepcopy(draft)
doc["title"] = "Cantina & Cocktail Bar"; doc["subtitle"] = "Iowa City, Iowa"
order = ["sec_cocktails", "sec_spirits", "sec_beer", "sec_cider", "sec_wine"]
doc["sections"] = sorted(doc["sections"], key=lambda s: order.index(s["id"]))
def fix(s):
    for i in s.get("items", []):
        i["desc"] = desc_text(i["id"])
        i.setdefault("meta", {})
        if i["id"] in MISSING: i["meta"]["missing"] = MISSING[i["id"]]
    for sb in s.get("subs", []): fix(sb)
for s in doc["sections"]:
    fix(s)
    if s["id"] == "sec_cocktails":
        s["subs"].sort(key=lambda sb: sb["id"] != "sub_cocktails_house_originals")  # De la Casa leads (left column)
        for sb in s["subs"]:
            sb["items"].sort(key=lambda i: i["id"] not in ("beta_margarita", "beta_old_fashioned"))
doc.setdefault("meta", {})["designer_notes"] = {"round": 18, "concept": "Where agave country meets the Iowa prairie at dusk",
    "copy_sources": {k: v[2] for k, v in LINE.items()}, "display_labels": LABEL, "taglines": [TAG],
    "section_order": order, "venue_name": {"printed": "Cantina", "needs_input": True, "note": "draft title is 'Bar menu'; real venue name requested"},
    "omitted_rows": {"junmai_ginjo": "phg.menu_items 57617f46 ($12, 'Junmai Ginjo sake.') is not in the draft snapshot; left off pending the venue's decision"}}
OUT.mkdir(exist_ok=True)
(OUT / "doc.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
def P(i):
    v = float(i["prices"][0]["value"]); return str(int(v)) if v.is_integer() else f"{v:g}"

# ---------------------------------------------------------------- measured positions from pass 1 (for the strata)
MEAS = HERE / "measure.json"
secs = None
if MEAS.exists():
    m = json.loads(MEAS.read_text()); secs = m["M"].get("secboxes")
SEAM = 262
if secs:
    E1 = (secs["cocktails"]["bottom"] + secs["spirits"]["top"]) / 2
    E2 = (secs["spirits"]["bottom"] + secs["pair"]["top"]) / 2
    WINE_END = secs["wine_end"]; LEFT_END = secs["left_end"]
else:
    E1, E2, WINE_END, LEFT_END = 430, 540, 700, 756

# ---------------------------------------------------------------- ART layer (SVG, pt; bleed 9 pt = 3.175 mm)
PAL = dict(paper="#F2E9D6", sand="#EADBC1", tan="#E1CBA9", rim="#FBF6EA", ink="#1D1815", red="#6E2A1B", price="#7C3322",
           terra="#9A3B22", hill_far="#C9774E", hill="#A8472A", corn="#C99A45", corn2="#E0B865", cornG="#6F8A4A",
           agf="#4E7F6A", agf2="#3F6E5B", leafA="#2E5A4B", leafB="#3F7362", leafC="#244A3E", leafD="#56866F", night="#17262B")
X0, X1 = -9, 621

def scissor(pts, rnd, j=0.7):
    """scissor-cut look: resample into short straight facets with small irregular offsets."""
    out = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, int(L / rnd.uniform(5, 9)))
        for k in range(n):
            t = k / n; out.append((ax + (bx - ax) * t + rnd.uniform(-j, j), ay + (by - ay) * t + rnd.uniform(-j, j)))
    out.append(pts[-1]); return out
def fmt(pts): return " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)

def edge(yfn, seed, x0=X0, x1=X1, step=6, amp=1.8):
    rnd = random.Random(seed); pts = []; x = x0
    while x < x1:
        pts.append((x, yfn(x) + rnd.uniform(-amp, amp))); x += rnd.uniform(step * .6, step * 1.4)
    pts.append((x1, yfn(x1))); return pts
def layer(pts, fill, flt="cut", bottom=801, rim=True, rimdy=-2.2):
    d = "M" + fmt(pts) + f" L{pts[-1][0]:.1f},{bottom} L{pts[0][0]:.1f},{bottom} Z"
    s = f'<g filter="url(#rim)"><path d="{d}" fill="{PAL["rim"]}" transform="translate(0,{rimdy})"/></g>' if rim else ""
    return s + f'<g filter="url(#{flt})"><path d="{d}" fill="{fill}"/></g>'

def leaf(bx, by, ang, L, W, cl, cr, bend, seed):
    """broad agave leaf (widest near the base, sharp tip), folded on the midrib in two tones, cut as scissor facets."""
    rnd = random.Random(seed)
    a = math.radians(ang); ux, uy = math.sin(a), -math.cos(a); px, py = -uy, ux
    Pt = lambda t, o: (bx + ux * L * t + px * (o + bend * L * t * t), by + uy * L * t + py * (o + bend * L * t * t))
    def side(sg):
        ts = [i / 14 for i in range(15)]
        prof = lambda t: W * .5 * (1 - t) ** 0.85 * (0.8 + 0.6 * t * (1 - t))
        return [Pt(t, sg * prof(t)) for t in ts]
    mid = [Pt(t, 0) for t in [i / 14 for i in range(15)]]
    left = scissor(side(-1), rnd) + scissor(mid[::-1], rnd, .3)
    right = scissor(side(1), rnd) + scissor(mid[::-1], rnd, .3)
    rim = scissor(side(-1), rnd, .9) + scissor(side(1)[::-1], rnd, .9)
    return (f'<path d="M{fmt(rim)} Z" fill="{PAL["rim"]}" transform="translate(1.1,-1.3)" filter="url(#rim)" opacity=".85"/>'
            f'<g filter="url(#leaf)"><path d="M{fmt(left)} Z" fill="{cl}"/><path d="M{fmt(right)} Z" fill="{cr}"/></g>')

A_, B_, C_, D_ = PAL["leafA"], PAL["leafB"], PAL["leafC"], PAL["leafD"]
ROS_X, ROS_Y = 548, 272
LEAVES = [(-66, 118, 34, D_, B_, -.10), (66, 150, 34, B_, A_, .10), (-44, 158, 40, B_, A_, -.08), (44, 190, 40, D_, B_, .08),
          (-22, 215, 44, D_, B_, -.05), (24, 222, 44, B_, C_, .05), (-8, 245, 46, A_, C_, -.02), (9, 238, 46, D_, B_, .03),
          (-82, 96, 30, B_, A_, -.12), (82, 112, 30, D_, B_, .12)]
leaves_svg = "".join(leaf(ROS_X + (i % 3 - 1) * 5, ROS_Y, a, L, W, cl, cr, bd, 40 + i) for i, (a, L, W, cl, cr, bd) in enumerate(LEAVES))

SUN = dict(cx=118, cy=150, r=80)
VP = (SUN["cx"] + 30, 206)   # shared vanishing point: corn rows and agave rows converge under the sun
SEAM_X = lambda y: 372 + (y - 205) * 0.55   # torn seam where Iowa (left) meets agave country (right)

def rows(x0, x1, colours, seed, n):
    """field strips converging to VP (corn rows on the left, agave rows on the right), each strip cut as scissor facets."""
    rnd = random.Random(seed); out = []
    xs = [x0 + (x1 - x0) * k / n for k in range(n + 1)]
    for k in range(n):
        a, b = xs[k], xs[k + 1]
        pts = [(VP[0] + (a - VP[0]) * .04, VP[1] + 1), (VP[0] + (b - VP[0]) * .04, VP[1] + 1), (b, 300), (a, 300)]
        pts = scissor(pts + [pts[0]], rnd, .5)
        out.append(f'<path d="M{fmt(pts)} Z" fill="{colours[k % len(colours)]}"/>')
    return "".join(out)

# hills: long, gentle prairie swells (Iowa), torn tops
hill_far = edge(lambda x: 182 + 7 * math.sin(x / 95 + 1.2) + 3 * math.sin(x / 31), 3)
hill_near = edge(lambda x: 197 + 5 * math.sin(x / 70 + 2.6) + 2 * math.sin(x / 23), 5)
field_top = edge(lambda x: 206 + 1.5 * math.sin(x / 40), 8, step=5, amp=1.2)
seam_pts = scissor([(SEAM_X(200), 200), (SEAM_X(235), 235), (SEAM_X(300), 300)], random.Random(12), 1.6)
corn_clip = f'M{X0},200 L{fmt(seam_pts)} L{X0},300 Z'
agave_clip = f'M{X1},200 L{fmt(seam_pts)} L{X1},300 Z'
page_top = edge(lambda x: SEAM + 2.5 * math.sin(x / 47) + 1.5 * math.sin(x / 13 + 1), 21, step=5, amp=1.6)

def stratum(y, seed, a=2.2): return edge(lambda x: y + a * math.sin(x / 53 + seed) + 1.2 * math.sin(x / 17 + seed * 2), seed, step=5, amp=1.3)
s1 = stratum(E1, 31); s2 = stratum(E2, 37)
# night ground: low on the left under Beer & Cider, rising as a prairie swell into the space under Wine
def night_y(x):
    base = 776
    hill = max(0.0, math.cos((x - 520) / 150 * math.pi / 2)) if abs(x - 520) < 150 else 0.0
    top = WINE_END + 22
    return base - (base - top) * hill ** 1.6 + 1.2 * math.sin(x / 19)
n_red = edge(lambda x: night_y(x) - 7, 51, step=5, amp=1.4); n_ng = edge(night_y, 53, step=5, amp=1.4)

DEFS = f'''<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F3DCBC"/><stop offset=".5" stop-color="#F2D2A8"/>
   <stop offset=".78" stop-color="#EBB17F"/><stop offset="1" stop-color="#E09567"/></linearGradient>
  <radialGradient id="goldlight" cx=".4" cy=".34" r=".8"><stop offset="0" stop-color="#EBC872"/><stop offset=".6" stop-color="#D6A546"/><stop offset="1" stop-color="#D4A24A"/></radialGradient>
  <filter id="rim" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".11" numOctaves="4" seed="11"/>
   <feDisplacementMap in="SourceGraphic" scale="4"/></filter>
  <filter id="cut" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".07" numOctaves="3" seed="7"/>
   <feDisplacementMap in="SourceGraphic" scale="2.4" result="d"/>
   <feDropShadow in="d" dx="-1.2" dy="1.8" stdDeviation="1.3" flood-color="#1B120C" flood-opacity=".32"/></filter>
  <filter id="lift" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".07" numOctaves="3" seed="17"/>
   <feDisplacementMap in="SourceGraphic" scale="2.2" result="d"/>
   <feDropShadow in="d" dx="-.6" dy="-1.4" stdDeviation="1.1" flood-color="#3A2414" flood-opacity=".30"/></filter>
  <filter id="leaf" x="-30%" y="-10%" width="160%" height="120%"><feDropShadow dx="-1.8" dy="2.4" stdDeviation="1.6" flood-color="#0C1A15" flood-opacity=".42"/></filter>
  <filter id="goldleaf" x="-5%" y="-5%" width="110%" height="110%">
   <feTurbulence type="fractalNoise" baseFrequency=".3" numOctaves="3" seed="21" result="n"/>
   <feColorMatrix in="n" type="matrix" values="0 0 0 0 .97  0 0 0 0 .87  0 0 0 0 .58  0 0 0 2.0 -1.05" result="fleck"/>
   <feComposite in="fleck" in2="SourceGraphic" operator="in" result="f2"/>
   <feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="f2"/></feMerge></filter>
  <filter id="fiber" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="3" seed="4" result="n"/>
   <feColorMatrix in="n" type="matrix" values="0 0 0 0 .22  0 0 0 0 .16  0 0 0 0 .10  0 0 0 -1.4 .95"/></filter>
  <clipPath id="heroclip"><path d="M{X0},{X0} L{X1},{X0} L{X1},{SEAM + 12} L{X0},{SEAM + 12} Z"/></clipPath>
  <clipPath id="cornclip"><path d="{corn_clip}"/></clipPath><clipPath id="agaveclip"><path d="{agave_clip}"/></clipPath>
 </defs>'''

HERO = f'''<g clip-path="url(#heroclip)">
  <rect x="{X0}" y="{X0}" width="630" height="290" fill="url(#sky)"/>
  <circle cx="{SUN['cx']}" cy="{SUN['cy']}" r="{SUN['r']}" fill="url(#goldlight)" filter="url(#goldleaf)"/>
  {layer(hill_far, PAL['hill_far'], bottom=300)}
  {layer(hill_near, PAL['hill'], bottom=300)}
  <g filter="url(#cut)"><g clip-path="url(#cornclip)">{layer(field_top, PAL['corn'], bottom=300, rim=False)}
     <g clip-path="url(#cornclip)"><g opacity="1">{rows(X0 - 260, SEAM_X(300), [PAL['cornG'], PAL['corn'], PAL['corn2'], PAL['corn']], 61, 22)}</g></g></g></g>
  <g filter="url(#rim)"><path d="M{fmt(seam_pts)} L{X1},300 L{X1},200 Z" fill="{PAL['rim']}" transform="translate(-2.4,0)"/></g>
  <g filter="url(#cut)"><g clip-path="url(#agaveclip)"><path d="M{fmt(field_top)} L{X1},300 L{X0},300 Z" fill="{PAL['agf']}"/>
     {rows(SEAM_X(300) - 40, X1 + 420, [PAL['agf2'], PAL['agf'], PAL['leafD'], PAL['agf']], 67, 20)}</g></g>
  <g>{leaves_svg}</g>
  <rect x="{X0}" y="{X0}" width="630" height="290" filter="url(#fiber)" opacity=".42"/>
 </g>'''

GROUND = f'''{layer(page_top, PAL['paper'], flt="lift")}
 {layer(s1, PAL['sand'], flt="lift")}
 {layer(s2, PAL['tan'], flt="lift")}
 {layer(n_red, PAL['terra'], flt="cut")}
 {layer(n_ng, PAL['night'], flt="cut")}
 <rect x="{X0}" y="{SEAM - 6}" width="630" height="{801 - SEAM + 6}" filter="url(#fiber)" opacity=".09"/>'''

def art_svg(cls, vb, prefix=""):
    s = f'<svg class="{cls}" viewBox="{vb}" preserveAspectRatio="xMidYMin meet" aria-hidden="true">{DEFS}{HERO}{GROUND}</svg>'
    if prefix: s = s.replace('id="', f'id="{prefix}').replace('url(#', f'url(#{prefix}')
    return s

# wordmark: CANTINA cut from the hills' deep red paper (scissor-roughened edge, cream fibre rim, paper shadow);
# the sun sits behind the first A and shows through its counter. Exact text, not baked into art.
WM_SIZE, WM_BASE, WM_X = 92, 128, 36
def wm_svg(cls, vb, prefix=""):
    s = f'''<svg class="{cls}" viewBox="{vb}" preserveAspectRatio="xMidYMin meet" aria-label="Cantina">
 <defs><filter id="wmcut" x="-5%" y="-10%" width="110%" height="130%"><feTurbulence type="fractalNoise" baseFrequency=".09" numOctaves="3" seed="5"/>
  <feDisplacementMap in="SourceGraphic" scale="2.2" result="d"/>
  <feDropShadow in="d" dx="-1.4" dy="2.0" stdDeviation="1.2" flood-color="#6B3A1E" flood-opacity=".14"/></filter></defs>
 <text class="tx wmtext" x="{WM_X}" y="{WM_BASE}" filter="url(#wmcut)">CANTINA</text></svg>'''
    if prefix: s = s.replace('id="', f'id="{prefix}').replace('url(#', f'url(#{prefix}')
    return s

# ---------------------------------------------------------------- TEXT layer
def desc_html(k):
    ing, note, _ = LINE[k]
    if not ing: return ""
    parts = [f'<span class="ing">{t.replace(" ", "&nbsp;")}</span>' for t in ing]
    if note: parts.append(f'<span class="ing note">{note.replace(" ", "&nbsp;")}</span>')
    return '<div class="desc tx">' + '<span class="sep">&nbsp;·</span> '.join(parts) + "</div>"
def item(i):
    return (f'<div class="item" data-ref="{i["id"]}"><div class="row"><span class="name tx">{i["name"]}</span>'
            f'<span class="lead"></span><span class="price tx">{P(i)}</span></div>{desc_html(i["id"])}</div>')
def sub(sb, sid=None):
    sid = sid or sb["id"]; lab = LABEL.get(sid, sb["name"])
    return f'<div class="sub" data-id="{sid}"><h3 class="tx">{lab}</h3>' + "".join(item(i) for i in sb["items"]) + "</div>"
def head(title, sid, tag="", tagcls="tag"):
    t = f'<span class="{tagcls} tx">{tag}</span>' if tag else ""
    return f'<div class="hrow" data-id="{sid}"><h2 class="tx">{title}</h2>{t}</div>'

S = {s["id"]: s for s in doc["sections"]}
ck, sp, be, ci, wi = S["sec_cocktails"], S["sec_spirits"], S["sec_beer"], S["sec_cider"], S["sec_wine"]
ck_subs = {sb["id"]: sb for sb in ck["subs"]}; sp_subs = {sb["id"]: sb for sb in sp["subs"]}
MENU = (
 f'<section class="sec full" data-id="sec_cocktails" data-stratum="dusk">{head("Cocktails", "sec_cocktails", TAG)}<div class="cols">'
 f'<div class="col" data-col="L">{sub(ck_subs["sub_cocktails_house_originals"])}</div>'
 f'<div class="col" data-col="R">{sub(ck_subs["sub_cocktails_classics"])}</div></div></section>'
 f'<section class="sec full" data-id="sec_spirits" data-stratum="late">{head("Spirits", "sec_spirits", "per pour", "pour")}<div class="cols">'
 f'<div class="col" data-col="L">{sub(sp_subs["sub_spirits_agave"])}</div>'
 f'<div class="col" data-col="R">{sub(sp_subs["sub_spirits_brandy"])}</div></div></section>'
 f'<div class="cols pair" data-stratum="evening">'
 f'<div class="col" data-col="L"><section class="sec" data-id="sec_beer">{head("Beer", "sec_beer")}{sub(be["subs"][0])}</section>'
 f'<section class="sec cider" data-id="sec_cider">{head("Cider", "sec_cider")}<div class="sub nosub" data-id="sec_cider">' + "".join(item(i) for i in ci["items"]) + '</div></section></div>'
 f'<div class="col" data-col="R"><section class="sec" data-id="sec_wine">{head("Wine", "sec_wine")}' + "".join(sub(sb) for sb in wi["subs"]) + '</section></div></div>')

B = 13  # the one baseline increment (pt) for the whole menu column; half-steps (6.5) only between items
CSS = f"""
@font-face {{font-family:'Fraunces';src:url('{FONTS}/fraunces.woff2') format('woff2');font-weight:100 900;font-style:normal;font-display:block}}
@font-face {{font-family:'Fraunces';src:url('{FONTS}/fraunces-i.woff2') format('woff2');font-weight:100 900;font-style:italic;font-display:block}}
@font-face {{font-family:'DM Sans';src:url('{FONTS}/DMSans-500-normal.ttf');font-weight:500;font-display:block}}
@font-face {{font-family:'DM Sans';src:url('{FONTS}/DMSans-700-normal.ttf');font-weight:700;font-display:block}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:#fff}}
.page{{position:relative;width:612pt;height:792pt;overflow:hidden;background:{PAL['paper']};color:{PAL['ink']};
  font-family:'Fraunces',serif;font-variant-numeric:lining-nums tabular-nums;-webkit-print-color-adjust:exact}}
.art,.wm{{position:absolute;left:-9pt;top:-9pt;width:630pt;height:810pt}}
.wmtext{{font-family:'Fraunces';font-weight:760;font-size:{WM_SIZE}px;letter-spacing:-.012em;fill:currentColor;color:#55200F;
  font-variation-settings:'opsz' 144,'SOFT' 30,'WONK' 0;stroke:{PAL['rim']};stroke-width:1.6px;paint-order:stroke}}
.subline{{position:absolute;left:36pt;top:32.6pt;font:700 8.5pt/13pt 'DM Sans',sans-serif;letter-spacing:.3em;color:{PAL['red']}}}
.menu{{position:absolute;left:36pt;top:var(--top,284pt);width:540pt}}
.sec.full+.sec.full,.sec.full+.pair{{margin-top:{2*B}pt}}
.hrow{{display:flex;align-items:baseline;justify-content:space-between;height:{2*B}pt;margin-bottom:{B/2}pt}}
h2{{font-weight:330;font-size:25pt;line-height:{2*B}pt;letter-spacing:.005em;font-variation-settings:'opsz' 144,'SOFT' 50;color:{PAL['ink']}}}
.tag{{font-style:italic;font-weight:400;font-size:12pt;line-height:{B}pt;color:#5A3A2A}}
.pour{{font:700 8.5pt/{B}pt 'DM Sans',sans-serif;letter-spacing:.24em;text-transform:uppercase;color:{PAL['terra']}}}
h3{{font:700 8.5pt/{B}pt 'DM Sans',sans-serif;letter-spacing:.24em;text-transform:uppercase;color:{PAL['terra']}}}
.cols{{display:grid;grid-template-columns:261pt 261pt;column-gap:18pt}}
.sub+.sub{{margin-top:{B}pt}}
.sec.cider{{margin-top:{2*B}pt}}
.item{{margin-top:{B/2}pt}}
.row{{display:flex;align-items:baseline;width:var(--m,100%);max-width:100%}}
.name{{font-weight:620;font-size:10pt;line-height:{B}pt;letter-spacing:.1em;text-transform:uppercase;white-space:nowrap}}
.lead{{flex:1;min-width:14pt;margin:0 4pt;height:.6pt;align-self:baseline;transform:translateY(-2.3pt);
  background:radial-gradient(circle,{PAL['price']} .42pt,transparent .5pt) 0 50%/3pt 1.2pt repeat-x;height:1.2pt}}
.price{{font-weight:640;font-size:11.5pt;line-height:{B}pt;min-width:14pt;text-align:right;color:{PAL['price']}}}
.desc{{font-weight:400;font-size:10.5pt;line-height:{B}pt;color:#40352D;width:var(--m,100%);max-width:100%;font-variation-settings:'opsz' 12}}
.desc .note{{font-style:italic}} .ing{{white-space:nowrap}}
.hero,.phonefoot,.phonesub{{display:none}}
@media (max-width:600px){{
 .page{{width:100%;height:auto;overflow:visible;background:{PAL['paper']}}}
 .art.print,.wm.print,.subline{{display:none}}
 .hero{{display:block;position:relative;width:100%;aspect-ratio:630/{SEAM + 12 + 9}}}
 .hero svg{{position:absolute;left:0;top:0;width:100%;height:100%}}
 .phonesub{{display:block;padding:12px 22px 0;font:700 11px/16px 'DM Sans',sans-serif;letter-spacing:.24em;color:{PAL['red']}}}
 .menu{{position:relative;left:0;top:0;width:auto;padding:0}}
 .cols{{display:block}}
 .sec.full,.pair>.col{{padding:14px 22px 22px}}
 .sec.full+.sec.full,.sec.full+.pair{{margin-top:0}}
 .sec[data-id=sec_spirits]{{background:{PAL['sand']}}} .pair{{background:{PAL['tan']}}}
 .col+.col{{margin-top:0}} .sec.full .col+.col{{margin-top:13px}}
 .tear{{display:block;width:100%;height:10px;margin-bottom:-1px}}
 .hrow{{height:34px;margin-bottom:4px}}
 h2{{font-size:30px;line-height:34px}}
 .tag{{font-size:16px;line-height:20px}} .pour,h3{{font-size:11.5px;line-height:17px}}
 .item{{margin-top:9px}} .sub+.sub{{margin-top:16px}} .sec.cider{{margin-top:24px}}
 .name{{font-size:14.5px;line-height:20px;white-space:normal}}
 .price{{font-size:17px;line-height:20px}}
 .desc{{font-size:15px;line-height:20px}}
 .phonefoot{{display:block;line-height:0}} .phonefoot svg{{width:100%;height:auto;display:block}}
}}
.tear{{display:none}}
"""
TEAR = lambda fill, seed: ('<svg class="tear" viewBox="0 0 390 10" preserveAspectRatio="none" aria-hidden="true"><path d="M0,10 L'
    + fmt(edge(lambda x: 5 + 2 * math.sin(x / 23 + seed), seed, 0, 390, 5, 1.4)) + f' L390,10 Z" fill="{fill}"/></svg>')
PHONE_FOOT = (f'<div class="phonefoot" aria-hidden="true"><svg viewBox="0 0 390 70"><rect width="390" height="70" fill="{PAL["tan"]}"/>'
    f'<path d="M0,70 L{fmt(edge(lambda x: 30 - 14 * max(0, math.cos((x - 290) / 110 * math.pi / 2)) ** 1.6 if abs(x - 290) < 110 else 30, 71, 0, 390, 5, 1.2))} L390,70 Z" fill="{PAL["terra"]}"/>'
    f'<path d="M0,70 L{fmt(edge(lambda x: 37 - 14 * max(0, math.cos((x - 290) / 110 * math.pi / 2)) ** 1.6 if abs(x - 290) < 110 else 37, 73, 0, 390, 5, 1.2))} L390,70 Z" fill="{PAL["night"]}"/></svg></div>')

MENU_PHONE = MENU.replace('data-stratum="late">', f'data-stratum="late">').replace('<section class="sec full" data-id="sec_spirits"', TEAR(PAL["sand"], 3) + '<section class="sec full" data-id="sec_spirits"').replace('<div class="cols pair"', TEAR(PAL["tan"], 5) + '<div class="cols pair"')
HVB = f"-9 -9 630 {SEAM + 12 + 9}"
JS = r"""
function layoutMenu(){
  const pt = 96/72;
  // one price measure per grid column (all left blocks share one price edge, all right blocks another)
  ['L', 'R'].forEach(k => { const cols = [...document.querySelectorAll('.menu .col[data-col=' + k + ']')];
    cols.forEach(c => c.style.removeProperty('--m')); let need = 0, cw = 1e9;
    cols.forEach(col => { cw = Math.min(cw, col.getBoundingClientRect().width);
      col.querySelectorAll('.row').forEach(r => { const n = r.querySelector('.name'), p = r.querySelector('.price');
        need = Math.max(need, n.scrollWidth + p.getBoundingClientRect().width + 22*pt); }); });
    const m = Math.min(cw, Math.ceil(Math.max(need, 170*pt) / (6.5*pt)) * 6.5*pt);
    cols.forEach(c => c.style.setProperty('--m', m + 'px')); });
  document.querySelectorAll('.desc').forEach(d => {
    d.querySelectorAll('.sep').forEach(s => s.style.visibility = 'visible');
    d.querySelectorAll('.sep').forEach(s => { const nx = s.nextElementSibling; if (!nx) return;
      if (nx.getBoundingClientRect().top > s.getBoundingClientRect().top + 2) s.style.visibility = 'hidden'; }); });
}
document.fonts.ready.then(layoutMenu); window.addEventListener('resize', layoutMenu); window.layoutMenu = layoutMenu;
"""
TOP = 284
if MEAS.exists():
    _m = json.loads(MEAS.read_text()); TOP = round(_m["M"]["top"] + (_m["ink"]["bottom"] - 36), 2)
HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cantina &amp; Cocktail Bar · Iowa City, Iowa</title><style>{CSS}</style></head><body>
<div class="page" style="--top:{TOP}pt">
{art_svg("art print", "-9 -9 630 810")}
{wm_svg("wm print", "-9 -9 630 810")}
<div class="hero">{art_svg("art phone", HVB, "p_")}{wm_svg("wm phone", HVB, "q_")}</div>
<div class="subline tx">&amp; COCKTAIL BAR&#8194;·&#8194;IOWA CITY, IOWA</div>
<div class="phonesub tx">&amp; COCKTAIL BAR · IOWA CITY, IOWA</div>
<main class="menu print-menu">{MENU}</main>
</div><script>{JS}</script></body></html>"""
# phone gets the torn tear strips between strata: inject them only for narrow screens (hidden in print by CSS)
HTML = HTML.replace(f'<main class="menu print-menu">{MENU}</main>', f'<main class="menu">{MENU_PHONE}</main>{PHONE_FOOT}')
(OUT / "menu.html").write_text(HTML)
print("ok", len(HTML), "E1", round(E1, 1), "E2", round(E2, 1), "wine_end", WINE_END, "top", TOP)
