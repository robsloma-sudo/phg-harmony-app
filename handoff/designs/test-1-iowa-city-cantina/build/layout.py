"""Round 6: layout.json (geometry + per-card edges) and proposal.md, both generated from doc.json and the render's measure.json."""
import json, pathlib
HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path("/home/user/phg-harmony-app/handoff/designs/test-1-iowa-city-cantina")
R = json.loads((HERE / "measure.json").read_text()); M = R["M"]
doc = json.loads((OUT / "doc.json").read_text()); N = doc["meta"]["designer_notes"]
PT = 0.75; MM = 25.4 / 72
r2 = lambda v: round(v + 0.0, 2)
def b(o): return {k: r2(o[k] * PT) for k in ("x", "y", "w", "h")}
spread = lambda v: r2(max(v) - min(v)) if v else 0.0

def lum(h):
    c = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]; c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def contrast(a, b): x, y = sorted([lum(a), lum(b)], reverse=True); return r2((x + 0.05) / (y + 0.05))
PAL = {"cream": "#F6EEDF", "card": "#FBF5EA", "featured_card": "#F3E3CB", "ink": "#231B16", "terracotta": "#A63C1A", "agave": "#2F5D50", "marigold": "#E3A018", "muted": "#5A4A3F", "loteria_rosa": "#C2185B"}
cards, elements = [], []
def el(kind, ref, o, **kw): elements.append(dict({"kind": kind, "ref": ref}, **b(o), **kw))
for k in ("banner", "title", "loc", "deck", "foot"): el({"banner": "image", "title": "header", "loc": "subheader", "deck": "grid", "foot": "ornament"}[k], k, M[k], **({"text": M[k]["text"]} if "text" in M[k] else {}))
for c in M["cards"]:
    cb = b(c["box"]); inner_bottom = cb["y"] + cb["h"] - r2((c["padding_px"]["bottom"] + c["border_px"]) * PT)
    nb_ = b(c["namebar"]); fg = b(c["figure"])
    nl = [r2(i["name"]["x"] * PT) for i in c["items"]]; pr = [r2((i["price"]["x"] + i["price"]["w"]) * PT) for i in c["items"]]
    el("card", c["ref"], c["box"], n=c["n"], featured=c["featured"]); el("ordinal", c["ref"], c["cardno"], text=c["cardno"]["text"]); el("header", c["ref"], c["name"], text=c["name"]["text"])
    el("figure", c["ref"], c["figure"]); el("name_bar", c["ref"], c["namebar"], text=c["namebar"]["text"])
    for s_ in c["subs"]: el("subheader", s_["ref"], s_["h3"], text=s_["h3"]["text"], es=s_["es"]["text"])
    for i in c["items"]:
        el("item_name", i["ref"], i["name"], text=i["name"]["text"]); el("price", i["ref"], i["price"], text=i["price"]["text"])
        if i["desc"]: el("description", i["ref"], i["desc"], text=i["desc"]["text"], lines=i["desc"]["lines"])
    cards.append({"n": c["n"], "ref": c["ref"], "name": c["name"]["text"], "loteria_name": c["namebar"]["text"], "featured": c["featured"], "box_pt": cb,
        "edges_pt": {"left": cb["x"], "top": cb["y"], "right": r2(cb["x"] + cb["w"]), "bottom": r2(cb["y"] + cb["h"])},
        "padding_pt": {k: r2(v * PT) for k, v in c["padding_px"].items()}, "border_pt": r2(c["border_px"] * PT),
        "ordinal_pt": b(c["cardno"]), "figure_pt": fg, "figure_share_of_card_height": r2(fg["h"] / cb["h"]), "name_bar_pt": nb_,
        "space_below_name_bar_pt": r2(inner_bottom - (nb_["y"] + nb_["h"])),
        "item_name_left_pt": sorted(set(nl)), "price_right_pt": sorted(set(pr)),
        "item_gaps_pt": sorted({r2(g * PT) for g in c["item_gaps_px"]}), "line_heights_pt": sorted({r2(v * PT) for v in c["line_heights_px"]}),
        "items": [{"ref": i["ref"], "name": i["name"]["text"], "price": i["price"]["text"], "desc": i["desc"]["text"] if i["desc"] else "",
                   "desc_lines": i["desc"]["lines"] if i["desc"] else 0, "last_line_words": i["desc"].get("tokens_on_last_line") if i["desc"] else None} for i in c["items"]],
    })
