"""Round 5: layout.json (geometry + per-card edges) and proposal.md, both generated from doc.json and the render's measure.json."""
import json, pathlib
HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path("/home/user/phg-harmony-app/handoff/designs/test-1-iowa-city-cantina")
R = json.loads((HERE / "measure.json").read_text()); M = R["M"]
doc = json.loads((OUT / "doc.json").read_text()); N = doc["meta"]["designer_notes"]
PT = 0.75; MM = 25.4 / 72
r2 = lambda v: round(v + 0.0, 2)
def b(o): return {k: r2(o[k] * PT) for k in ("x", "y", "w", "h")}
spread = lambda v: r2(max(v) - min(v)) if v else 0.0

cards = []
for c in M["cards"]:
    cb = b(c["box"]); right = cb["x"] + cb["w"]; bottom = cb["y"] + cb["h"]
    nl = [r2(i["name"]["x"] * PT) for i in c["items"]]
    pr = [r2((i["price"]["x"] + i["price"]["w"]) * PT) for i in c["items"]]
    dl = [r2(i["desc"]["x"] * PT) for i in c["items"]]
    sl = [r2(s["h3"]["x"] * PT) for s in c["subs"]]
    cn = b(c["cardno"]); ic = b(c["icon"])
    cards.append({
        "n": c["n"], "ref": c["ref"], "name": c["name"]["text"], "kicker": c["kicker"]["text"], "featured": c["featured"], "box_pt": cb,
        "border_pt": r2(c["border_px"] * PT), "padding_pt": {k: r2(v * PT) for k, v in c["padding_px"].items()},
        "cardno_left_pt": cn["x"], "icon_right_pt": r2(ic["x"] + ic["w"]),
        "item_name_left_pt": sorted(set(nl)), "name_left_spread_mm": r2(spread(nl) * MM),
        "price_right_pt": sorted(set(pr)), "price_right_spread_mm": r2(spread(pr) * MM),
        "desc_left_pt": sorted(set(dl)), "subheader_left_pt": sorted(set(sl)),
        "inner_left_pt": r2(min(nl) - cb["x"]), "inner_right_pt": r2(right - max(pr)),
        "free_space_below_content_pt": r2(bottom - c["padding_px"]["bottom"] * PT - c["border_px"] * PT - c["content_bottom"] * PT),
        "banner_pt": b(c["banner"]), "icon_pt": ic,
        "items": [{"ref": i["ref"], "name": i["name"]["text"], "price": i["price"]["text"], "name_pt": b(i["name"]), "price_pt": b(i["price"]),
                   "desc_pt": b(i["desc"]), "desc_lines": i["desc"].get("lines"), "desc": i["desc"]["text"]} for i in c["items"]],
        "subs": [{"ref": s["ref"], "text": s["h3"]["text"], "es": s["es"]["text"], "x_pt": r2(s["h3"]["x"] * PT)} for s in c["subs"]],
    })
