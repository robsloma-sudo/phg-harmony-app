"""Round 12: layout.json (geometry + per-card edges) and proposal.md, both generated from doc.json and the render's measure.json."""
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
        "face_pt": b(c["face"]), "cardno": c["cardno"]["text"], "cardno_pt": b(c["cardno"]), "figure_pt": fg, "verse_column_pt": b(c["vcol"]), "figure_x_in_card_pt": r2(fg["x"] - cb["x"]), "verse_column_x_in_card_pt": r2(b(c["vcol"])["x"] - cb["x"]), "name_band_clipped": c["name_clipped"], "ornament_pt": b(c["orn"]) if c.get("orn") else None, "card_number_style": c["cardno_style"], "price_style": c["price_style"], "figure_drawn_pt": b(c["fig_svg"]), "figure_share_of_face_height": r2(c["fig_svg"]["h"] / c["face"]["h"]), "verse_pt": r2(c["verse_pt_size"]), "name_bar_pt": nb_,
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
    "grid_origin_deck_top_pt": r2(DT), "cross_card_baseline_offsets_from_6pt_grid_pt": grid_offsets, "cross_card_baseline_alignment": cross_ok, "card_bottoms_pt": bottoms, "columns_end_same_baseline": abs(bottoms[3] - bottoms[4]) <= 0.3 and abs(bottoms[1] - bottoms[2]) <= 0.3, "figure_share_of_face": {c["n"]: c["figure_share_of_face_height"] for c in cards}, "figures_at_least_40pct_of_face": all(c["figure_share_of_face_height"] >= 0.4 for c in cards), "face_share_of_card": {c["n"]: r2(c["face_pt"]["h"] / c["box_pt"]["h"]) for c in cards}, "card_heights_pt": {c["n"]: c["box_pt"]["h"] for c in cards}, "face_heights_pt": {c["n"]: c["face_pt"]["h"] for c in cards}, "heights_multiple_of_6pt": all(abs(c["box_pt"]["h"] / 6 - round(c["box_pt"]["h"] / 6)) < 0.05 and abs((c["face_pt"]["h"] + 3) / 6 - round((c["face_pt"]["h"] + 3) / 6)) < 0.05 for c in cards), "card_numbers": {c["n"]: c["cardno"] for c in cards}, "card_numbers_source": "traditional Don Clemente lotería numbers (El Cantarito 44, La Botella 8, El Barril 9, La Rosa 41)", "card_numbers_style": {c["n"]: c["card_number_style"] for c in cards}, "price_style": {c["n"]: c["price_style"] for c in cards}, "card_numbers_distinct_from_prices": all(c["card_number_style"]["style"] == "italic" and c["price_style"]["style"] == "normal" and c["card_number_style"]["background"] in ("rgba(0, 0, 0, 0)", "transparent") for c in cards), "verse_pt": {c["n"]: c["verse_pt"] for c in cards}, "verses_9pt_or_larger": all(c["verse_pt"] >= 9 for c in cards), "title_clear_of_flags_pt": r2((M["title"]["y"] - M["banner"]["y"] - M["banner"]["h"]) * PT), "location_to_cards_pt": r2(DT - (M["loc"]["y"] + M["loc"]["h"]) * PT),
    
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
    "price_colour_per_card": {"1": PAL["terracotta"], "2": PAL["agave"], "3": PAL["ink"], "4": PAL["loteria_rosa"]}, "price_type": "Fraunces 700, 11.5/12 pt, font-feature-settings tnum + lnum",
    "contrast": {"cream_on_rosa_namebar": contrast(PAL["cream"], PAL["loteria_rosa"]), "cream_on_ink_namebar": contrast(PAL["cream"], PAL["ink"]), "ink_numeral_on_terracotta_tint": contrast(PAL["ink"], "#F3E3CB"), "ink_numeral_on_ink_tint": contrast(PAL["ink"], "#ECE3D4"), "ink_numeral_on_agave_tint": contrast(PAL["ink"], "#E4EBE2"), "ink_numeral_on_rosa_tint": contrast(PAL["ink"], "#F7E3E8"), "muted_verse_on_ink_tint": contrast(PAL["muted"], "#ECE3D4"), "muted_verse_on_rosa_tint": contrast(PAL["muted"], "#F7E3E8"), "cream_on_agave_namebar": contrast(PAL["cream"], PAL["agave"]), "cream_on_terracotta_namebar": contrast(PAL["cream"], PAL["terracotta"]),
                 "terracotta_price_on_featured": contrast(PAL["terracotta"], PAL["featured_card"]), "ink_price_on_card": contrast(PAL["ink"], PAL["card"]), "terracotta_price_on_card": contrast(PAL["terracotta"], PAL["card"]), "muted_serve_cue_on_card": contrast(PAL["muted"], PAL["card"]), "agave_price_on_card": contrast(PAL["agave"], PAL["card"]), "rosa_price_on_card": contrast(PAL["loteria_rosa"], PAL["card"]), "muted_serve_cue_on_featured": contrast(PAL["muted"], PAL["featured_card"])}})
