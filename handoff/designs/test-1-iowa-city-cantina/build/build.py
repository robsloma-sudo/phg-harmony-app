"""TEST-1 round 5 (concept round): Lotería de la Cantina.
Six numbered lotería cards on an equal-height grid (featured row + 2 x 2), built from the verbatim draft doc.
Every printed line is traced in doc.meta.designer_notes.copy_sources (gateway rows, draft words, recipe words)."""
import json, copy, html, pathlib, base64, math, re
from string import Template

HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path("/home/user/phg-harmony-app/handoff/designs/test-1-iowa-city-cantina")
draft = json.loads((HERE / "draft_doc.json").read_text())
ROUND = 5

# ------------------------------------------------------------ copy + sources (gateway log_id 112)
C = {  # id: (printed line, words from, gateway row ids, still missing)
 "beta_old_fashioned": ("Brown butter-washed bourbon, demerara syrup, bitters; orange peel. Stirred; over a large cube.",
   "draft (brown butter-washed bourbon, demerara, bitters); recipe (syrup, orange peel, stirred, large cube)", [], ["allergen confirmation (brown butter: dairy)"]),
 "beta_daiquiri": ("White rum, fresh lime, house demerara syrup; lime coin. Shaken; up, in a coupe.",
   "draft (white rum, lime, house demerara syrup); recipe (fresh, lime coin, shaken, coupe)", [], []),
 "beta_margarita": ("Blanco tequila, fresh lime, orange liqueur, agave syrup; lime wheel. Bright and citrus-forward. Shaken; on the rocks.",
   "draft (tequila blanco, lime, orange liqueur, agave, 'Bright and citrus-forward'); recipe (fresh, syrup, lime wheel, shaken, rocks)", [], []),
 "beta_manhattan": ("Rye whiskey, sweet vermouth; cocktail cherry. Stirred; up, in a coupe.",
   "draft (rye, sweet vermouth); recipe (whiskey, cherry, stirred, coupe). Bitters hidden: public_components aromatic-bitters = false", [], ["venue to confirm hiding the bitters"]),
 "beta_blanco_tequila": ("Also called plata; a tequila class under Mexican standard NOM-006.",
   "beverage_categories 'Blanco / plata' (path spirits.agave_spirits.tequila.blanco, authority NOM-006-SCFI-2012 §5)",
   ["beverage_categories 04d72e1f-650d-490c-8ad8-54a6eb8aa766"], ["brand", "pour size"]),
 "beta_anejo_tequila": ("The aged class of tequila under Mexican standard NOM-006.",
   "beverage_categories 'Añejo' (path spirits.agave_spirits.tequila.anejo, NOM-006-SCFI-2012 §5); 'aged' is the translation of añejo",
   ["beverage_categories 9f4dae69-e84c-4b65-b7d9-1b417658b78d"], ["brand", "pour size", "age statement"]),
 "beta_cognac_vsop": ("From the brandy shelf; VSOP marks its age grade.",
   "draft sub 'Brandy'; beverage_categories row listing VSOP as an age term (rhum agricole 'Vieux (VO, VSOP, XO age terms)'); no cognac-specific row found",
   ["beverage_categories d4d63f58-17f9-5f5a-3be7-5d3c503c92d0"], ["brand", "pour size", "cognac row in beverage_categories"]),
 "beta_czech_pilsner": ("Crisp pale lager, bottom-fermented.",
   "draft (crisp pale lager); spirit_lexicon 28 (pilsner -> lager); beverage_categories pils under beer.bottom_fermented_beer",
   ["spirit_lexicon 28", "beverage_categories bc899a48-991c-4f5e-9668-6436721d514f"], ["brewery", "ABV", "pour size"]),
 "beta_dry_hopped_ipa": ("Hop-forward India pale ale, a top-fermented ale.",
   "draft (hop-forward); spirit_lexicon 27 (ipa); beverage_categories 'India Pale Ale' (beer.top_fermented_beer.ale)",
   ["spirit_lexicon 27", "beverage_categories edec21ae-ca4e-406c-b370-f2d371f64f1d"], ["brewery", "ABV", "pour size"]),
 "beta_amber_lager": ("Toasty and bottom-fermented, from the lager family.",
   "draft (toasty); beverage_categories amber lager styles under beer.bottom_fermented_beer.lager",
   ["beverage_categories 6b92613e-b1fb-1418-d5fb-399bfd0fdb1b", "beverage_categories ccbedf84-2c0f-3f07-fa85-895db7fc0f05"], ["brewery", "ABV", "pour size", "Czech or American style"]),
 "beta_dry_cider": ("Sparkling and dry; a fruit drink of its own, beside beer and wine.",
   "draft (dry, sparkling); spirit_lexicon 21 (cider); beverage_categories 'Cider' domain (filed with fruit wines, not beer) and 'Spirits & liqueurs' note (sibling of beer, wine, cider)",
   ["spirit_lexicon 21", "beverage_categories 5cae8177-7997-4a92-9ad2-e8c35051dbab", "beverage_categories 914ea33c-7cc8-454f-b925-a1164fddce5e"], ["producer", "ABV", "format (draft or can)"]),
 "beta_malbec": ("Dry red wine.", "draft words; no malbec row found (flagged)", [], ["producer", "region", "vintage", "malbec row in beverage_categories", "pour size"]),
 "beta_pinot_grigio": ("Dry white wine.", "draft words; no pinot grigio row found (flagged)", [], ["producer", "region", "vintage", "pinot grigio row in beverage_categories", "pour size"]),
 "beta_brut_rose": ("Dry and sparkling.", "draft words (dry, sparkling); no brut rosé row found (flagged)", [], ["producer", "region", "vintage", "glass or bottle price (label empty)"]),
}
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
        low = line.lower()
        assert it["name"].lower() not in low and "pour" not in low, (it["id"], line)
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

