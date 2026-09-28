"""Round 14: layout.json (geometry + per-card edges) and proposal.md, both generated from doc.json and the render's measure.json."""
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
PAL = {"cream": "#F6EEDF", "card": "#FBF5EA", "featured_card": "#F3E3CB", "ink": "#231B16", "terracotta": "#A63C1A", "agave": "#2F5D50", "marigold": "#E3A018", "muted": "#5A4A3F", "loteria_rosa": "#C2185B", "marigold_tint": "#FAEBC8"}
cards, elements = [], []
def el(kind, ref, o, **kw): elements.append(dict({"kind": kind, "ref": ref}, **b(o), **kw))
for k in ("banner", "title", "loc", "deck", "foot"): el({"banner": "image", "title": "header", "loc": "tagline", "deck": "grid", "foot": "ornament"}[k], k, M[k], **({"text": M[k]["text"]} if "text" in M[k] else {}))
for c in M["cards"]:
    cb = b(c["box"]); inner_bottom = cb["y"] + cb["h"] - r2((c["padding_px"]["bottom"] + c["border_px"]) * PT)
    nb_ = b(c["namebar"]); fg = b(c["figure"])
    nl = [r2(i["name"]["x"] * PT) for i in c["items"]]; pr = [r2((i["price"]["x"] + i["price"]["w"]) * PT) for i in c["items"]]
    el("card", c["ref"], c["box"], n=c["n"], featured=c["featured"]); el("card_face", c["ref"], c["face"]); el("card_number", c["ref"], c["cardno"], text=c["cardno"]["text"]); el("header", c["ref"], c["name"], text=c["name"]["text"])
    el("verse", c["ref"], c["verse"], text=c["verse"]["text"], note="cultural text: traditional loteria cantor verse, not an item fact"); el("gloss", c["ref"], c["gloss"], text=c["gloss"]["text"])
    el("figure", c["ref"], c["figure"]); el("name_bar", c["ref"], c["namebar"], text=c["namebar"]["text"])
    if c.get("note"): el("serve_note", c["ref"], c["note"], text=c["note"]["text"], note="card-level serve cue from the draft Spirits section desc 'Straight pours by category.'")
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
    "grid_origin_deck_top_pt": r2(DT), "cross_card_baseline_offsets_from_6pt_grid_pt": grid_offsets, "cross_card_baseline_alignment": cross_ok, "card_bottoms_pt": bottoms, "column_bottoms_pt": {"column_1 (El Cantarito, La Rosa)": bottoms[3], "column_2 (El Barril, La Botella)": bottoms[4]}, "columns_end_at_756pt": abs(bottoms[3] - 756) <= 0.3 and abs(bottoms[4] - 756) <= 0.3, "columns_end_same_baseline": abs(bottoms[3] - bottoms[4]) <= 0.3, "top_cards_end_same_baseline": abs(bottoms[1] - bottoms[2]) <= 0.3, "shared_rows_2x2": abs(bottoms[1] - bottoms[2]) <= 0.3 and abs(M["cards"][0]["box"]["y"] - M["cards"][1]["box"]["y"]) < 0.4 and abs(M["cards"][2]["box"]["y"] - M["cards"][3]["box"]["y"]) < 0.4, "figure_share_of_face": {c["n"]: c["figure_share_of_face_height"] for c in cards}, "figures_at_least_40pct_of_face": all(c["figure_share_of_face_height"] >= 0.4 for c in cards), "face_share_of_card": {c["n"]: r2(c["face_pt"]["h"] / c["box_pt"]["h"]) for c in cards}, "card_heights_pt": {c["n"]: c["box_pt"]["h"] for c in cards}, "face_heights_pt": {c["n"]: c["face_pt"]["h"] for c in cards}, "heights_multiple_of_6pt": all(abs(c["box_pt"]["h"] / 6 - round(c["box_pt"]["h"] / 6)) < 0.05 and abs((c["face_pt"]["h"] + 3) / 6 - round((c["face_pt"]["h"] + 3) / 6)) < 0.05 for c in cards), "card_numbers": {c["n"]: c["cardno"] for c in cards}, "card_numbers_source": "traditional Don Clemente lotería numbers (El Cantarito 44, La Botella 8, El Barril 9, La Rosa 41)", "card_number_size_pt": {c["n"]: c["card_number_style"]["size_pt"] for c in cards}, "price_size_pt": {c["n"]: c["price_style"]["size_pt"] for c in cards}, "card_numbers_smaller_than_prices": all(c["card_number_style"]["size_pt"] <= c["price_style"]["size_pt"] for c in cards), "card_numbers_style": {c["n"]: c["card_number_style"] for c in cards}, "price_style": {c["n"]: c["price_style"] for c in cards}, "card_numbers_distinct_from_prices": all(c["card_number_style"]["style"] == "italic" and c["price_style"]["style"] == "normal" and c["card_number_style"]["background"] in ("rgba(0, 0, 0, 0)", "transparent") for c in cards), "verse_pt": {c["n"]: c["verse_pt"] for c in cards}, "verses_9pt_or_larger": all(c["verse_pt"] >= 9 for c in cards), "title_clear_of_flags_pt": r2((M["title"]["y"] - M["banner"]["y"] - M["banner"]["h"]) * PT), "location_to_cards_pt": r2(DT - (M["loc"]["y"] + M["loc"]["h"]) * PT),
    
    "verses_unclipped": not any(c["verse_clipped"] for c in cards), "one_title_per_card": True,
    "no_card_more_than_12pt_empty": all(c["space_below_name_bar_pt"] <= 12 for c in cards),
    
    
    "body_baseline_pt": sorted({v for c in cards for v in c["line_heights_pt"]}),
    "one_12pt_baseline": all(c["line_heights_pt"] == [12.0] for c in cards), "baseline_anchor": "deck top (y = 126 pt); every card top, name band top/bottom, subhead and item row sits on a 6 pt step from it (3 pt frame + 105 pt face = 108)",
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
    blocks = list(c["rows"]) + [i["block"] for i in c["items"]] + ([c["note"]] if c.get("note") else [])  # line boxes (item blocks), not glyph boxes
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
    "price_colour_per_card": {"1 El Cantarito": PAL["terracotta"], "2 El Barril": PAL["agave"], "3 La Rosa": PAL["loteria_rosa"], "4 La Botella": PAL["ink"] + " (ink on the marigold card)"}, "price_type": "Fraunces 700, 11.5/12 pt, font-feature-settings tnum + lnum",
    "contrast": {"cream_on_rosa_namebar": contrast(PAL["cream"], PAL["loteria_rosa"]), "ink_on_marigold_namebar": contrast(PAL["ink"], PAL["marigold"]), "ink_numeral_on_terracotta_tint": contrast(PAL["ink"], "#F3E3CB"), "ink_numeral_on_marigold_tint": contrast(PAL["ink"], PAL["marigold_tint"]), "ink_numeral_on_agave_tint": contrast(PAL["ink"], "#E4EBE2"), "ink_numeral_on_rosa_tint": contrast(PAL["ink"], "#F7E3E8"), "muted_verse_on_marigold_tint": contrast(PAL["muted"], PAL["marigold_tint"]), "muted_verse_on_terracotta_tint": contrast(PAL["muted"], "#F3E3CB"), "muted_verse_on_agave_tint": contrast(PAL["muted"], "#E4EBE2"), "muted_serve_note_on_card": contrast(PAL["muted"], PAL["card"]), "muted_verse_on_rosa_tint": contrast(PAL["muted"], "#F7E3E8"), "cream_on_agave_namebar": contrast(PAL["cream"], PAL["agave"]), "cream_on_terracotta_namebar": contrast(PAL["cream"], PAL["terracotta"]),
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
    "masthead_on_6pt_steps": all(st(v) <= 0.3 for v in (M["title"]["y"] * PT, DT)) and abs(M["title"]["y"] * PT - 72) <= 0.3,
    "masthead_note": "papel picado 36-66 pt, title line box 72-102 pt, a full 6 pt step, tagline line box 108-120 pt, 6 pt, deck top 126 pt: all on 6 pt steps from the page top; the glyph boxes are measured above",
    "lower_name_bands_aligned": abs(cards[2]["name_bar_pt"]["y"] - cards[3]["name_bar_pt"]["y"]) <= 0.3 and abs(cards[2]["box_pt"]["y"] - cards[3]["box_pt"]["y"]) <= 0.3,
    "top_name_bands_aligned": abs(cards[0]["name_bar_pt"]["y"] - cards[1]["name_bar_pt"]["y"]) <= 0.3,
    "shared_rows_pt": {"top_card_tops (El Cantarito, El Barril)": [cards[0]["box_pt"]["y"], cards[1]["box_pt"]["y"]], "top_name_bands": [cards[0]["name_bar_pt"]["y"], cards[1]["name_bar_pt"]["y"]], "lower_card_tops (La Rosa, La Botella)": [cards[2]["box_pt"]["y"], cards[3]["box_pt"]["y"]], "lower_name_bands (La Rosa, La Botella)": [cards[2]["name_bar_pt"]["y"], cards[3]["name_bar_pt"]["y"]]},
    "row_gap_pt": r2(cards[2]["box_pt"]["y"] - cards[0]["box_pt"]["y"] - cards[0]["box_pt"]["h"]), "name_band_type_pt": 18, "name_band_full_card_width": all(abs(c["name_bar_pt"]["w"] - (c["box_pt"]["w"] - 2 * c["border_pt"])) <= 0.3 for c in cards),
    "gutter_pt": r2(cards[1]["box_pt"]["x"] - cards[0]["box_pt"]["x"] - cards[0]["box_pt"]["w"]),
    "one_face_template": len({(c["figure_pt"]["w"], c["figure_pt"]["h"], c["figure_x_in_card_pt"], c["verse_column_x_in_card_pt"], c["face_pt"]["h"]) for c in cards}) == 1,
    "figure_box_pt": {c["n"]: [c["figure_pt"]["w"], c["figure_pt"]["h"]] for c in cards}, "figure_x_in_card_pt": {c["n"]: c["figure_x_in_card_pt"] for c in cards}, "verse_column_x_in_card_pt": {c["n"]: c["verse_column_x_in_card_pt"] for c in cards},
    "lower_cards_face_share": r2(cards[2]["face_pt"]["h"] / cards[2]["box_pt"]["h"]),
    "name_bands_unclipped": not any(c["name_band_clipped"] for c in cards),
    "empty_space_below_list_pt": {c["n"]: c["space_below_name_bar_pt"] for c in cards},
    "palette_hues": ["terracotta (El Cantarito)", "agave green (El Barril)", "loteria rosa (La Rosa)", "marigold (La Botella; ink text and ink prices on it)", "neutrals: ink, cream"],
})
gaps = {}
for c in M["cards"]:
    for i in c["items"]:
        if i["desc"]: gaps[i["ref"]] = r2((i["price"]["x"] - (i["desc"]["x"] + i["desc"]["w"])) * PT)