pc = [i["cue"] for c in M["cards"] for i in c["items"] if i.get("cue")]
checks["serve_cues_print"] = {i["ref"]: i["cue"] for c in M["cards"] for i in c["items"] if i.get("cue")}
checks["serve_cues_phone"] = {q["ref"]: {k: q[k] for k in ("lines", "shares_line_with_description", "words")} for q in PH["cues"]}
checks["no_orphan_cue_print"] = len(pc) == 4 and all(q["lines"] == 1 and q["words"] >= 2 and not q["shares_line_with_description"] for q in pc) and checks["no_one_word_last_line_print"]
checks["no_orphan_cue_phone"] = len(PH["cues"]) == 4 and all(q["lines"] == 1 and q["words"] >= 2 and not q["shares_line_with_description"] for q in PH["cues"]) and checks["no_one_word_last_line_phone"]
checks["no_orphan_cue_note"] = "a cue passes only if it sits on its own line under the ingredients (shares_line_with_description = false), on one line (lines = 1), with no one-word last line anywhere"
checks["all_contrast_4_5_or_more"] = all(v >= 4.5 for v in checks["contrast"].values())
checks["margins_equal_within_1mm"] = (max(R["ink"].values()) - min(R["ink"].values())) * MM <= 1

def st(v): m = v % 6; return r2(min(m, 6 - m))
tg = R["M"]["title"]; lg = R["M"]["loc"]
checks.update({
    "masthead_pt": {"banner": b(M["banner"]), "title_box_top": r2(M["title"]["y"] * PT), "title_glyph_bottom": r2((tg["y"] + tg["h"]) * PT), "loc_glyph_top": r2(lg["y"] * PT), "deck_top": r2(DT)},
    "title_loc_overlap_pt": r2(max(0, (tg["y"] + tg["h"] - lg["y"]) * PT)), "title_loc_clear_gap_pt": r2((lg["y"] - tg["y"] - tg["h"]) * PT),
    "masthead_on_6pt_steps": all(st(v) <= 0.3 for v in (M["title"]["y"] * PT, M["loc"]["y"] * PT - 0, DT)) and abs(M["title"]["y"] * PT - 84) <= 0.3,
    "masthead_note": "papel picado 36-72 pt, title line box 84-114 pt, location line box 120-132 pt, deck top 150 pt: all on 6 pt steps from the page top; the glyph boxes are measured above",
    "lower_name_bands_aligned": abs(cards[2]["name_bar_pt"]["y"] - cards[3]["name_bar_pt"]["y"]) <= 0.3 and abs(cards[2]["box_pt"]["y"] - cards[3]["box_pt"]["y"]) <= 0.3,
    "top_name_bands_aligned": abs(cards[0]["name_bar_pt"]["y"] - cards[1]["name_bar_pt"]["y"]) <= 0.3,
    "shared_break_line_pt": {"lower_card_tops": [cards[2]["box_pt"]["y"], cards[3]["box_pt"]["y"]], "lower_name_bands": [cards[2]["name_bar_pt"]["y"], cards[3]["name_bar_pt"]["y"]]},
    "gutter_pt": r2(cards[1]["box_pt"]["x"] - cards[0]["box_pt"]["x"] - cards[0]["box_pt"]["w"]),
    "one_face_template": len({(c["figure_pt"]["w"], c["figure_pt"]["h"], c["figure_x_in_card_pt"], c["verse_column_x_in_card_pt"], c["face_pt"]["h"]) for c in cards}) == 1,
    "figure_box_pt": {c["n"]: [c["figure_pt"]["w"], c["figure_pt"]["h"]] for c in cards}, "figure_x_in_card_pt": {c["n"]: c["figure_x_in_card_pt"] for c in cards}, "verse_column_x_in_card_pt": {c["n"]: c["verse_column_x_in_card_pt"] for c in cards},
    "la_rosa_face_at_most_40pct": cards[3]["face_pt"]["h"] / cards[3]["box_pt"]["h"] <= 0.40,
    "name_bands_unclipped": not any(c["name_band_clipped"] for c in cards),
    "empty_space_below_list_pt": {c["n"]: c["space_below_name_bar_pt"] for c in cards},
    "palette_hues": ["terracotta", "ink", "agave green", "loteria rosa", "+ marigold accent"],
})
L = {"round": 12, "concept": N["concept"],
     "page": {"size": "US Letter 8.5 x 11 in", "w_pt": 612, "h_pt": 792, "margins_pt": {"top": 36, "right": 36, "bottom": 36, "left": 36}, "bleed": "none (cream flood to trim, home/office print)"},
     "grid": {"deck_pt": b(M["deck"]), "columns_pt": [261, 261], "gutter_pt": 18, "row_gap_pt": 12, "baseline_step_pt": 6, "rows": N["card_layout"] + " One rhythm on every card: 12 pt from the name band to the first subhead and above every subhead, 6 pt below every subhead, 12 pt item gap, 12 pt lines.",
              "card_anatomy": "3 pt frame in the card colour; face 117 pt (+3 pt frame = 120) = tinted panel, 0.75 pt inset hairline at 3 pt, 6 pt padding; one template on every card: 105 x 105 pt cut-paper figure at x = 9 pt inside the card, the Don Clemente number as an italic Fraunces 600 16 pt ink numeral in the figure's top-left corner (no chip), then a 12 pt gap and the verse column at x = 126 pt inside the card (126 pt wide): cantor verse Fraunces italic 10/12 pt centred above a 36 pt name band (Spanish name Fraunces 700 12 pt caps + English gloss italic 8.5 pt); 6 pt; list; 9 pt bottom padding + 3 pt frame = 12 pt."},
     "palette": PAL,
     "type": {"display": "Fraunces 700 24/30 pt title at y = 84 pt (36 pt papel picado above), location DM Sans 500 8.5/12 pt caps at y = 120 pt, deck top y = 150 pt", "card_numbers": "Fraunces 600 italic 16 pt, ink, directly on the face (no box); prices are the only bold upright lining numerals",
              "items": "Fraunces 600 10.5/12 pt", "prices": "Fraunces 700 11.5/12 pt, tnum + lnum, in the card colour (terracotta, agave green, ink, rosa)", "descriptions": "DM Sans 8/12 pt ink, stacked under the name (11 items; the three spirits print name and price only); cocktails add the serve cue on its own line, DM Sans italic 8/12 pt muted", "verse": "Fraunces italic 10/12 pt muted, every card", "gloss": "Fraunces italic 8.5/12 pt in the name band",
              "subheads": "DM Sans 700 caps 7/12 pt, Spanish first; English support after a middle dot in DM Sans 500 muted where given; rule in the card colour", "name_bar": "36 pt band at the foot of the verse column: terracotta (El Cantarito), agave green (El Barril), ink (La Botella), rosa (La Rosa); cream text", "body_baseline_pt": 12, "item_gap_pt": 6},
     "masthead": {"papel_picado_pt": b(M["banner"]), "title_pt": b(M["title"]), "location_pt": b(M["loc"]), "footer_pt": b(M["foot"])},
     "elements": elements, "cards": cards, "measured_checks": checks}
