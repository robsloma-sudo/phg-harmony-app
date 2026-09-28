"""TEST-1 round 16 (from round 15): shared band line per row (same face + figure per row), card feet close the row difference; Manhattan follows the draft (no bitters); draft subheads AGAVE / BRANDY; sourced leads and style tags; doc order = reading order; 18 pt card numbers in the card colour; La Botella prices in ink; even face tints; title tagged "title".
Round 15 notes follow.
TEST-1 round 15 (from round 14): one item pitch on every card; row differences absorbed in the face (figure scales); La Botella gloss + ochre prices; SPANISH · English subheads; copa labels.
Round 14 notes follow.
TEST-1 round 14 (from round 13): locked 2 x 2 tabla, shared rows, beer top-right, full-width name bands.
Round 13 notes follow.
TEST-1 round 13 (from round 12): Lotería de la Cantina, a real lotería tabla (2 + 2, read in rows).
Top row: El Cantarito (44, cocktails, Clásicos first) | La Botella (8, agave & brandy). Lower row, one shared break line: El Barril (9) | La Rosa (41).
One face template on every card: 105 pt figure box at the same x, italic lotería numeral in its top-left corner (ink, no chip),
verse column at the same x offset with the name band at its foot. Every printed line is traced in doc.meta.designer_notes.copy_sources."""
import json, copy, html, pathlib, base64, math, re
from string import Template

HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path("/home/user/phg-harmony-app/handoff/designs/test-1-iowa-city-cantina")
draft = json.loads((HERE / "draft_doc.json").read_text())
ROUND = 16
NBSP = " "

# phg.recipe_versions rows (join phg.menu_items.current_recipe_version_id = phg.recipe_versions.id; gateway log_id 168)
RV = {"beta_old_fashioned": ("7095fd3d-58fb-43f5-8e8f-1a0afadeafa7", "Rocks", "Stir with ice and strain over a large cube", "Orange peel"),
      "beta_daiquiri": ("14d45e57-72fa-4d23-8274-24e5c80e4b12", "Coupe", "Shake with ice and fine strain", "Lime coin"),
      "beta_margarita": ("f06abb74-762a-4f89-81b2-76a9e4714f3c", "Rocks", "Shake with ice and strain over fresh ice", "Lime wheel"),
      "beta_manhattan": ("9fb77eaa-c5eb-477c-8e21-acbc89a0e942", "Coupe", "Stir with ice and strain", "Cocktail cherry")}
# beverage_categories rows checked this round (gateway log_id 167 and 171). None carries a definition (notes = null; authority_note only names the NOM-006 class),
# and spirit_lexicon has no blanco / añejo / VSOP term (log_id 169, 0 rows). So the spirits print their name only and are flagged.
BC = {"beta_blanco_tequila": ["beverage_categories 04d72e1f-650d-490c-8ad8-54a6eb8aa766 'Blanco / plata' (notes null; authority_note 'NOM-006-SCFI-2012 §5, clase.')"],
      "beta_anejo_tequila": ["beverage_categories 9f4dae69-e84c-4b65-b7d9-1b417658b78d 'Añejo' (notes null; authority_note 'NOM-006-SCFI-2012 §5, clase.')"],
      "beta_cognac_vsop": ["beverage_categories a88f6e79-9438-6e3d-2656-406fad2b829f 'Cognac' (notes null)", "beverage_categories bec5063c-5274-9534-91da-53a2f10c8255 'VSOP' (notes null, no age statement)"]}

