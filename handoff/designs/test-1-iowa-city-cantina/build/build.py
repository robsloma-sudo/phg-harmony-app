"""TEST-1 round 11: Lotería de la Cantina, a real lotería tabla.
Four lotería cards (2 + 2): El Cantarito (44, featured, top-left, tallest) over La Botella (8); El Barril (9) over La Rosa (41).
Every card: thick frame, Don Clemente number in the top-left corner, figure + verse face, name band under the figure, list below.
Every printed line is traced in doc.meta.designer_notes.copy_sources (draft words, draft components, gateway rows)."""
import json, copy, html, pathlib, base64, math, re
from string import Template

HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path("/home/user/phg-harmony-app/handoff/designs/test-1-iowa-city-cantina")
draft = json.loads((HERE / "draft_doc.json").read_text())
ROUND = 11
NBSP = " "

# ------------------------------------------------------------ copy + sources (draft words only)
C = {  # id: (character line, words from, gateway row ids, still missing)
 "beta_old_fashioned": ("Brown butter-washed bourbon, demerara and bitters.",
   "draft desc (brown butter-washed bourbon, demerara, bitters); draft_doc components: 'Demerara Syrup' (prep), 'Aromatic Bitters'; serve_format 'Stir with ice and strain over a large cube'; recipe (orange peel)", [], ["allergen confirmation (brown butter: dairy)"]),
 "beta_daiquiri": ("White rum, fresh lime and house demerara syrup.",
   "draft desc (white rum, lime, house demerara syrup); draft_doc components: 'Fresh Lime Juice', 'Demerara Syrup' ('House 1:1 demerara syrup'); serve_format 'Shake with ice and fine strain'; recipe (lime coin, coupe). No flavour lead: the draft has no character words for it (family 'Sour' is a class, not guest copy)", [], []),
 "beta_margarita": ("Bright and citrus-forward: blanco tequila, fresh lime, orange liqueur and agave syrup.",
   "draft desc (tequila blanco, lime, orange liqueur, agave, 'Bright and citrus-forward'); draft_doc components: 'Fresh Lime Juice', 'Agave Syrup' (prep); serve_format 'Shake with ice and strain over fresh ice'; recipe (lime wheel)", [], []),
 "beta_manhattan": ("Spirit-forward: rye whiskey, sweet vermouth and aromatic bitters.",
   "draft desc / menu_items.menu_description 'Rye, sweet vermouth, aromatic bitters.'; draft meta.family 'Spirit-Forward' (character lead); draft_doc components: 'Rye Whiskey', 'Sweet Vermouth', 'Aromatic Bitters', 'Cocktail Cherry'; serve_format 'Stir with ice and strain'; recipe (coupe). Bitters printed: the venue's own menu_description names them, so the public_components hide is dropped", [], []),
 "beta_blanco_tequila": ("Tequila blanco, by the pour.",
   "draft desc 'Blanco tequila pour.' in guest form (no words added). Row checked: beverage_categories 04d72e1f 'Blanco / plata' (gateway log_id 130)",
   ["beverage_categories 04d72e1f-650d-490c-8ad8-54a6eb8aa766"], ["brand", "pour size"]),
 "beta_anejo_tequila": ("Tequila añejo, by the pour.",
   "draft desc 'Añejo tequila pour.' in guest form (no words added). Row checked: beverage_categories 9f4dae69 'Añejo' (gateway log_id 130)",
   ["beverage_categories 9f4dae69-e84c-4b65-b7d9-1b417658b78d"], ["brand", "age statement", "pour size"]),
 "beta_cognac_vsop": ("VSOP Cognac, by the pour.",
   "draft desc 'VSOP Cognac pour.' in guest form (no words added). Rows checked: beverage_categories a88f6e79 (Cognac) and bec5063c (VSOP) (gateway log_id 130)",
   ["beverage_categories a88f6e79-9438-6e3d-2656-406fad2b829f", "beverage_categories bec5063c-5274-9534-91da-53a2f10c8255"], ["brand / house", "pour size"]),
 "beta_czech_pilsner": ("Crisp pale lager.", "draft menu_description, verbatim", [], ["brewery", "ABV", "pour size"]),
 "beta_dry_hopped_ipa": ("Hop-forward draft IPA.", "draft menu_description, verbatim", [], ["brewery", "ABV", "pour size"]),
 "beta_amber_lager": ("Toasty amber lager.", "draft menu_description, verbatim", [], ["brewery", "ABV", "pour size"]),
 "beta_dry_cider": ("Dry sparkling cider.", "draft menu_description, verbatim", [], ["producer", "ABV", "format (draft or can)"]),
 "beta_malbec": ("Dry red wine.", "draft menu_description, verbatim", [], ["producer", "region", "vintage", "pour size"]),
 "beta_pinot_grigio": ("Dry white wine.", "draft menu_description, verbatim", [], ["producer", "region", "vintage", "pour size"]),
 "beta_brut_rose": ("Dry sparkling rosé.", "draft menu_description, verbatim", [], ["producer", "region", "vintage", "glass or bottle (price label empty in the draft)"]),
}
# serve cues: non-breaking spaces inside the fixed phrases; the whole cue is also kept on one line in CSS
SERVE = {"beta_old_fashioned": f"Over one{NBSP}large{NBSP}cube, orange{NBSP}peel.", "beta_daiquiri": f"In{NBSP}a{NBSP}coupe, lime{NBSP}coin.",
         "beta_margarita": f"On{NBSP}the{NBSP}rocks, lime{NBSP}wheel.", "beta_manhattan": f"In{NBSP}a{NBSP}coupe, cocktail{NBSP}cherry."}
