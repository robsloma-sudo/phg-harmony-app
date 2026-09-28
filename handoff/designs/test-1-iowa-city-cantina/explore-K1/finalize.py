"""K1 hard gates from _measure.json + menu-print-bleed.pdf -> gates.json (all measured, nothing asserted by hand)."""
import json, pathlib, re, hashlib
HERE = pathlib.Path(__file__).resolve().parent
MAN_PATH = HERE.parent / "expanded-v1" / "manifest.json"
MAN = json.loads(MAN_PATH.read_text()); M = json.loads((HERE / "_measure.json").read_text())

def fmt(p): return f"{p:.2f}" if abs(p - round(p)) > 1e-9 else str(int(round(p)))
def oak_expect(it):
    c, s = it["cls"], it["sensory"]
    if s.startswith("Unaged"): return "dot:0-0"
    if c == "reposado": return "bar:2-12"
    if c == "añejo": return "bar:12-36"
    if c == "cognac VSOP": return "over:48-48"
    return "ns:0-0"

man = {}
for sec in ("cocktails", "zero_proof", "beer_cider", "wine", "spirits"):
    for g, items in MAN[sec].items():
        for it in items: man[it["name"]] = (sec, g, it)

def content_check(fmtname, contents):
    dom = {}
    for c in contents:
        for it in c["items"]:
            dom.setdefault(it["name"], []).append((it, c))
    errs = []
    extra = sorted(set(dom) - set(man)); missing = sorted(set(man) - set(dom))
    if extra: errs.append(f"extra items {extra}")
    if missing: errs.append(f"missing items {missing}")
    for name, lst in dom.items():
        if len(lst) != 1: errs.append(f"{name} printed {len(lst)}x")
        if name not in man: continue
        sec, g, it = man[name]; d, c = lst[0]
        if d["price"] != fmt(it["price"]) or float(d["price"]) != float(it["price"]): errs.append(f"{name} price {d['price']} != {it['price']}")
        want_ring = it["status"] != "approved_db"
        if d["ring"] != want_ring: errs.append(f"{name} ring {d['ring']} status {it['status']}")
        if sec == "cocktails":
            if d["ingredients"] != " · ".join(it["ingredients"]): errs.append(f"{name} ingredients '{d['ingredients']}'")
            if (d["garnish"] or None) != it.get("garnish"): errs.append(f"{name} garnish {d['garnish']}")
            if d["glass"] != it["glass"]: errs.append(f"{name} glass {d['glass']}")
            if d["gar_in_ig"]: errs.append(f"{name} garnish inside ingredient line")
            if not d["glyph"]: errs.append(f"{name} no glass glyph")
        if sec == "spirits":
            sens = d["sensory"]
            if sens is None:
                gs = [x["sensory"] for x in c["gsd"] if x["group"] == g.upper() or x["group"].lower() == g.lower()]
                sens = gs[0] if gs else None
            if sens != it["sensory"]: errs.append(f"{name} sensory '{sens}'")
            if d["cls"] != it["cls"]: errs.append(f"{name} class {d['cls']}")
            if d["nom"] != (it["nom"] or "—"): errs.append(f"{name} NOM {d['nom']}")
            if d["region"] != (it["region"] or "—"): errs.append(f"{name} region {d['region']}")
            if d["oak"] != oak_expect(it): errs.append(f"{name} oak {d['oak']}")
        elif d["sensory"] != it["sensory"]:
            errs.append(f"{name} sensory '{d['sensory']}'")
    return {"items_checked": len(dom), "manifest_items": len(man), "errors": errs, "pass": not errs}