rows = {}
for c in cards: rows.setdefault(c["box_pt"]["y"], []).append(c)
checks = {
    "inner_left_spread_mm_across_cards": r2(spread([c["inner_left_pt"] for c in cards]) * MM),
    "inner_right_spread_mm_across_cards": r2(spread([c["inner_right_pt"] for c in cards]) * MM),
    "max_name_left_spread_in_a_card_mm": max(c["name_left_spread_mm"] for c in cards),
    "max_price_right_spread_in_a_card_mm": max(c["price_right_spread_mm"] for c in cards),
    "names_desc_subs_share_left_edge": all(set(c["item_name_left_pt"]) | set(c["desc_left_pt"]) | set(c["subheader_left_pt"]) == set(c["item_name_left_pt"]) for c in cards),
    "cardno_on_name_edge": all(abs(c["cardno_left_pt"] - c["item_name_left_pt"][0]) < 0.6 for c in cards),
    "icon_on_price_edge": all(abs(c["icon_right_pt"] - c["price_right_pt"][0]) < 0.6 for c in cards),
    "row_heights_pt": {str(y): sorted({c["box_pt"]["h"] for c in cs}) for y, cs in sorted(rows.items())},
    "equal_height_within_every_row": all(len({c["box_pt"]["h"] for c in cs}) == 1 for cs in rows.values()),
    "no_card_overflow": all(c["free_space_below_content_pt"] >= 0 for c in cards),
    "printed_ink_margins_pt": R["ink"], "fonts_loaded": R["fonts"], "letter_png_px": R["png"], "phone_png_px": R["phone_png"],
    "phone": {"scroll_width_px": R["ph"]["scrollWidth"], "tab_bar_position": R["ph"]["tabs"], "tabs": R["ph"]["tab_count"],
              "cards_stacked_single_column": len({round(c["x"]) for c in R["ph"]["cards"]}) == 1},
}
L = {"round": 5, "concept": N["concept"],
     "page": {"size": "US Letter 8.5 x 11 in", "w_pt": 612, "h_pt": 792, "margins_pt": {"top": 36, "right": 36, "bottom": 36, "left": 36}, "bleed": "none (cream flood to trim, home/office print)"},
     "grid": {"deck_pt": b(M["deck"]), "gutter_pt": 12, "rows": "featured row (House Originals 318 pt | Classics 210 pt) + 2 rows of 2 x 264 pt; rows sized to content, spare height shared equally; cards stretch to equal height per row",
              "card_inner": "1.5 pt ink frame + inset hairline at 3 pt (lotería double rule); padding 9 / 12 / 10 / 12 pt on every card"},
     "palette": {"cream": "#F6EEDF", "card": "#FBF5EA", "featured_card": "#F3E3CB", "ink": "#231B16", "terracotta": "#A63C1A", "agave": "#2F5D50", "marigold": "#E3A018", "muted": "#5A4A3F"},
     "type": {"display": "Fraunces 700 (title 30/34 pt, banner names 13.5/15 pt, featured 17/19 pt)", "numerals": "Fraunces 600 terracotta, lining tabular: card ordinals 26 pt (featured 36 pt), prices 11.5 pt (featured 14 pt)",
              "items": "Fraunces 600 11.5/14 pt (featured 14/17 pt)", "descriptions": "DM Sans 8.5/11 pt (featured 9.5/12.5 pt)", "subheads": "DM Sans 700 caps 7.5 pt + Fraunces italic 9 pt Spanish",
              "kickers": "Fraunces italic 9/11 pt", "min_print_size_pt": 6.5},
     "masthead": {"papel_picado_pt": b(M["banner"]), "title_pt": b(M["title"]), "location_pt": b(M["loc"]), "footer_pt": b(M["foot"])},
     "cards": cards, "checks": checks}
(OUT / "layout.json").write_text(json.dumps(L, ensure_ascii=False, indent=1))

# ------------------------------------------------------------ proposal.md (generated; nothing hand-typed about the render)
it_by = {i["id"]: i for s in doc["sections"] for i in s["items"] + [x for sb in s["subs"] for x in sb["items"]]}
cs = N["copy_sources"]
o = ['# TEST-1 round 5: "Cantina & Cocktail Bar", Iowa City (proposal v5, concept round)', "",
     "Generated by `build/layout.py` from `doc.json` and the Chromium render (`build/measure.json`). needs_input = true (questions below).", "",
     "## Round 5: Lotería de la Cantina", "",
     "- " + N["concept"],
     "- The card system is the structure. Six cards, numbered in reading order. Card 1, House Originals, is the large featured card (318 pt wide against 210 pt, terracotta frame, 36 pt ordinal, 46 pt icon) in the top-left prime spot.",
     "- Card 2, Classics, leads with the Margarita. Cards 3 to 6 are Spirits, Beer, Cider and Wine, on a 2 x 2 grid of equal cards. Every card stretches to its row height, so the columns balance by construction.",
     "- The papel picado tops the page only. The icons are flat cut-paper SVGs: tumbler with a cube, coupe, agave, tap handle, apple and bottle.",
     "- Numeral system: card ordinals and prices use one face (Fraunces 600), one colour (terracotta) and lining tabular figures. The icon's right edge sits on the price edge, and the ordinal's left edge sits on the name edge.",
     "- Phone: the cards stack in one column, under a sticky bar of pennant-shaped flag tabs (numeral + English name) that jump to each card.",
     "- Copy: no line repeats its item name or says \"pour\" (the build asserts both). The spirits, beer and cider lines come from one gateway query (log_id 112). Serve phrases are in guest voice.", "",
     "## Cards (measured)", "", "| # | Card | Spanish | Box (x, y, w, h pt) | Inner L / R pt | Name-edge spread | Price-edge spread | Free space pt |", "|---|---|---|---|---|---|---|---|"]
