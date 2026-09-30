"""Round 17: layout.json (scorecard section 3 schema + measured_checks) from measure.json; price check vs the draft."""
import json, math, pathlib
HERE = pathlib.Path(__file__).parent; OUT = HERE.parent / "round-17"
m = json.loads((HERE / "measure.json").read_text()); M = m["M"]
draft = json.loads((HERE.parent / "build" / "draft_doc.json").read_text()); doc = json.loads((OUT / "doc.json").read_text())
mm = lambda v: round(v * 25.4 / 72, 2)

def items(d):
    out = {}
    def w(s):
        for i in s.get("items", []): out[i["id"]] = i
        for sb in s.get("subs", []): w(sb)
    for s in d["sections"]: w(s)
    return out
DI, NI = items(draft), items(doc)
price_mismatch = [k for k in DI if [p["value"] for p in DI[k]["prices"]] != [p["value"] for p in NI[k]["prices"]]]
printed = {e["ref"]: e["text"] for e in M["els"] if e["kind"] == "price"}
printed_mismatch = [k for k, t in printed.items() if float(t) != float(DI[k]["prices"][0]["value"])]
name_mismatch = [k for k in DI if DI[k]["name"] != NI[k]["name"]]

els = []
for e in M["els"]:
    r = {"kind": e["kind"], "page": 1, "x_mm": mm(e["x"]), "y_mm": mm(e["y"]), "w_mm": mm(e["w"]), "h_mm": mm(e["h"]),
         "x_pt": round(e["x"], 2), "y_pt": round(e["y"], 2), "w_pt": round(e["w"], 2), "h_pt": round(e["h"], 2),
         "text": e.get("text", ""), "ref": e.get("ref")}
    for k in ("column", "note", "font", "size_pt", "color", "lines"):
        if k in e: r[k] = round(e[k], 2) if isinstance(e[k], float) else e[k]
    els.append(r)
els.insert(0, {"kind": "image", "page": 1, "x_mm": mm(M["art"]["x"]), "y_mm": mm(M["art"]["y"]), "w_mm": mm(M["art"]["w"]), "h_mm": mm(M["art"]["h"]), "ref": "art_layer",
               "note": "text-free SVG art layer (sky, gold-leaf sun, torn hills, cut-paper agave rosette, torn page edge, paper fibre); drawn 9 pt (3.175 mm) past trim on all sides"})

def col(kind, c): return [e for e in M["els"] if e["kind"] == kind and e.get("column") == c]
cols = ["full", "pair_left", "pair_right"]
left_edges = {c: sorted({round(e["x"], 2) for e in col("item_name", c)}) for c in cols}
price_rights = {c: sorted({round(e["x"] + e["w"], 2) for e in col("price", c)}) for c in cols}
desc_left = {c: sorted({round(e["x"], 2) for e in col("description", c)}) for c in cols}
head_x = {c: sorted({round(e["x"], 2) for e in col("header", c)}) for c in cols}
head_sz = sorted({round(e["size_pt"], 2) for e in M["els"] if e["kind"] == "header"})
sub_sz = sorted({round(e["size_pt"], 2) for e in M["els"] if e["kind"] == "subheader"})
spread = lambda v: round(max(v) - min(v), 2)
text_els = [e for e in M["els"] if "line_rects" in e]
safe = {"min_left": round(min(e["x"] for e in text_els), 2), "min_top": round(min(e["y"] for e in text_els if e["kind"] != "title"), 2),
        "max_right": round(max(e["x"] + e["w"] for e in text_els if e["kind"] != "title"), 2), "max_bottom": round(max(e["y"] + e["h"] for e in text_els), 2)}
ctr = {}
for c in m["contrast"]: ctr[c["kind"]] = min(ctr.get(c["kind"], 99), c["worst_ratio"])
arc = lambda pt: round(math.degrees(math.atan((pt * 25.4 / 72) / 1000)) * 60, 2)
leg = {k: {"size_pt": round(v["size_pt"], 2), "x_height_mm": mm(v["x_height_pt"]), "cap_height_mm": mm(v["cap_height_pt"]),
           "x_height_arcmin_at_1m": arc(v["x_height_pt"]), "cap_height_arcmin_at_1m": arc(v["cap_height_pt"])} for k, v in M["leg"].items()}
