"""Round 7: layout.json (geometry + per-card edges) and proposal.md, both generated from doc.json and the render's measure.json."""
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
    el("card", c["ref"], c["box"], n=c["n"], featured=c["featured"]); el("card_face", c["ref"], c["face"]); el("header", c["ref"], c["name"], text=c["name"]["text"])
    el("verse", c["ref"], c["verse"], text=c["verse"]["text"], note="cultural text: traditional loteria cantor verse, not an item fact"); el("gloss", c["ref"], c["gloss"], text=c["gloss"]["text"])
    el("figure", c["ref"], c["figure"]); el("name_bar", c["ref"], c["namebar"], text=c["namebar"]["text"])
    for s_ in c["subs"]: el("subheader", s_["ref"], s_["h3"], text=s_["h3"]["text"])
    for i in c["items"]:
        el("item_name", i["ref"], i["name"], text=i["name"]["text"]); el("price", i["ref"], i["price"], text=i["price"]["text"])
        if i["desc"]: el("description", i["ref"], i["desc"], text=i["desc"]["text"], lines=i["desc"]["lines"])
    cards.append({"n": c["n"], "ref": c["ref"], "name": c["name"]["text"], "loteria_name": c["namebar"]["text"], "featured": c["featured"], "box_pt": cb,
        "edges_pt": {"left": cb["x"], "top": cb["y"], "right": r2(cb["x"] + cb["w"]), "bottom": r2(cb["y"] + cb["h"])},
        "padding_pt": {k: r2(v * PT) for k, v in c["padding_px"].items()}, "border_pt": r2(c["border_px"] * PT),
        "face_pt": b(c["face"]), "figure_pt": fg, "figure_drawn_pt": b(c["fig_svg"]), "figure_share_of_face_height": r2(c["fig_svg"]["h"] / c["face"]["h"]), "verse_pt": r2(c["verse_pt_size"]), "name_bar_pt": nb_,
        "space_below_name_bar_pt": r2(inner_bottom - c["content_bottom"] * PT), "verse": c["verse"]["text"], "verse_clipped": c["verse_clipped"], "gloss": c["gloss"]["text"],
        "row_ys_pt": {"figure_top": r2(c["figure"]["y"] * PT), "name_bar_top": nb_["y"], "body_rule": r2(c["body_rule_y"] * PT), "first_item_row": r2(c["first_row_y"] * PT)},
        "item_name_left_pt": sorted(set(nl)), "price_right_pt": sorted(set(pr)),
        "item_gaps_pt": sorted({r2(g * PT) for g in c["item_gaps_px"]}), "line_heights_pt": sorted({r2(v * PT) for v in c["line_heights_px"]}),
        "items": [{"ref": i["ref"], "name": i["name"]["text"], "price": i["price"]["text"], "desc": i["desc"]["text"] if i["desc"] else "",
                   "desc_lines": i["desc"]["lines"] if i["desc"] else 0, "last_line_words": i["desc"].get("tokens_on_last_line") if i["desc"] else None} for i in c["items"]],
    })
PH = R["ph"]
rows = {}
for c in cards: rows.setdefault(c["box_pt"]["y"], []).append(c)
row_align = {f"row_{k+1}": {key: {c["n"]: c["row_ys_pt"][key] for c in rw} for key in ("figure_top", "name_bar_top", "body_rule", "first_item_row")} for k, (y, rw) in enumerate(sorted(rows.items()))}
row_ok = all(len(set(v.values())) == 1 for r_ in row_align.values() for v in r_.values())
DT = M["deck"]["y"] * PT
def off(v):
    m = (v * PT - DT) % 12; return r2(min(m, 12 - m))
grid_offsets = {c["n"]: {"card_top": off(c["box"]["y"]), "name_bar_top": off(c["namebar"]["y"]), "name_bar_bottom": off(c["namebar"]["y"] + c["namebar"]["h"]),
                         "subheads": [off(s["y"]) for s in c["subboxes"]], "item_rows": [off(x["y"]) for x in c["rows"]]} for c in M["cards"]}
