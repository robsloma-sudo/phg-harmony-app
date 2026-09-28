import json, pathlib
HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path("/home/user/phg-harmony-app/handoff/designs/test-1-iowa-city-cantina")
R = json.loads((HERE / "measure.json").read_text()); M = R["M"]
doc = json.loads((OUT / "doc.json").read_text())
PT = 0.75; MM = 25.4 / 72
r2 = lambda v: round(v + 0.0, 2)
def pt(b): return {k: r2(b[k] * PT) for k in ("x", "y", "w", "h")}

els = []
for e in M["elements"]:
    b = pt(e)
    d = {"kind": e["kind"], "page": 1, "column": e["column"], "x_pt": b["x"], "y_pt": b["y"], "w_pt": b["w"], "h_pt": b["h"],
         "x_mm": r2(b["x"] * MM), "y_mm": r2(b["y"] * MM), "w_mm": r2(b["w"] * MM), "h_mm": r2(b["h"] * MM), "text": e["text"]}
    if "slot" in e:
        s = pt(e["slot"]); d["slot_pt"] = {"x": s["x"], "y": s["y"], "w": s["w"], "h": s["h"]}
    if "baseline" in e: d["baseline_pt"] = r2(e["baseline"] * PT)
    if e.get("lines"): d["lines"] = e["lines"]
    for k in ("ref", "level", "note"):
        if e.get(k): d[k] = e[k]
    els.append(d)

chk = {}
spread = lambda v: r2(max(v) - min(v))
vis = [e for e in els if e["kind"] != "item_block"]
L = min(e["x_pt"] for e in vis); T = min(e["y_pt"] for e in vis)
Rr = 612 - max(e["x_pt"] + e["w_pt"] for e in vis); B = 792 - max(e["y_pt"] + e["h_pt"] for e in vis)
chk["margins_element_boxes_pt"] = {"left": r2(L), "top": r2(T), "right": r2(Rr), "bottom": r2(B), "declared": 36}
chk["margins_printed_ink_pt"] = dict(R["ink"], method="non-background pixels in the 2550x3300 preview (threshold 24/255)",
                                     max_dev_mm=r2(max(abs(v - 36) for k, v in R["ink"].items()) * MM))
for col in (1, 2):
    g = lambda kind, lvl=None: [e for e in els if e["kind"] == kind and e["column"] == col and (lvl is None or e.get("level") == lvl)]
    chk[f"col{col}"] = {
        "item_name_x_pt": sorted({e["x_pt"] for e in g("item_name")}),
        "description_x_pt": sorted({e["x_pt"] for e in g("description")}),
        "price_right_edge_pt": sorted({r2(e["x_pt"] + e["w_pt"]) for e in g("price")}),
        "price_right_spread_mm": r2(spread([e["x_pt"] + e["w_pt"] for e in g("price")]) * MM),
        "section_header_x_pt": sorted({e["x_pt"] for e in g("header", "section")}),
        "subheader_x_pt": sorted({e["x_pt"] for e in g("subheader", "sub")}),
        "kicker_right_edge_pt": sorted({r2(e["x_pt"] + e["w_pt"]) for e in els if e.get("level") == "kicker" and e["column"] == col}),
    }

# ---- vertical rhythm on slots (the layout geometry)
slots = []
for e in els:
    if e["column"] and "slot_pt" in e and e["kind"] in ("header", "subheader", "item_name", "description") :
        slots.append((e["column"], e["kind"], e.get("ref"), e["slot_pt"]["y"], e["slot_pt"]["y"] + e["slot_pt"]["h"]))
blocks = {}
for c, k, ref, y0, y1 in slots:  # merge item name+desc into one block per item
    key = (c, "item" if k in ("item_name", "description") else k, ref)
    a = blocks.get(key); blocks[key] = (min(a[0], y0), max(a[1], y1)) if a else (y0, y1)
em = next((e for e in els if e.get("note", "").startswith("column end mark")), None)
if em: blocks[(em["column"], "endmark", "endmark")] = (em["y_pt"], em["y_pt"] + em["h_pt"])
seqs = {c: sorted([(v[0], v[1], k[1], k[2]) for k, v in blocks.items() if k[0] == c]) for c in (1, 2)}
gaps = {"below_section_header": [], "above_section_header": [], "subheader_to_item": [], "items_to_next_subheader": [], "item_to_item": [], "to_endmark": []}
for c, seq in seqs.items():
    for (a0, a1, ak, ar), (b0, b1, bk, br) in zip(seq, seq[1:]):
        gap = r2(b0 - a1)
        if ak == "header": gaps["below_section_header"].append({"section": ar, "next": bk, "gap_pt": gap})
        elif bk == "header": gaps["above_section_header"].append(gap)
        elif ak == "subheader": gaps["subheader_to_item"].append(gap)
        elif bk == "subheader": gaps["items_to_next_subheader"].append(gap)
        elif bk == "endmark": gaps["to_endmark"].append(gap)
        else: gaps["item_to_item"].append(gap)