# ------------------------------------------------------------ copy + sources (draft words only)
C = {  # id: (description line or "", words from, gateway row ids, still missing)
 "beta_margarita": ("Bright and citrus-forward: tequila blanco, fresh lime, orange liqueur and agave syrup.",
   "draft desc 'Tequila blanco, lime, orange liqueur, agave. Bright and citrus-forward.' (source word order 'tequila blanco' kept); orange liqueur, agave, 'Bright and citrus-forward'); draft_doc components 'Fresh Lime Juice', 'Agave Syrup' (prep)", [], []),
 "beta_manhattan": ("Stirred: rye, sweet vermouth.",
   "lead 'Stirred:' from phg.recipe_versions 9fb77eaa method 'Stir with ice and strain' (draft serve_format the same); 'Rye, sweet vermouth' from the draft desc 'Rye, sweet vermouth, aromatic bitters.' with the bitters left off because the draft meta.public_components {'aromatic-bitters': false} hides them", [], ["public display of aromatic bitters (needs_input 11)"]),
 "beta_old_fashioned": ("Stirred: brown butter-washed bourbon, demerara syrup and aromatic bitters.",
   "lead 'Stirred:' from phg.recipe_versions 7095fd3d method 'Stir with ice and strain over a large cube'; draft_doc components verbatim: 'Brown Butter-Washed Bourbon' (prep), 'Demerara Syrup' (prep), 'Aromatic Bitters' (draft_doc component: kind ingredient, role 'Bitters', 2 dash)", [], ["allergen confirmation (brown butter: dairy)"]),
 "beta_daiquiri": ("Shaken: white rum, fresh lime and house demerara syrup.",
   "lead 'Shaken:' from the draft serve_format 'Shake with ice and fine strain' (phg.recipe_versions 14d45e57 method, same words); draft desc (white rum, lime, house demerara syrup); draft_doc components 'Fresh Lime Juice', 'Demerara Syrup' ('House 1:1 demerara syrup')", [], []),
 "beta_blanco_tequila": ("Tequila blanco, poured straight.", "draft item desc 'Blanco tequila pour.' (category words) + draft Spirits section desc 'Straight pours by category.' -> 'poured straight'", BC["beta_blanco_tequila"], ["brand", "age statement", "pour size"]),
 "beta_anejo_tequila": ("Tequila añejo, poured straight.", "draft item desc 'Añejo tequila pour.' (category words) + draft Spirits section desc 'Straight pours by category.' -> 'poured straight'", BC["beta_anejo_tequila"], ["brand", "age statement", "pour size"]),
 "beta_cognac_vsop": ("Cognac VSOP, poured straight.", "draft item desc 'VSOP Cognac pour.' (category words) + draft Spirits section desc 'Straight pours by category.' -> 'poured straight'", BC["beta_cognac_vsop"], ["brand", "age statement", "pour size"]),
 "beta_czech_pilsner": ("Crisp pale lager · draft", "style tag (Style · serve): draft desc 'Crisp pale lager.' + draft sub 'Draft'", [], ["brewery", "ABV", "pour size"]),
 "beta_dry_hopped_ipa": ("Hop-forward IPA · draft", "style tag (Style · serve): draft desc 'Hop-forward draft IPA.' (word 'draft' moved to the serve slot) + draft sub 'Draft'", [], ["brewery", "ABV", "pour size"]),
 "beta_amber_lager": ("Toasty amber lager · draft", "style tag (Style · serve): draft desc 'Toasty amber lager.' + draft sub 'Draft'", [], ["brewery", "ABV", "pour size"]),
 "beta_dry_cider": ("Dry sparkling cider", "style tag (Style · serve): draft desc 'Dry sparkling cider.' (no serve: the Cider section has no Draft sub)", [], ["producer", "ABV", "format (draft or can)"]),
 "beta_malbec": ("Malbec · dry red", "style tag (Style · serve): item name 'Malbec' + draft desc 'Dry red wine.'", [], ["producer", "region", "vintage", "pour size"]),
 "beta_pinot_grigio": ("Pinot Grigio · dry white", "style tag (Style · serve): item name 'Pinot Grigio' + draft desc 'Dry white wine.'", [], ["producer", "region", "vintage", "pour size"]),
 "beta_brut_rose": ("Brut rosé · dry sparkling", "style tag (Style · serve): item name 'Brut Rosé' + draft desc 'Dry sparkling rosé.'", [], ["producer", "region", "vintage", "glass or bottle (price label empty in the draft; not printed)"]),
}
# serve cues: glass + garnish from phg.recipe_versions (RV); own line under the ingredients, non-breaking inside
SERVE = {"beta_margarita": f"On{NBSP}the{NBSP}rocks, lime{NBSP}wheel.", "beta_manhattan": f"In{NBSP}a{NBSP}coupe, cocktail{NBSP}cherry.",
         "beta_old_fashioned": f"Over{NBSP}a{NBSP}large{NBSP}cube, orange{NBSP}peel.", "beta_daiquiri": f"In{NBSP}a{NBSP}coupe, lime{NBSP}coin."}
CUE_SRC = {"beta_margarita": "glassware 'Rocks' + method 'strain over fresh ice' -> 'On the rocks'; garnish 'Lime wheel'",
           "beta_manhattan": "glassware 'Coupe' -> 'In a coupe'; garnish 'Cocktail cherry'",
           "beta_old_fashioned": "method 'strain over a large cube' -> 'Over a large cube'; garnish 'Orange peel'",
           "beta_daiquiri": "glassware 'Coupe' -> 'In a coupe'; garnish 'Lime coin'"}
BANNED = ["nom-006", "class", "shelf", "fermented", "by the pour", "tbc", "spirit-forward", "rye whiskey", "one large"]
for k, v in C.items():
    assert not any(w in (v[0] + SERVE.get(k, "")).lower() for w in BANNED), k
NOTE = {}
GLOSS = {}   # round 16: band glosses are the plain section names in title case
COPA = {"beta_malbec", "beta_pinot_grigio"}   # print label "copa": the items sit under the draft sub "By the Glass"; Brut Rosé stays unlabelled
PWR = {"sec_cocktails": 14, "sec_beer": 14, "sec_wine": 36, "sec_spirits": 14}   # price column width pt per card (2 tabular digits; La Rosa adds "copa" + 4 pt)
DESC_GAP = 18
assert "fresh lime" in C["beta_margarita"][0] and "bitters" not in C["beta_manhattan"][0] and "aromatic bitters" in C["beta_old_fashioned"][0]