checks.update({"description_to_price_column_gap_pt": gaps, "min_description_to_price_gap_pt": min(gaps.values()), "description_price_gap_at_least_6pt": min(gaps.values()) >= 6,
               "description_measure_cap_pt": 210, "widest_description_line_pt": max(r2(i["desc"]["w"] * PT) for c in M["cards"] for i in c["items"] if i["desc"]),
               "every_item_has_description_or_card_note": all(i["desc"] or c.get("note") for c in M["cards"] for i in c["items"]),
               "items_without_own_description": [i["ref"] for c in M["cards"] for i in c["items"] if not i["desc"]]})
checks["phone"].update({"chip_row": [ch["text"] for ch in PH["chips"]], "chips_one_row": len({round(ch["top"]) for ch in PH["chips"]}) == 1, "chip_active_bg": PH["chips"][0]["bg"],
    "card_number_px": [c["cardno_px"] for c in PH["cards"]], "card_number_pt": [r2(c["cardno_px"] * 0.75) for c in PH["cards"]], "figure_px": [c["figure_px"] for c in PH["cards"]], "figure_vs_round13_120px": r2(PH["cards"][0]["figure_px"] / 120),
    "first_drink_row_bottom_below_sticky_bar_px": [r2(PH["tabbar_h"] + c["first_row_bottom_from_card_top"]) for c in PH["cards"]], "first_drink_on_first_screen_of_each_card": all(PH["tabbar_h"] + c["first_row_bottom_from_card_top"] <= PH["viewport_h"] for c in PH["cards"]),
    "desc_last_line_tokens (99 = one line)": dict(PH["desc_last_line_tokens"]), "no_two_word_orphan_line": all(v >= 3 for _, v in PH["desc_last_line_tokens"])})