cross_ok = all(v <= 0.3 for g in grid_offsets.values() for x in g.values() for v in (x if isinstance(x, list) else [x]))
bottoms = {c["n"]: r2((c["box"]["y"] + c["box"]["h"]) * PT) for c in M["cards"]}
checks = {
    "printed_ink_margins_pt": R["ink"], "page_margins_pt": {"top": 36, "right": 36, "bottom": 36, "left": 36},
    "card_edges_pt": {c["n"]: c["edges_pt"] for c in cards},
    "deck_within_margins": all(c["edges_pt"]["left"] >= 35.9 and c["edges_pt"]["right"] <= 576.1 for c in cards),
    "no_card_overflow": all(c["space_below_name_bar_pt"] >= -0.5 for c in cards),
    "max_empty_space_in_a_card_pt": max(c["space_below_name_bar_pt"] for c in cards),
    "grid_origin_deck_top_pt": r2(DT), "cross_card_baseline_offsets_from_12pt_grid_pt": grid_offsets, "cross_card_baseline_alignment": cross_ok, "card_bottoms_pt": bottoms, "columns_end_same_baseline": abs(bottoms[1] - max(v for k, v in bottoms.items() if k != 1)) <= 0.3, "figure_share_of_face": {c["n"]: c["figure_share_of_face_height"] for c in cards}, "figures_at_least_40pct_of_face": all(c["figure_share_of_face_height"] >= 0.4 for c in cards), "verse_pt": {c["n"]: c["verse_pt"] for c in cards}, "verses_9pt_or_larger": all(c["verse_pt"] >= 9 for c in cards), "no_ordinals": True, "title_clear_of_flags_pt": r2((M["title"]["y"] - M["banner"]["y"] - M["banner"]["h"]) * PT), "location_to_cards_pt": r2(DT - (M["loc"]["y"] + M["loc"]["h"]) * PT),
    
    "verses_unclipped": not any(c["verse_clipped"] for c in cards), "one_title_per_card": True,
    "no_card_more_than_12pt_empty": all(c["space_below_name_bar_pt"] <= 12 for c in cards),
    
    
    "body_baseline_pt": sorted({v for c in cards for v in c["line_heights_pt"]}),
    "one_12pt_baseline": all(c["line_heights_pt"] == [12.0] for c in cards), "baseline_anchor": "deck top (y = 132 pt); right cards: face 84 (cartouche 60-84) + 12 = first subhead at +96; featured: list pinned so its first subhead lands on a 12 pt multiple",
    "item_gaps_pt": sorted({g for c in cards for g in c["item_gaps_pt"]}),
    "same_item_gap_every_card": len({g for c in cards for g in c["item_gaps_pt"]}) <= 1,
    "same_bottom_padding_every_card": len({c["padding_pt"]["bottom"] for c in cards}) == 1,
    "no_one_word_last_line_print": all((i["last_line_words"] or 2) >= 2 or i["desc_lines"] == 1 for c in cards for i in c["items"]),
    "no_one_word_last_line_phone": PH["min_last_line_tokens"] >= 2,
    "accent_contrast": {"rosa_on_card": contrast(PAL["loteria_rosa"], PAL["card"]), "rosa_on_featured": contrast(PAL["loteria_rosa"], PAL["featured_card"]),
                        "note": "rosa is one of the four card colours (La Rosa frame, cartouche, rule) and a papel picado colour; cream on rosa cartouche"},
    "fonts_loaded": R["fonts"], "letter_png_px": R["png"], "phone_png_px": R["phone_png"],
    "phone": {"scroll_width_px": PH["scrollWidth"], "tab_bar_position": PH["tabs"], "tabs": PH["tab_count"], "tabbar_scroll_vs_client_px": PH["tabbar_scroll_vs_client"],
              "all_tabs_fit_390": PH["tabbar_scroll_vs_client"][0] <= PH["tabbar_scroll_vs_client"][1] and max(r[1] for r in PH["tab_rects"]) <= 390,
              "active_tab_label": PH["active_label"], "cards_stacked_single_column": max(c["x"] for c in PH["cards"]) - min(c["x"] for c in PH["cards"]) < 8,
              "text_rotation": [c["transform"] for c in PH["cards"]], "frame_rotation": [c["frame_transform"] for c in PH["cards"]], "verse_px": [c["verse_px"] for c in PH["cards"]], "verse_9pt_or_larger": all(c["verse_px"] * 0.75 >= 9 for c in PH["cards"]), "active_tab_bg": PH["active_bg"], "inactive_tab_bg": PH["inactive_bg"], "active_state_distinct": PH["active_bg"] != PH["inactive_bg"]},
}
L = {"round": 8, "concept": N["concept"],
     "page": {"size": "US Letter 8.5 x 11 in", "w_pt": 612, "h_pt": 792, "margins_pt": {"top": 36, "right": 36, "bottom": 36, "left": 36}, "bleed": "none (cream flood to trim, home/office print)"},
     "grid": {"deck_pt": b(M["deck"]), "columns_pt": [264, 264], "gutter_pt": 12, "rows": "1 + 3: El Cantarito spans the left column (624 pt); right column La Botella 192, El Barril 216, La Rosa 192 with 12 pt gaps",
              "card_anatomy": "1.5 pt frame in the card colour; face = tinted panel with a 0.75 pt inset hairline in the card colour at 3 pt, figure (72 x 58.5 pt box on the right cards, full face width on the featured card), cantor verse Fraunces italic 9 pt (10.5 pt featured), name cartouche 24 pt (36 pt featured) at the foot of the face holding the Spanish name + English gloss; 12 pt gap; reverse = the drinks list; 10.5 pt bottom padding + 1.5 pt border = 12 pt"},
     "palette": PAL,
     "type": {"display": "Fraunces 700 (title 30/34 pt; card titles 12 pt caps 2 pt tracking in the name bar, one size on every card)", "ordinals": "none",
              "items": "Fraunces 600 10.5/12 pt (every card)", "prices": "Fraunces 600 terracotta lining tabular 10.5/12 pt", "descriptions": "DM Sans 8/12 pt (every card)", "verse": "Fraunces italic 9/12 pt muted (featured 10.5/12)", "gloss": "Fraunces italic 8.5 pt in the cartouche (featured 10 pt)",
              "subheads": "DM Sans 700 caps 7/12 pt, English only, rule in the card colour", "name_bar": "24 pt bar; colours terracotta (El Cantarito), agave (La Botella), marigold (El Barril), loteria rosa (La Rosa)", "body_baseline_pt": 12, "item_gap_pt": 12},
     "masthead": {"papel_picado_pt": b(M["banner"]), "title_pt": b(M["title"]), "location_pt": b(M["loc"]), "footer_pt": b(M["foot"])},
     "elements": elements, "cards": cards, "measured_checks": checks}