secs = {s["id"]: s for s in draft["sections"]}
doc = copy.deepcopy(draft)
doc["title"] = "Cantina & Cocktail Bar"; doc["subtitle"] = "Iowa City, Iowa"
S = {k: copy.deepcopy(secs[k]) for k in secs}
def sub(sec, sid): return next(sb for sb in S[sec]["subs"] if sb["id"] == sid)
def pick(sb, ids): return [next(i for i in sb["items"] if i["id"] == x) for x in ids]
ho, cl = sub("sec_cocktails", "sub_cocktails_house_originals"), sub("sec_cocktails", "sub_cocktails_classics")
cl["name"] = "Clásicos · Classics"; cl["items"] = pick(cl, ["beta_margarita", "beta_manhattan"])
ho["name"] = "De la Casa · House Originals"; ho["items"] = pick(ho, ["beta_old_fashioned", "beta_daiquiri"])
S["sec_cocktails"]["subs"] = [cl, ho]                                    # Clásicos lead: the Margarita is the first drink on the menu
ag, br = sub("sec_spirits", "sub_spirits_agave"), sub("sec_spirits", "sub_spirits_brandy")
# round 13: the draft's own subheads are restored (SPANISH · English); no section is merged in doc.json
ag["name"] = "Agave · Agave"; ag["items"] = pick(ag, ["beta_blanco_tequila", "beta_anejo_tequila"]); br["name"] = "Brandy · Brandy"; S["sec_spirits"]["subs"] = [ag, br]
dr = sub("sec_beer", "sub_beer_draft"); dr["name"] = "De Barril · Draft"
cid = {"id": "sec_cider", "name": "Sidra · Cider"}   # the draft's own Cider section (no subs); printed as a subhead on El Barril
S["sec_cider"]["name"] = "Sidra · Cider"
bg, sp = sub("sec_wine", "sub_wine_by_the_glass"), sub("sec_wine", "sub_wine_sparkling")
bg["name"] = "Por Copa · By the Glass"; sp["name"] = "Espumoso · Sparkling"
new = [S[k] for k in ["sec_cocktails", "sec_spirits", "sec_beer", "sec_cider", "sec_wine"]]
for s in new:
    for it in s["items"] + [i for sb in s["subs"] for i in sb["items"]]:
        line, src, rows, miss = C[it["id"]]
        it["desc"] = (line + " " + SERVE[it["id"]].replace(NBSP, " ")) if it["id"] in SERVE else line; it.pop("missing_ingredients", None)
        it["meta"] = dict(it.get("meta") or {}); it["meta"]["missing_ingredients"] = list(miss)
        # round 15: Manhattan meta.public_components stays as the draft has it ({"aromatic-bitters": false}); the print override is recorded in doc.meta
doc["sections"] = new

def flat(d, skip_pc=False):
    return {i["id"]: (i["name"], json.dumps(i["prices"], sort_keys=True), json.dumps(i.get("phg"), sort_keys=True),
                      json.dumps({k: v for k, v in (i.get("meta") or {}).items() if k not in ("missing_ingredients",) + (("public_components",) if skip_pc else ())}, sort_keys=True), json.dumps(i.get("components"), sort_keys=True))
            for s in d["sections"] for i in s["items"] + [x for sb in s["subs"] for x in sb["items"]]}
assert flat(doc) == flat(draft) and len(flat(doc)) == 14, "item/price/meta drift"
for k, (rv, *_r) in RV.items():
    it = next(i for s in doc["sections"] for sb in s["subs"] for i in sb["items"] if i["id"] == k); assert it["phg"]["recipe_version_id"] == rv, k

allitems = {i["id"]: i for s in new for i in s["items"] + [x for sb in s["subs"] for x in sb["items"]]}
V = {"cantarito": "Tanto va el cántaro al agua, que se quiebra y te moja las enaguas.", "botella": "La herramienta del borracho.",
     "barril": "Tanto bebió el albañil, que quedó como barril.", "rosa": "Rosita, Rosaura, ven que te quiero ahora."}