def price_check(contents, is_phone=False):
    inline, table = [], []
    for c in contents:
        for it in c["items"]:
            (table if it["table"] else inline).append(it)
    worst = max(inline, key=lambda i: i["gap_em"])
    ok_inline = all(i["same_line"] and i["gap_em"] <= 1.0 for i in inline)
    out = {"inline_rows": len(inline), "max_gap_em": round(worst["gap_em"], 3), "worst": worst["name"], "all_same_line": all(i["same_line"] for i in inline), "pass_inline": ok_inline}
    if table:
        rights = [round(i["price_right"], 2) for i in table]
        out.update({"table_rows": len(table), "table_price_right_edge_spread_px": round(max(rights) - min(rights), 2),
                    "table_guide": "each table row sits on its own furrow rule that runs through the price column", "pass_table": max(rights) - min(rights) <= 0.5})
    out["pass"] = out["pass_inline"] and out.get("pass_table", True)
    return out

def contrast(key):
    rows = M[key]; w = min(rows, key=lambda r: r["worst_ratio"])
    return {"elements": len(rows), "min_ratio": w["worst_ratio"], "min_element": w["text"], "pass": w["worst_ratio"] >= 4.5}

def sizes(texts, letter=True):
    k = 0.75 if letter else 1.0
    m = min(texts, key=lambda t: t["size_px"])
    return {"min_size": round(m["size_px"] * k, 2), "unit": "pt" if letter else "css px", "element": m["text"][:40], "pass": round(m["size_px"] * k, 2) >= (8.5 if letter else 12)}

BANNED = ["beauty lives here too", "sip at your own risk", "plants, people, pours", "plants · people · pours", "possibilit", "adventure tastes better together",
          "every round takes you further in", "good drinks", "good people", "grows here", "brighter tomorrow", "higher vibes", "higher state"]
def banned(texts):
    t = " ".join(x.lower() for x in texts)
    return [b for b in BANNED if b in t]

def non_item_text(c):
    return sorted(set(c["heads"]))

gates = {"manifest_sha256_16": hashlib.sha256(MAN_PATH.read_bytes()).hexdigest()[:16]}
letter = [M["front_content"], M["back_content"]]
gates["content_letter"] = content_check("letter", letter)
gates["content_phone"] = content_check("phone", [M["phone_content"]])
gates["price_proximity_letter"] = price_check(letter)
gates["price_proximity_phone"] = price_check([M["phone_content"]], True)
gates["contrast_worst_pixel"] = {"front": contrast("front_contrast"), "back": contrast("back_contrast"), "phone": contrast("phone_contrast"),
    "method": "page rendered twice at 300 dpi (phone 3x): with text, and with all .tx text transparent. Each text line box is narrowed to its ink box (+2 px) from the difference image, and every background pixel inside it is compared with the text colour; the minimum ratio is reported."}
gates["legibility"] = {"letter_front": sizes(M["front_texts"]), "letter_back": sizes(M["back_texts"]), "phone": sizes(M["phone_texts"], False)}
alltext = [M["front_content"]["alltext"], M["back_content"]["alltext"], M["phone_content"]["alltext"]]
gates["no_taglines"] = {"banned_hits": banned(alltext), "non_item_strings": sorted(set(sum([non_item_text(c) for c in letter], []))) + ["Cantina", "& Cocktail Bar · Iowa City, Iowa",
    "legend: Contour strips · Iowa / Agave hileras · Jalisco / months in oak (NOM class) / unaged / age not stated / proposed — pending approval", "table heads: class / NOM / region / 0 12 24 36 mo oak / $"],
    "pass": not banned(alltext)}
gates["ingredient_role_order_and_garnish_separate"] = {"note": "ingredients printed exactly in manifest order (manifest ingredient_order = role order); garnish is its own element on the serve line with the glass, never inside the ingredient line",
    "pass": gates["content_letter"]["pass"] and gates["content_phone"]["pass"]}