chk["vertical_gaps_pt"] = {k: (v if k == "below_section_header" else sorted(set(v))) for k, v in gaps.items()}
allvals = [x["gap_pt"] for x in gaps["below_section_header"]] + [g for k, v in gaps.items() if k != "below_section_header" for g in v]
chk["all_gaps_multiple_of_12"] = all(abs(v / 12 - round(v / 12)) < 1e-6 for v in allvals)
chk["all_slot_tops_and_heights_multiple_of_12"] = all(abs((v[0]) % 12) < 1e-6 and abs((v[1] - v[0]) % 12) < 1e-6 for v in blocks.values())

# ---- baselines on the shared 12pt grid (both columns + masthead)
bls = []
for e in els:
    if "baseline_pt" not in e: continue
    if e["kind"] == "description":
        n = e.get("lines", 1); last = e["baseline_pt"]
        bls += [("description", e["column"], r2(last - 12 * i)) for i in range(n)]
    else:
        bls.append((e.get("level") or e["kind"], e["column"], e["baseline_pt"]))
phase = sorted({r2(b % 12) for _, c, b in bls if c or _ in ("title", "location")})
chk["baseline_grid_12pt"] = {"phases_mod_12": phase, "text_lines_checked": len(bls),
                             "note": "every text baseline (title, location, headers, kickers, subheaders, names, prices, every description line, both columns) sits at y = 12k + phase"}
hb = {e["ref"]: e["baseline_pt"] for e in els if e.get("level") == "section"}
kb = {e["ref"]: e["baseline_pt"] for e in els if e.get("level") == "kicker"}
chk["kicker_vs_header_baseline_delta_pt"] = {k: r2(kb[k] - hb[k]) for k in hb}
nb = {e["ref"]: e["baseline_pt"] for e in els if e["kind"] == "item_name"}
pb = {e["ref"]: e["baseline_pt"] for e in els if e["kind"] == "price"}
chk["name_price_baseline_max_delta_pt"] = r2(max(abs(nb[k] - pb[k]) for k in nb))
# header baseline -> next baseline distance (identical whatever follows)
nxt = {}
for c, seq in seqs.items():
    for (a0, a1, ak, ar), (b0, b1, bk, br) in zip(seq, seq[1:]):
        if ak == "header":
            nb_ = next(e["baseline_pt"] for e in els if e["column"] == c and "baseline_pt" in e and e["kind"] in ("subheader", "item_name") and e["slot_pt"]["y"] == b0)
            nxt[ar] = r2(nb_ - hb[ar])
chk["section_header_baseline_to_next_baseline_pt"] = nxt
chk["column_bottoms_pt"] = [r2((c["y"] + c["h"]) * PT) for c in M["cols"]]
dv = next(e for e in els if e.get("note") == "dotted column divider")
chk["divider_pt"] = {"top": dv["y_pt"], "bottom": r2(dv["y_pt"] + dv["h_pt"]),
                     "last_content_slot_bottom": max(v[1] for k, v in blocks.items() if k[1] == "item")}
chk["footer_slot_pt"] = [r2(M["foot"]["y"] * PT), r2((M["foot"]["y"] + M["foot"]["h"]) * PT)]
chk["baseline_shifts_pt"] = R["shifts"]