BAND = 24
GAP = 12                                        # gutter = row gap = 12 pt
HJ = json.loads((HERE / "heights.json").read_text())   # written by fit.py: order, rows, one face per row, feet
DECK = HJ["deck"]; ORDER = HJ["order"]
ROWTXT = {"beer_top": "Row 1: El Cantarito (44, cocktails) | El Barril (9, beer & cider); row 2: La Rosa (41, wine) | La Botella (8, agave & brandy)", "agave_top": "Row 1: El Cantarito (44, cocktails) | La Botella (8, agave & brandy); row 2: El Barril (9, beer & cider) | La Rosa (41, wine)"}[ORDER]           # "agave_top" (La Botella top-right) or "beer_top" (El Barril top-right)
DEF = {  # ref: (gloss, lotería name, don clemente number, figure, colour, groups, verse)
 "sec_cocktails": ("Cocktails", "El Cantarito", 44, "cantarito", "terra", [(cl, cl["items"]), (ho, ho["items"])], V["cantarito"]),
 "sec_beer": ("Beer & Cider", "El Barril", 9, "barrel", "agave", [(dr, dr["items"]), (cid, S["sec_cider"]["items"])], V["barril"]),
 "sec_wine": ("Wine", "La Rosa", 41, "rose", "rosa", [(bg, bg["items"]), (sp, sp["items"])], V["rosa"]),
 "sec_spirits": ("Spirits", "La Botella", 8, "bottle", "mari", [(ag, ag["items"]), (br, br["items"])], V["botella"])}