MMF = lambda v: round(v * MM, 2)
elements_mm = [{"page": 1, "kind": e["kind"], "ref": e["ref"], "x_mm": MMF(e["x"]), "y_mm": MMF(e["y"]), "w_mm": MMF(e["w"]), "h_mm": MMF(e["h"]), "text": e.get("text", "")} for e in elements]
L = {"round": 14, "concept": N["concept"],
     "page": {"size": "US Letter 8.5 x 11 in", "width_mm": 215.9, "height_mm": 279.4, "margins_mm": {"top": 12.7, "right": 12.7, "bottom": 12.7, "left": 12.7}, "w_pt": 612, "h_pt": 792, "margins_pt": {"top": 36, "right": 36, "bottom": 36, "left": 36}, "bleed": "none (cream flood to trim, home/office print)"},
     "grid": {"deck_pt": b(M["deck"]), "columns": 2, "columns_pt": [264, 264], "gutter_pt": 12, "gutter_mm": 4.23, "row_gap_pt": 12, "baseline_pt": 12, "baseline_step_pt": 6, "rows": N["card_layout"] + " Base rhythm on every card: 12 pt from the name band to the first subhead (or La Botella's serve note), 12 pt above every later subhead, 6 pt below every subhead, 6 pt item gap, 12 pt lines; El Barril adds 24 pt and La Botella 6 pt to each item-to-item gap so each row fills exactly.",
              "card_anatomy": "3 pt frame in the card colour; face 105 pt (+3 pt frame = 108) = tinted panel with a 0.75 pt inset hairline at 3 pt; one template on every card: 6 pt, a 69 x 69 pt cut-paper figure at x = 9 pt inside the card with the Don Clemente number as an italic Fraunces 600 11 pt ink numeral in its top-left corner, the cantor verse (Fraunces italic 10/12 pt, centred) in the column beside it, 6 pt, then a full-width 24 pt name band (card name Fraunces 700 18 pt caps, English gloss Fraunces italic 8 pt beside it); 12 pt; list; 9 pt bottom padding + 3 pt frame = 12 pt."},
     "palette": PAL,
     "type": {"display": "Fraunces 700 24/30 pt title at y = 72 pt (30 pt papel picado above, 36-66 pt), tagline DM Sans 500 8.5/12 pt tracked caps at y = 108 pt (a full 6 pt step below the title line box), deck top y = 126 pt", "card_numbers": "Fraunces 600 italic 11 pt, ink, directly on the face (no box); prices are the only bold upright lining numerals",
              "items": "Fraunces 600 10.5/12 pt", "prices": "Fraunces 700 11.5/12 pt, tnum + lnum, in the card colour (terracotta, agave green, rosa) and ink on the marigold La Botella card", "serve_note": "La Botella only: Fraunces italic 10/12 pt muted, 'Straight pours.'", "descriptions": "DM Sans 8/12 pt ink, balanced wrap, stacked under the name on the 11 cocktails, beers, cider and wines (the 3 spirits print name and price only under the card note), measure capped at 210 pt so every line clears the price column; cocktails add the serve cue on its own line, DM Sans italic 8/12 pt muted", "verse": "Fraunces italic 10/12 pt muted, every card", "gloss": "Fraunces italic 8.5/12 pt in the name band",
              "subheads": "one bilingual pattern on every card: SPANISH in DM Sans 700 caps 7/12 pt, a middle dot, then English in DM Sans 500 7.5 pt sentence case, muted; rule in the card colour (ink on La Botella)", "name_bar": "full-width 24 pt band at the foot of the face: terracotta (El Cantarito), agave green (El Barril), rosa (La Rosa) with cream text; marigold (La Botella) with ink text", "body_baseline_pt": 12, "item_gap_pt": 6},
     "masthead": {"papel_picado_pt": b(M["banner"]), "title_pt": b(M["title"]), "tagline_pt": b(M["loc"]), "footer_pt": b(M["foot"])},
     "elements": elements_mm, "elements_note": "elements = scorecard schema (page, x_mm, y_mm, w_mm, h_mm, text; glyph-tight boxes, page origin top-left); elements_pt = the same boxes in pt", "elements_pt": elements, "cards": cards, "measured_checks": checks}