TBC = {"beta_brut_rose": "glass / bottle TBC"}
BANNED = ["nom-006", "class", "shelf", "fermented", "lager family", "beside beer", "age grade"]
for k, v in C.items():
    assert not any(w in v[0].lower() for w in BANNED), k
    assert not any(r in " ".join(v[2]) for r in ("d4d63f58", "bc899a48")), k
assert "aromatic bitters" in C["beta_manhattan"][0]
assert all(C[k][0] for k in C), "every item has a description line"

secs = {s["id"]: s for s in draft["sections"]}
doc = copy.deepcopy(draft)
doc["title"] = "Cantina & Cocktail Bar"; doc["subtitle"] = "Iowa City, Iowa"
S = {k: copy.deepcopy(secs[k]) for k in secs}
def sub(sec, sid): return next(sb for sb in S[sec]["subs"] if sb["id"] == sid)
def pick(sb, ids): return [next(i for i in sb["items"] if i["id"] == x) for x in ids]
ho, cl = sub("sec_cocktails", "sub_cocktails_house_originals"), sub("sec_cocktails", "sub_cocktails_classics")
ho["items"] = pick(ho, ["beta_old_fashioned", "beta_daiquiri"]); cl["items"] = pick(cl, ["beta_margarita", "beta_manhattan"])
S["sec_cocktails"]["subs"] = [ho, cl]                                    # House Originals lead
ag, br = sub("sec_spirits", "sub_spirits_agave"), sub("sec_spirits", "sub_spirits_brandy")
ag["name"] = "Agave & Brandy"; ag["items"] = pick(ag, ["beta_blanco_tequila", "beta_anejo_tequila"]) + br["items"]; S["sec_spirits"]["subs"] = [ag]
dr = sub("sec_beer", "sub_beer_draft"); dr["name"] = "Draft & Cider"; dr["items"] = dr["items"] + S["sec_cider"]["items"]  # cider folded in
S["sec_beer"]["name"] = "Beer & Cider"
bg, sp = sub("sec_wine", "sub_wine_by_the_glass"), sub("sec_wine", "sub_wine_sparkling")
bg["name"] = "Red, White & Sparkling"; bg["items"] = bg["items"] + sp["items"]; S["sec_wine"]["subs"] = [bg]
new = [S[k] for k in ["sec_cocktails", "sec_spirits", "sec_beer", "sec_wine"]]
for s in new:
    for it in s["items"] + [i for sb in s["subs"] for i in sb["items"]]:
        line, src, rows, miss = C[it["id"]]
        it["desc"] = (line + " " + SERVE[it["id"]].replace(NBSP, " ")) if it["id"] in SERVE else line; it.pop("missing_ingredients", None)
        it["meta"] = dict(it.get("meta") or {}); it["meta"]["missing_ingredients"] = list(miss)
        if it["id"] == "beta_manhattan":
            it["meta"]["public_components"] = {}   # bitters printed: venue's own menu_description names them