SEQ = {"beer_top": ["sec_cocktails", "sec_beer", "sec_wine", "sec_spirits"], "agave_top": ["sec_cocktails", "sec_spirits", "sec_beer", "sec_wine"]}[ORDER]
ROWH = {1: HJ["row1"], 2: HJ["row1"], 3: HJ["row2"], 4: HJ["row2"]}
FACEH = {n: HJ["face"]["row1" if n <= 2 else "row2"] for n in (1, 2, 3, 4)}   # round 16: one face height per row
FIGH = {n: f - 6 - 6 - BAND for n, f in FACEH.items()}                            # so one figure scale per row
FOOT = {n: HJ["foot"][SEQ[n - 1]] for n in (1, 2, 3, 4)}                          # card foot on the shorter card of a row
CARDS = [(n, ref, *DEF[ref][:5], DEF[ref][5], DEF[ref][6], 1 if n % 2 else 2, ROWH[n]) for n, ref in enumerate(SEQ, 1)]
XG = {n: 0 for n in (1, 2, 3, 4)}
PW = {n: PWR[ref] for n, ref in enumerate(SEQ, 1)}
assert sorted(i["id"] for c in CARDS for g in c[7] for i in g[1]) == sorted(allitems), "every item on exactly one card"
assert all(c[10] % 6 == 0 for c in CARDS) and all((f + 3) % 6 == 0 for f in FACEH.values()) and HJ["row1"] + GAP + HJ["row2"] == DECK and all(v % 6 == 0 for v in FOOT.values())
# doc.json section order = printed reading order (row 1 left, row 1 right, row 2 left, row 2 right); Cider follows Beer (printed on El Barril)
doc["sections"] = [S[r] for ref in SEQ for r in ([ref, "sec_cider"] if ref == "sec_beer" else [ref])]
new = doc["sections"]
assert flat(doc) == flat(draft)
P = dict(cream="#F6EEDF", card="#FBF5EA", feat="#F3E3CB", ink="#231B16", terra="#A63C1A", agave="#2F5D50", mari="#E3A018", muted="#5A4A3F", rosa="#C2185B", ochre="#8A5A00")
TINT_A = 0.10   # round 16: every face tint = 10 % of its card colour over the card paper
def mix(c, a=TINT_A, base="#FBF5EA"):
    f = lambda h: [int(h[i:i+2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * a + y * (1 - a)):02X}" for x, y in zip(f(c), f(base)))
TINT = {k: mix(P[k]) for k in ("terra", "agave", "mari", "rosa")}
P.update({f"t_{k}": v for k, v in TINT.items()})
doc["meta"] = dict(doc.get("meta") or {})
doc["meta"]["designer_notes"] = {
    "round": ROUND,
    "recipe_versions": {k: list(v) for k, v in RV.items()},
    "concept": ("Lotería de la Cantina, a real tabla of four cards locked in a 2 x 2 grid with shared rows, read in rows. " + ROWTXT + ". Every card: 3 pt frame in its colour; one face template "
                "(the Don Clemente number as a 19 pt italic numeral in the card colour at the face's top-left, a cut-paper figure, the cantor verse beside it, and a full-width 24 pt name band at the foot of the face carrying the card name in 18 pt caps). "
                "Both cards in a row share one face height and one figure scale, so their name bands and first subheads sit on one line; the shorter card of a row closes the difference with a card foot (thin rule + 'Nº n · NAME' in the card colour). "
                "The drinks list sits below under the draft's own subheads, SPANISH · English, 8.5 pt tracked caps in the card colour."),
    "cards": [{"n": c[0], "ref": c[1], "name": c[2], "loteria_name": c[3].upper(), "loteria_number": c[4], "number_source": "traditional Don Clemente lotería numbering",
               "cantor_verse": c[8], "verse_status": "cultural text (traditional lotería cantor verse), not an item fact; see needs_input", "figure": c[5], "featured": c[0] == 1,
               "card_h_pt": c[10], "face_h_pt": FACEH[c[0]], "figure_pt": FIGH[c[0]], "foot_pt": FOOT[c[0]], "band_gloss": GLOSS.get(c[1], c[2]), "items": [i["id"] for g in c[7] for i in g[1]]} for c in CARDS],
    "copy_sources": {k: {"printed": v[0], "serve_cue": SERVE.get(k, "").replace(NBSP, " "), "serve_cue_source": (f"phg.recipe_versions {RV[k][0]}: " + CUE_SRC[k]) if k in RV else "",
                         "recipe_version_id": RV[k][0] if k in RV else None, "words_from": v[1], "gateway_rows": v[2], "missing": v[3]} for k, v in C.items()},
    "gateway_query": ("Round 12 gateway calls (public.phg_designer_query): log_id 167 (beverage_categories 04d72e1f, 9f4dae69, a88f6e79, bec5063c), "
                      "log_id 168 (phg.menu_items joined to phg.recipe_versions on current_recipe_version_id: glassware, garnish, method), "
                      "log_id 169 (spirit_lexicon terms blanco / añejo / VSOP / plata: 0 rows), log_id 170 (spirit_lexicon columns: term, family, subfamily, notes; no definitions), "
                      "log_id 171 (every beverage_categories row under tequila and cognac: blanco, añejo and VSOP have notes = null)."),
    "spirits_copy": "Round 16: each spirit prints its category words from its own draft line plus 'poured straight' from the draft Spirits section desc 'Straight pours by category.' ('Tequila blanco, poured straight.', 'Tequila añejo, poured straight.', 'Cognac VSOP, poured straight.'); the band gloss is 'Spirits'; subheads are the draft names 'Agave' and 'Brandy' (AGAVE · Agave, BRANDY · Brandy). Round 15 note (superseded): Round 15: the three spirits print name and price only. The card-level serve cue now sits in the La Botella name band as its italic gloss, 'Spirits · straight pours' (the draft Spirits section desc 'Straight pours by category.' shortened), so the first subhead sits 12 pt below the band as on every card. Subheads 'Tequila · Agave' (the draft sub is 'Agave'; the item names say Tequila) and 'Coñac · Brandy' (the draft sub is 'Brandy'; the item name says Cognac). Brand, age statement and pour size are flagged in missing_ingredients.",
    "manhattan": "Round 16: follows the draft. meta.public_components {'aromatic-bitters': false} hides the bitters, so the Manhattan prints 'Stirred: rye, sweet vermouth.' ('Stirred:' from phg.recipe_versions 9fb77eaa method 'Stir with ice and strain'). needs_input 11 asks the venue whether to show the bitters.",
    "old_fashioned_bitters": "'aromatic bitters' is the draft_doc component name 'Aromatic Bitters' (kind ingredient, role 'Bitters', 2 dash); the draft desc says 'bitters'.",
    "print_price_labels": {"beta_malbec": "copa", "beta_pinot_grigio": "copa", "source": "both items sit under the draft sub 'By the Glass'; the doc price label stays as the draft has it (empty); Brut Rosé stays unlabelled"},
    "description_measure": f"one measure per card: text column (237 pt) minus the price column ({PW} pt) minus a fixed {DESC_GAP} pt gap; text-wrap pretty with the last two words bound, so no line ends in a one-word orphan",
    "brut_rose_price": "Prints like every other price under 'Espumoso · Sparkling', unlabelled. The empty glass / bottle label is asked in needs_input only.",
    "structure_changes": "Round 16: doc.json sections follow the printed reading order (" + ", ".join(SEQ[:1] + ["sec_beer, sec_cider" if x == "sec_beer" else x for x in SEQ[1:]]) + "); subheads AGAVE · Agave and BRANDY · Brandy use the draft names. Round 15: One subhead pattern on every card, SPANISH · English with the English as the gloss: 'Clásicos · Classics', 'De la Casa · House Originals', 'De Barril · Draft', 'Sidra · Cider' (the draft's own Cider section, printed as a subhead on El Barril), 'Por Copa · By the Glass', 'Espumoso · Sparkling', 'Tequila · Agave', 'Coñac · Brandy'. No section or subsection is merged in doc.json.",
    "card_layout": f"Locked 2 x 2 tabla with shared rows: columns 264 / 264 pt, 12 pt gutter = 12 pt row gap. {ROWTXT}. Row heights {HJ['row1']} / {HJ['row2']} pt; deck {DECK} pt from y = 126 to 756 pt on a 6 pt grid; both columns end at 756 pt. One item pitch on every card (6 pt item gap, 12 pt lines). One face per row: {HJ['face']} pt (figures {FIGH} pt). Card feet: {FOOT} pt.",
    "order_used": ORDER, "order_note": HJ.get("order_note", ""),
    "retired_junmai_ginjo": "Junmai Ginjo is a phg.menu_items row that is not in draft_doc.json; it is intentionally left off pending the venue's decision.",
    "palette_note": f"Four lotería hues: terracotta (El Cantarito), agave green (El Barril), lotería rosa (La Rosa), marigold (La Botella: marigold frame, band and rules; its numeral, subheads and foot text in burnt ochre #8A5A00 for contrast; prices in ink). Every face is tinted at the same strength ({int(TINT_A*100)} % of the card colour over the card paper: {TINT}). Ink and cream are the neutrals.",
}
(OUT / "doc.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2))

# ------------------------------------------------------------ palette + graphics

def dia(cx, cy, w, h, f): return f'<path d="M{cx:.2f} {cy-h:.2f} L{cx+w:.2f} {cy:.2f} L{cx:.2f} {cy+h:.2f} L{cx-w:.2f} {cy:.2f} Z" fill="{f}"/>'
def agave_leaves(cx, cy, r, f):
    o = ""
    for ang, ln in zip((-70, -45, -22, 0, 22, 45, 70), (0.7, 0.85, 0.95, 1.0, 0.95, 0.85, 0.7)):
        t = math.radians(ang); L = r * ln; tx, ty = cx + L * math.sin(t), cy - L * math.cos(t); nx, ny = math.cos(t) * r * .16, math.sin(t) * r * .16
        o += f'<path d="M{cx-nx:.2f} {cy-ny:.2f} Q{(cx+tx)/2-nx*.7:.2f} {(cy+ty)/2-ny*.7:.2f} {tx:.2f} {ty:.2f} Q{(cx+tx)/2+nx*.7:.2f} {(cy+ty)/2+ny*.7:.2f} {cx+nx:.2f} {cy+ny:.2f} Z" fill="{f}"/>'
    return o

def papel(n=11, W=540, H=30, cls="banner", dims='width="540pt" height="30pt"'):
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
    dd = f'<p class="desc"><span class="chr">{nb(ln)}</span></p>' if ln else ""
    if it["id"] in SERVE:
        dd += f'<p class="cue">{html.escape(SERVE[it["id"]]).replace(NBSP, "&nbsp;")}</p>'
    lab = '<span class="plabel" lang="es">copa</span>' if it["id"] in COPA else ""
    return (f'<div class="item" data-ref="{it["id"]}"><div class="row"><span class="name">{nb(it["name"])}</span><span class="lead"></span>'
            f'<span class="pcol">{lab}<span class="price num">{it["prices"][0]["value"]:g}</span></span></div>{dd}</div>')

def h3(name):
    es, _, en = name.partition(" · ")
    return f'<span lang="es">{html.escape(es)}</span>' + (f'<span class="en" lang="en"> · {html.escape(en)}</span>' if en else "")

def foot_html(n, num, lot):
    # round 16: the row's height difference closes with a card foot on the shorter card: a thin rule, then the card's own number and name (already printed on its face)
    if not FOOT[n]: return ""
    return f'<div class="cfoot" aria-hidden="true"><span class="frule"></span><p class="fline"><span class="fno">Nº&nbsp;{num}</span> · {html.escape(lot.upper())}</p></div>'

def card_html(n, cid, name, lot, num, fig, col, groups, verse, column, h):
    body = []
    for sb, items in groups:
        body.append(f'<div class="sub" data-id="{sb["id"]}"><h3>{h3(sb["name"])}</h3><span class="subrule"></span></div>')
        body.append('<div class="items">' + "".join(item_html(i) for i in items) + "</div>")
    orn = ""  # no filler ornament (Coordinator, round 12 fix)
    note = f'<p class="note">{html.escape(NOTE[cid])}</p>' if cid in NOTE else ""
    return (f'<article class="card c-{col}{" featured" if n == 1 else ""}" id="card-{n}" data-id="{cid}" data-n="{n}" style="--h:{h}pt;--xg:{XG[n]}pt;--foot:{FOOT[n]}pt;--face:{FACEH[n]}pt;--fig:{FIGH[n]}pt;--pw:{PW[n]}pt;grid-column:{column};grid-row:{START[n]} / span {h // 6}">'
            f'<div class="face"><span class="cardno" aria-label="Lotería card {num}">{num}</span><div class="ftop"><div class="figure">{icon(fig, "fig")}</div>'
            f'<div class="vcol"><p class="verse" lang="es">{html.escape(verse)}</p></div></div>'
            f'<div class="namebar"><h2 lang="es">{html.escape(lot.upper())}</h2><span class="gloss" lang="en">{html.escape(GLOSS.get(cid, name))}</span></div></div>'
            f'<div class="body">{note}{"".join(body)}{orn}</div>{foot_html(n, num, lot)}</article>')

cols = {1: [], 2: []}
START = {1: 1, 2: 1, 3: HJ["row1"] // 6 + GAP // 6 + 1, 4: HJ["row1"] // 6 + GAP // 6 + 1}   # grid rows are 6 pt; shared rows
deck = "".join(card_html(*c) for c in CARDS)  # grid order = reading order: 1 2 / 3 4
tabs = "".join(f'<a class="tab c-{c[6]}{" active" if c[0] == 1 else ""}" data-n="{c[0]}" href="#card-{c[0]}" aria-label="{html.escape(c[3])}, {html.escape(c[2])}">'
               f'<span class="tno">{c[4]}</span><span class="lbl">{html.escape(c[3].split(" ", 1)[1])}</span></a>' for c in CARDS)
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
.c-terra { --c:$terra; --tint:$t_terra; } .c-agave { --c:$agave; --tint:$t_agave; } .c-mari { --c:$mari; --tint:$t_mari; --tc:$ochre; --pc:$ink; --on:$ink; } .c-rosa { --c:$rosa; --tint:$t_rosa; }
.page { width:612pt; height:792pt; padding:36pt; background:$cream; display:flex; flex-direction:column; margin:0 auto; }
.banner { display:block; width:540pt; height:30pt; flex:none; }
.banner-m, .tabs { display:none; }
.title { font-family:'Fraunces', serif; font-weight:700; font-size:24pt; line-height:30pt; height:30pt; letter-spacing:-0.3pt; text-align:center; margin:6pt 0 0; }
.title .amp { color:$terra; font-style:italic; font-weight:600; }
.loc { text-align:center; font-size:8.5pt; line-height:12pt; height:12pt; letter-spacing:3pt; text-transform:uppercase; color:$muted; font-weight:500; margin:6pt 0 6pt; }
.num { font-family:'Fraunces', serif; font-weight:700; color:var(--pc, var(--c, $terra)); font-variant-numeric:lining-nums tabular-nums; font-feature-settings:'tnum' 1,'lnum' 1; }
.nw { white-space:nowrap; }
.deck { flex:none; display:grid; grid-template-columns:264pt 264pt; grid-template-rows:repeat(${nrows}, 6pt); column-gap:${gap}pt; row-gap:0; height:${deck}pt; }
.card { position:relative; min-width:0; height:var(--h); display:flex; flex-direction:column; background:$card; border:3pt solid var(--c); padding:0 0 9pt; overflow:hidden; }
.face { position:relative; flex:none; height:var(--face); display:flex; flex-direction:column; padding:6pt 0 0; background:var(--tint); box-shadow: inset 0 0 0 3pt var(--tint), inset 0 0 0 3.75pt var(--c); }
.ftop { flex:none; height:var(--fig); display:flex; gap:12pt; padding:0 6pt 0 30pt; margin-bottom:6pt; }   /* 24 pt numeral column at the face's top-left */
.figure { position:relative; flex:none; width:var(--fig); height:var(--fig); }
.figure .fig { display:block; width:100%; height:100%; }
.cardno { position:absolute; z-index:2; left:6pt; top:3pt; font-family:'Fraunces', serif; font-style:italic; font-weight:700; font-size:19pt; line-height:24pt; color:var(--tc, var(--c)); font-feature-settings:'lnum' 1; }
.vcol { flex:1; min-width:0; display:flex; flex-direction:column; padding-right:6pt; }
.verse { margin:0; flex:1; display:flex; align-items:center; justify-content:center; text-align:center; font-family:'Fraunces', serif; font-style:italic; font-weight:400; font-size:10pt; line-height:12pt; color:$muted; text-wrap:balance; }
.namebar { flex:none; height:${band}pt; display:flex; align-items:baseline; justify-content:center; gap:7pt; background:var(--c); color:var(--on, $cream); }
.namebar h2 { margin:0; font-family:'Fraunces', serif; font-weight:700; font-size:18pt; line-height:${band}pt; letter-spacing:1.2pt; white-space:nowrap; }
.gloss { font-family:'Fraunces', serif; font-style:italic; font-size:8pt; line-height:${band}pt; white-space:nowrap; }
.body { flex:1; min-height:0; display:flex; flex-direction:column; margin-top:12pt; padding:0 10.5pt; }
.note { margin:0 0 12pt; font-family:'Fraunces', serif; font-style:italic; font-size:10pt; line-height:12pt; color:$muted; }
.items .item + .item, .items + .sub { margin-top:calc(var(--gi) + var(--xg, 0pt)); }
.sub { flex:none; display:flex; align-items:center; gap:6pt; height:12pt; margin-bottom:6pt; }
.items { flex:none; }
.items + .sub { --gi:12pt; }
.items { --gi:6pt; }
h3 { margin:0; font-size:8.5pt; line-height:12pt; letter-spacing:1.6pt; text-transform:uppercase; color:var(--tc, var(--c)); font-weight:700; white-space:nowrap; }
h3 .en { font-weight:500; letter-spacing:0.3pt; text-transform:none; font-size:8.5pt; }
.subrule { flex:1; border-top:0.75pt solid var(--tc, var(--c)); }

.row { display:flex; align-items:baseline; height:12pt; }
.lead { flex:1; }
.name { font-family:'Fraunces', serif; font-size:10.5pt; line-height:12pt; font-weight:600; }
.pcol { flex:none; display:flex; align-items:baseline; justify-content:flex-end; gap:4pt; min-width:var(--pw); margin-left:8pt; }
.plabel { font-size:7.5pt; line-height:12pt; font-style:italic; color:$muted; }
.price { font-size:11.5pt; line-height:12pt; }
.desc { margin:0; max-width:calc(100% - var(--pw) - 18pt); font-size:8pt; line-height:12pt; color:$ink; text-wrap:pretty; }
.cue { margin:0; font-size:8pt; line-height:12pt; font-style:italic; color:$muted; white-space:nowrap; }
.orn { flex:1; min-height:0; display:flex; align-items:center; justify-content:center; margin-top:12pt; }
.orn-svg { display:block; }
.foot { display:block; height:0; margin:0; flex:none; }
.cfoot { flex:none; height:var(--foot); display:flex; flex-direction:column; justify-content:flex-end; padding:0 10.5pt; }
.frule { display:block; height:0; border-top:0.75pt solid var(--c); margin-bottom:5.25pt; }
.fline { margin:0; height:12pt; font-size:7.5pt; line-height:12pt; letter-spacing:1.6pt; font-weight:700; color:var(--tc, var(--c)); text-align:center; white-space:nowrap; }
.fno { font-family:'Fraunces', serif; font-style:italic; letter-spacing:0.3pt; font-size:9pt; }
@media screen and (max-width: 600px) {
  html, body { background:$cream; }
  .page { width:auto; height:auto; padding:0 16px 24px; display:block; }
  .banner { display:none; } .banner-m { display:block; width:100%; height:auto; margin-top:12px; }
  .title { font-size:32px; line-height:38px; height:auto; margin-top:12px; text-wrap:balance; }
  .loc { font-size:11px; line-height:16px; height:auto; margin:4px 0 12px; }
  .tabs { display:grid; grid-template-columns:repeat(4, 1fr); gap:6px; position:sticky; top:0; z-index:5; background:$cream; padding:6px 0 8px; margin:0 0 12px; }
  .tab { position:relative; min-width:0; height:44px; display:flex; align-items:center; justify-content:center; gap:4px; text-decoration:none; border:2px solid var(--c); border-radius:3px; background:$card; color:$ink; }
  .tab .tno { font-family:'Fraunces', serif; font-style:italic; font-weight:700; font-size:15px; line-height:20px; }
  .tab .lbl { font-size:12px; line-height:20px; font-weight:600; white-space:nowrap; }
  .tab.active { background:var(--c); color:var(--on, $cream); box-shadow: inset 0 -3px 0 $ink; }
  .deck { display:block; height:auto; }
  .card { height:auto !important; margin:0 0 24px; scroll-margin-top:66px; border-width:4px; padding:0 0 16px; box-shadow:3px 4px 0 rgba(35,27,22,.18); --xg:0pt !important; }
  .face { height:auto; padding:8px 0 0; }
  .ftop { height:auto; gap:12px; padding:0 8px; margin-bottom:8px; }
  .figure { width:72px; height:72px; margin-left:26px; }
  .cardno { font-size:18px; line-height:24px; left:8px; top:6px; } .cfoot { display:none; }
  .verse { font-size:14px; line-height:18px; }
  .namebar { height:auto; padding:4px 6px; } .namebar h2 { font-size:22px; line-height:30px; letter-spacing:1.2px; } .gloss { font-size:12px; line-height:30px; }
  .body { margin-top:14px; padding:0 16px; }
  .note { font-size:15px; line-height:20px; margin-bottom:12px; }
  .sub { height:auto; } h3 { font-size:11.5px; line-height:20px; }
  .row { height:auto; } .name { font-size:18px; line-height:24px; } .price { font-size:19px; line-height:24px; }
  .desc, .cue { font-size:14.5px; line-height:20px; } .desc { max-width:calc(100% - 44px); }
  .plabel { font-size:13px; line-height:24px; } .pcol { min-width:0; }
  .items { --gi:12px; } .items + .sub { --gi:16px; } .sub { margin-bottom:6px; }
  .orn { display:none; }
}
@media print { .tabs, .banner-m { display:none !important; } }
""").substitute(P, nrows=DECK // 6, deck=DECK, band=BAND, gap=GAP)

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cantina &amp; Cocktail Bar · Iowa City, Iowa</title>
<style>{FONTS}{CSS}</style></head>
<body><div class="page">
<header class="mast">{papel()}{papel(5, 340, 56, "banner-m", 'width="100%"')}
<h1 class="title">Cantina <span class="amp">&amp;</span> Cocktail Bar</h1><p class="loc tagline">Iowa City, Iowa</p></header>
<nav class="tabs" aria-label="Jump to a card">{tabs}</nav>
<main class="deck">{deck}</main>
<footer class="foot" aria-hidden="true"></footer>
</div>{JS}</body></html>
"""
(OUT / "menu.html").write_text(HTML)
print("built round", ROUND, "cards", [(c[3], c[4]) for c in CARDS])