PH = R["ph"]
checks = {
    "printed_ink_margins_pt": R["ink"], "page_margins_pt": {"top": 36, "right": 36, "bottom": 36, "left": 36},
    "card_edges_pt": {c["n"]: c["edges_pt"] for c in cards},
    "deck_within_margins": all(c["edges_pt"]["left"] >= 35.9 and c["edges_pt"]["right"] <= 576.1 for c in cards),
    "no_card_overflow": all(c["space_below_name_bar_pt"] >= -0.5 for c in cards),
    "max_empty_space_in_a_card_pt": max(c["space_below_name_bar_pt"] for c in cards),
    "no_card_more_than_12pt_empty": all(c["space_below_name_bar_pt"] <= 12 for c in cards),
    "figure_at_least_25pct_of_card_height": all(c["figure_share_of_card_height"] >= 0.25 for c in cards),
    "figure_shares": {c["n"]: c["figure_share_of_card_height"] for c in cards},
    "body_baseline_pt": sorted({v for c in cards for v in c["line_heights_pt"]}),
    "one_12pt_baseline": all(c["line_heights_pt"] == [12.0] for c in cards),
    "item_gaps_pt": sorted({g for c in cards for g in c["item_gaps_pt"]}),
    "same_item_gap_every_card": len({g for c in cards for g in c["item_gaps_pt"]}) <= 1,
    "same_bottom_padding_every_card": len({c["padding_pt"]["bottom"] for c in cards}) == 1,
    "equal_height_within_every_row": all(len({c["box_pt"]["h"] for c in cards if c["box_pt"]["y"] == y}) == 1 for y in {c["box_pt"]["y"] for c in cards}),
    "no_one_word_last_line_print": all((i["last_line_words"] or 2) >= 2 or i["desc_lines"] == 1 for c in cards for i in c["items"]),
    "no_one_word_last_line_phone": PH["min_last_line_tokens"] >= 2,
    "accent_contrast": {"rosa_on_card": contrast(PAL["loteria_rosa"], PAL["card"]), "rosa_on_featured": contrast(PAL["loteria_rosa"], PAL["featured_card"]),
                        "note": "rosa is used only for card ordinals and one small figure accent per card; both exceed 4.5:1"},
    "fonts_loaded": R["fonts"], "letter_png_px": R["png"], "phone_png_px": R["phone_png"],
    "phone": {"scroll_width_px": PH["scrollWidth"], "tab_bar_position": PH["tabs"], "tabs": PH["tab_count"], "tabbar_scroll_vs_client_px": PH["tabbar_scroll_vs_client"],
              "all_tabs_fit_390": PH["tabbar_scroll_vs_client"][0] <= PH["tabbar_scroll_vs_client"][1] and max(r[1] for r in PH["tab_rects"]) <= 390,
              "active_tab_label": PH["active_label"], "cards_stacked_single_column": max(c["x"] for c in PH["cards"]) - min(c["x"] for c in PH["cards"]) < 8,
              "dealt_rotation": [c["transform"] for c in PH["cards"]]},
}
L = {"round": 6, "concept": N["concept"],
     "page": {"size": "US Letter 8.5 x 11 in", "w_pt": 612, "h_pt": 792, "margins_pt": {"top": 36, "right": 36, "bottom": 36, "left": 36}, "bleed": "none (cream flood to trim, home/office print)"},
     "grid": {"deck_pt": b(M["deck"]), "columns_pt": [196, 160, 160], "gutter_pt": 12, "rows": "2 rows, 1 : 1.06; cards stretch to row height; the figure takes the spare height (flex), so no card has dead space",
              "card_anatomy": "1.5 pt frame + inset hairline at 3 pt; padding 7 / 10 / 8 / 10 pt on every card; ordinal top-left (24 pt row) + English name; central cut-paper figure; body; 20 pt lotería name bar at the foot"},
     "palette": PAL,
     "type": {"display": "Fraunces 700 (title 30/34 pt; card names 11.5 pt, featured 13 pt, on a 24 pt head row)", "ordinals": "Fraunces 700 19 pt, loteria rosa",
              "items": "Fraunces 600 10.5/12 pt (featured 11.5/12)", "prices": "Fraunces 600 terracotta lining tabular 10.5/12 pt", "descriptions": "DM Sans 8/12 pt (featured 8.5/12)",
              "subheads": "DM Sans 700 caps 7/12 pt + Fraunces italic 8.5/12 pt Spanish", "name_bar": "Fraunces 700 caps 10 pt (featured 11 pt), 2 pt tracking", "body_baseline_pt": 12, "item_gap_pt": 6},
     "masthead": {"papel_picado_pt": b(M["banner"]), "title_pt": b(M["title"]), "location_pt": b(M["loc"]), "footer_pt": b(M["foot"])},
     "elements": elements, "cards": cards, "measured_checks": checks}