doc["sections"] = new

def flat(d, skip_pc=False):
    return {i["id"]: (i["name"], json.dumps(i["prices"], sort_keys=True), json.dumps(i.get("phg"), sort_keys=True),
                      json.dumps({k: v for k, v in (i.get("meta") or {}).items() if k not in ("missing_ingredients",) + (("public_components",) if skip_pc else ())}, sort_keys=True), json.dumps(i.get("components"), sort_keys=True))
            for s in d["sections"] for i in s["items"] + [x for sb in s["subs"] for x in sb["items"]]}
assert flat(doc, True) == flat(draft, True) and len(flat(doc)) == 14, "item/price/meta drift"

allitems = {i["id"]: i for s in new for i in s["items"] + [x for sb in s["subs"] for x in sb["items"]]}
V = {"cantarito": "Tanto va el cántaro al agua, que se quiebra y te moja las enaguas.", "botella": "La herramienta del borracho.",
     "barril": "Tanto bebió el albañil, que quedó como barril.", "rosa": "Rosita, Rosaura, ven que te quiero ver."}
# (n, ref, gloss, lotería name, don clemente number, figure, colour, groups, verse, column, card h, face h)
CARDS = [
 (1, "sec_cocktails", "Cocktails", "El Cantarito", 44, "cantarito", "terra", [(ho, ho["items"]), (cl, cl["items"])], V["cantarito"], 1, 384, 141),
 (2, "sec_spirits", "Spirits", "La Botella", 8, "bottle", "blue", [(ag, ag["items"])], V["botella"], 1, 222, 81),
 (3, "sec_beer", "Beer & Cider", "El Barril", 9, "barrel", "agave", [(dr, dr["items"])], V["barril"], 2, 318, 141),
 (4, "sec_wine", "Wine", "La Rosa", 41, "rose", "rosa", [(bg, bg["items"])], V["rosa"], 2, 288, 147),
]
assert sorted(i["id"] for c in CARDS for g in c[7] for i in g[1]) == sorted(allitems), "every item on exactly one card"
for col in (1, 2):
    hs = [c[10] for c in CARDS if c[9] == col]; assert sum(hs) + 12 * (len(hs) - 1) == 618, (col, hs)