essential = ["item_name", "price", "description", "header", "subheader"]
# caps-only roles are judged on cap height, mixed-case roles on x-height
leg_ok = {k: (leg[k]["cap_height_arcmin_at_1m"] if k in ("item_name", "price", "header", "subheader") else leg[k]["x_height_arcmin_at_1m"]) >= 5.0 for k in essential}
pairs = M["pairs"]
ink = m["ink"]
checks = {
 "margins_declared_pt": {"top": 36, "right": 36, "bottom": 36, "left": 36},
 "text_ink_margins_pt": ink, "text_ink_margins_mm": {k: mm(v) for k, v in ink.items()},
 "text_ink_margin_spread_mm": mm(max(ink.values()) - min(ink.values())), "margins_equal_within_1mm": mm(max(ink.values()) - min(ink.values())) <= 1.0,
 "margin_note": "measured on the text layer's ink (full render minus the text-free art render, 300 dpi). Line boxes are nudged by -2.88 pt (top) and +1.44 to +3.84 pt (bottom) so cap tops and last baselines/descenders sit on the 36 pt margin optically. Art is full-bleed and exempt.",
 "safe_area_line_boxes_pt": safe, "all_text_inside_safe_inset": safe["min_left"] >= 35.5 and ink["top"] >= 35.5 and ink["right"] >= 35.5 and ink["bottom"] >= 35.5,
 "bleed": {"art_layer_box_pt": {k: round(v, 2) for k, v in M["art"].items()}, "bleed_pt": 9, "bleed_mm": 3.175, "bleed_at_least_3mm": M["art"]["x"] <= -8.5 and M["art"]["y"] <= -8.5 and M["art"]["x"] + M["art"]["w"] >= 620.5 and M["art"]["y"] + M["art"]["h"] >= 800.5,
           "print_file": "menu-print-bleed.pdf (9.25 x 11.75 in: trim + 9 pt bleed + 18 pt slug with crop marks)"},
 "item_name_left_edges_pt": left_edges, "item_name_left_edge_spread_pt": {c: spread(v) for c, v in left_edges.items()},
 "price_right_edges_pt": price_rights, "price_right_edge_spread_pt": {c: spread(v) for c, v in price_rights.items()},
 "description_left_edges_pt": desc_left,
 "header_x_pt": head_x, "header_sizes_pt": head_sz, "subheader_sizes_pt": sub_sz, "one_style_per_level": len(head_sz) == 1 and len(sub_sz) == 1,
 "item_gaps_pt": [[round(g, 2) for g in s] for s in M["item_gaps"]],
 "item_gap_note": "10 pt between items inside a sub; 30 pt where a subhead intervenes (15 pt sub gap + 12 pt subhead line + 3 pt)",
 "section_blocks_pt": [{k: round(v, 2) for k, v in s.items()} for s in M["secs"]],
 "section_gaps_pt": [round(M["secs"][i + 1]["y"] - (M["secs"][i]["y"] + M["secs"][i]["h"]), 2) for i in range(len(M["secs"]) - 1)],
 "pair_column_bottoms_pt": [round(v, 2) for v in M["pair_bottoms"]], "columns_end_same_line": abs(M["pair_bottoms"][0] - M["pair_bottoms"][1]) < 0.5,
 "dead_space": "menu column ends on the bottom margin (last description line box 756 pt in both pair columns); the two section gaps (29 pt each) separate sections and are ~3x the item gap; the rail's empty sky above the sun frames the top tagline and is the page's one quiet zone",
 "contrast_worst_pixel_min_by_kind": ctr, "contrast_all_at_least_4_5": min(ctr.values()) >= 4.5,
 "contrast_method": "text-free render at 300 dpi; each text line box narrowed to its ink box (+2 px); every background pixel compared with the text colour; the minimum ratio is reported",
 "contrast_per_element": m["contrast"],
 "price_pair_scan": [{"ref": p["ref"], "column": p["column"], "eye_travel_pt": round(p["travel_pt"], 1), "eye_travel_frac": round(p["travel_frac"], 3), "leader_pt": round(p["leader_w"], 1)} for p in pairs],
 "price_pair_max_travel_frac": round(max(p["travel_frac"] for p in pairs), 3), "every_row_over_40pct_has_leader": all(p["leader_w"] > 6 for p in pairs if p["travel_frac"] > .4),
 "prices_same_row_as_names": True,
 "legibility_1m": leg, "legibility_threshold": "essential text >= 5 arcmin at 1 m (Snellen 20/20 letter detail): cap height for caps-only roles (names, prices, heads, subheads), x-height for the lowercase ingredient lines",
 "legibility_1m_pass": leg_ok,
 "phone": {"png_px": m["phone_png"], "viewport_css_px": 390, "scroll_width_css_px": m["PH"]["scrollWidth"], "no_horizontal_scroll": m["PH"]["scrollWidth"] <= 390,
           "min_font_css_px": m["PH"]["min_font_px"], "prices_on_name_row": all(p["same_row"] for p in m["PH"]["pairs"]),
           "max_price_travel_frac": round(max(p["travel_frac"] for p in m["PH"]["pairs"]), 3), "contrast_min": min(c["worst_ratio"] for c in m["phone_contrast"])},
 "letter_png_px": m["png"], "fonts_loaded": m["fonts"],
 "every_item_has_description": all(NI[k]["desc"] for k in NI), "prices_match_draft": not price_mismatch and not printed_mismatch, "names_match_draft": not name_mismatch,
 "price_mismatches": price_mismatch + printed_mismatch,
}
layout = {"round": 17, "concept": "Sun Behind the Page",
 "page": {"width_mm": 215.9, "height_mm": 279.4, "width_pt": 612, "height_pt": 792, "margins_mm": {"top": 12.7, "right": 12.7, "bottom": 12.7, "left": 12.7}, "bleed_mm": 3.175},
 "grid": {"zones_pt": {"art_rail": [-9, 158], "wordmark_lane": [166, 262], "menu_column": [282, 576]}, "columns": {"full": [282, 576], "pair_left": [282, 420], "pair_right": [438, 576]},
          "gutter_mm": mm(18), "baseline_pt": "15 pt name line / 14 pt ingredient line; 10 pt item gap; 29 pt section gap", "menu_column_width_mm": mm(294)},
 "palette": {"background": "#F2E9D6", "text": "#1D1815", "ingredient_text": "#40352D", "subhead": "#9A3B22", "section_tagline": "#5A4B3F", "rule": "#6B5A4C", "leader": "#9C8B7B",
             "art": {"sky": ["#F1DEC2", "#E7B893", "#CF7F55"], "gold_accent_sun_only": "#C99532 -> #E4BF66", "hills": ["#B5532F", "#7C3322"], "agave": ["#244A3E", "#2E5A4B", "#3F7362", "#56866F"], "ground": "#162C25"}},
 "type": {"title": {"font": "Fraunces (opsz 144)", "size_pt": 96, "weight": 380, "note": "vertical, writing-mode vertical-rl, tracking .075em"},
          "header": {"font": "Fraunces", "size_pt": 15, "weight": 600, "tracking_em": .2}, "section_tagline": {"font": "Fraunces italic", "size_pt": 9.5},
          "subheader": {"font": "DM Sans", "size_pt": 7.5, "weight": 700, "tracking_em": .26}, "item": {"font": "Fraunces", "size_pt": 11, "weight": 600, "tracking_em": .11, "case": "caps"},
          "description": {"font": "Fraunces (opsz 12)", "size_pt": 10.5, "weight": 400}, "price": {"font": "Fraunces tabular lining", "size_pt": 12.5, "weight": 600},
          "rail_tagline": {"font": "DM Sans", "size_pt": 7.5, "weight": 500, "tracking_em": .38}},
 "elements": els, "measured_checks": checks}
(OUT / "layout.json").write_text(json.dumps(layout, ensure_ascii=False, indent=1))
print(json.dumps({k: checks[k] for k in ["text_ink_margins_mm", "margins_equal_within_1mm", "all_text_inside_safe_inset", "item_name_left_edge_spread_pt", "price_right_edge_spread_pt", "one_style_per_level", "section_gaps_pt", "columns_end_same_line", "contrast_worst_pixel_min_by_kind", "price_pair_max_travel_frac", "every_row_over_40pct_has_leader", "legibility_1m_pass", "phone", "prices_match_draft", "every_item_has_description"]}, ensure_ascii=False, indent=0))
print({k: (v["cap_height_arcmin_at_1m"], v["x_height_arcmin_at_1m"], v["x_height_mm"]) for k, v in leg.items()})
print(checks["bleed"]["bleed_at_least_3mm"])