ink = {"front": M["front_ink_margins_pt"], "back": M["back_ink_margins_pt"]}
fits = {s: {"menu_text_bottom_pt": round(M[f"{s}_content"]["menuBottom"] * .75, 2), "legend_top_pt": round(M[f"{s}_content"]["legTop"] * .75, 2)} for s in ("front", "back")}
gates["safe_area"] = {"text_ink_margins_pt": ink, "min_pt": min(min(v.values()) for v in ink.values()), "required_pt": 36,
    "menu_clears_legend": {s: v["menu_text_bottom_pt"] < v["legend_top_pt"] for s, v in fits.items()}, "menu_vs_legend": fits,
    "proposal_ring_left_pt": {s: round(M[f"{s}_content"]["rings_min_left"] * .75, 2) for s in ("front", "back")},
    "note": "text ink measured on the difference between the full render and the text-free render; the hairline proposal rings are non-text key marks that hang 9.5 pt left of the names (outside the text margin, 26.5 pt from trim).",
    "pass": min(min(v.values()) for v in ink.values()) >= 36 and all(v["menu_text_bottom_pt"] < v["legend_top_pt"] for v in fits.values())}
# bleed PDF
try:
    import pymupdf as fitz
    doc = fitz.open(HERE / "menu-print-bleed.pdf")
    pages = [{"w_pt": round(p.rect.width, 2), "h_pt": round(p.rect.height, 2)} for p in doc]
    bleed = []
    for i, p in enumerate(doc):
        pix = p.get_pixmap(dpi=72, clip=fitz.Rect(18, 18, 648, 828))  # trim + 9 pt bleed
        # sample the 9 pt bleed band (outside trim) at the top edge: art must be present (not white)
        import numpy as np
        a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3]
        top = a[1:8, 20:600]; left = a[20:780, 1:8]
        bleed.append({"page": i + 1, "top_bleed_nonwhite_frac": round(float((top.min(-1) < 245).mean()), 3), "left_bleed_nonwhite_frac": round(float((left.min(-1) < 245).mean()), 3),
                      "top_bleed_mean_rgb": [int(x) for x in top.reshape(-1, 3).mean(0)]})
        p.get_pixmap(dpi=40).save(str(HERE / f"_bleed-p{i + 1}.png"))
    gates["bleed_pdf"] = {"file": "menu-print-bleed.pdf", "pages": pages, "sheet": "666 x 846 pt = 612 x 792 trim + 2 x (9 pt = 3.175 mm bleed + 18 pt slug), crop marks at trim", "bleed_samples": bleed,
                          "pass": len(pages) == 2 and all(abs(p["w_pt"] - 666) < .5 and abs(p["h_pt"] - 846) < .5 for p in pages) and all(b["top_bleed_nonwhite_frac"] > .95 for b in bleed)}
except Exception as e:
    gates["bleed_pdf"] = {"error": repr(e), "pass": False}
gates["formats"] = {"front_png": M["front_png"], "back_png": M["back_png"], "phone_png": M["phone_png"], "phone_scroll_width_css": M["phone_scroll_width"], "no_horizontal_scroll": M["phone_scroll_width"] <= 390,
                    "fonts_loaded": sorted(set(M["fonts_loaded"]))}
gates["all_hard_gates_pass"] = all(v.get("pass", True) for k, v in gates.items() if isinstance(v, dict) and "pass" in v) and all(gates["contrast_worst_pixel"][s]["pass"] for s in ("front", "back", "phone")) and all(v["pass"] for v in gates["legibility"].values())
(HERE / "gates.json").write_text(json.dumps(gates, ensure_ascii=False, indent=1))
print(json.dumps({k: (v.get("pass") if isinstance(v, dict) else v) for k, v in gates.items()}, ensure_ascii=False))
for k in ("content_letter", "content_phone"): print(k, gates[k]["errors"][:6])
print(gates["price_proximity_letter"], gates["price_proximity_phone"]["max_gap_em"])
print({s: gates["contrast_worst_pixel"][s]["min_ratio"] for s in ("front", "back", "phone")}, gates["legibility"], gates["safe_area"]["text_ink_margins_pt"], gates["safe_area"]["menu_vs_legend"])
print(gates["bleed_pdf"])
