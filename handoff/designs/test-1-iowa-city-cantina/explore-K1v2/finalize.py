"""K1v2 hard gates from _measure.json + menu-print-bleed.pdf -> gates.json (every number measured).
Also splits the phone render into full-width parts of about 4,700 px (preview-phone-1.png ...)."""
import json, pathlib, hashlib
import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
MAN_PATH = HERE.parent / "expanded-v2" / "manifest.json"
MAN = json.loads(MAN_PATH.read_text()); M = json.loads((HERE / "_measure.json").read_text())

# printed deviations the coordinator asked for (everything else must match the manifest exactly)
REGION_SUPPRESS = {"Tres Generaciones Añejo"}
BREWERY_SHORT = {"Tecate": "Cuauhtémoc Moctezuma · Tecate, B.C.", "Amber Lager": "Dos Equis Ámbar · Cuauhtémoc Moctezuma"}
RECIPE_FLAG = {"Spicy Pineapple Margarita"}
nb = lambda s: s.replace(" ", " ") if isinstance(s, str) else s
money = lambda p: str(int(round(p)))

def oak_expect(it):
    c, s = it["cls"], it["sensory"]
    if "not stated" in (it.get("oak") or ""): return None
    if c == "cognac VSOP": return "vsop:48-48"
    if s.startswith("Unaged"): return "dot:0-0"
    if c == "reposado": return "bar:2-12"
    if c == "añejo": return "bar:12-36"
    return None

man = {}
for sec in ("cocktails", "zero_proof", "beer_cider", "wine", "spirits"):
    for g, items in MAN[sec].items():
        for it in items: man[it["name"]] = (sec, g, it)
for f in MAN["flights"]: man[f["name"]] = ("flights", "Vuelos", f)

def content_check(contents):
    dom = {}
    for c in contents:
        for it in c["items"]: dom.setdefault(nb(it["name"]), []).append(it)
    errs = []
    extra, missing = sorted(set(dom) - set(man)), sorted(set(man) - set(dom))
    if extra: errs.append(f"extra {extra}")
    if missing: errs.append(f"missing {missing}")
    counts = {"prices": 0, "pours": 0, "bottle_prices": 0, "breweries": 0, "producers": 0, "flights": 0}
    for name, lst in dom.items():
        if len(lst) != 1: errs.append(f"{name} printed {len(lst)}x"); continue
        if name not in man: continue
        sec, g, it = man[name]; d = lst[0]; P = [nb(x) for x in d["prices"]]
        if d["ring"] != (it["status"] != "approved_db"): errs.append(f"{name} ring {d['ring']} vs {it['status']}")
        sens = nb(d["sensory"])
        if sens != it["sensory"]: errs.append(f"{name} sensory '{sens}'")
        if sec == "spirits":
            want = [money(it["pours"][k]) for k in MAN["spirit_pour_sizes"]["sizes"]]
            if P != want: errs.append(f"{name} pours {P} != {want}")
            if want[1] != money(it["price"]): errs.append(f"{name} 1.5 oz pour {want[1]} != price {it['price']}")
            counts["pours"] += 3
            if (d["nom"] or None) != it["nom"]: errs.append(f"{name} NOM {d['nom']}")
            reg = None if name in REGION_SUPPRESS else it["region"]
            got = nb(d["region"]).replace("· ", "", 1).strip() if d["region"] else None
            if got != reg: errs.append(f"{name} region {got} != {reg}")
            if d["oak"] != oak_expect(it): errs.append(f"{name} oak {d['oak']} != {oak_expect(it)}")
        elif sec == "wine":
            if P != [money(it["glass"]), money(it["bottle"])]: errs.append(f"{name} copa/botella {P}")
            counts["prices"] += 1; counts["bottle_prices"] += 1; counts["producers"] += 1
            if nb(d["brewery"]) != it["producer"]: errs.append(f"{name} producer '{d['brewery']}'")
            if d["brewery_ring"] != ((it.get("producer_status") or "").startswith("PROPOSED") and it["status"] == "approved_db"): errs.append(f"{name} producer ring")
        else:
            if P != [money(it["price"])]: errs.append(f"{name} price {P} != {it['price']}")
            counts["prices"] += 1
        if sec == "cocktails":
            if [nb(x) for x in d["ing_list"]] != it["ingredients"]: errs.append(f"{name} ingredients {d['ing_list']}")
            if (nb(d["garnish"]) or None) != it.get("garnish"): errs.append(f"{name} garnish {d['garnish']}")
            if d["glass"] != it["glass"]: errs.append(f"{name} glass {d['glass']}")
            if d["gar_in_ig"]: errs.append(f"{name} garnish inside ingredients")
            if not d["glyph"]: errs.append(f"{name} no glass glyph")
            if (name in RECIPE_FLAG) != any("recipe to confirm" in nb(f) for f in d["flags"]): errs.append(f"{name} recipe flag")
        if sec == "zero_proof" and not any("recipe to confirm" in nb(f) for f in d["flags"]): errs.append(f"{name} no recipe flag")
        if sec == "beer_cider":
            want = BREWERY_SHORT.get(name, it["brewery"])
            if nb(d["brewery"]) != want: errs.append(f"{name} brewery '{d['brewery']}'")
            counts["breweries"] += 1
            if d["brewery_ring"] != ((it.get("brewery_status") or "").startswith("PROPOSED") and it["status"] == "approved_db"): errs.append(f"{name} brewery ring")
        if sec == "flights":
            if [nb(x) for x in d["ing_list"]] != it["items"]: errs.append(f"{name} items {d['ing_list']}")
            if nb(d["pour"]) != it["pour"]: errs.append(f"{name} pour {d['pour']}")
            counts["flights"] += 1
    return {"items_checked": len(dom), "manifest_items": len(man), **counts, "errors": errs, "pass": not errs,
            "printed_deviations": {"Tres Generaciones Añejo region": "omitted (NOM 1102 is shared with Hornitos, region null) — coordinator",
                                   "brewery lines shortened": BREWERY_SHORT, "flags added": "recipe to confirm (zero proof, Spicy Pineapple Margarita), beer ABV to confirm (key)"}}

