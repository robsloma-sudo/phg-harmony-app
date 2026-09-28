"""TEST-1 round 6: Lotería de la Cantina, real lotería anatomy.
Six portrait lotería cards on a 3 x 2 grid (featured agave card top-left), built from the verbatim draft doc.
Every printed line is traced in doc.meta.designer_notes.copy_sources (gateway rows, draft words, recipe words)."""
import json, copy, html, pathlib, base64, math, re
from string import Template

HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path("/home/user/phg-harmony-app/handoff/designs/test-1-iowa-city-cantina")
draft = json.loads((HERE / "draft_doc.json").read_text())
ROUND = 10

# ------------------------------------------------------------ copy + sources (draft menu_description words; one gateway row)
C = {  # id: (printed line, words from, gateway row ids, still missing)
 "beta_old_fashioned": ("Brown butter-washed bourbon, demerara and bitters.",
   "draft desc (brown butter-washed bourbon, demerara, bitters); draft_doc components: 'Demerara Syrup' (prep); serve_format 'Stir with ice and strain over a large cube'; recipe (orange peel)", [], ["allergen confirmation (brown butter: dairy)"]),
 "beta_daiquiri": ("White rum, fresh lime and house demerara syrup.",
   "draft desc (white rum, lime, house demerara syrup); draft_doc components: 'Fresh Lime Juice', 'Demerara Syrup' ('House 1:1 demerara syrup'); serve_format 'Shake with ice and fine strain'; recipe (lime coin, coupe)", [], []),
 "beta_margarita": ("Bright and citrus-forward: blanco tequila, fresh lime, orange liqueur and agave syrup.",
   "draft desc (tequila blanco, lime, orange liqueur, agave, 'Bright and citrus-forward'); draft_doc components: 'Fresh Lime Juice', 'Agave Syrup' (prep); serve_format 'Shake with ice and strain over fresh ice'; recipe (lime wheel)", [], []),
 "beta_manhattan": ("Rye whiskey and sweet vermouth.",
   "draft desc (rye, sweet vermouth); draft_doc components: 'Rye Whiskey', 'Cocktail Cherry'; serve_format 'Stir with ice and strain'; recipe (coupe). Bitters hidden: public_components aromatic-bitters = false", [], ["venue to confirm hiding the bitters"]),
 "beta_blanco_tequila": ("",
   "name only (round 8: spirits are name-only for consistency). Row checked: beverage_categories row 04d72e1f: name 'Blanco / plata', node_kind 'style', path spirits.agave_spirits.tequila.blanco (gateway log_id 130). 'Unaged' is not in the row, so it is not printed",
   ["beverage_categories 04d72e1f-650d-490c-8ad8-54a6eb8aa766"], ["brand", "age statement (n/a for blanco)", "pour size"]),
 "beta_anejo_tequila": ("", "name only: gateway log_id 130 found row 9f4dae69 (name 'Añejo', notes null): no guest words beyond the name; the draft line 'Añejo tequila pour.' only repeats the name", ["beverage_categories 9f4dae69-e84c-4b65-b7d9-1b417658b78d (checked, nothing printable)"], ["brand", "pour size", "age statement", "guest line"]),
 "beta_cognac_vsop": ("", "name only (round 8: spirits are name-only for consistency). Rows checked: beverage_categories rows a88f6e79 (Cognac, path spirits.brandy_fruit_spirits.grape_brandy.cognac) and bec5063c (VSOP, child of Cognac); 'grape brandy' is the parent node in the cited path (gateway log_id 130)", ["beverage_categories a88f6e79-9438-6e3d-2656-406fad2b829f", "beverage_categories bec5063c-5274-9534-91da-53a2f10c8255"], ["brand / house", "pour size"]),
 "beta_czech_pilsner": ("Crisp pale lager.", "draft menu_description, verbatim", [], ["brewery", "ABV", "pour size"]),
 "beta_dry_hopped_ipa": ("Hop-forward draft IPA.", "draft menu_description, verbatim", [], ["brewery", "ABV", "pour size"]),
 "beta_amber_lager": ("Toasty amber lager.", "draft menu_description, verbatim", [], ["brewery", "ABV", "pour size"]),
 "beta_dry_cider": ("Dry sparkling cider.", "draft menu_description, verbatim", [], ["producer", "ABV", "format (draft or can)"]),
 "beta_malbec": ("Dry red wine.", "draft menu_description, verbatim", [], ["producer", "region", "vintage", "pour size"]),
 "beta_pinot_grigio": ("Dry white wine.", "draft menu_description, verbatim", [], ["producer", "region", "vintage", "pour size"]),
 "beta_brut_rose": ("Dry sparkling rosé.", "draft menu_description, verbatim", [], ["producer", "region", "vintage", "glass or bottle price (label empty)"]),
}
SERVE = {"beta_old_fashioned": "Over one large cube, orange peel.", "beta_daiquiri": "In a coupe, lime coin.", "beta_margarita": "On the rocks, lime wheel.", "beta_manhattan": "In a coupe, cocktail cherry."}
BANNED = ["nom-006", "class", "shelf", "fermented", "lager family", "beside beer", "age grade", "pour"]
for k, v in C.items():
    assert not any(w in v[0].lower() for w in BANNED), k
    assert not any(r in " ".join(v[2]) for r in ("d4d63f58", "bc899a48")), k
