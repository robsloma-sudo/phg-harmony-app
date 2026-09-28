"""TEST-1 round 6: Lotería de la Cantina, real lotería anatomy.
Six portrait lotería cards on a 3 x 2 grid (featured agave card top-left), built from the verbatim draft doc.
Every printed line is traced in doc.meta.designer_notes.copy_sources (gateway rows, draft words, recipe words)."""
import json, copy, html, pathlib, base64, math, re
from string import Template

HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path("/home/user/phg-harmony-app/handoff/designs/test-1-iowa-city-cantina")
draft = json.loads((HERE / "draft_doc.json").read_text())
ROUND = 6

# ------------------------------------------------------------ copy + sources (draft menu_description words; one gateway row)
C = {  # id: (printed line, words from, gateway row ids, still missing)
 "beta_old_fashioned": ("Brown butter-washed bourbon, demerara syrup, bitters; orange peel. Stirred; over a large cube.",
   "draft (brown butter-washed bourbon, demerara, bitters); recipe (syrup, orange peel, stirred, large cube)", [], ["allergen confirmation (brown butter: dairy)"]),
 "beta_daiquiri": ("White rum, fresh lime, house demerara syrup; lime coin. Shaken; up, in a coupe.",
   "draft (white rum, lime, house demerara syrup); recipe (fresh, lime coin, shaken, coupe)", [], []),
 "beta_margarita": ("Blanco tequila, fresh lime, orange liqueur, agave syrup; lime wheel. Bright and citrus-forward. Shaken; on the rocks.",
   "draft (tequila blanco, lime, orange liqueur, agave, 'Bright and citrus-forward'); recipe (fresh, syrup, lime wheel, shaken, rocks)", [], []),
 "beta_manhattan": ("Rye whiskey, sweet vermouth; cocktail cherry. Stirred; up, in a coupe.",
   "draft (rye, sweet vermouth); recipe (whiskey, cherry, stirred, coupe). Bitters hidden: public_components aromatic-bitters = false", [], ["venue to confirm hiding the bitters"]),
 "beta_blanco_tequila": ("Also called plata.",
   "beverage_categories row name 'Blanco / plata'. The row does not say 'unaged' in the words used, so 'unaged' is not printed",
   ["beverage_categories 04d72e1f-650d-490c-8ad8-54a6eb8aa766"], ["brand", "pour size"]),
 "beta_anejo_tequila": ("", "name only: the draft line 'Añejo tequila pour.' only repeats the name", [], ["brand", "pour size", "age statement"]),
 "beta_cognac_vsop": ("", "name only: the draft line 'VSOP Cognac pour.' only repeats the name; no cognac row cited", [], ["brand / house", "pour size"]),
 "beta_czech_pilsner": ("Crisp pale lager.", "draft menu_description, verbatim", [], ["brewery", "ABV", "pour size"]),
 "beta_dry_hopped_ipa": ("Hop-forward draft IPA.", "draft menu_description, verbatim", [], ["brewery", "ABV", "pour size"]),
 "beta_amber_lager": ("Toasty amber lager.", "draft menu_description, verbatim", [], ["brewery", "ABV", "pour size"]),
 "beta_dry_cider": ("Dry sparkling cider.", "draft menu_description, verbatim", [], ["producer", "ABV", "format (draft or can)"]),
 "beta_malbec": ("Dry red wine.", "draft menu_description, verbatim", [], ["producer", "region", "vintage", "pour size"]),
 "beta_pinot_grigio": ("Dry white wine.", "draft menu_description, verbatim", [], ["producer", "region", "vintage", "pour size"]),
 "beta_brut_rose": ("Dry sparkling rosé.", "draft menu_description, verbatim", [], ["producer", "region", "vintage", "glass or bottle price (label empty)"]),
}
BANNED = ["nom-006", "class", "shelf", "fermented", "lager family", "beside beer", "age grade", "pour"]
for k, v in C.items():
    assert not any(w in v[0].lower() for w in BANNED), k
    assert not any(r in " ".join(v[2]) for r in ("d4d63f58", "bc899a48")), k