def price_check(contents):
    inline, spirits, wine = [], {}, []
    for c in contents:
        for it in c["items"]:
            if it["kind"] == "spirit": spirits.setdefault(it["col"], []).append(it)
            elif it["wine"]: wine.append(it)
            else: inline.append(it)
    worst = max(inline, key=lambda i: i["gap_em"])
    out = {"inline_rows": len(inline), "inline_max_gap_em": round(worst["gap_em"], 3), "inline_worst": worst["name"],
           "inline_all_same_line": all(i["same_line"] for i in inline)}
    spreads = {}
    for col, rows in spirits.items():
        for k in range(3):
            v = [r["price_right"][k] for r in rows]; spreads[f"table col {col} pour {k}"] = round(max(v) - min(v), 2)
    for k in range(2):
        v = [r["price_right"][k] for r in wine]; spreads[f"wine {'copa' if k == 0 else 'botella'}"] = round(max(v) - min(v), 2)
    out["aligned_price_columns_right_edge_spread_px"] = spreads
    out["guide"] = "every table and wine row sits on its own furrow rule, which runs through its price columns"
    out["pass"] = out["inline_all_same_line"] and worst["gap_em"] <= 1.0 and all(v <= 0.5 for v in spreads.values())
    return out

def contrast(key):
    rows = M[key]; w = min(rows, key=lambda r: r["worst_ratio"])
    return {"elements": len(rows), "min_ratio": w["worst_ratio"], "min_element": w["text"], "pass": w["worst_ratio"] >= 4.5}

def sizes(texts, letter=True):
    k = 0.75 if letter else 1.0
    m = min(texts, key=lambda t: t["size_px"])
    v = round(m["size_px"] * k, 2)
    return {"min_size": v, "unit": "pt" if letter else "css px", "element": m["text"][:40], "pass": v >= (8.5 if letter else 12)}

BANNED = ["beauty lives here too", "sip at your own risk", "plants, people, pours", "plants · people · pours", "possibilit", "adventure tastes better together",
          "every round takes you further in", "good drinks", "good people", "grows here", "brighter tomorrow", "higher vibes", "higher state"]

gates = {"manifest": "expanded-v2/manifest.json", "manifest_sha256_16": hashlib.sha256(MAN_PATH.read_bytes()).hexdigest()[:16]}
letter = [M["front_content"], M["back_content"]]
gates["content_letter"] = content_check(letter)
gates["content_phone"] = content_check([M["phone_content"]])
gates["price_proximity_letter"] = price_check(letter)
gates["price_proximity_phone"] = price_check([M["phone_content"]])
gates["contrast_worst_pixel"] = {s: contrast(f"{s}_contrast") for s in ("front", "back", "phone")}
gates["contrast_worst_pixel"]["method"] = "text-free render at 300 dpi (phone 3x); each text line box narrowed to its ink box (+2 px); every background pixel compared with the text colour"
gates["contrast_worst_pixel"]["pass"] = all(gates["contrast_worst_pixel"][s]["pass"] for s in ("front", "back", "phone"))
gates["legibility"] = {"letter_front": sizes(M["front_texts"]), "letter_back": sizes(M["back_texts"]), "phone": sizes(M["phone_texts"], False)}
gates["legibility"]["pass"] = all(v["pass"] for k, v in gates["legibility"].items() if isinstance(v, dict))
gates["text_overlap"] = {s: {"text_elements": len(M[f"{s}_texts"]), "overlapping_pairs": len(M[f"{s}_overlaps"]), "pairs": M[f"{s}_overlaps"][:20]} for s in ("front", "back", "phone")}
gates["text_overlap"]["method"] = "every leaf text element, per text line: the 1 em band centred in its line's content area x full advance width; any two different elements intersecting by > 0.6 css px both ways count"
gates["text_overlap"]["pass"] = all(not M[f"{s}_overlaps"] for s in ("front", "back", "phone"))
allt = " ".join(c["alltext"].lower() for c in letter + [M["phone_content"]])
hits = [b for b in BANNED if b in allt]
gates["no_taglines"] = {"banned_hits": hits, "non_item_strings": sorted(set(sum([c["heads"] for c in letter], []))) + ["Cantina", "& Cocktail Bar · Iowa City, Iowa",
    "key: proposed — pending approval / months in oak (class range) / unaged / beer ABV to confirm / copa · botella / NOM / 0 12 24 36 / 1 oz 1½ oz 2 oz"], "pass": not hits}