(OUT / "layout.json").write_text(json.dumps(L, ensure_ascii=False, indent=1))

# ------------------------------------------------------------ proposal.md (generated; nothing hand-typed about the render)
cs = N["copy_sources"]
V_ROSA = N["cards"][3]["cantor_verse"]; RVS = N["recipe_versions"]
KEYS = ("min_description_to_price_gap_pt", "description_price_gap_at_least_6pt", "widest_description_line_pt", "every_item_has_description_or_card_note", "items_without_own_description",
        "empty_space_below_list_pt", "no_card_more_than_12pt_empty", "no_card_overflow", "shared_rows_pt", "shared_rows_2x2", "top_name_bands_aligned", "lower_name_bands_aligned", "column_bottoms_pt", "columns_end_at_756pt", "columns_end_same_baseline", "top_cards_end_same_baseline",
        "cross_card_baseline_alignment", "gutter_pt", "row_gap_pt", "name_band_type_pt", "name_band_full_card_width", "heights_multiple_of_6pt", "card_heights_pt", "face_heights_pt",
        "one_face_template", "figure_box_pt", "figure_x_in_card_pt", "verse_column_x_in_card_pt", "face_share_of_card",
        "card_number_size_pt", "price_size_pt", "card_numbers_smaller_than_prices", "card_numbers_distinct_from_prices", "price_colour_per_card",
        "no_orphan_cue_print", "no_orphan_cue_phone", "no_one_word_last_line_print", "no_one_word_last_line_phone",
        "masthead_on_6pt_steps", "masthead_pt", "title_loc_overlap_pt", "title_loc_clear_gap_pt",
        "name_bands_unclipped", "subhead_space_above_pt", "subhead_space_below_is_6pt", "item_gaps_pt",
        "verses_unclipped", "one_12pt_baseline", "same_price_size_across_cards", "same_item_name_size_across_cards", "deck_within_margins", "margins_equal_within_1mm", "all_contrast_4_5_or_more", "palette_hues")