ES = {"sub_cocktails_classics": "Clásicos", "sub_cocktails_house_originals": "De la casa", "sub_spirits_agave": "Del agave",
      "sub_spirits_brandy": "Brandy y coñac", "sub_beer_draft": "De barril", "sub_wine_by_the_glass": "Por copa", "sub_wine_sparkling": "Espumoso"}
KICKER = {"sec_spirits": "Destilados", "sec_beer": "Cerveza", "sec_cider": "Sidra", "sec_wine": "Vino"}

secs = {s["id"]: s for s in draft["sections"]}
doc = copy.deepcopy(draft)
doc["title"] = "Cantina & Cocktail Bar"; doc["subtitle"] = "Iowa City, Iowa"
new = [copy.deepcopy(secs[k]) for k in ["sec_cocktails", "sec_spirits", "sec_beer", "sec_cider", "sec_wine"]]
subs = {sb["name"]: sb for sb in new[0]["subs"]}
ho, cl = subs["House Originals"], subs["Classics"]
ho["items"] = [next(i for i in ho["items"] if i["id"] == x) for x in ["beta_old_fashioned", "beta_daiquiri"]]
cl["items"] = [next(i for i in cl["items"] if i["id"] == x) for x in ["beta_margarita", "beta_manhattan"]]
new[0]["subs"] = [ho, cl]
for s in new:
    for sb in s["subs"]:
        if sb["id"] not in ES:  # sub ids differ from the guessed keys: map by name
            ES[sb["id"]] = {"Agave": "Del agave", "Brandy": "Brandy y coñac", "Draft": "De barril", "By the Glass": "Por copa", "Sparkling": "Espumoso",
                            "Classics": "Clásicos", "House Originals": "De la casa"}[sb["name"]]
    for it in s["items"] + [i for sb in s["subs"] for i in sb["items"]]:
        line, src, rows, miss = C[it["id"]]
        it["desc"] = line; it.pop("missing_ingredients", None)
        it["meta"] = dict(it.get("meta") or {}); it["meta"]["missing_ingredients"] = list(miss)
assert "bitters" in C["beta_old_fashioned"][0] and "bitters" not in C["beta_manhattan"][0]
assert "Bright and citrus-forward" in C["beta_margarita"][0]
doc["sections"] = new

def flat(d):
    return {i["id"]: (i["name"], json.dumps(i["prices"], sort_keys=True), json.dumps(i.get("phg"), sort_keys=True),
                      json.dumps({k: v for k, v in (i.get("meta") or {}).items() if k != "missing_ingredients"}, sort_keys=True), json.dumps(i.get("components"), sort_keys=True))
            for s in d["sections"] for i in s["items"] + [x for sb in s["subs"] for x in sb["items"]]}
assert flat(doc) == flat(draft) and len(flat(doc)) == 14, "item/price/meta drift"