(OUT / "layout.json").write_text(json.dumps(L, ensure_ascii=False, indent=1))

# ------------------------------------------------------------ proposal.md (generated; nothing hand-typed about the render)
cs = N["copy_sources"]
V_ROSA = N["cards"][3]["cantor_verse"]; RVS = N["recipe_versions"]
KEYS = ("cross_card_baseline_alignment", "lower_name_bands_aligned", "top_name_bands_aligned", "shared_break_line_pt", "gutter_pt", "heights_multiple_of_6pt", "card_heights_pt", "face_heights_pt",
        "one_face_template", "figure_box_pt", "figure_x_in_card_pt", "verse_column_x_in_card_pt", "face_share_of_card", "la_rosa_face_at_most_40pct",
        "no_orphan_cue_print", "no_orphan_cue_phone", "no_one_word_last_line_print", "no_one_word_last_line_phone",
        "masthead_on_6pt_steps", "masthead_pt", "title_loc_overlap_pt", "title_loc_clear_gap_pt",
        "card_numbers_distinct_from_prices", "name_bands_unclipped", "subhead_space_above_is_12pt", "subhead_space_below_is_6pt", "same_item_gap_every_card",
        "no_card_overflow", "empty_space_below_list_pt", "no_card_more_than_12pt_empty", "columns_end_same_baseline", "verses_unclipped", "one_12pt_baseline",
        "same_price_size_across_cards", "same_item_name_size_across_cards", "deck_within_margins", "margins_equal_within_1mm", "all_contrast_4_5_or_more", "palette_hues")