gates["ingredient_role_order_and_garnish_separate"] = {"note": "ingredients printed in exact manifest order (the manifest's role order); garnish is its own element on the serve line", "pass": gates["content_letter"]["pass"] and gates["content_phone"]["pass"]}
ink = {"front": M["front_ink_margins_pt"], "back": M["back_ink_margins_pt"]}
mn = min(min(v.values()) for v in ink.values())
gates["safe_area"] = {"text_ink_margins_pt": ink, "min_pt": mn, "required_pt": 36, "pass": mn >= 36,
                      "note": "text ink from the difference between the full and text-free renders; hairline proposal rings and glass glyphs are non-text marks that hang in the gutter/margin"}
try:
    import pymupdf as fitz
    doc = fitz.open(HERE / "menu-print-bleed.pdf")
    pages = [{"w_pt": round(p.rect.width, 2), "h_pt": round(p.rect.height, 2)} for p in doc]
    bl = []
    for i, p in enumerate(doc):
        a = np.frombuffer((pix := p.get_pixmap(dpi=72, clip=fitz.Rect(18, 18, 648, 828))).samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3]
        bl.append({"page": i + 1, "top_bleed_nonwhite": round(float((a[1:8, 20:600].min(-1) < 245).mean()), 3), "left_bleed_nonwhite": round(float((a[20:780, 1:8].min(-1) < 245).mean()), 3)})
    gates["bleed_pdf"] = {"file": "menu-print-bleed.pdf", "pages": pages, "sheet": "666 x 846 pt = 612 x 792 trim + 2 x (9 pt = 3.175 mm bleed + 18 pt slug), crop marks", "bleed": bl,
                          "pass": len(pages) == 2 and all(abs(p["w_pt"] - 666) < .5 and abs(p["h_pt"] - 846) < .5 for p in pages) and all(b["top_bleed_nonwhite"] > .95 and b["left_bleed_nonwhite"] > .95 for b in bl)}
except Exception as e:
    gates["bleed_pdf"] = {"error": repr(e), "pass": False}
# phone parts
im = Image.open(HERE / "preview-phone.png"); H = im.size[1]; n = -(-H // 4700); h = -(-H // n)
for old in HERE.glob("preview-phone-*.png"): old.unlink()
parts = []
for i in range(n):
    fn = f"preview-phone-{i + 1}.png"; im.crop((0, i * h, im.size[0], min(H, (i + 1) * h))).save(HERE / fn); parts.append([fn, im.size[0], min(H, (i + 1) * h) - i * h])
gates["formats"] = {"front_png": M["front_png"], "back_png": M["back_png"], "phone_png": M["phone_png"], "phone_parts": parts,
                    "phone_scroll_width_css": M["phone_scroll_width"], "no_horizontal_scroll": M["phone_scroll_width"] <= 390, "fonts_loaded": sorted(set(M["fonts_loaded"]))}
gates["all_hard_gates_pass"] = all(v["pass"] for v in gates.values() if isinstance(v, dict) and "pass" in v)
(HERE / "gates.json").write_text(json.dumps(gates, ensure_ascii=False, indent=1))
print(json.dumps({k: v.get("pass") for k, v in gates.items() if isinstance(v, dict) and "pass" in v}, ensure_ascii=False), "ALL", gates["all_hard_gates_pass"])
for k in ("content_letter", "content_phone"): print(k, {x: gates[k][x] for x in ("items_checked", "prices", "pours", "bottle_prices", "breweries", "producers", "flights")}, gates[k]["errors"][:8])
print(gates["price_proximity_letter"]); print(gates["price_proximity_phone"]["inline_max_gap_em"])
print({s: gates["contrast_worst_pixel"][s]["min_ratio"] for s in ("front", "back", "phone")}, {k: v["min_size"] for k, v in gates["legibility"].items() if isinstance(v, dict)})
print({s: gates["text_overlap"][s]["overlapping_pairs"] for s in ("front", "back", "phone")}, gates["safe_area"]["text_ink_margins_pt"], gates["bleed_pdf"].get("bleed"), parts)