def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def cr(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return round((la + 0.05) / (lb + 0.05), 2)
BG = "#F6EEDF"
chk["contrast_vs_background"] = {"text #231B16": cr("#231B16", BG), "prices/kickers/ampersand #A63C1A": cr("#A63C1A", BG),
                                  "subheaders #2F5D50": cr("#2F5D50", BG), "descriptions #5A4A3F": cr("#5A4A3F", BG),
                                  "marigold #E3A018 (non-text ornaments only)": cr("#E3A018", BG)}

items = {i["id"]: i for s in doc["sections"] for i in s["items"] + [x for sb in s["subs"] for x in sb["items"]]}
price_txt = {e["ref"]: e["text"] for e in els if e["kind"] == "price"}
desc_txt = {e["ref"]: e["text"].replace("\u00a0", " ") for e in els if e["kind"] == "description"}
chk["items_rendered"] = len(price_txt)
chk["printed_prices_match_doc"] = all(price_txt[k] == f'{items[k]["prices"][0]["value"]:g}' for k in items)
chk["printed_desc_equals_doc_desc"] = all(desc_txt[k] == items[k]["desc"] for k in items)
chk["desc_lines"] = {e["ref"]: e["lines"] for e in els if e["kind"] == "description"}
chk["png_px"] = {"letter": R["png"], "phone": R["phone_png"], "phone_scrollWidth_css": R["ph_w"]}
chk["phone_gap_below_every_section_header_px"] = {x["sec"]: x["gap_px"] for x in R["ph"]}

layout = {
    "round": 2,
    "units": "pt (1/72 in) and mm; origin top-left of the page; every number measured from the Chromium render of menu.html",
    "page": {"size": "US Letter portrait", "width_pt": 612, "height_pt": 792, "width_mm": 215.9, "height_mm": 279.4,
             "margins_pt": {"top": 36, "right": 36, "bottom": 36, "left": 36}, "margins_mm": {"top": 12.7, "right": 12.7, "bottom": 12.7, "left": 12.7},
             "bleed": "none; background is full-bleed cream, extend it 0.125in for trade printing"},
    "grid": {"columns": 2, "column_x_pt": [36, 318], "column_width_pt": 258, "column_width_mm": 91.02, "gutter_pt": 24, "gutter_mm": 8.47,
             "baseline_pt": 12, "baseline_phase_pt": phase,
             "rows_pt": {"banner": [36, 84], "title": [108, 156], "location": [156, 168], "double_rule": [180, 192],
                         "columns": [216, 720], "footer": [732, 756]},
             "note": "every slot height and every vertical gap is a multiple of 12pt; baselines are nudged within their slots so all sit 3pt above a 12pt grid line"},
    "palette": {"background": "#F6EEDF", "text": "#231B16", "accent": "#A63C1A", "secondary": "#2F5D50", "highlight": "#E3A018", "muted": "#5A4A3F",
                "flag_terracotta": "#B4441F",
                "roles": {"#A63C1A": "prices, kickers, ampersand, footer sign-off", "#2F5D50": "subheaders, rules, agave ornaments",
                          "#E3A018": "non-text ornaments only (diamonds, dotted divider, flags)", "#5A4A3F": "descriptions, location line",
                          "#B4441F": "papel picado flags (graphic only)"}},
    "type": {"title": {"font": "Fraunces", "weight": 700, "size_pt": 40, "slot_pt": 48},
             "location": {"font": "DM Sans", "weight": 500, "size_pt": 9, "slot_pt": 12, "tracking_pt": 3.2, "case": "upper"},
             "header": {"font": "Fraunces", "weight": 700, "size_pt": 24, "slot_pt": 24},
             "kicker": {"font": "DM Sans", "weight": 700, "size_pt": 8, "slot_pt": 12, "tracking_pt": 2.4, "case": "upper", "colour": "#A63C1A",
                        "align": "right edge = price column edge, baseline = header baseline"},
             "subheader": {"font": "DM Sans", "weight": 700, "size_pt": 8.5, "slot_pt": 12, "tracking_pt": 2, "case": "upper"},
             "item": {"font": "Fraunces", "weight": 600, "size_pt": 13, "slot_pt": 12},
             "description": {"font": "DM Sans", "weight": 400, "size_pt": 9, "line_pt": 12},
             "price": {"font": "Fraunces", "weight": 600, "size_pt": 13, "slot_pt": 12, "numerals": "lining, tabular",
                       "format": "whole dollars, no $ sign, no decimals, right-aligned"},
             "footer": {"font": "Fraunces Italic", "weight": 600, "size_pt": 11, "slot_pt": 24},
             "min_print_size_pt": 8},
    "spacing_pt": {"section_gap": 36, "below_section_header": 12, "subheader_to_first_item": 12, "items_to_next_subheader": 24,
                   "item_gap": 12, "desc_right_indent": 30, "columns_to_footer": 12},
    "elements": els,
    "measured_checks": chk,
}
(OUT / "layout.json").write_text(json.dumps(layout, indent=1, ensure_ascii=False))
print(json.dumps(chk, indent=1, ensure_ascii=False))