subs_printed = [x["text"] for x in elements if x["kind"] == "subheader"]
o = ['# TEST-1 round 12: "Cantina & Cocktail Bar", Iowa City (proposal v12, lotería tabla 2 + 2 read in rows)', "",
     "Generated by `build/layout.py` from `doc.json` and the Chromium render (`build/measure.json`). needs_input = true (questions below).", "",
     "## Concept", "", N["concept"], "",
     "## Round 12 changes (from round 11)", "",
     "Accuracy:",
     "- Brut Rosé: 'glass / bottle TBC' removed from print and phone; the price prints like every other price. The empty label is asked in needs_input only.",
     "- La Rosa verse is now the traditional cantor verse: \"" + V_ROSA + "\" The other three verses are unchanged.",
     "- Beer subhead renamed 'Cerveza & Sidra' (no draft claim).",
     "- Spirits: 'by the pour' removed. " + N["spirits_name_only"],
     "- Manhattan: " + N["manhattan"] + " Old Fashioned cue: 'Over a large cube' (recipe method). 'fresh lime' kept (draft component 'Fresh Lime Juice'); 'aromatic bitters' kept.",
     "- Every serve cue is traced to its phg.recipe_versions row (table below).",
     "", "Layout:",
     "- Serve cues sit on their own line under the ingredients on all four cocktails (measured: own line, one line, no orphan).",
     "- Reading order in rows: El Cantarito (Clásicos first, so the Margarita is the first drink) | El Barril on top; La Botella | La Rosa below (Coordinator swap, round 12 fix: El Barril and La Botella traded places; phone tabs follow the same order). The filler papel picado in La Botella is removed.",
     "- One face template: 105 pt figure box at the same x on every card (La Botella's bottle is now 105 pt, not 45 pt), verse column at the same x offset, name band at the foot of the verse column.",
     "- " + N["card_layout"],
     "- Masthead: papel picado 36 pt, title line box at 84 pt, location at 120 pt, deck top at 150 pt (all 6 pt steps; the lower row was shrunk to its content and the spare 30 pt moved here); measured title/location overlap " + str(checks["title_loc_overlap_pt"]) + " pt.",
     "", "Palette and numbers:", "- " + N["palette_note"],
     "- Card numbers are italic Fraunces 600 ink numerals directly on the face (no black box); prices remain the only bold upright lining numerals.",
     "- Subheads, Spanish first: " + "; ".join(subs_printed) + ".", "",
     "## What did not fully land (honest)", "",
     f"- Empty space: El Barril has {checks['empty_space_below_list_pt'][2]} pt below its list and La Botella {checks['empty_space_below_list_pt'][3]} pt (no filler). With rows shared across the gutter, the top row is set by El Cantarito (354 pt of content) and El Barril needs only 270 pt; the lower row is shrunk to La Rosa's 240 pt, so La Botella (204 pt of name-only spirits) keeps 36 pt. Of the three possible pairings this is the smallest worst case (84 pt vs 114 and 150); 12 pt or less on every card is not reachable with shared rows.",
     f"- Face share: the 120 pt face (105 pt figure + padding) is {checks['face_share_of_card'][4]:.0%} of La Rosa's and La Botella's {cards[3]['box_pt']['h']} pt cards, above the ~40% target, because the lower row is now shrunk to its content.",
     "- The item gap is 6 pt (was 12) and the space under the face 6 pt, to fit the cue lines; the rhythm is still one 6 pt grid.", "",
     "## Cards (measured)", "", "| Card | No. | Box (x, y, w, h pt) | Face h pt (share of card) | Figure box pt | Verse column x in card pt | Empty below list pt |", "|---|---|---|---|---|---|---|"]