(OUT / "layout.json").write_text(json.dumps(L, ensure_ascii=False, indent=1))

# ------------------------------------------------------------ proposal.md (generated; nothing hand-typed about the render)
it_by = {i["id"]: i for s in doc["sections"] for i in s["items"] + [x for sb in s["subs"] for x in sb["items"]]}
cs = N["copy_sources"]
o = ['# TEST-1 round 6: "Cantina & Cocktail Bar", Iowa City (proposal v6, Lotería refined)', "",
     "Generated by `build/layout.py` from `doc.json` and the Chromium render (`build/measure.json`). needs_input = true (questions below).", "",
     "## Round 6 changes", "",
     "- " + N["concept"],
     "- Copy: no taxonomy wording. Beer, cider and wine lines are the draft menu_description words. Blanco prints \"Also called plata.\" Añejo and Cognac VSOP are name-only, and their brand/age is flagged. Rows d4d63f58 and bc899a48 are no longer cited.",
     "- Card 1 (featured, top-left, terracotta frame, wider 196 pt column) is the agave story: Margarita, then Blanco and Añejo. Card 2 is House Originals. Classics and Brandy are separate one-item portrait cards. Cider joins Beer as Cerveza y Sidra.",
     "- One header treatment: no eyebrows. Every card has an ordinal (loteria rosa) top-left, the English name, a large figure that absorbs spare height, and a name bar at the foot.",
     "- 12 pt baseline for all body lines, 6 pt item gaps, 8 pt bottom padding on every card. Hyphenated compounds are non-breaking, and the last two words of every line are tied.",
     "- Phone: 6 grid tabs (numeral + figure icon; the English name only under the active tab), sticky; the cards stack as dealt cards (alternating ±0.7° tilt, offset shadow).",
     "- Manhattan: the bitters stay hidden (public_components aromatic-bitters = false). The Old Fashioned prints \"bitters\". Prices are unchanged (the build asserts item/price/meta parity with the draft).", "",
     "## Cards (measured)", "", "| # | Card | Name bar | Box (x, y, w, h pt) | Figure share | Space below name bar pt | Item gaps pt | Line heights pt |", "|---|---|---|---|---|---|---|---|"]