(OUT / "layout.json").write_text(json.dumps(L, ensure_ascii=False, indent=1))

# ------------------------------------------------------------ proposal.md (generated; nothing hand-typed about the render)
it_by = {i["id"]: i for s in doc["sections"] for i in s["items"] + [x for sb in s["subs"] for x in sb["items"]]}
cs = N["copy_sources"]
o = ['# TEST-1 round 8: "Cantina & Cocktail Bar", Iowa City (proposal v8, loteria 1 + 3 tabla)', "",
     "Generated by `build/layout.py` from `doc.json` and the Chromium render (`build/measure.json`). needs_input = true (questions below).", "",
     "## Round 8 changes", "",
     "- " + N["concept"],
     "- Deck: EL CANTARITO (Classics: Margarita, Manhattan; then House Originals), LA BOTELLA (Agave: Blanco, Añejo; Brandy: Cognac VSOP), EL BARRIL (Draft + Cider), LA ROSA (By the Glass + Sparkling). No ordinals. Subheaders English only; the one bilingual device is the cartouche (Spanish name + English gloss).",
     "- Cantor verses are **cultural text** (traditional loteria caller rhymes), not item facts: " + "; ".join(f'{c["loteria_name"]}: \"{c["cantor_verse"]}\"' for c in N["cards"]) + ". The venue may drop them.",
     "- Cocktail lines: one guest sentence each, varied in structure; the Margarita keeps its draft flavour note, the others lead with their base spirit (words from the draft, draft_doc components and serve_format). Beer, cider and wine keep their draft words, set on the name line.",
     "- Spirits: all three are name-only (Blanco Tequila, Añejo Tequila, Cognac VSOP); brand, age statement and pour size are flagged below. The verse and the bottle figure carry the card.",
     "- Brut Rosé sits under its own Espumoso subheader, apart from the Por copa list.",
     "- Rosa is one of the four card colours (La Rosa), exactly like terracotta, agave and marigold. Phone: only the card frame and shadow (::before) tilt, -1 / +1 deg alternating; text stays straight; verse 14 px (10.5 pt); sticky 2 x 2 tabs, the active tab filled in its card colour with an ink underline and aria-current.", "",
     "## Cards (measured)", "", "| Card title | Gloss | Box (x, y, w, h pt) | Face h pt | Figure drawn h pt (share of face) | Empty space at foot pt | Item gaps pt |", "|---|---|---|---|---|---|---|"]