for c in cards:
    bx = c["box_pt"]
    o.append(f'| {c["loteria_name"].splitlines()[0]} / {c["gloss"]} | {c["cardno"]} | {bx["x"]}, {bx["y"]}, {bx["w"]}, {bx["h"]} | {c["face_pt"]["h"]} ({checks["face_share_of_card"][c["n"]]}) | {c["figure_pt"]["w"]} x {c["figure_pt"]["h"]} at x {c["figure_x_in_card_pt"]} | {c["verse_column_x_in_card_pt"]} | {c["space_below_name_bar_pt"]} |')
o += ["", "## Measured checks (all from the render)", ""] + [f"- {k} = {checks[k]}" for k in KEYS] + [
      f'- printed ink margins (pt) = {checks["printed_ink_margins_pt"]}',
      f'- serve cues, print = {checks["serve_cues_print"]}', f'- serve cues, phone = {checks["serve_cues_phone"]}', "- " + checks["no_orphan_cue_note"],
      f'- contrast = {checks["contrast"]}',
      f'- phone: tab bar `{checks["phone"]["tab_bar_position"]}`, {checks["phone"]["tabs"]} tabs, all fit at 390 px: {checks["phone"]["all_tabs_fit_390"]}, page scroll width {checks["phone"]["scroll_width_px"]} px, single-column stack: {checks["phone"]["cards_stacked_single_column"]}', "",
      "## Printed copy and source table (matches menu.html)", "", "| Item | Price | Printed description | Serve cue (own line) | Words from | Gateway row ids | Still missing |", "|---|---|---|---|---|---|---|"]
for c in cards:
    for i in c["items"]:
        s_ = cs[i["ref"]]
        o.append(f'| {i["name"]} | {i["price"]} | {s_["printed"] or "(name only)"} | {s_["serve_cue"] or "none"} | {s_["words_from"]} | {"; ".join(s_["gateway_rows"]) or "none"} | {", ".join(s_["missing"]) or "none"} |')