for c in cards:
    bx = c["box_pt"]
    o.append(f'| {c["n"]} | {c["name"]}{" (featured)" if c["featured"] else ""} | {c["loteria_name"]} | {bx["x"]}, {bx["y"]}, {bx["w"]}, {bx["h"]} | {c["figure_share_of_card_height"]} | {c["space_below_name_bar_pt"]} | {c["item_gaps_pt"]} | {c["line_heights_pt"]} |')
o += ["", "Measured checks: " + "; ".join(f"{k} = {checks[k]}" for k in ("no_card_overflow", "no_card_more_than_12pt_empty", "figure_at_least_25pct_of_card_height", "one_12pt_baseline", "same_item_gap_every_card", "same_bottom_padding_every_card", "equal_height_within_every_row", "no_one_word_last_line_print", "no_one_word_last_line_phone", "deck_within_margins"))
      + f'. Printed ink margins (pt): {checks["printed_ink_margins_pt"]}. Accent contrast: {checks["accent_contrast"]["rosa_on_card"]}:1 on card, {checks["accent_contrast"]["rosa_on_featured"]}:1 on featured. '
      f'Phone: tab bar `{checks["phone"]["tab_bar_position"]}`, {checks["phone"]["tabs"]} tabs, all fit at 390 px: {checks["phone"]["all_tabs_fit_390"]}, page scroll width {checks["phone"]["scroll_width_px"]} px, single-column stack: {checks["phone"]["cards_stacked_single_column"]}.',
      "", "Subheader pairs: " + "; ".join(f"{k} / *{v}*" for k, v in N["sub_kickers"].items()) + ".", "",
      "## Printed copy and source table (matches menu.html)", "", "| Item | Price | Printed line | Words from | Gateway row ids | Still missing |", "|---|---|---|---|---|---|"]
for c in cards:
    for i in c["items"]:
        s = cs[i["ref"]]
        o.append(f'| {i["name"]} | {i["price"]} | {s["printed"] or "(name only)"} | {s["words_from"]} | {", ".join(s["gateway_rows"]) or "none"} | {", ".join(s["missing"]) or "none"} |')
o += ["", "Gateway query (the only one this round): " + N["gateway_query"] + ".", "",
      "## Flags and needs_input (questions for the venue, via the Coordinator)", "",
      "1. **Pour sizes are missing** for Blanco Tequila, Añejo Tequila, Cognac VSOP and all draft beers; wine pour sizes too. None is printed. Añejo: brand and age statement? Cognac VSOP: brand/house? Blanco: does the venue want \"unaged\" (not in the cited row, so not printed)?",
      "2. **Brut Rosé: glass or bottle?** The price label is empty in the draft. " + N["brut_rose_price"],
      "3. **Manhattan bitters:** " + N["manhattan_bitters"] + " The Old Fashioned prints \"bitters\" (draft word).",
      "4. Beer, cider and wine lines are the draft words only. Brand, producer, region, vintage and ABV are still missing (see the table).",
      "5. Brown Butter Old Fashioned: please confirm the dairy allergen note.",
      "6. " + N["retired_junmai_ginjo"], "",
      "## References (library `menu_visual_documents.id`)", "",
      "572 (Coa Cantina Iowa City: agave first, the price band); 7923 (Coa Cantina Des Moines: a compact list led by cocktails); 4969 (Blue Agave, Iowa: the Classic / Signature tiers); "
      "208 (Alta Calidad, Brooklyn: pour size in the header, once supplied); 2585 (La Buena Vida, Fort Collins: Spanish/English headers).", "",
      "## Files", "", "menu.html, menu.pdf, preview-letter.png (" + "x".join(map(str, R["png"])) + " px, 300 dpi, not downscaled), preview-phone.png ("
      + "x".join(map(str, R["phone_png"])) + " px), doc.json, layout.json, proposal.md; copies in round-6/. Earlier rounds: round-1/ to round-5/proposal.md.", ""]
(OUT / "proposal.md").write_text("\n".join(o))
print(json.dumps({k: v for k, v in checks.items() if k not in ("card_edges_pt",)}, ensure_ascii=False))