for c in cards:
    bx = c["box_pt"]
    o.append(f'| {c["n"]} | {c["name"]}{" (featured)" if c["featured"] else ""} | {c["kicker"]} | {bx["x"]}, {bx["y"]}, {bx["w"]}, {bx["h"]} | {c["inner_left_pt"]} / {c["inner_right_pt"]} | {c["name_left_spread_mm"]} mm | {c["price_right_spread_mm"]} mm | {c["free_space_below_content_pt"]} |')
o += ["", f'Inner padding spread across all cards: left {checks["inner_left_spread_mm_across_cards"]} mm, right {checks["inner_right_spread_mm_across_cards"]} mm. '
      f'Equal height within every row: {checks["equal_height_within_every_row"]}. No overflow: {checks["no_card_overflow"]}. Printed ink margins (pt): {checks["printed_ink_margins_pt"]}. '
      f'Phone: tab bar `{checks["phone"]["tab_bar_position"]}`, {checks["phone"]["tabs"]} tabs, scroll width {checks["phone"]["scroll_width_px"]} px, single-column stack: {checks["phone"]["cards_stacked_single_column"]}.',
      "", "Subheader pairs: " + "; ".join(f"{k} / *{v}*" for k, v in N["sub_kickers"].items()) + ".", "",
      "## Printed copy and source table (matches menu.html)", "", "| Item | Price | Printed line | Words from | Gateway row ids | Still missing |", "|---|---|---|---|---|---|"]
for c in cards:
    for i in c["items"]:
        s = cs[i["ref"]]
        o.append(f'| {i["name"]} | {i["price"]} | {s["printed"]} | {s["words_from"]} | {", ".join(s["gateway_rows"]) or "none"} | {", ".join(s["missing"]) or "none"} |')
o += ["", "Gateway query (the only one this round): " + N["gateway_query"] + ".", "",
      "## Flags and needs_input (questions for the venue, via the Coordinator)", "",
      "1. **Pour sizes are missing** for Blanco Tequila, Añejo Tequila, Cognac VSOP and all draft beers; wine pour sizes too. None is printed.",
      "2. **Brut Rosé: glass or bottle?** The price label is empty in the draft. " + N["brut_rose_price"],
      "3. **Manhattan bitters:** " + N["manhattan_bitters"] + " The Old Fashioned prints \"bitters\" (draft word).",
      "4. No gateway rows exist for malbec, pinot grigio or brut rosé, and none for cognac VSOP specifically. Those lines use only the draft words. Brand, producer, region, vintage and ABV are still missing (see the table).",
      "5. Brown Butter Old Fashioned: please confirm the dairy allergen note.",
      "6. " + N["retired_junmai_ginjo"], "",
      "## References (library `menu_visual_documents.id`)", "",
      "572 (Coa Cantina Iowa City: agave first, the price band); 7923 (Coa Cantina Des Moines: a compact list led by cocktails); 4969 (Blue Agave, Iowa: the Classic / Signature tiers); "
      "208 (Alta Calidad, Brooklyn: pour size in the header, once supplied); 2585 (La Buena Vida, Fort Collins: Spanish/English headers).", "",
      "## Files", "", "menu.html, menu.pdf, preview-letter.png (" + "x".join(map(str, R["png"])) + " px, 300 dpi, not downscaled), preview-phone.png ("
      + "x".join(map(str, R["phone_png"])) + " px), doc.json, layout.json, proposal.md; copies in round-5/. Earlier rounds: round-1/ to round-4/proposal.md.", ""]
(OUT / "proposal.md").write_text("\n".join(o))
print(json.dumps({k: v for k, v in checks.items() if k not in ("printed_ink_margins_pt",)}, ensure_ascii=False))