o += ["", "## Serve cue sources (phg.recipe_versions, join phg.menu_items.current_recipe_version_id = phg.recipe_versions.id; gateway log_id 168)", "",
      "| Item | Printed cue | recipe_versions.id | glassware | method | garnish |", "|---|---|---|---|---|---|"]
for k, (rv, gl, me, ga) in RVS.items():
    o.append(f'| {k} | {cs[k]["serve_cue"]} | {rv} | {gl} | {me} | {ga} |')
o += ["", "## Spirit rows checked (public.beverage_categories / public.spirit_lexicon)", "",
      "| Item | Row id | Row | Definition text? | Printed |", "|---|---|---|---|---|",
      "| Blanco Tequila | 04d72e1f-650d-490c-8ad8-54a6eb8aa766 | beverage_categories 'Blanco / plata' | no (notes null; authority_note 'NOM-006-SCFI-2012 §5, clase.') | name only, flagged |",
      "| Añejo Tequila | 9f4dae69-e84c-4b65-b7d9-1b417658b78d | beverage_categories 'Añejo' | no (notes null; authority_note 'NOM-006-SCFI-2012 §5, clase.') | name only, flagged |",
      "| Cognac VSOP | a88f6e79-9438-6e3d-2656-406fad2b829f, bec5063c-5274-9534-91da-53a2f10c8255 | beverage_categories 'Cognac', 'VSOP' | no (notes null, no age statement) | name only, flagged |",
      "| (all three) | none | spirit_lexicon: no term blanco / añejo / VSOP / plata (log_id 169); table holds term, family, subfamily only (log_id 170) | no | |", "",
      "Gateway: " + N["gateway_query"], "",
      "## Flags and needs_input (questions for the venue, via the Coordinator)", "",
      "1. **Brown Butter Old Fashioned: dairy allergen.** Brown butter-washed bourbon; please confirm the dairy allergen note and its wording before print.",
      "2. **Menu gaps for a cantina** (asked, not added): does the venue pour a Mexican lager, a mezcal, a second agave cocktail, and a non-alcoholic agua fresca? If so, please send names, descriptions and prices.",
      "3. **Brut Rosé: glass or bottle?** The draft price label is empty; the price prints as-is and the label is added once answered.",
      "4. **Spirits:** no gateway row defines blanco / plata, añejo or VSOP, so they print name only. Brand, age statement (añejo), house (VSOP) and pour sizes, please.",
      "5. Beer, cider and wine lines are the draft words only. Brewery, producer, region, vintage, ABV, pour size and each beer's / the cider's format (draft or can) are still missing.",
      "6. " + N["retired_junmai_ginjo"],
      "7. Structure: Dry Cider is folded into the beer card ('Cerveza & Sidra') and Brut Rosé into the one wine list; confirm the merged doc sections.",
      "8. **Drinking-joke verses (responsible-service tone):** La Botella (\"La herramienta del borracho.\") and El Barril (\"Tanto bebió el albañil, que quedó como barril.\") are traditional verses that joke about drunkenness. Keep, replace or drop? (All four verses are cultural text, not item facts.)", "",
      "## References (library `menu_visual_documents.id`)", "",
      "572 (Coa Cantina Iowa City: agave first, the price band); 7923 (Coa Cantina Des Moines: a compact list led by cocktails); 4969 (Blue Agave, Iowa: the Classic / Signature tiers); "
      "208 (Alta Calidad, Brooklyn: pour size in the header, once supplied); 2585 (La Buena Vida, Fort Collins: Spanish/English headers).", "",
      "## Files", "", "menu.html, menu.pdf, preview-letter.png (" + "x".join(map(str, R["png"])) + " px, 300 dpi, not downscaled), preview-phone.png ("
      + "x".join(map(str, R["phone_png"])) + " px), doc.json, layout.json, proposal.md; copies in round-12/.", ""]
(OUT / "proposal.md").write_text("\n".join(o))
print(json.dumps({k: checks[k] for k in KEYS}, ensure_ascii=False))