assert all(c[10] % 6 == 0 and (c[11] + 3) % 6 == 0 for c in CARDS)
doc["meta"] = dict(doc.get("meta") or {})
doc["meta"]["designer_notes"] = {
    "round": ROUND,
    "concept": ("Lotería de la Cantina, a real tabla of four cards (2 + 2): El Cantarito (44) is the featured card, top-left and tallest, over La Botella (8); "
                "El Barril (9) over La Rosa (41). Every card has a 3 pt frame in its colour, its traditional Don Clemente number in the top-left corner "
                "(marigold numeral on an ink chip), one face composition (cut-paper figure left, cantor verse right, scaled to the card), and the lotería name "
                "in the band under the figure (one title style, one size). The drinks list is the card's reverse."),
    "cards": [{"n": c[0], "ref": c[1], "name": c[2], "loteria_name": c[3].upper(), "loteria_number": c[4], "number_source": "traditional Don Clemente lotería numbering (Coordinator correction, round 11)",
               "cantor_verse": c[8], "verse_status": "cultural text (traditional lotería cantor verse), not an item fact; see needs_input question 7", "figure": c[5], "featured": c[0] == 1,
               "card_h_pt": c[10], "face_h_pt": c[11], "items": [i["id"] for g in c[7] for i in g[1]]} for c in CARDS],
    "copy_sources": {k: {"printed": (v[0] + " " + SERVE[k].replace(NBSP, " ")) if k in SERVE else v[0], "serve_cue": SERVE.get(k, "").replace(NBSP, " "), "proof_marker": TBC.get(k, ""),
                         "words_from": v[1], "gateway_rows": v[2], "missing": v[3]} for k, v in C.items()},
    "gateway_query": "no new gateway query this round; rows cited are from round 5 (log_id 112) and round 7 (log_id 130) phg_designer_query over public.beverage_categories. Beer, cider and wine lines are the draft menu_description words.",
    "manhattan_bitters": "Printed: 'aromatic bitters' is in the venue's own menu_items.menu_description ('Rye, sweet vermouth, aromatic bitters.') and in the draft components; the public_components hide is dropped.",
    "brut_rose_price": "Listed with the other wines under one subhead; a muted 'glass / bottle TBC' proof marker is printed on its description line, right-aligned under the price, because the draft price label is empty.",
    "structure_changes": "Spirits: one subhead 'Agave & Brandy'. Beer: one subhead 'Draft & Cider' with Dry Cider folded in (sec_cider section merged into sec_beer; item id and meta unchanged). Wine: one subhead 'Red, White & Sparkling' (Sparkling subsection merged; words from the draft descriptions). Cocktails: House Originals lead.",
    "card_layout": "2 + 2 tabla, columns 264 / 264 pt, 12 pt gutter. Left: El Cantarito 384 (face 141) + 12 + La Botella 222 (face 81) = 618. Right: El Barril 318 (face 141) + 12 + La Rosa 288 (face 147) = 618. All heights multiples of 6 pt from the deck top; name bands of El Cantarito and El Barril share one baseline.",
    "why_2_plus_2": "With every item's description stacked, the right column of the round-10 1 + 3 tabla would leave only about 45 pt per face, and a 35-40 % face on a full-height El Cantarito would leave about 230 pt empty. Moving La Botella under El Cantarito solves both.",
    "retired_junmai_ginjo": "Retired Junmai Ginjo ($12) in phg.menu_items is not in the draft and is left off (please confirm).",
    "palette_note": "La Botella takes deep agave blue #1E3F66 (was ink). Marigold appears as type only on dark grounds: the card-number numerals on ink chips.",
}
(OUT / "doc.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2))

# ------------------------------------------------------------ palette + graphics
P = dict(cream="#F6EEDF", card="#FBF5EA", feat="#F3E3CB", ink="#231B16", terra="#A63C1A", agave="#2F5D50", mari="#E3A018", muted="#5A4A3F", rosa="#C2185B", blue="#1E3F66")
def dia(cx, cy, w, h, f): return f'<path d="M{cx:.2f} {cy-h:.2f} L{cx+w:.2f} {cy:.2f} L{cx:.2f} {cy+h:.2f} L{cx-w:.2f} {cy:.2f} Z" fill="{f}"/>'
def agave_leaves(cx, cy, r, f):
    o = ""
    for ang, ln in zip((-70, -45, -22, 0, 22, 45, 70), (0.7, 0.85, 0.95, 1.0, 0.95, 0.85, 0.7)):
        t = math.radians(ang); L = r * ln; tx, ty = cx + L * math.sin(t), cy - L * math.cos(t); nx, ny = math.cos(t) * r * .16, math.sin(t) * r * .16
        o += f'<path d="M{cx-nx:.2f} {cy-ny:.2f} Q{(cx+tx)/2-nx*.7:.2f} {(cy+ty)/2-ny*.7:.2f} {tx:.2f} {ty:.2f} Q{(cx+tx)/2+nx*.7:.2f} {(cy+ty)/2+ny*.7:.2f} {cx+nx:.2f} {cy+ny:.2f} Z" fill="{f}"/>'
    return o

def papel(n=11, W=540, H=36, cls="banner", dims='width="540pt" height="36pt"'):
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


def item_html(it):
    ln = C[it["id"]][0]
    if it["id"] in SERVE:
        t = re.sub(r"(\w+(?:-\w+)+)", r'<span class="nw">\1</span>', html.escape(ln))
        dd = f'<p class="desc"><span class="chr">{t}</span> <span class="cue">{html.escape(SERVE[it["id"]]).replace(NBSP, "&nbsp;")}</span></p>'
    elif it["id"] in TBC:
        dd = f'<p class="desc has-tbc"><span class="chr">{nb(ln)}</span><span class="tbc">{html.escape(TBC[it["id"]])}</span></p>'
    else:
        dd = f'<p class="desc"><span class="chr">{nb(ln)}</span></p>'
    return (f'<div class="item" data-ref="{it["id"]}"><div class="row"><span class="name">{nb(it["name"])}</span><span class="lead"></span>'
            f'<span class="price num">{it["prices"][0]["value"]:g}</span></div>{dd}</div>')

def card_html(n, cid, name, lot, num, fig, col, groups, verse, column, h, F):
    body = []
    for sb, items in groups:
        body.append(f'<div class="sub" data-id="{sb["id"]}"><h3>{html.escape(sb["name"])}</h3><span class="subrule"></span></div>')
        body.append('<div class="items">' + "".join(item_html(i) for i in items) + "</div>")
    return (f'<article class="card c-{col}{" featured" if n == 1 else ""}" id="card-{n}" data-id="{cid}" data-n="{n}" style="--h:{h}pt; --f:{F}pt; --fig:{F - 36}pt">'
            f'<div class="face"><span class="cardno" aria-label="Lotería card {num}">{num}</span>'
            f'<div class="art"><div class="figure">{icon(fig, "fig")}</div><p class="verse" lang="es">{html.escape(verse)}</p></div>'
            f'<div class="namebar"><h2 lang="es">{html.escape(lot.upper())}</h2><span class="gloss" lang="en">{html.escape(name)}</span></div></div>'
            f'<div class="body">{"".join(body)}</div></article>')

cols = {1: [], 2: []}
for c in CARDS: cols[c[9]].append(card_html(*c))
tabs = "".join(f'<a class="tab c-{c[6]}{" active" if c[0] == 1 else ""}" data-n="{c[0]}" href="#card-{c[0]}" aria-label="{html.escape(c[3])}, {html.escape(c[2])}">'
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
.c-terra { --c:$terra; --tint:#F3E3CB; } .c-agave { --c:$agave; --tint:#E4EBE2; } .c-blue { --c:$blue; --tint:#E3E8EE; } .c-rosa { --c:$rosa; --tint:#F7E3E8; }
.page { width:612pt; height:792pt; padding:36pt; background:$cream; display:flex; flex-direction:column; margin:0 auto; }
.banner { display:block; width:540pt; height:36pt; flex:none; }
.banner-m, .tabs { display:none; }
.title { font-family:'Fraunces', serif; font-weight:700; font-size:24pt; line-height:24pt; height:24pt; letter-spacing:-0.3pt; text-align:center; margin:18pt 0 0; }
.title .amp { color:$terra; font-style:italic; font-weight:600; }
.loc { text-align:center; font-size:8.5pt; line-height:12pt; height:12pt; letter-spacing:3pt; text-transform:uppercase; color:$muted; font-weight:500; margin:0 0 12pt; }
.num { font-family:'Fraunces', serif; font-weight:700; color:var(--c, $terra); font-variant-numeric:lining-nums tabular-nums; font-feature-settings:'tnum' 1,'lnum' 1; }
.nw { white-space:nowrap; }
.deck { flex:none; display:flex; gap:12pt; height:618pt; }
.col { flex:none; width:264pt; display:flex; flex-direction:column; gap:12pt; }
.card { position:relative; flex:none; height:var(--h); display:flex; flex-direction:column; background:$card; border:3pt solid var(--c); padding:0 0 9pt; overflow:hidden; }
.face { position:relative; flex:none; height:var(--f); display:flex; flex-direction:column; background:var(--tint); box-shadow: inset 0 0 0 3pt var(--tint), inset 0 0 0 3.75pt var(--c); }
.cardno { position:absolute; left:6pt; top:6pt; z-index:2; width:24pt; height:24pt; background:$ink; color:$mari; font-family:'Fraunces', serif; font-weight:700; font-size:12pt; line-height:24pt; text-align:center; font-feature-settings:'tnum' 1,'lnum' 1; }
.art { flex:1; min-height:0; display:flex; align-items:center; gap:12pt; padding:6pt 12pt 6pt 36pt; }
.figure { flex:none; width:var(--fig); height:var(--fig); }
.figure .fig { display:block; width:100%; height:100%; }
.verse { margin:0; flex:1; text-align:center; font-family:'Fraunces', serif; font-style:italic; font-weight:400; font-size:10pt; line-height:12pt; color:$muted; text-wrap:balance; }
.namebar { flex:none; height:24pt; display:flex; align-items:baseline; justify-content:center; gap:6pt; background:var(--c); color:$cream; }
.namebar h2 { margin:0; font-family:'Fraunces', serif; font-weight:700; font-size:12pt; line-height:24pt; letter-spacing:2pt; white-space:nowrap; }
.gloss { font-family:'Fraunces', serif; font-style:italic; font-size:8.5pt; line-height:24pt; white-space:nowrap; opacity:.9; }
.body { flex:none; margin-top:12pt; padding:0 10.5pt; }
.sub { display:flex; align-items:center; gap:6pt; height:12pt; margin-bottom:6pt; }
.items + .sub { margin-top:12pt; }
h3 { margin:0; font-size:7pt; line-height:12pt; letter-spacing:1.4pt; text-transform:uppercase; color:$ink; font-weight:700; white-space:nowrap; }
.subrule { flex:1; border-top:0.75pt solid var(--c); }
.item + .item { margin-top:12pt; }
.row { display:flex; align-items:baseline; height:12pt; }
.lead { flex:1; }
.name { font-family:'Fraunces', serif; font-size:10.5pt; line-height:12pt; font-weight:600; }
.price { font-size:11.5pt; line-height:12pt; margin-left:8pt; }
.desc { margin:0; padding-right:8pt; font-size:8pt; line-height:12pt; color:$muted; }
.desc .chr { color:$ink; } .desc .cue { font-style:italic; color:$muted; white-space:nowrap; }
.desc.has-tbc { display:flex; align-items:baseline; padding-right:0; height:12pt; }
.tbc { margin-left:auto; padding-left:8pt; font-style:italic; font-size:7.5pt; letter-spacing:.2pt; color:$muted; white-space:nowrap; line-height:12pt; }
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
  .tab.active { background:var(--c); color:$cream; box-shadow: inset 0 -4px 0 $ink; }
  .deck { display:block; height:auto; } .col { width:auto; display:block; }
  .card { height:auto; margin:0 0 24px; scroll-margin-top:110px; border-width:4px; padding:0 0 16px; box-shadow:3px 4px 0 rgba(35,27,22,.18); }
  .face { height:auto; }
  .cardno { left:8px; top:8px; width:32px; height:32px; font-size:16px; line-height:32px; }
  .art { padding:12px 16px 12px 48px; gap:14px; }
  .figure { width:104px; height:104px; }
  .featured .figure { width:128px; height:128px; }
  .verse { font-size:15px; line-height:20px; }
  .namebar { height:40px; } .namebar h2 { font-size:18px; line-height:40px; letter-spacing:2px; }
  .gloss { font-size:14px; line-height:40px; }
  .body { margin-top:16px; padding:0 16px; }
  .sub { height:auto; } h3 { font-size:11.5px; line-height:20px; }
  .row { height:auto; } .name { font-size:18px; line-height:24px; } .price { font-size:19px; line-height:24px; }
  .desc { font-size:14.5px; line-height:20px; padding-right:24px; }
  .desc.has-tbc { padding-right:0; height:auto; } .tbc { font-size:13px; line-height:20px; }
  .item + .item { margin-top:14px; } .items + .sub { margin-top:16px; } .sub { margin-bottom:6px; }
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
<main class="deck"><div class="col">{"".join(cols[1])}</div><div class="col">{"".join(cols[2])}</div></main>
<footer class="foot" aria-hidden="true"></footer>
</div>{JS}</body></html>
"""
(OUT / "menu.html").write_text(HTML)
print("built round", ROUND, "cards", [(c[3], c[4]) for c in CARDS])