allitems = {i["id"]: i for s in new for i in s["items"] + [x for sb in s["subs"] for x in sb["items"]]}
subn = {sb["name"]: sb for s in new for sb in s["subs"]}
cider_sub = {"id": "sec_cider", "name": "Cider"}; ES["sec_cider"] = "Sidra"
CARDS = [  # (n, ref, english, tab label, lotería name, figure, colour, groups)
 (1, "sub_spirits_agave", "Margarita & Agave", "Agave", "El Agave", "agave", "terra",
     [(None, [allitems["beta_margarita"]]), (subn["Agave"], subn["Agave"]["items"])]),
 (2, ho["id"], "House Originals", "House", "El Vaso", "tumbler", "agave", [(None, ho["items"])]),
 (3, cl["id"], "Classics", "Classics", "La Copa", "coupe", "mari", [(None, [allitems["beta_manhattan"]])]),
 (4, "sec_beer", "Beer & Cider", "Beer", "Cerveza y Sidra", "barrel", "agave",
     [(subn["Draft"], subn["Draft"]["items"]), (cider_sub, next(x for x in new if x["id"] == "sec_cider")["items"])]),
 (5, "sub_spirits_brandy", "Brandy", "Brandy", "La Copita", "snifter", "terra", [(None, subn["Brandy"]["items"])]),
 (6, "sec_wine", "Wine", "Wine", "La Botella", "bottle", "mari", [(subn["By the Glass"], subn["By the Glass"]["items"]), (subn["Sparkling"], subn["Sparkling"]["items"])]),
]
assert sorted(i["id"] for c in CARDS for g in c[7] for i in g[1]) == sorted(allitems), "every item on exactly one card"
doc["meta"] = dict(doc.get("meta") or {})
doc["meta"]["designer_notes"] = {
    "round": ROUND, "concept": "Lotería de la Cantina: six portrait lotería cards, each with the ordinal in the top-left corner, the English list name, a large central cut-paper figure and a lotería name bar at the foot (EL AGAVE, EL VASO, LA COPA, CERVEZA Y SIDRA, LA COPITA, LA BOTELLA). Card 1 tells the agave story: Margarita, then Blanco and Añejo.",
    "cards": [{"n": c[0], "ref": c[1], "name": c[2], "loteria_name": c[4].upper(), "figure": c[5], "featured": c[0] == 1, "items": [i["id"] for g in c[7] for i in g[1]]} for c in CARDS],
    "sub_kickers": {sb["name"]: ES[sb["id"]] for s in new for sb in s["subs"]},
    "copy_sources": {k: {"printed": v[0], "words_from": v[1], "gateway_rows": v[2], "missing": v[3]} for k, v in C.items()},
    "gateway_query": "round 5 phg_designer_query (log_id 112) over public.beverage_categories; only row 04d72e1f (Blanco / plata) is cited this round. Beer, cider and wine lines are the draft menu_description words.",
    "manhattan_bitters": "Not printed: public_components aromatic-bitters = false (venue to confirm).",
    "brut_rose_price": "Printed as a plain price with no glass/bottle label (label empty in the draft; question open).",
    "card_layout": "3 x 2 portrait grid: featured column 196 pt, two 160 pt columns, 12 pt gutters. Classics and Brandy are separate one-item cards so every card stays a portrait with a full figure.",
    "retired_junmai_ginjo": "Retired Junmai Ginjo ($12) in phg.menu_items is not in the draft and is left off (please confirm).",
}
(OUT / "doc.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2))

# ------------------------------------------------------------ palette + graphics
P = dict(cream="#F6EEDF", card="#FBF5EA", feat="#F3E3CB", ink="#231B16", terra="#A63C1A", agave="#2F5D50", mari="#E3A018", muted="#5A4A3F", rosa="#C2185B")
def dia(cx, cy, w, h, f): return f'<path d="M{cx:.2f} {cy-h:.2f} L{cx+w:.2f} {cy:.2f} L{cx:.2f} {cy+h:.2f} L{cx-w:.2f} {cy:.2f} Z" fill="{f}"/>'
def agave_leaves(cx, cy, r, f):
    o = ""
    for ang, ln in zip((-70, -45, -22, 0, 22, 45, 70), (0.7, 0.85, 0.95, 1.0, 0.95, 0.85, 0.7)):
        t = math.radians(ang); L = r * ln; tx, ty = cx + L * math.sin(t), cy - L * math.cos(t); nx, ny = math.cos(t) * r * .16, math.sin(t) * r * .16
        o += f'<path d="M{cx-nx:.2f} {cy-ny:.2f} Q{(cx+tx)/2-nx*.7:.2f} {(cy+ty)/2-ny*.7:.2f} {tx:.2f} {ty:.2f} Q{(cx+tx)/2+nx*.7:.2f} {(cy+ty)/2+ny*.7:.2f} {cx+nx:.2f} {cy+ny:.2f} Z" fill="{f}"/>'
    return o

def papel(n=11, W=540, H=36, cls="banner", dims='width="540pt" height="36pt"'):
    cell = W / n; fw = cell - 6; cols = [P["terra"], P["mari"], P["agave"]]
    o = [f'<svg class="{cls}" viewBox="0 0 {W} {H}" {dims} xmlns="http://www.w3.org/2000/svg" aria-hidden="true">',
         f'<path d="M1 0.4 Q{W/2} 4 {W-1} 0.4" stroke="{P["ink"]}" stroke-width="0.8" fill="none"/>']
    for k in range(n):
        x = k * cell + 3; top, hem = 3, H - 4; c = cols[k % 3]; sw = fw / 5
        d = f"M{x:.2f} {top} L{x+fw:.2f} {top} L{x+fw:.2f} {hem}" + "".join(f" A{sw/2:.2f} {sw/2*.9:.2f} 0 0 1 {x+fw-(j+1)*sw:.2f} {hem}" for j in range(5))
        o.append(f'<path d="{d} Z" fill="{c}"/>' + "".join(dia(x + sw / 2 + j * sw, top + 4.5, 1.4, 1.9, P["cream"]) for j in range(5)))
        cx, cy = x + fw / 2, (top + hem) / 2 + 3
        o.append(agave_leaves(cx, cy + 6, 11, P["cream"]) if k % 2 == 0 else dia(cx, cy, 7, 8, P["cream"]) + dia(cx, cy, 4, 5, c) + dia(cx, cy, 1.6, 2, P["cream"]))
    return "".join(o) + "</svg>"

def icon(kind, size):
    t, a, m, i, c, pk = P["terra"], P["agave"], P["mari"], P["ink"], P["card"], P["rosa"]
    g = {
     "tumbler": f'<path d="M9 11 L31 11 L29 34 Q29 36 27 36 L13 36 Q11 36 11 34 Z" fill="{t}"/><rect x="14.5" y="17" width="11" height="11" fill="{c}" transform="rotate(8 20 22.5)"/>'
                f'<path d="M26 4 Q34 6 35 14" stroke="{m}" stroke-width="3" fill="none"/>{dia(20, 32, 2, 1.5, pk)}',
     "coupe": f'<path d="M5 9 L35 9 Q34 21 20 22 Q6 21 5 9 Z" fill="{a}"/><rect x="19" y="21" width="2" height="11" fill="{a}"/><path d="M12 36 Q20 30 28 36 Z" fill="{a}"/>'
              f'{dia(20, 14, 2.2, 3, c)}{dia(13, 13, 1.4, 2, c)}{dia(27, 13, 1.4, 2, c)}<circle cx="32" cy="8" r="5" fill="{pk}"/><circle cx="32" cy="8" r="2" fill="{c}"/>',
     "agave": agave_leaves(20, 36, 32, a) + dia(20, 26, 1.6, 3, pk) + dia(12, 28, 1.2, 2.2, c) + dia(28, 28, 1.2, 2.2, c) + f'<rect x="6" y="36" width="28" height="2.5" fill="{m}"/>',
     "tap": f'<rect x="15" y="2" width="10" height="17" rx="2" fill="{m}"/>{dia(20, 10, 2.2, 3.4, c)}<rect x="10" y="19" width="20" height="6" rx="1" fill="{t}"/>'
            f'<path d="M22 25 L22 31 L17 31 L17 28 L19 28 L19 25 Z" fill="{t}"/><circle cx="18.2" cy="35" r="2" fill="{m}"/>',
     "apple": f'<path d="M20 12 C12 6 4 12 6 22 C8 32 14 38 20 35 C26 38 32 32 34 22 C36 12 28 6 20 12 Z" fill="{a}"/><path d="M21 11 Q24 3 31 4 Q28 11 21 11 Z" fill="{m}"/>'
              f'<rect x="19.2" y="5" width="1.6" height="7" fill="{i}"/>{dia(20, 23, 3, 4.5, c)}{dia(20, 23, 1.2, 1.8, a)}',
     "bottle": f'<path d="M17 2 L23 2 L23 11 Q29 14 29 20 L29 36 Q29 38 27 38 L13 38 Q11 38 11 36 L11 20 Q11 14 17 11 Z" fill="{t}"/><rect x="16" y="1" width="8" height="3" fill="{i}"/>'
               f'<rect x="13.5" y="21" width="13" height="11" fill="{c}"/>{dia(20, 26.5, 2.4, 3.2, pk)}',
     "barrel": f'<path d="M10 4 Q6.5 20 10 36 L30 36 Q33.5 20 30 4 Z" fill="{t}"/><rect x="8.4" y="10" width="23.2" height="2.4" fill="{i}"/><rect x="8.4" y="27.6" width="23.2" height="2.4" fill="{i}"/>'
               f'{dia(20, 20, 3.4, 5, c)}{dia(20, 20, 1.4, 2.1, pk)}<rect x="16" y="36" width="8" height="2.5" fill="{m}"/>',
     "snifter": f'<path d="M9 11 Q7 28 20 29 Q33 28 31 11 Z" fill="{a}"/><path d="M10.6 20 Q20 23 29.4 20 Q30 27 20 27.6 Q10 27 10.6 20 Z" fill="{m}"/><rect x="19" y="29" width="2" height="5" fill="{a}"/>'
                f'<path d="M12 38 Q20 32 28 38 Z" fill="{a}"/>{dia(20, 15, 1.8, 2.6, pk)}',
    }[kind]
    return f'<svg class="{size}" viewBox="-2 -2 44 44" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">{g}</svg>'

def nb(t):
    t = html.escape(t)
    t = re.sub(r"(\w+(?:-\w+)+)", r'<span class="nw">\1</span>', t)  # citrus-forward, butter-washed, hop-forward
    i = t.rfind(" ")
    return t[:i] + "&nbsp;" + t[i+1:] if i > 0 else t

def item_html(it):
    d = f'<p class="desc">{nb(it["desc"])}</p>' if it["desc"] else ""
    return (f'<div class="item" data-ref="{it["id"]}"><div class="row"><span class="name">{nb(it["name"])}</span>'
            f'<span class="price num">{it["prices"][0]["value"]:g}</span></div>{d}</div>')

def card_html(n, cid, name, tab, lot, fig, col, groups):
    f = n == 1
    body = []
    for sb, items in groups:
        if sb is not None:
            body.append(f'<div class="sub" data-id="{sb["id"]}"><h3>{html.escape(sb["name"])}</h3><span class="es">{ES[sb["id"]]}</span><span class="subrule"></span></div>')
        body.append('<div class="items">' + "".join(item_html(i) for i in items) + "</div>")
    return (f'<article class="card c-{col}{" featured" if f else ""}" id="card-{n}" data-id="{cid}" data-n="{n}">'
            f'<header class="head"><span class="cardno">{n}</span><h2>{html.escape(name)}</h2></header>'
            f'<div class="figure">{icon(fig, "fig")}</div><div class="body">{"".join(body)}</div>'
            f'<div class="namebar"><span>{html.escape(lot.upper())}</span></div></article>')

cards = [card_html(*c) for c in CARDS]
tabs = "".join(f'<a class="tab c-{c[6]}{" active" if c[0] == 1 else ""}" data-n="{c[0]}" href="#card-{c[0]}" aria-label="{c[0]} {html.escape(c[2])}">'
               f'<span class="tn">{c[0]}</span>{icon(c[5], "ticon")}<span class="lbl">{html.escape(c[3])}</span></a>' for c in CARDS)
JS = """<script>(()=>{const t=[...document.querySelectorAll('.tab')],s=n=>t.forEach(a=>a.classList.toggle('active',a.dataset.n==n));
t.forEach(a=>a.addEventListener('click',()=>s(a.dataset.n)));if('IntersectionObserver'in window){const o=new IntersectionObserver(e=>e.forEach(x=>{if(x.isIntersecting)s(x.target.dataset.n)}),{rootMargin:'-35% 0px -55% 0px'});
document.querySelectorAll('.card').forEach(c=>o.observe(c));}})();</script>"""

FONTS = "".join(
    "@font-face {{ font-family:'{}'; font-style:{}; font-weight:{}; font-display:block; src:url(data:font/ttf;base64,{}) format('truetype'); }}\n".format(
        f.stem.split('-')[0].replace('DMSans', 'DM Sans'), f.stem.split('-')[2], f.stem.split('-')[1], base64.b64encode(f.read_bytes()).decode())
    for f in sorted((HERE / "fonts").glob("*.ttf")))

CSS = Template("""
@page { size: 8.5in 11in; margin: 0; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; background:#d9d2c6; }
body { -webkit-print-color-adjust:exact; print-color-adjust:exact; font-family:'DM Sans', sans-serif; color:$ink; }
.page { width:612pt; height:792pt; padding:36pt; background:$cream; display:flex; flex-direction:column; margin:0 auto; }
.banner { display:block; width:540pt; height:36pt; flex:none; }
.banner-m, .tabs { display:none; }
.title { font-family:'Fraunces', serif; font-weight:700; font-size:30pt; line-height:34pt; letter-spacing:-0.3pt; text-align:center; margin:4pt 0 0; }
.title .amp { color:$terra; font-style:italic; font-weight:600; }
.loc { text-align:center; font-size:8.5pt; line-height:12pt; letter-spacing:3pt; text-transform:uppercase; color:$muted; font-weight:500; margin:0 0 10pt; }
.num { font-family:'Fraunces', serif; font-weight:600; color:$terra; font-variant-numeric:lining-nums tabular-nums; font-feature-settings:'lnum' 1,'tnum' 1; }
.nw { white-space:nowrap; }
.deck { flex:1; display:grid; grid-template-columns:196pt 160pt 160pt; grid-template-rows:minmax(0,1fr) minmax(0,1.06fr); gap:12pt; min-height:0; }
.card { position:relative; display:flex; flex-direction:column; background:$card; border:1.5pt solid $ink; overflow:visible;
        box-shadow: inset 0 0 0 3pt $card, inset 0 0 0 3.75pt $ink; padding:7pt 10pt 8pt; min-height:0; }
.card.featured { background:$feat; border-color:$terra; box-shadow: inset 0 0 0 3pt $feat, inset 0 0 0 4.5pt $terra; }
/* lotería anatomy: ordinal top-left, English name, large central figure, name bar at the foot */
.head { display:grid; grid-template-columns:20pt 1fr 20pt; align-items:baseline; height:24pt; flex:none; }
.cardno { font-family:'Fraunces', serif; font-weight:700; font-size:19pt; line-height:24pt; color:$rosa; font-variant-numeric:lining-nums; }
.head h2 { grid-column:2; text-align:center; font-family:'Fraunces', serif; font-weight:700; font-size:11.5pt; line-height:24pt; margin:0; white-space:nowrap; }
.featured .head h2 { font-size:13pt; }
.figure { position:relative; flex:1 1 0; min-height:0; margin:0 0 6pt; }
.figure .fig { position:absolute; inset:0; width:100%; height:100%; display:block; }
.body { flex:none; border-top:0.75pt solid $ink; padding-top:6pt; }
.featured .body { border-top-color:$terra; }
.sub { display:flex; align-items:baseline; gap:5pt; height:12pt; }
.items + .sub { margin-top:6pt; }
h3 { margin:0; font-size:7pt; line-height:12pt; letter-spacing:1.4pt; text-transform:uppercase; color:$agave; font-weight:700; white-space:nowrap; }
.sub .es { font-family:'Fraunces', serif; font-style:italic; font-size:8.5pt; line-height:12pt; color:$terra; white-space:nowrap; }
.subrule { flex:1; border-top:0.5pt solid $agave; opacity:.5; align-self:center; }
.item + .item { margin-top:6pt; }
.row { display:flex; justify-content:space-between; align-items:baseline; }
.name { font-family:'Fraunces', serif; font-size:10.5pt; line-height:12pt; font-weight:600; }
.price { font-size:10.5pt; line-height:12pt; margin-left:8pt; }
.desc { margin:0; padding-right:8pt; font-size:8pt; line-height:12pt; color:$muted; }
.featured .name, .featured .price { font-size:11.5pt; } .featured .desc { font-size:8.5pt; }
.namebar { flex:none; height:20pt; margin-top:8pt; display:flex; align-items:center; justify-content:center; font-family:'Fraunces', serif; font-weight:700;
           font-size:10pt; letter-spacing:2pt; line-height:20pt; white-space:nowrap; border-top:1.5pt solid $ink; }
.featured .namebar { font-size:11pt; border-top-color:$terra; }
.c-terra .namebar { background:$terra; color:$cream; } .c-agave .namebar { background:$agave; color:$cream; } .c-mari .namebar { background:$mari; color:$ink; }
.foot { display:flex; align-items:center; gap:10pt; height:12pt; margin-top:6pt; flex:none; }
.foot .fr { flex:1; border-top:0.5pt solid $ink; opacity:.5; }
.foot .salud { font-family:'Fraunces', serif; font-style:italic; font-size:11pt; color:$terra; font-weight:600; }
@media screen and (max-width: 600px) {
  html, body { background:$cream; }
  .page { width:auto; height:auto; padding:0 16px 24px; display:block; }
  .banner { display:none; } .banner-m { display:block; width:100%; height:auto; margin-top:12px; }
  .title { font-size:32px; line-height:38px; margin-top:12px; text-wrap:balance; }
  .loc { font-size:11px; line-height:16px; margin-bottom:12px; }
  .tabs { display:grid; grid-template-columns:repeat(6, 1fr); gap:4px; position:sticky; top:0; z-index:5; background:$cream; padding:6px 0 8px; margin:0 0 14px; }
  .tab { min-width:0; display:flex; flex-direction:column; align-items:center; text-decoration:none; padding:5px 2px 12px; clip-path:polygon(0 0,100% 0,100% 82%,50% 100%,0 82%); }
  .tab .tn { font-family:'Fraunces', serif; font-weight:700; font-size:15px; line-height:18px; }
  .tab .ticon { width:22px; height:22px; background:$card; border-radius:3px; }
  .tab .lbl { display:none; font-size:10px; line-height:13px; font-weight:700; margin-top:2px; white-space:nowrap; }
  .tab.active .lbl { display:block; } .tab.active { outline:2px solid $rosa; outline-offset:-2px; }
  .tab.c-terra { background:$terra; color:$cream; } .tab.c-agave { background:$agave; color:$cream; } .tab.c-mari { background:$mari; color:$ink; }
  .deck { display:block; }
  .card { margin:0 4px 18px; scroll-margin-top:96px; padding:12px 16px 14px; box-shadow: inset 0 0 0 4px $card, inset 0 0 0 5px $ink, 3px 4px 0 rgba(35,27,22,.18); }
  .card.featured { box-shadow: inset 0 0 0 4px $feat, inset 0 0 0 6px $terra, 3px 4px 0 rgba(35,27,22,.18); }
  .card:nth-child(odd) { transform:rotate(-0.8deg); } .card:nth-child(even) { transform:rotate(0.7deg); }
  .head { grid-template-columns:30px 1fr 30px; height:auto; } .cardno { font-size:28px; line-height:34px; }
  .head h2, .featured .head h2 { font-size:20px; line-height:34px; white-space:normal; }
  .figure { flex:none; height:150px; } .featured .figure { height:190px; }
  .sub { height:auto; } h3 { font-size:11.5px; line-height:20px; } .sub .es { font-size:14px; line-height:20px; }
  .name, .price, .featured .name, .featured .price { font-size:18px; line-height:24px; }
  .desc, .featured .desc { font-size:14.5px; line-height:20px; padding-right:24px; }
  .item + .item { margin-top:12px; } .items + .sub { margin-top:14px; }
  .namebar, .featured .namebar { height:34px; line-height:34px; font-size:15px; margin-top:14px; }
  .foot { margin-top:20px; height:28px; } .foot .salud { font-size:16px; }
}
@media print { .tabs, .banner-m { display:none !important; } }
""").substitute(P)

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cantina &amp; Cocktail Bar · Iowa City, Iowa</title>
<style>{FONTS}{CSS}</style></head>
<body><div class="page">
<header class="mast">{papel()}{papel(5, 340, 56, "banner-m", 'width="100%"')}
<h1 class="title">Cantina <span class="amp">&amp;</span> Cocktail Bar</h1><p class="loc">Iowa City, Iowa</p></header>
<nav class="tabs" aria-label="Jump to a card">{tabs}</nav>
<main class="deck">{"".join(cards)}</main>
<footer class="foot"><span class="fr"></span><span class="salud">¡Salud!</span><span class="fr"></span></footer>
</div>{JS}</body></html>
"""
(OUT / "menu.html").write_text(HTML)
print("built round", ROUND, "cards", [c[2] for c in CARDS])