CARDS = [  # (n, id, english, eyebrow, kicker, icon, colour, groups)
 (1, ho["id"], "House Originals", "Cocktails", "Cócteles de la casa", "tumbler", "terra", [(None, ho["items"])]),
 (2, cl["id"], "Classics", "Cocktails", "Cócteles clásicos", "coupe", "agave", [(None, cl["items"])]),
]
for n, (sid, icon, col) in enumerate([("sec_spirits", "agave", "mari"), ("sec_beer", "tap", "terra"), ("sec_cider", "apple", "agave"), ("sec_wine", "bottle", "mari")], 3):
    s = next(x for x in new if x["id"] == sid)
    groups = ([(None, s["items"])] if s["items"] else []) + [(sb, sb["items"]) for sb in s["subs"]]
    CARDS.append((n, sid, s["name"], None, KICKER[sid], icon, col, groups))

doc["meta"] = dict(doc.get("meta") or {})
doc["meta"]["designer_notes"] = {
    "round": ROUND, "concept": "Lotería de la Cantina: each list is a numbered lotería card (frame, ordinal, cut-paper icon, banner with English name and Spanish kicker).",
    "cards": [{"n": c[0], "ref": c[1], "name": c[2], "kicker": c[4], "icon": c[5], "featured": c[0] == 1} for c in CARDS],
    "sub_kickers": {sb["name"]: ES[sb["id"]] for s in new for sb in s["subs"]},
    "copy_sources": {k: {"printed": v[0], "words_from": v[1], "gateway_rows": v[2], "missing": v[3]} for k, v in C.items()},
    "gateway_query": "one phg_designer_query over public.spirit_lexicon + public.beverage_categories (log_id 112); no rows for malbec, pinot grigio, brut rosé, or a cognac-specific VSOP",
    "manhattan_bitters": "Not printed: public_components aromatic-bitters = false (venue to confirm).",
    "brut_rose_price": "Printed as a plain price with no glass/bottle label (label empty in the draft; question open).",
    "retired_junmai_ginjo": "Retired Junmai Ginjo ($12) in phg.menu_items is not in the draft and is left off (please confirm).",
}
(OUT / "doc.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2))

# ------------------------------------------------------------ palette + graphics
P = dict(cream="#F6EEDF", card="#FBF5EA", feat="#F3E3CB", ink="#231B16", terra="#A63C1A", agave="#2F5D50", mari="#E3A018", muted="#5A4A3F")
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
    t, a, m, i, c = P["terra"], P["agave"], P["mari"], P["ink"], P["card"]
    g = {
     "tumbler": f'<path d="M9 11 L31 11 L29 34 Q29 36 27 36 L13 36 Q11 36 11 34 Z" fill="{t}"/><rect x="14.5" y="17" width="11" height="11" fill="{c}" transform="rotate(8 20 22.5)"/>'
                f'<path d="M26 4 Q34 6 35 14" stroke="{m}" stroke-width="3" fill="none"/>{dia(20, 32, 2, 1.5, c)}',
     "coupe": f'<path d="M5 9 L35 9 Q34 21 20 22 Q6 21 5 9 Z" fill="{a}"/><rect x="19" y="21" width="2" height="11" fill="{a}"/><path d="M12 36 Q20 30 28 36 Z" fill="{a}"/>'
              f'{dia(20, 14, 2.2, 3, c)}{dia(13, 13, 1.4, 2, c)}{dia(27, 13, 1.4, 2, c)}<circle cx="32" cy="8" r="5" fill="{m}"/><circle cx="32" cy="8" r="2" fill="{c}"/>',
     "agave": agave_leaves(20, 36, 32, a) + dia(20, 26, 1.6, 3, c) + dia(12, 28, 1.2, 2.2, c) + dia(28, 28, 1.2, 2.2, c) + f'<rect x="6" y="36" width="28" height="2.5" fill="{m}"/>',
     "tap": f'<rect x="15" y="2" width="10" height="17" rx="2" fill="{m}"/>{dia(20, 10, 2.2, 3.4, c)}<rect x="10" y="19" width="20" height="6" rx="1" fill="{t}"/>'
            f'<path d="M22 25 L22 31 L17 31 L17 28 L19 28 L19 25 Z" fill="{t}"/><circle cx="18.2" cy="35" r="2" fill="{m}"/>',
     "apple": f'<path d="M20 12 C12 6 4 12 6 22 C8 32 14 38 20 35 C26 38 32 32 34 22 C36 12 28 6 20 12 Z" fill="{a}"/><path d="M21 11 Q24 3 31 4 Q28 11 21 11 Z" fill="{m}"/>'
              f'<rect x="19.2" y="5" width="1.6" height="7" fill="{i}"/>{dia(20, 23, 3, 4.5, c)}{dia(20, 23, 1.2, 1.8, a)}',
     "bottle": f'<path d="M17 2 L23 2 L23 11 Q29 14 29 20 L29 36 Q29 38 27 38 L13 38 Q11 38 11 36 L11 20 Q11 14 17 11 Z" fill="{t}"/><rect x="16" y="1" width="8" height="3" fill="{i}"/>'
               f'<rect x="13.5" y="21" width="13" height="11" fill="{c}"/>{dia(20, 26.5, 2.4, 3.2, m)}',
    }[kind]
    return f'<svg class="icon" viewBox="0 0 40 40" width="{size}pt" height="{size}pt" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">{g}</svg>'

def nb(t):
    t = html.escape(t); i = t.rfind(" ")
    return t[:i] + "&nbsp;" + t[i+1:] if i > 0 else t

def item_html(it):
    return (f'<div class="item" data-ref="{it["id"]}"><div class="row"><span class="name">{html.escape(it["name"])}</span>'
            f'<span class="price num">{it["prices"][0]["value"]:g}</span></div><p class="desc">{nb(it["desc"])}</p></div>')

def card_html(n, cid, name, eyebrow, kicker, ic, col, groups):
    f = n == 1
    body = []
    for sb, items in groups:
        if sb is not None:
            body.append(f'<div class="sub" data-id="{sb["id"]}"><h3>{html.escape(sb["name"])}</h3><span class="es">{ES[sb["id"]]}</span><span class="subrule"></span></div>')
        body.append('<div class="items">' + "".join(item_html(i) for i in items) + "</div>")
    eb = f'<span class="eyebrow">{eyebrow}</span>' if eyebrow else ""
    return (f'<article class="card c-{col}{" featured" if f else ""}" id="card-{n}" data-id="{cid}" data-n="{n}">'
            f'<header class="head"><span class="cardno num">{n}</span><div class="bannerband">{eb}<h2>{html.escape(name)}</h2><span class="kicker">{kicker}</span></div>'
            f'{icon(ic, 46 if f else 36)}</header><div class="body">{"".join(body)}</div></article>')

cards = [card_html(*c) for c in CARDS]
tabs = "".join(f'<a class="tab c-{c[6]}" href="#card-{c[0]}"><span class="num">{c[0]}</span> {html.escape(c[2])}</a>' for c in CARDS)

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
/* numeral system: card ordinals and prices share one face, weight, colour and lining tabular figures */
.num { font-family:'Fraunces', serif; font-weight:600; color:$terra; font-variant-numeric:lining-nums tabular-nums; font-feature-settings:'lnum' 1,'tnum' 1; }
.deck { flex:1; display:grid; grid-template-columns:1fr 1fr; grid-template-rows:auto auto auto; gap:12pt; min-height:0; }
.top { grid-column:1 / 3; display:grid; grid-template-columns:318pt 1fr; gap:12pt; }
.card { position:relative; display:flex; flex-direction:column; background:$card; border:1.5pt solid $ink;
        box-shadow: inset 0 0 0 3pt $card, inset 0 0 0 3.75pt $ink; padding:9pt 12pt 10pt; min-height:0; }
.card.featured { background:$feat; border-color:$terra; box-shadow: inset 0 0 0 3pt $feat, inset 0 0 0 4.5pt $terra; }
.head { display:flex; align-items:center; gap:8pt; height:38pt; flex:none; }
.featured .head { height:54pt; }
.cardno { width:24pt; font-size:26pt; line-height:1; text-align:left; flex:none; }
.featured .cardno { width:30pt; font-size:36pt; }
.icon { flex:none; display:block; }
.bannerband { flex:1; align-self:stretch; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; margin:2pt 0;
   clip-path:polygon(0 0,100% 0,calc(100% - 7pt) 50%,100% 100%,0 100%,7pt 50%); padding:0 12pt; }
.c-terra .bannerband { background:$terra; color:$cream; } .c-agave .bannerband { background:$agave; color:$cream; } .c-mari .bannerband { background:$mari; color:$ink; }
.bannerband h2 { font-family:'Fraunces', serif; font-weight:700; font-size:13.5pt; line-height:15pt; margin:0; white-space:nowrap; }
.featured .bannerband h2 { font-size:17pt; line-height:19pt; }
.eyebrow { font-size:6.5pt; line-height:8pt; letter-spacing:1.8pt; text-transform:uppercase; font-weight:700; opacity:.9; }
.kicker { font-family:'Fraunces', serif; font-style:italic; font-size:9pt; line-height:11pt; font-weight:500; }
.body { flex:1; margin-top:6pt; border-top:0.75pt solid $ink; padding-top:6pt; }
.featured .body { border-top-color:$terra; }
.sub { display:flex; align-items:baseline; gap:6pt; height:12pt; margin-bottom:3pt; }
.items + .sub { margin-top:7pt; }
h3 { margin:0; font-size:7.5pt; line-height:12pt; letter-spacing:1.6pt; text-transform:uppercase; color:$agave; font-weight:700; white-space:nowrap; }
.sub .es { font-family:'Fraunces', serif; font-style:italic; font-size:9pt; color:$terra; white-space:nowrap; }
.subrule { flex:1; border-top:0.5pt solid $agave; opacity:.5; align-self:center; }
.item + .item { margin-top:5pt; }
.row { display:flex; justify-content:space-between; align-items:baseline; }
.name { font-family:'Fraunces', serif; font-size:11.5pt; line-height:14pt; font-weight:600; }
.price { font-size:11.5pt; line-height:14pt; margin-left:10pt; }
.desc { margin:0; padding-right:14pt; font-size:8.5pt; line-height:11pt; color:$muted; }
.featured .name, .featured .price { font-size:14pt; line-height:17pt; }
.featured .desc { font-size:9.5pt; line-height:12.5pt; }
.featured .item + .item { margin-top:11pt; }
.foot { display:flex; align-items:center; gap:10pt; height:12pt; margin-top:6pt; flex:none; }
.foot .fr { flex:1; border-top:0.5pt solid $ink; opacity:.5; }
.foot .salud { font-family:'Fraunces', serif; font-style:italic; font-size:11pt; color:$terra; font-weight:600; }
@media screen and (max-width: 600px) {
  html, body { background:$cream; }
  .page { width:auto; height:auto; padding:0 16px 24px; display:block; }
  .banner { display:none; } .banner-m { display:block; width:100%; height:auto; margin-top:12px; }
  .title { font-size:32px; line-height:38px; margin-top:12px; text-wrap:balance; }
  .loc { font-size:11px; line-height:16px; margin-bottom:12px; }
  .tabs { display:flex; position:sticky; top:0; z-index:5; gap:4px; overflow-x:auto; background:$cream; padding:6px 0 10px; margin:0 -16px 12px; padding-left:16px; scrollbar-width:none; }
  .tab { flex:none; text-decoration:none; font-size:13px; font-weight:700; padding:7px 10px 13px; clip-path:polygon(0 0,100% 0,100% 78%,50% 100%,0 78%); }
  .tab .num { color:inherit; }
  .tab.c-terra { background:$terra; color:$cream; } .tab.c-agave { background:$agave; color:$cream; } .tab.c-mari { background:$mari; color:$ink; }
  .deck, .top { display:block; }
  .card { margin-bottom:16px; scroll-margin-top:64px; padding:12px 16px 16px; }
  .head, .featured .head { height:auto; min-height:56px; }
  .bannerband { padding:6px 14px; }
  .bannerband h2 { font-size:20px; line-height:24px; white-space:normal; } .featured .bannerband h2 { font-size:23px; line-height:27px; }
  .eyebrow { font-size:10px; line-height:13px; } .kicker { font-size:14px; line-height:18px; }
  .cardno { font-size:32px; width:26px; } .featured .cardno { font-size:40px; width:32px; }
  .sub { height:auto; margin-bottom:8px; } h3 { font-size:11.5px; line-height:18px; } .sub .es { font-size:14px; }
  .name, .price, .featured .name, .featured .price { font-size:18px; line-height:24px; }
  .desc, .featured .desc { font-size:14.5px; line-height:20px; padding-right:28px; }
  .item + .item, .featured .item + .item { margin-top:14px; } .items + .sub { margin-top:16px; }
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
<main class="deck"><div class="top">{cards[0]}{cards[1]}</div>{"".join(cards[2:])}</main>
<footer class="foot"><span class="fr"></span><span class="salud">¡Salud!</span><span class="fr"></span></footer>
</div></body></html>
"""
(OUT / "menu.html").write_text(HTML)
print("built round", ROUND, "cards", [c[2] for c in CARDS])