ES = {"sub_cocktails_classics": "Clásicos", "sub_cocktails_house_originals": "De la casa", "sub_spirits_agave": "Agave",
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
new[0]["subs"] = [cl, ho]
for s in new:
    for sb in s["subs"]:
        if sb["id"] not in ES:  # sub ids differ from the guessed keys: map by name
            ES[sb["id"]] = {"Agave": "Agave", "Brandy": "Brandy y coñac", "Draft": "De barril", "By the Glass": "Por copa", "Sparkling": "Espumoso",
                            "Classics": "Clásicos", "House Originals": "De la casa"}[sb["name"]]
    for it in s["items"] + [i for sb in s["subs"] for i in sb["items"]]:
        line, src, rows, miss = C[it["id"]]
        it["desc"] = (line + " " + SERVE[it["id"]]) if it["id"] in SERVE else line; it.pop("missing_ingredients", None)
        it["meta"] = dict(it.get("meta") or {}); it["meta"]["missing_ingredients"] = list(miss)
assert all(";" not in C[k][0] for k in C)
assert "pour" not in " ".join(v[0].lower() for v in C.values())
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
cider_sub = {"id": "sec_cider", "name": "Cider"}; ES["sec_cider"] = "Sidra"; ES[cl["id"] + "_2"] = ES[cl["id"]]
CARDS = [  # (n, ref, english gloss, tab label, loteria title, figure, colour, groups, cantor verse)
 (1, "sec_cocktails", "Cocktails", "El Cantarito", "El Cantarito", "cantarito", "terra",
     [(cl, [allitems["beta_margarita"], allitems["beta_manhattan"]]), (ho, ho["items"])],
     "Tanto va el cántaro al agua, que se quiebra y te moja las enaguas."),
 (2, "sec_spirits", "Spirits", "La Botella", "La Botella", "bottle", "ink",
     [(subn["Agave"], subn["Agave"]["items"]), (subn["Brandy"], subn["Brandy"]["items"])], "La herramienta del borracho."),
 (3, "sec_beer", "Beer & Cider", "El Barril", "El Barril", "barrel", "agave",
     [(subn["Draft"], subn["Draft"]["items"]), (cider_sub, next(x for x in new if x["id"] == "sec_cider")["items"])],
     "Tanto bebió el albañil, que quedó como barril."),
 (4, "sec_wine", "Wine", "La Rosa", "La Rosa", "rose", "rosa",
     [(subn["By the Glass"], subn["By the Glass"]["items"]), (subn["Sparkling"], subn["Sparkling"]["items"])], "Rosita, Rosaura, ven que te quiero ver."),
]
assert sorted(i["id"] for c in CARDS for g in c[7] for i in g[1]) == sorted(allitems), "every item on exactly one card"
doc["meta"] = dict(doc.get("meta") or {})
doc["meta"]["designer_notes"] = {
    "round": ROUND, "concept": "Lotería de la Cantina: a 2 x 2 tabla of four lotería cards (El Cantarito featured top-left, La Botella, El Barril, La Rosa). Each card: our own ordinal 1-4 and the cantor verse on the top row, a fixed cut-paper figure box, the Spanish lotería name as the one card title in a coloured name bar, a small italic English gloss under it, then the list.", "concept_r6": "six portrait lotería cards, each with the ordinal in the top-left corner, the English list name, a large central cut-paper figure and a lotería name bar at the foot (EL AGAVE, EL VASO, LA COPA, CERVEZA Y SIDRA, LA COPITA, LA BOTELLA). Card 1 tells the agave story: Margarita, then Blanco and Añejo.",
    "cards": [{"n": c[0], "ref": c[1], "name": c[2], "loteria_name": c[4].upper(), "cantor_verse": c[8], "verse_status": "cultural text (traditional lotería cantor verse), not an item fact", "figure": c[5], "featured": c[0] == 1, "items": [i["id"] for g in c[7] for i in g[1]]} for c in CARDS],
    "sub_kickers": {sb["name"]: ES[sb["id"]] for s in new for sb in s["subs"]},
    "copy_sources": {k: {"printed": (v[0] + " " + SERVE[k]) if k in SERVE else v[0], "serve_cue": SERVE.get(k, ""), "words_from": v[1], "gateway_rows": v[2], "missing": v[3]} for k, v in C.items()},
    "gateway_query": "round 5 phg_designer_query (log_id 112) over public.beverage_categories; round 7 query log_id 130 (añejo, cognac, VSOP; rhum agricole excluded): cited rows 04d72e1f (Blanco / plata), 9f4dae69 (Añejo, nothing printable), a88f6e79 (Cognac) and bec5063c (VSOP). Beer, cider and wine lines are the draft menu_description words.",
    "manhattan_bitters": "Not printed: public_components aromatic-bitters = false (venue to confirm).",
    "brut_rose_price": "Printed under its own Espumoso (Sparkling) subheader, apart from the Por copa glass list, so it does not read as a glass price; the glass/bottle label is empty in the draft (question open).",
    "card_layout": "2 x 2 grid, columns 312 / 216 pt, 12 pt gutter; fixed rows of 12 pt steps", "card_layout_r6": "3 x 2 portrait grid: featured column 196 pt, two 160 pt columns, 12 pt gutters. Classics and Brandy are separate one-item cards so every card stays a portrait with a full figure.",
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

def papel(n=11, W=540, H=24, cls="banner", dims='width="540pt" height="24pt"'):
    cell = W / n; fw = cell - 6; cols = [P["terra"], P["mari"], P["agave"], P["rosa"]]
    o = [f'<svg class="{cls}" viewBox="0 0 {W} {H}" {dims} xmlns="http://www.w3.org/2000/svg" aria-hidden="true">',
         f'<path d="M1 0.4 Q{W/2} 4 {W-1} 0.4" stroke="{P["ink"]}" stroke-width="0.8" fill="none"/>']
    for k in range(n):
        x = k * cell + 3; top, hem = 3, H - 4; c = cols[k % 4]; sw = fw / 5
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
     "cantarito": f'<path d="M13 6 L27 6 L25 11 Q35 16 33 26 Q31 37 20 37 Q9 37 7 26 Q5 16 15 11 Z" fill="{t}"/><path d="M31 15 Q39 17 36 26 Q35 29 32 29" stroke="{t}" stroke-width="2.6" fill="none"/>'
                  f'<rect x="12" y="4" width="16" height="3" fill="{i}"/><path d="M9 22 L31 22 L31 25 L9 25 Z" fill="{m}"/>{dia(20, 29.5, 2.4, 3.2, c)}{dia(13, 29.5, 1.4, 2, pk)}{dia(27, 29.5, 1.4, 2, pk)}',
     "rose": f'<path d="M20 20 L20 38" stroke="{a}" stroke-width="2.2"/><path d="M20 30 Q12 26 10 30 Q15 34 20 31 Z" fill="{a}"/><path d="M20 26 Q28 22 30 26 Q25 30 20 27 Z" fill="{a}"/>'
             f'<circle cx="20" cy="13" r="10" fill="{pk}"/><path d="M13 12 Q20 4 27 12 Q20 9 13 12 Z" fill="{c}"/><path d="M15 16 Q20 22 25 16 Q20 18 15 16 Z" fill="{c}"/>{dia(20, 12.5, 1.8, 2.4, c)}',
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


def item_html(it, inline):
    d = it["desc"]
    if inline:
        dd = f'<span class="desc in">{html.escape(d)}</span>' if d else ""
        return (f'<div class="item" data-ref="{it["id"]}"><div class="row"><span class="name">{nb(it["name"])}</span>{dd}<span class="lead"></span>'
                f'<span class="price num">{it["prices"][0]["value"]:g}</span></div></div>')
    if it["id"] in SERVE:
        ln = C[it["id"]][0]; t = re.sub(r"(\w+(?:-\w+)+)", r'<span class="nw">\1</span>', html.escape(ln))
        dd = f'<p class="desc"><span class="chr">{t}</span> <span class="cue">{nb(SERVE[it["id"]])}</span></p>'
    else:
        dd = f'<p class="desc">{nb(d)}</p>' if d else ""
    return (f'<div class="item" data-ref="{it["id"]}"><div class="row"><span class="name">{nb(it["name"])}</span><span class="lead"></span>'
            f'<span class="price num">{it["prices"][0]["value"]:g}</span></div>{dd}</div>')

def card_html(n, cid, name, tab, lot, fig, col, groups, verse):
    f = n == 1; inline = cid in ("sec_beer", "sec_wine")
    body = []
    for sb, items in groups:
        body.append(f'<div class="sub" data-id="{sb["id"]}"><h3>{html.escape(sb["name"])}</h3><span class="subrule"></span></div>')
        body.append('<div class="items">' + "".join(item_html(i, inline) for i in items) + "</div>")
    return (f'<article class="card c-{col}{" featured" if f else ""}" id="card-{n}" data-id="{cid}" data-n="{n}">'
            f'<div class="face"><div class="art"><div class="figure">{icon(fig, "fig")}</div><p class="verse" lang="es">{html.escape(verse)}</p></div>'
            f'<div class="namebar"><h2 lang="es">{html.escape(lot.upper())}</h2><span class="gloss" lang="en">{html.escape(name)}</span></div></div>'
            f'<div class="body">{"".join(body)}</div></article>')

cards = [card_html(*c) for c in CARDS]
tabs = "".join(f'<a class="tab c-{c[6]}{" active" if c[0] == 1 else ""}" data-n="{c[0]}" href="#card-{c[0]}" aria-label="{html.escape(c[4])}, {html.escape(c[2])}">'
               f'{icon(c[5], "ticon")}<span class="lbl">{html.escape(c[3])}</span></a>' for c in CARDS)
JS = """<script>(()=>{const t=[...document.querySelectorAll('.tab')],s=n=>t.forEach(a=>{const on=a.dataset.n==n;a.classList.toggle('active',on);on?a.setAttribute('aria-current','true'):a.removeAttribute('aria-current')});
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
.c-terra { --c:$terra; --tint:#F3E3CB; } .c-agave { --c:$agave; --tint:#E4EBE2; } .c-ink { --c:$ink; --tint:#ECE4D6; } .c-rosa { --c:$rosa; --tint:#F7E3E8; }
.page { width:612pt; height:792pt; padding:15pt 36pt; background:$cream; display:flex; flex-direction:column; margin:0 auto; }
.banner { display:block; width:540pt; height:24pt; flex:none; }
.banner-m, .tabs { display:none; }
.title { font-family:'Fraunces', serif; font-weight:700; font-size:24pt; line-height:24pt; height:24pt; letter-spacing:-0.3pt; text-align:center; margin:18pt 0 0; }
.title .amp { color:$terra; font-style:italic; font-weight:600; }
.loc { text-align:center; font-size:8.5pt; line-height:12pt; height:12pt; letter-spacing:3pt; text-transform:uppercase; color:$muted; font-weight:500; margin:0 0 12pt; }
.num { font-family:'Fraunces', serif; font-weight:600; color:var(--c, $terra); font-variant-numeric:lining-nums tabular-nums; font-feature-settings:'lnum' 1,'tnum' 1; }
.nw { white-space:nowrap; }
.deck { flex:none; display:grid; grid-template-columns:264pt 264pt; grid-template-rows:auto auto auto; gap:12pt; }
.card { position:relative; display:flex; flex-direction:column; background:$card; border:1.5pt solid var(--c); padding:0 0 10.5pt; }
.featured { grid-column:1; grid-row:1 / span 3; }
#card-2 { grid-column:2; grid-row:1; } #card-3 { grid-column:2; grid-row:2; } #card-4 { grid-column:2; grid-row:3; }
.face { flex:none; height:58.5pt; display:flex; flex-direction:column; background:var(--tint); box-shadow: inset 0 0 0 3pt var(--tint), inset 0 0 0 3.75pt var(--c); }
.featured .face { flex:1 1 auto; height:auto; }
.art { flex:1; min-height:0; display:flex; align-items:center; gap:6pt; padding:0 12pt 0 6pt; }
.figure { position:relative; flex:none; width:72pt; height:34.5pt; }
.figure .fig { position:absolute; left:0; top:3pt; width:100%; height:calc(100% - 3pt); display:block; }
.verse { margin:0; flex:1; text-align:center; font-family:'Fraunces', serif; font-style:italic; font-weight:400; font-size:9pt; line-height:12pt; color:$muted; text-wrap:balance; }
.featured .art { flex-direction:column; align-items:stretch; padding:18pt 18pt 6pt; gap:0; }
.featured .verse { flex:none; order:-1; font-size:10.5pt; line-height:12pt; height:24pt; }
.featured .figure { flex:1 1 auto; width:auto; height:auto; }
.featured .figure .fig { top:6pt; height:calc(100% - 6pt); }
.namebar { flex:none; height:24pt; display:flex; align-items:baseline; justify-content:center; gap:6pt; background:var(--c); color:$cream; }
.namebar h2 { margin:0; font-family:'Fraunces', serif; font-weight:700; font-size:12pt; line-height:24pt; letter-spacing:2pt; white-space:nowrap; }
.gloss { font-family:'Fraunces', serif; font-style:italic; font-size:8.5pt; line-height:24pt; white-space:nowrap; opacity:.9; }
.featured .namebar { height:36pt; } .featured .namebar h2 { font-size:16pt; line-height:36pt; letter-spacing:3pt; } .featured .gloss { font-size:10pt; line-height:36pt; }
.body { flex:none; margin-top:12pt; padding:0 10.5pt; }
.sub { display:flex; align-items:center; gap:6pt; height:12pt; margin-bottom:12pt; }
.items + .sub { margin-top:24pt; }
h3 { margin:0; font-size:7pt; line-height:12pt; letter-spacing:1.4pt; text-transform:uppercase; color:$ink; font-weight:700; white-space:nowrap; }
.subrule { flex:1; border-top:0.75pt solid var(--c); }
.item + .item { margin-top:12pt; }
.row { display:flex; align-items:baseline; height:12pt; }
.lead { flex:1; }
.name { font-family:'Fraunces', serif; font-size:10.5pt; line-height:12pt; font-weight:600; }
.price { font-size:10.5pt; line-height:12pt; margin-left:8pt; }
.desc { margin:0; padding-right:8pt; font-size:8pt; line-height:12pt; color:$muted; }
.desc .chr { color:$ink; } .desc .cue { font-style:italic; color:$muted; }
.desc.in { margin-left:6pt; padding-right:0; white-space:nowrap; }
.foot { display:block; height:0; margin:0; flex:none; }
@media screen and (max-width: 600px) {
  html, body { background:$cream; }
  .page { width:auto; height:auto; padding:0 16px 24px; display:block; }
  .banner { display:none; } .banner-m { display:block; width:100%; height:auto; margin-top:12px; }
  .title { font-size:32px; line-height:38px; height:auto; margin-top:12px; text-wrap:balance; }
  .loc { font-size:11px; line-height:16px; height:auto; margin-bottom:12px; }
  .tabs { display:grid; grid-template-columns:repeat(2, 1fr); gap:6px; position:sticky; top:0; z-index:5; background:$cream; padding:6px 0 8px; margin:0 0 16px; }
  .tab { min-width:0; display:flex; align-items:center; gap:6px; text-decoration:none; padding:4px 8px; border:1.5px solid var(--c); border-radius:2px; background:$card; color:$ink; }
  .tab .ticon { width:22px; height:22px; flex:none; }
  .tab .lbl { font-family:'Fraunces', serif; font-size:13px; line-height:18px; font-weight:700; letter-spacing:1px; white-space:nowrap; text-transform:uppercase; }
  .tab.active { background:var(--c); color:$cream; box-shadow: inset 0 -4px 0 $ink; } .
  .tab.active .ticon { background:$card; border-radius:3px; }
  .deck { display:block; }
  .card { margin:0 4px 24px; scroll-margin-top:110px; background:transparent; border:0; padding:0 0 16px; isolation:isolate; }
  .card::before { content:""; position:absolute; inset:0; z-index:-1; background:$card; border:1.5px solid var(--c); box-shadow:3px 4px 0 rgba(35,27,22,.18); transform:rotate(-1deg); }
  .card:nth-child(even)::before { transform:rotate(1deg); }
  .face, .featured .face { height:auto; background:transparent; box-shadow:none; }
  .art, .featured .art { flex-direction:column; align-items:stretch; padding:16px 16px 8px; gap:8px; }
  .verse, .featured .verse { order:-1; height:auto; font-size:14px; line-height:20px; }
  .figure, .featured .figure { flex:none; width:100%; height:128px; }
  .figure .fig, .featured .figure .fig { top:0; height:100%; }
  .namebar, .featured .namebar { height:40px; margin:0 12px; } .namebar h2, .featured .namebar h2 { font-size:18px; line-height:40px; letter-spacing:2px; }
  .gloss, .featured .gloss { font-size:14px; line-height:40px; }
  .body { margin-top:14px; padding:0 16px; }
  .sub { height:auto; } h3 { font-size:11.5px; line-height:20px; }
  .row { flex-wrap:wrap; height:auto; } .name, .price { font-size:18px; line-height:24px; }
  .desc { font-size:14.5px; line-height:20px; padding-right:24px; }
  .desc.in { order:3; flex-basis:100%; margin-left:0; white-space:normal; }
  .item + .item { margin-top:12px; } .items + .sub { margin-top:24px; } .sub { margin-bottom:12px; }
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
<footer class="foot" aria-hidden="true"></footer>
</div>{JS}</body></html>
"""
(OUT / "menu.html").write_text(HTML)

N = doc["meta"]["designer_notes"]
N["concept"] = ("Lotería de la Cantina, 1 + 3 tabla: El Cantarito is the tall featured card filling the left column; La Botella, El Barril and La Rosa stack in the right column and end on the same baseline. "
                "Every card has a face (framed tinted panel in its palette colour) holding a large cut-paper figure, the cantor verse (9 pt or larger) and the lotería name cartouche at its foot "
                "(Spanish name + small English gloss, the one bilingual device); the drinks list sits below the face as the card's reverse. No ordinals. English-only subheaders.")
N["card_layout"] = "1 + 3: columns 264 / 264 pt, 12 pt gutter; right cards 204 / 240 / 204 pt with 12 pt gaps = 672 pt = the featured card; everything on a 12 pt grid from the deck top"
N["sub_kickers"] = {sb["name"]: "(English only)" for s in new for sb in s["subs"]}
N["rosa"] = "Lotería rosa is one of the four card colours (La Rosa) and one of the four papel picado colours, like terracotta, agave and marigold; no other rosa accents."
N["ordinals"] = "Dropped in round 8 (read as wrong deck numbers)."
for cc in N["cards"]:
    cc["printed_ordinal"] = None
(OUT / "doc.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2))
print("built round", ROUND, "cards", [c[2] for c in CARDS])
