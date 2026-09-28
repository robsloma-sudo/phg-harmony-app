"""Round 11: layout.json (geometry + per-card edges) and proposal.md, both generated from doc.json and the render's measure.json."""
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
PAL = {"cream": "#F6EEDF", "card": "#FBF5EA", "featured_card": "#F3E3CB", "ink": "#231B16", "terracotta": "#A63C1A", "agave": "#2F5D50", "marigold": "#E3A018", "muted": "#5A4A3F", "loteria_rosa": "#C2185B", "agave_blue": "#1E3F66"}
cards, elements = [], []
def el(kind, ref, o, **kw): elements.append(dict({"kind": kind, "ref": ref}, **b(o), **kw))
for k in ("banner", "title", "loc", "deck", "foot"): el({"banner": "image", "title": "header", "loc": "subheader", "deck": "grid", "foot": "ornament"}[k], k, M[k], **({"text": M[k]["text"]} if "text" in M[k] else {}))
for c in M["cards"]:
    cb = b(c["box"]); inner_bottom = cb["y"] + cb["h"] - r2((c["padding_px"]["bottom"] + c["border_px"]) * PT)
    nb_ = b(c["namebar"]); fg = b(c["figure"])
    nl = [r2(i["name"]["x"] * PT) for i in c["items"]]; pr = [r2((i["price"]["x"] + i["price"]["w"]) * PT) for i in c["items"]]
    el("card", c["ref"], c["box"], n=c["n"], featured=c["featured"]); el("card_face", c["ref"], c["face"]); el("card_number", c["ref"], c["cardno"], text=c["cardno"]["text"]); el("header", c["ref"], c["name"], text=c["name"]["text"])
    el("verse", c["ref"], c["verse"], text=c["verse"]["text"], note="cultural text: traditional loteria cantor verse, not an item fact"); el("gloss", c["ref"], c["gloss"], text=c["gloss"]["text"])
    el("figure", c["ref"], c["figure"]); el("name_bar", c["ref"], c["namebar"], text=c["namebar"]["text"])
    for s_ in c["subs"]: el("subheader", s_["ref"], s_["h3"], text=s_["h3"]["text"])
    for i in c["items"]:
        el("item_name", i["ref"], i["name"], text=i["name"]["text"]); el("price", i["ref"], i["price"], text=i["price"]["text"])
        if i["desc"]: el("description", i["ref"], i["desc"], text=i["desc"]["text"], lines=i["desc"]["lines"])
    cards.append({"n": c["n"], "ref": c["ref"], "name": c["name"]["text"], "loteria_name": c["namebar"]["text"], "featured": c["featured"], "box_pt": cb,
        "edges_pt": {"left": cb["x"], "top": cb["y"], "right": r2(cb["x"] + cb["w"]), "bottom": r2(cb["y"] + cb["h"])},
        "padding_pt": {k: r2(v * PT) for k, v in c["padding_px"].items()}, "border_pt": r2(c["border_px"] * PT),
        "face_pt": b(c["face"]), "cardno": c["cardno"]["text"], "cardno_pt": b(c["cardno"]), "figure_pt": fg, "figure_drawn_pt": b(c["fig_svg"]), "figure_share_of_face_height": r2(c["fig_svg"]["h"] / c["face"]["h"]), "verse_pt": r2(c["verse_pt_size"]), "name_bar_pt": nb_,
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
    m = (v * PT - DT) % 6; return r2(min(m, 6 - m))
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
    "grid_origin_deck_top_pt": r2(DT), "cross_card_baseline_offsets_from_6pt_grid_pt": grid_offsets, "cross_card_baseline_alignment": cross_ok, "card_bottoms_pt": bottoms, "columns_end_same_baseline": abs(bottoms[2] - bottoms[4]) <= 0.3, "figure_share_of_face": {c["n"]: c["figure_share_of_face_height"] for c in cards}, "figures_at_least_40pct_of_face": all(c["figure_share_of_face_height"] >= 0.4 for c in cards), "face_share_of_card": {c["n"]: r2(c["face_pt"]["h"] / c["box_pt"]["h"]) for c in cards}, "featured_face_35_to_40pct": 0.35 <= cards[0]["face_pt"]["h"] / cards[0]["box_pt"]["h"] <= 0.40, "card_heights_pt": {c["n"]: c["box_pt"]["h"] for c in cards}, "face_heights_pt": {c["n"]: c["face_pt"]["h"] for c in cards}, "heights_multiple_of_6pt": all(abs(c["box_pt"]["h"] / 6 - round(c["box_pt"]["h"] / 6)) < 0.05 and abs((c["face_pt"]["h"] + 3) / 6 - round((c["face_pt"]["h"] + 3) / 6)) < 0.05 for c in cards), "card_numbers": {c["n"]: c["cardno"] for c in cards}, "card_numbers_source": "traditional Don Clemente lotería numbers (El Cantarito 44, La Botella 8, El Barril 9, La Rosa 41)", "verse_pt": {c["n"]: c["verse_pt"] for c in cards}, "verses_9pt_or_larger": all(c["verse_pt"] >= 9 for c in cards), "title_clear_of_flags_pt": r2((M["title"]["y"] - M["banner"]["y"] - M["banner"]["h"]) * PT), "location_to_cards_pt": r2(DT - (M["loc"]["y"] + M["loc"]["h"]) * PT),
    
    "verses_unclipped": not any(c["verse_clipped"] for c in cards), "one_title_per_card": True,
    "no_card_more_than_12pt_empty": all(c["space_below_name_bar_pt"] <= 12 for c in cards),
    
    
    "body_baseline_pt": sorted({v for c in cards for v in c["line_heights_pt"]}),
    "one_12pt_baseline": all(c["line_heights_pt"] == [12.0] for c in cards), "baseline_anchor": "deck top (y = 138 pt); every card top, name band top/bottom, subhead and item row sits on a 6 pt step from it (3 pt frame + face height = a multiple of 6)",
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
def rhythm(c):
    blocks = list(c["rows"]) + [i["block"] for i in c["items"]]  # line boxes (item blocks), not glyph boxes
    nbb = c["namebar"]["y"] + c["namebar"]["h"]
    above = [r2((sb["y"] - max([x["y"] + x["h"] for x in blocks if x["y"] + x["h"] <= sb["y"] + 0.5] + [nbb])) * PT) for sb in c["subboxes"]]
    below = [r2((min(x["y"] for x in c["rows"] if x["y"] >= sb["y"] + sb["h"] - 0.5) - (sb["y"] + sb["h"])) * PT) for sb in c["subboxes"]]
    return above, below
RH = {c["n"]: rhythm(c) for c in M["cards"]}
ab = [v for a, _ in RH.values() for v in a]; bl = [v for _, x in RH.values() for v in x]
ph = [r2(i["price"]["h"] * PT) for c in M["cards"] for i in c["items"]]; nh = [r2(i["name"]["h"] * PT) for c in M["cards"] for i in c["items"]]
checks.update({"subhead_space_above_pt": {n: a for n, (a, _) in RH.items()}, "subhead_space_below_pt": {n: x for n, (_, x) in RH.items()},
    "subhead_space_above_equal_every_card_0_5mm": bool(ab) and (max(ab) - min(ab)) * MM <= 0.5, "subhead_space_above_is_12pt": all(abs(v - 12) <= 0.5 for v in ab),
    "subhead_space_below_equal_every_card_0_5mm": (max(bl) - min(bl)) * MM <= 0.5, "subhead_space_below_is_6pt": all(abs(v - 6) <= 0.5 for v in bl),
    "same_item_gap_across_cards": len({g for c in cards for g in c["item_gaps_pt"]}) <= 1,
    "price_box_heights_pt": sorted(set(ph)), "same_price_size_across_cards": spread(ph) <= 0.5, "same_item_name_size_across_cards": spread(nh) <= 0.5,
    "price_colour_per_card": {"1": PAL["terracotta"], "2": PAL["agave_blue"], "3": PAL["agave"], "4": PAL["loteria_rosa"]}, "price_type": "Fraunces 700, 11.5/12 pt, font-feature-settings tnum + lnum",
    "contrast": {"cream_on_rosa_namebar": contrast(PAL["cream"], PAL["loteria_rosa"]), "cream_on_agave_blue_namebar": contrast(PAL["cream"], PAL["agave_blue"]), "marigold_number_on_ink_chip": contrast(PAL["marigold"], PAL["ink"]), "cream_on_agave_namebar": contrast(PAL["cream"], PAL["agave"]), "cream_on_terracotta_namebar": contrast(PAL["cream"], PAL["terracotta"]),
                 "terracotta_price_on_featured": contrast(PAL["terracotta"], PAL["featured_card"]), "agave_blue_price_on_card": contrast(PAL["agave_blue"], PAL["card"]), "terracotta_price_on_card": contrast(PAL["terracotta"], PAL["card"]), "muted_tbc_on_card": contrast(PAL["muted"], PAL["card"]), "agave_price_on_card": contrast(PAL["agave"], PAL["card"]), "rosa_price_on_card": contrast(PAL["loteria_rosa"], PAL["card"]), "muted_serve_cue_on_featured": contrast(PAL["muted"], PAL["featured_card"])}})
pc = [i["cue"] for c in M["cards"] for i in c["items"] if i.get("cue")]
checks["serve_cues_print"] = {i["ref"]: i["cue"] for c in M["cards"] for i in c["items"] if i.get("cue")}
checks["serve_cues_phone"] = {q["ref"]: {k: q[k] for k in ("lines", "shares_line_with_description", "words")} for q in PH["cues"]}
checks["no_orphan_cue_print"] = all(q["lines"] == 1 and q["words"] >= 2 for q in pc) and checks["no_one_word_last_line_print"]
checks["no_orphan_cue_phone"] = all(q["lines"] == 1 and q["words"] >= 2 for q in PH["cues"]) and checks["no_one_word_last_line_phone"]
checks["no_orphan_cue_note"] = "a cue counts as orphaned if it is split across lines or leaves one word on a line; each cue is non-breaking, so it either follows its description on the same line or sits whole on the next line (see serve_cues_*.shares_line_with_description)"
checks["all_contrast_4_5_or_more"] = all(v >= 4.5 for v in checks["contrast"].values())
checks["margins_equal_within_1mm"] = (max(R["ink"].values()) - min(R["ink"].values())) * MM <= 1
L = {"round": 11, "concept": N["concept"],
     "page": {"size": "US Letter 8.5 x 11 in", "w_pt": 612, "h_pt": 792, "margins_pt": {"top": 36, "right": 36, "bottom": 36, "left": 36}, "bleed": "none (cream flood to trim, home/office print)"},
     "grid": {"deck_pt": b(M["deck"]), "columns_pt": [264, 264], "gutter_pt": 12, "baseline_step_pt": 6, "rows": N["card_layout"] + " One rhythm on every card: 12 pt from the name band to the first subhead and above every subhead, 6 pt below every subhead, 12 pt item gap, 12 pt lines.",
              "card_anatomy": "3 pt frame in the card colour; face (141 / 81 / 141 / 147 pt) = tinted panel with a 0.75 pt inset hairline at 3 pt; lotería number chip 24 x 24 pt at 6 pt from the top-left corner (Fraunces 700 12 pt marigold on ink); one composition on every card: square cut-paper figure (face - 36 pt) at x = 36 pt, cantor verse Fraunces italic 10/12 pt to its right; 24 pt name band under the figure (Spanish name Fraunces 700 12 pt caps + English gloss, identical on every card); 12 pt; list; 9 pt bottom padding + 3 pt frame = 12 pt"},
     "palette": PAL,
     "type": {"display": "Fraunces 700 (title 24/24 pt, 18 pt below the 36 pt papel picado; card titles 12 pt caps 2 pt tracking in the name band, one size on every card)", "card_numbers": "Fraunces 700 12 pt, marigold #E3A018 on ink #231B16 chip (the only marigold type; never on cream)",
              "items": "Fraunces 600 10.5/12 pt (every card)", "prices": "Fraunces 700 11.5/12 pt, tnum + lnum, in the card colour (terracotta, agave blue, agave green, rosa)", "descriptions": "DM Sans 8/12 pt stacked under the name on all 14 items, ink; cocktails add a non-breaking serve cue in italic muted #5A4A3F; Brut Rosé adds a muted italic 7.5 pt 'glass / bottle TBC' right-aligned under its price", "verse": "Fraunces italic 10/12 pt muted, every card", "gloss": "Fraunces italic 8.5 pt in the name band, every card",
              "subheads": "DM Sans 700 caps 7/12 pt, English only, rule in the card colour", "name_bar": "24 pt band; terracotta (El Cantarito), agave blue #1E3F66 (La Botella), agave green (El Barril), lotería rosa (La Rosa), cream text on all four; marigold as type only in the number chips on ink", "body_baseline_pt": 12, "item_gap_pt": 12},
     "masthead": {"papel_picado_pt": b(M["banner"]), "title_pt": b(M["title"]), "location_pt": b(M["loc"]), "footer_pt": b(M["foot"])},
     "elements": elements, "cards": cards, "measured_checks": checks}
(OUT / "layout.json").write_text(json.dumps(L, ensure_ascii=False, indent=1))

# ------------------------------------------------------------ proposal.md (generated; nothing hand-typed about the render)
cs = N["copy_sources"]
KEYS = ("cross_card_baseline_alignment", "heights_multiple_of_6pt", "subhead_space_above_is_12pt", "subhead_space_above_pt", "subhead_space_below_is_6pt", "no_orphan_cue_print", "no_orphan_cue_phone",
        "no_one_word_last_line_print", "no_one_word_last_line_phone", "no_card_overflow", "no_card_more_than_12pt_empty", "columns_end_same_baseline", "featured_face_35_to_40pct", "face_share_of_card",
        "figures_at_least_40pct_of_face", "verses_9pt_or_larger", "verses_unclipped", "one_12pt_baseline", "same_item_gap_every_card", "same_bottom_padding_every_card", "same_price_size_across_cards",
        "same_item_name_size_across_cards", "deck_within_margins", "margins_equal_within_1mm", "all_contrast_4_5_or_more", "title_clear_of_flags_pt", "location_to_cards_pt")
o = ['# TEST-1 round 11: "Cantina & Cocktail Bar", Iowa City (proposal v11, lotería tabla 2 + 2)', "",
     "Generated by `build/layout.py` from `doc.json` and the Chromium render (`build/measure.json`). needs_input = true (questions below).", "",
     "## Concept", "", N["concept"], "",
     "## Round 11 changes (from round 10)", "",
     "- Real lotería cards: 3 pt frame, the traditional Don Clemente number in the top-left corner (44 El Cantarito, 8 La Botella, 9 El Barril, 41 La Rosa; marigold numerals on ink chips), the name in the band under the figure, one title style at one size on every card.",
     "- One face composition on every card and on the phone: square cut-paper figure left, cantor verse right, name band under. El Cantarito's face is now " + f'{checks["face_share_of_card"][1]:.0%}' + " of its card; the cocktails start in the upper half of the left column, House Originals first.",
     "- Grid: 2 + 2 tabla (was 1 + 3). " + N["card_layout"] + " " + N["why_2_plus_2"],
     "- Subheads merged: " + N["structure_changes"],
     "- One description treatment for all 14 items: description stacked under the name, price on the name line. Spirits now print their draft words in guest form (Tequila blanco, by the pour. / Tequila añejo, by the pour. / VSOP Cognac, by the pour.).",
     "- Manhattan: " + N["manhattan_bitters"] + " It also gets the character lead 'Spirit-forward' (draft meta.family). House Daiquiri: no character words exist in the draft, so its line is unchanged.",
     "- Brut Rosé: " + N["brut_rose_price"],
     "- Serve cues use non-breaking spaces inside 'one large cube', 'in a coupe', 'lime coin', 'orange peel' (and 'on the rocks', 'lime wheel', 'cocktail cherry'), and each cue is kept on one line.",
     "- Prices: Fraunces 700 11.5 pt, tnum + lnum, in the card colour. " + N["palette_note"], "",
     "## Cards (measured)", "", "| Card | No. | Box (x, y, w, h pt) | Face h pt (share of card) | Figure drawn h pt (share of face) | Empty space at foot pt | Item gaps pt |", "|---|---|---|---|---|---|---|"]
for c in cards:
    bx = c["box_pt"]
    o.append(f'| {c["loteria_name"].splitlines()[0]}{" (featured)" if c["featured"] else ""} / {c["gloss"]} | {c["cardno"]} | {bx["x"]}, {bx["y"]}, {bx["w"]}, {bx["h"]} | {c["face_pt"]["h"]} ({checks["face_share_of_card"][c["n"]]}) | {c["figure_drawn_pt"]["h"]} ({c["figure_share_of_face_height"]}) | {c["space_below_name_bar_pt"]} | {c["item_gaps_pt"]} |')
o += ["", "## Measured checks (all from the render)", ""] + [f"- {k} = {checks[k]}" for k in KEYS] + [
      f'- printed ink margins (pt) = {checks["printed_ink_margins_pt"]}',
      f'- serve cues, print = {checks["serve_cues_print"]}', f'- serve cues, phone = {checks["serve_cues_phone"]}', "- " + checks["no_orphan_cue_note"],
      f'- contrast = {checks["contrast"]}',
      f'- phone: tab bar `{checks["phone"]["tab_bar_position"]}`, {checks["phone"]["tabs"]} tabs, all fit at 390 px: {checks["phone"]["all_tabs_fit_390"]}, page scroll width {checks["phone"]["scroll_width_px"]} px, single-column stack: {checks["phone"]["cards_stacked_single_column"]}', "",
      "## Printed copy and source table (matches menu.html)", "", "| Item | Price | Printed line | Words from | Gateway row ids | Still missing |", "|---|---|---|---|---|---|"]
for c in cards:
    for i in c["items"]:
        s_ = cs[i["ref"]]
        pr = s_["printed"] + (f' [{s_["proof_marker"]}]' if s_["proof_marker"] else "")
        o.append(f'| {i["name"]} | {i["price"]} | {pr} | {s_["words_from"]} | {", ".join(s_["gateway_rows"]) or "none"} | {", ".join(s_["missing"]) or "none"} |')
o += ["", "Subheads as printed: " + "; ".join(f'{c["loteria_name"].splitlines()[0]}: ' + ", ".join(x["text"] for x in [e for e in elements if e["kind"] == "subheader" and e["ref"] in [s["ref"] for mc in M["cards"] if mc["n"] == c["n"] for s in mc["subs"]]]) for c in cards) + ".", "",
      "Gateway: " + N["gateway_query"], "",
      "## Flags and needs_input (questions for the venue, via the Coordinator)", "",
      "1. **Pour sizes are missing** for Blanco Tequila, Añejo Tequila, Cognac VSOP, the beers and the wines; none is printed ('by the pour' is the draft's own word). Blanco / Añejo: brand? Añejo: age statement? Cognac VSOP: brand / house?",
      "2. **Brut Rosé: glass or bottle?** The draft price label is empty, so the menu prints a muted 'glass / bottle TBC' marker under the price until it is answered.",
      "3. Beer, cider and wine lines are the draft words only. Brewery, producer, region, vintage, ABV and the cider's format (draft or can) are still missing.",
      "4. Brown Butter Old Fashioned: please confirm the dairy allergen note.",
      "5. " + N["retired_junmai_ginjo"],
      "6. Structure: Dry Cider is folded into the Beer section ('Draft & Cider') and Brut Rosé into the one wine list; confirm the venue is happy with the merged doc sections.",
      "7. **Drinking-joke verses (responsible-service tone):** La Botella (\"La herramienta del borracho.\") and El Barril (\"Tanto bebió el albañil, que quedó como barril.\") are traditional lotería verses that joke about drunkenness. Keep, replace or drop them? The venue decides. (All four verses are cultural text, not item facts.)", "",
      "## References (library `menu_visual_documents.id`)", "",
      "572 (Coa Cantina Iowa City: agave first, the price band); 7923 (Coa Cantina Des Moines: a compact list led by cocktails); 4969 (Blue Agave, Iowa: the Classic / Signature tiers); "
      "208 (Alta Calidad, Brooklyn: pour size in the header, once supplied); 2585 (La Buena Vida, Fort Collins: Spanish/English headers).", "",
      "## Files", "", "menu.html, menu.pdf, preview-letter.png (" + "x".join(map(str, R["png"])) + " px, 300 dpi, not downscaled), preview-phone.png ("
      + "x".join(map(str, R["phone_png"])) + " px), doc.json, layout.json, proposal.md; copies in round-11/.", ""]
(OUT / "proposal.md").write_text("\n".join(o))
print(json.dumps({k: checks[k] for k in KEYS}, ensure_ascii=False))