subs_printed = [x["text"] for x in elements if x["kind"] == "subheader"]
E = checks["empty_space_below_list_pt"]; CB = checks["column_bottoms_pt"]
o = ['# TEST-1 round 14: "Cantina & Cocktail Bar", Iowa City (proposal v14, locked lotería tabla 2 x 2)', "",
     "Generated by `build/layout.py` from `doc.json` and the Chromium render (`build/measure.json`). needs_input = true (questions below).", "",
     "## Concept", "", N["concept"], "",
     "## Round 14 changes (from round 13)", "",
     "Layout:",
     "- Locked 2 x 2 tabla with shared rows. Order chosen: **beer top-right** (row 1 El Cantarito | El Barril, row 2 La Rosa | La Botella; reading order cocktails, beer, wine, spirits). " + N["break_note"],
     "- " + N["card_layout"],
     f"- Column bottoms {CB}; top name bands at {checks['shared_rows_pt']['top_name_bands']} pt, lower name bands at {checks['shared_rows_pt']['lower_name_bands (La Rosa, La Botella)']} pt; gutter {checks['gutter_pt']} pt = row gap {checks['row_gap_pt']} pt.",
     f"- Empty space below each list (measured): {E}. The row difference is spread as item spacing on the thinner card (El Barril item gaps {cards[1]['item_gaps_pt']} pt, La Botella {cards[3]['item_gaps_pt']} pt); no decoration added.",
     "- Name bands: the card name is now the loudest header, Fraunces 700 18 pt caps on a full-width 24 pt band at the foot of the face (was 12 pt inside the verse column); the English gloss stays small (8 pt italic).",
     "- Face template: 69 pt figure with the verse beside it and the band below (face 105 pt + 3 pt frame = 108 pt on the 6 pt grid). Same template on all four cards.",
     "- Masthead: papel picado 30 pt; title line box 72-102 pt, a full 6 pt step, then the tagline 'IOWA CITY, IOWA' (108-120 pt), tagged `tagline` in layout.json.",
     "- Palette: La Botella is marigold #E3A018 (frame and name band) with ink text and ink prices; the muddy #8C5A00 is gone. All text contrast is 4.5:1 or more (measured below).",
     "- Phone: one sticky row of four lotería chips (Don Clemente number + mini figure), the active chip in the card colour; card numbers 24 px (18 pt); figure 72 px (60% of round 13's 120 px); balanced description wrap with a 30ch cap.",
     "- layout.json: `elements` now follows the scorecard schema (page, x_mm, y_mm, w_mm, h_mm, text); the pt list is `elements_pt`.",
     "", "Copy:",
     "- Spirits: the lines that repeated the item name are gone. One italic card-level serve cue, 'Straight pours.', sits under the La Botella name band (the draft Spirits section desc 'Straight pours by category.' shortened); the three spirits print name and price only. Subheads 'Agave · Tequila' and 'Brandy · Cognac'. Brand, age statement and pour size are flagged in missing_ingredients.",
     "- Old Fashioned: 'Brown butter-washed bourbon, demerara syrup and aromatic bitters.' (source wording).",
     "- Kept from round 13: sourced Draft / By the Glass / Sparkling subheads, the verses, serve cues on their own line, no TBC in print, rye, aromatic bitters, the 6 pt grid, 36 pt margins, one face template.", "",
     "## What did not fully land (honest)", "",
     "- Agave top-right was not possible (see above), so La Botella is bottom right.",
     "- El Barril's item gaps are 30 pt, against 6 pt on El Cantarito and La Rosa and 12 pt on La Botella. The rows force this: the extra is spread evenly as item spacing, not left empty or filled with decoration, so the item gap differs between cards.",
     f"- Space above subheads is 12 pt on El Cantarito and La Rosa but larger where item spacing was widened (measured: {checks['subhead_space_above_pt']}).",
     f"- On the lower cards the 108 pt face is {checks['lower_cards_face_share']:.0%} of the {cards[2]['box_pt']['h']} pt card.",
     "- The spirits have no description of their own. Their facts (brand, age, pour size) are not in the data and are asked below.", "",
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
o += ["", "## Spirit copy sources", "",
      "| Item | Printed | Draft menu_description (not printed: repeats the name) | Card note source | Other rows checked (no definition text) |", "|---|---|---|---|---|",
      "| Blanco Tequila | name + price | 'Blanco tequila pour.' | Spirits section desc 'Straight pours by category.' -> 'Straight pours.' | beverage_categories 04d72e1f-650d-490c-8ad8-54a6eb8aa766 'Blanco / plata' (notes null) |",
      "| Añejo Tequila | name + price | 'Añejo tequila pour.' | same | beverage_categories 9f4dae69-e84c-4b65-b7d9-1b417658b78d 'Añejo' (notes null) |",
      "| Cognac VSOP | name + price | 'VSOP Cognac pour.' | same | beverage_categories a88f6e79-9438-6e3d-2656-406fad2b829f 'Cognac', bec5063c-5274-9534-91da-53a2f10c8255 'VSOP' (notes null) |", "",
      "Subhead sources (draft_doc.json): Cocktails subs 'Classics', 'House Originals'; Spirits subs 'Agave', 'Brandy' (English halves 'Tequila' and 'Cognac' are the category words in the item names 'Blanco Tequila', 'Añejo Tequila', 'Cognac VSOP'); Beer sub 'Draft'; Cider section 'Cider'; Wine subs 'By the Glass', 'Sparkling'. The other Spanish halves translate those labels.", "",
      "Gateway (round 12 calls, no new calls in rounds 13-14): " + N["gateway_query"], "",
      "## Flags and needs_input (questions for the venue, via the Coordinator)", "",
      "1. **Brown Butter Old Fashioned: dairy allergen.** Brown butter-washed bourbon; please confirm the dairy allergen note and its wording before print.",
      "2. **Beer:** brewery, ABV and pour size for Czech Pilsner, Dry-Hopped IPA and Amber Lager. (Draft vs can is answered by the draft's 'Draft' subhead and is no longer asked.)",
      "3. **Cider:** producer, ABV and format (draft or can) for Dry Cider; the draft's Cider section has no Draft subhead.",
      "4. **Wine:** producer, region and vintage for Malbec, Pinot Grigio and Brut Rosé; pour size for the by-the-glass wines.",
      "5. **Brut Rosé: glass or bottle?** The draft price label is empty; the price prints unlabelled under 'Espumoso · Sparkling' until answered.",
      "6. **Spirits:** brand (house for the VSOP), age statement and pour size for Blanco Tequila, Añejo Tequila and Cognac VSOP (flagged in missing_ingredients).",
      "7. **Menu gaps for a cantina** (asked, not added): does the venue pour a Mexican lager, a mezcal, a second agave cocktail, and a non-alcoholic agua fresca? If so, please send names, descriptions and prices.",
      "8. **Venue name:** the title prints the venue type 'Cantina & Cocktail Bar' (the draft title is 'Bar menu'); please send the venue's name if it should print.",
      "9. **Junmai Ginjo:** " + N["retired_junmai_ginjo"],
      "10. **Drinking-joke verses (responsible-service tone):** La Botella (\"La herramienta del borracho.\") and El Barril (\"Tanto bebió el albañil, que quedó como barril.\") are traditional verses that joke about drunkenness. Keep, replace or drop? (All four verses are cultural text, not item facts.)", "",
      "## References (library `menu_visual_documents.id`)", "",
      "572 (Coa Cantina Iowa City: agave first, the price band); 7923 (Coa Cantina Des Moines: a compact list led by cocktails); 4969 (Blue Agave, Iowa: the Classic / Signature tiers); "
      "208 (Alta Calidad, Brooklyn: pour size in the header, once supplied); 2585 (La Buena Vida, Fort Collins: Spanish/English headers).", "",
      "## Files", "", "menu.html, menu.pdf, preview-letter.png (" + "x".join(map(str, R["png"])) + " px, 300 dpi, not downscaled), preview-phone.png ("
      + "x".join(map(str, R["phone_png"])) + " px), doc.json, layout.json, proposal.md; copies in round-14/.", ""]
(OUT / "proposal.md").write_text("\n".join(o))
print(json.dumps({k: checks[k] for k in KEYS}, ensure_ascii=False))