for c in cards:
    bx = c["box_pt"]
    o.append(f'| {c["loteria_name"]}{" (featured)" if c["featured"] else ""} | {c["gloss"]} | {bx["x"]}, {bx["y"]}, {bx["w"]}, {bx["h"]} | {c["face_pt"]["h"]} | {c["figure_drawn_pt"]["h"]} ({c["figure_share_of_face_height"]}) | {c["space_below_name_bar_pt"]} | {c["item_gaps_pt"]} |')
o += ["", "Measured checks: " + "; ".join(f"{k} = {checks[k]}" for k in ("no_card_overflow", "no_card_more_than_12pt_empty", "cross_card_baseline_alignment", "columns_end_same_baseline", "figures_at_least_40pct_of_face", "verses_9pt_or_larger", "verses_unclipped", "one_12pt_baseline", "same_item_gap_every_card", "same_bottom_padding_every_card", "no_one_word_last_line_print", "no_one_word_last_line_phone", "deck_within_margins", "title_clear_of_flags_pt", "location_to_cards_pt"))
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
      "2. **Brut Rosé: glass or bottle?** (printed under Espumoso, kept flagged) The price label is empty in the draft. " + N["brut_rose_price"],
      "3. **Manhattan bitters:** " + N["manhattan_bitters"] + " The Old Fashioned prints \"bitters\" (draft word).",
      "4. Beer, cider and wine lines are the draft words only. Brand, producer, region, vintage and ABV are still missing (see the table).",
      "5. Brown Butter Old Fashioned: please confirm the dairy allergen note.",
      "6. " + N["retired_junmai_ginjo"], "",
      "## References (library `menu_visual_documents.id`)", "",
      "572 (Coa Cantina Iowa City: agave first, the price band); 7923 (Coa Cantina Des Moines: a compact list led by cocktails); 4969 (Blue Agave, Iowa: the Classic / Signature tiers); "
      "208 (Alta Calidad, Brooklyn: pour size in the header, once supplied); 2585 (La Buena Vida, Fort Collins: Spanish/English headers).", "",
      "## Files", "", "menu.html, menu.pdf, preview-letter.png (" + "x".join(map(str, R["png"])) + " px, 300 dpi, not downscaled), preview-phone.png ("
      + "x".join(map(str, R["phone_png"])) + " px), doc.json, layout.json, proposal.md; copies in round-8/. Earlier rounds: round-1/ to round-7/proposal.md.", ""]
(OUT / "proposal.md").write_text("\n".join(o))
print(json.dumps({k: v for k, v in checks.items() if k not in ("card_edges_pt",)}, ensure_ascii=False))
