#!/usr/bin/env python3
"""
phg_bar_math.py - deterministic bar math for the Harmony Recipe Book Designer.  v0.2.0

PREVIEW / WHAT-IF TOOL. Authoritative values live in Supabase:
  costs      -> phg_recipe_cost / phg_prep_cost / phg_menu_item_cost (via phg-costing)
  balance    -> phg_mix.calc_recipe_balance
  units      -> phg.units / phg_cost_convert
Anything printed in a final book that came only from this script must be labelled
"preview" (costs) or carry its inputs (balance).

Model follows the CocktailCalc / Liquid Intelligence approach:
  spec -> pre-dilution volume, ethanol, sugar, acid -> technique dilution formula
  -> final volume, ABV, TA %, Brix -> compare with style corridor -> batch.

No network, no secrets. Python 3.9+ standard library only.

Usage:
  python3 phg_bar_math.py demo
  python3 phg_bar_math.py recipe  recipe.json      # balance + dilution + corridor check
  python3 phg_bar_math.py batch   recipe.json --servings 40 | --volume-ml 750 [--container-ml 750]
  python3 phg_bar_math.py fatwash --spirit-ml 750 --fat-g 113 [--fat-water-pct 16] [--loss-pct 8]
  python3 phg_bar_math.py acid    --juice-ml 1000 --current-ta 1.0 --target-ta 6.0 --profile lime
  python3 phg_bar_math.py cost    recipe.json     # preview cost (needs price fields)

recipe.json:
{
  "name": "Daiquiri", "technique": "shaken",           # shaken|stirred|built|carbonated|blended|none
  "dilution_pct": null,                                # optional override (% of pre-dilution volume)
  "lines": [
    {"name":"White rum","ml":60,"abv":40,"sugar_g_100ml":0,"ta_g_100ml":0,"density":0.948},
    {"name":"Lime juice","ml":22.5,"abv":0,"sugar_g_100ml":1.73,"ta_g_100ml":6.0,"density":1.023},
    {"name":"Simple 1:1 (w/w)","ml":22.5,"abv":0,"sugar_g_100ml":61.49,"ta_g_100ml":0,"density":1.2298}
  ]
}
Optional per line for cost preview: "pack_cost": 24.0, "pack_size": 1000, "pack_unit": "ml", "yield_pct": 100
  (pack_unit "floz_us" for packages labelled in US fl oz; recipe "oz" is always the 30 ml house ounce)
"""
from __future__ import annotations
import argparse, json, math, sys

# ---- units: HOUSE STANDARD oz = 30 ml (owner decision 2026-10-06) -------------
# floz_us (29.5735 ml) is ONLY for purchase package sizes printed in US fl oz (e.g. 12 fl oz can = 355 ml).
UNIT_ML = {"ml": 1.0, "l": 1000.0, "oz": 30.0, "floz_us": 29.5735295625, "tbsp": 14.78676478125,
           "tsp": 4.92892159375, "gal": 3785.411784, "bbl": 117347.765304}
UNIT_G = {"g": 1.0, "kg": 1000.0, "lb": 453.59237}

# ---- dilution (Liquid Intelligence, as implemented by CocktailCalc) ----------
# NOTE: phg_mix.techniques.tq_dilution_targets stores shaken const 0.0203 and stirred
# coefficient 1.26. 0.0203 yields ~35% shaken dilution, contradicting PHG corridor
# bp_corridor_shaken_sour (50-60%). Constants below reproduce the corridors; verify
# against the book and bench trial T6 before promoting.
def dilution_fraction(technique: str, abv_frac: float) -> float:
    a = abv_frac
    t = technique.lower()
    if t == "shaken":
        return -1.567 * a * a + 1.742 * a + 0.203
    if t == "stirred":
        return -1.21 * a * a + 1.246 * a + 0.145
    if t == "built":       # over a large cube at service; corridor note ~24%
        return 0.24
    if t == "carbonated":  # pre-diluted with cold water before carbonation; tune to 14-16% ABV
        return 0.20
    if t == "blended":     # ice is part of the recipe; dilution set by ice weight, not formula
        return 0.0
    return 0.0

# ---- style corridors (mirror phg_mix.balance_profiles, family_corridor) ------
CORRIDORS = {
    "built":      {"abv": (27, 32), "sugar_g_100ml": (7, 9),  "acid_pct": (0, 0)},
    "stirred":    {"abv": (21, 29), "sugar_g_100ml": (4, 7),  "acid_pct": (0, 0.15), "dilution": (40, 45)},
    "shaken":     {"abv": (15, 20), "sugar_g_100ml": (7, 9),  "acid_pct": (0.9, 1.2), "dilution": (50, 60)},
    "egg_white":  {"abv": (12, 15), "sugar_g_100ml": (7, 9),  "acid_pct": (0.8, 1.0)},
    "carbonated": {"abv": (14, 16), "sugar_g_100ml": (5, 8),  "acid_pct": (0.4, 0.5)},
    "blended":    {"abv": (10, 13), "sugar_g_100ml": (9, 11), "acid_pct": (0.6, 0.8)},
}

def _ml(line: dict) -> float:
    if line.get("ml") is not None:
        return float(line["ml"])
    q, u = line.get("qty"), (line.get("unit") or "").lower()
    if q is None:
        raise ValueError(f"{line.get('name')}: no ml/qty")
    if u in UNIT_ML:
        return float(q) * UNIT_ML[u]
    if u in UNIT_G and line.get("density"):
        return float(q) * UNIT_G[u] / float(line["density"])
    if u in ("dash", "drop"):
        per = line.get("ml_per_" + u)
        if per is None:
            return 0.0  # trace; reported as gap
        return float(q) * float(per)
    raise ValueError(f"{line.get('name')}: cannot convert unit '{u}'")

def analyse(recipe: dict) -> dict:
    vol = eth = sugar = acid = mass = 0.0
    gaps, rows = [], []
    for ln in recipe["lines"]:
        ml = _ml(ln)
        unit = (ln.get("unit") or "").lower()
        if unit in ("dash", "drop") and ln.get("ml_per_" + unit) is None:
            gaps.append(f"{ln['name']}: {unit} volume not standardised (treated as trace)")
        abv = ln.get("abv"); s = ln.get("sugar_g_100ml"); ta = ln.get("ta_g_100ml"); d = ln.get("density")
        for k, v in (("abv", abv), ("sugar_g_100ml", s), ("ta_g_100ml", ta), ("density", d)):
            if v is None:
                gaps.append(f"{ln['name']}: {k} MISSING")
        vol += ml
        eth += ml * (abv or 0) / 100
        sugar += ml * (s or 0) / 100
        acid += ml * (ta or 0) / 100
        mass += ml * (d or 1.0)
        rows.append({"name": ln["name"], "ml": round(ml, 2),
                     "g": round(ml * d, 1) if d else None,
                     "oz": round(ml / UNIT_ML["oz"], 3)})
    abv0 = eth / vol if vol else 0
    tech = recipe.get("technique", "none")
    dil = (recipe["dilution_pct"] / 100) if recipe.get("dilution_pct") is not None else dilution_fraction(tech, abv0)
    water = vol * dil
    fvol = vol + water
    fmass = mass + water * 0.9982
    res = {
        "name": recipe.get("name"), "technique": tech, "lines": rows,
        "pre_dilution": {"volume_ml": round(vol, 1), "abv_pct": round(abv0 * 100, 1),
                         "sugar_g": round(sugar, 2), "acid_g": round(acid, 3)},
        "dilution_pct": round(dil * 100, 1), "dilution_water_ml": round(water, 1),
        "final": {"volume_ml": round(fvol, 1),
                  "abv_pct": round(eth / fvol * 100, 1) if fvol else None,
                  "ta_pct": round(acid / fvol * 100, 2) if fvol else None,          # g/100 ml
                  "sugar_g_100ml": round(sugar / fvol * 100, 2) if fvol else None,
                  "brix_est": round(sugar / fmass * 100, 1) if fmass else None},  # approx; ethanol skews refractometer
        "gaps": gaps,
    }
    cor_key = recipe.get("corridor") or tech
    cor = CORRIDORS.get(cor_key)
    if cor:
        chk = {}
        f = res["final"]
        for key, val in (("abv", f["abv_pct"]), ("sugar_g_100ml", f["sugar_g_100ml"]), ("acid_pct", f["ta_pct"])):
            lo, hi = cor[key]
            chk[key] = {"value": val, "range": [lo, hi],
                        "status": "ok" if lo <= val <= hi else ("low" if val < lo else "high")}
        if "dilution" in cor:
            lo, hi = cor["dilution"]
            chk["dilution"] = {"value": res["dilution_pct"], "range": [lo, hi],
                               "status": "ok" if lo <= res["dilution_pct"] <= hi else "out"}
        res["corridor_check"] = {"corridor": cor_key, "checks": chk,
                                 "note": "Corridors are starting windows, not rules. Taste decides."}
    return res

def batch(recipe: dict, servings: float | None = None, volume_ml: float | None = None,
          container_ml: float | None = None, include_dilution: bool = True, overage_pct: float = 0.0) -> dict:
    a = analyse(recipe)
    per_serve_final = a["final"]["volume_ml"] if include_dilution else a["pre_dilution"]["volume_ml"]
    if servings is None and volume_ml is None:
        raise ValueError("give servings or volume_ml")
    if servings is None:
        if container_ml and abs(volume_ml - container_ml) < 1e-6:
            volume_ml = container_ml * 0.97  # "fill one bottle" -> leave headspace
        servings = volume_ml / per_serve_final
    servings *= (1 + overage_pct / 100)
    lines = []
    for ln, row in zip(recipe["lines"], a["lines"]):
        ml = row["ml"] * servings
        g = ml * ln["density"] if ln.get("density") else None
        lines.append({"name": ln["name"], "ml": round(ml, 0 if ml >= 100 else 1),
                      "g": (round(g, 1) if g is not None and g < 20 else round(g) if g is not None else None),
                      "oz": round(ml / UNIT_ML["oz"], 2)})
    if include_dilution and a["dilution_water_ml"]:
        w = a["dilution_water_ml"] * servings
        lines.append({"name": "Filtered water (dilution)", "ml": round(w), "g": round(w * 0.9982), "oz": round(w / UNIT_ML["oz"], 2)})
    total_ml = sum(l["ml"] for l in lines)
    out = {"name": recipe.get("name"), "servings": round(servings, 2), "include_dilution": include_dilution,
           "lines": lines, "total_ml_nominal": round(total_ml),
           "total_g": round(sum(l["g"] for l in lines if l["g"] is not None)),
           "final_abv_pct": a["final"]["abv_pct"] if include_dilution else a["pre_dilution"]["abv_pct"],
           "serve_ml": round(per_serve_final, 1),
           "notes": ["Batch by WEIGHT: ethanol-water mixing contracts volume (up to ~3-4%), so measured volume runs short.",
                     "Fresh citrus/dairy: do not hold in batch beyond the prep's shelf life; add at service or use acid-adjusted/stabilised preps."]}
    if container_ml:
        usable = container_ml * 0.97  # leave ~3% headspace
        out["containers"] = {"container_ml": container_ml, "fill_ml": round(usable),
                             "count": max(1, math.ceil(total_ml / usable - 0.01)), "serves_per_container": round(usable / per_serve_final, 1)}
    if include_dilution and out["final_abv_pct"] < 25 and recipe.get("technique") == "stirred":
        out["notes"].append("Below ~25% ABV a freezer-stored batch may slush at -18 C; bench test or store in fridge.")
    return out

def fatwash(spirit_ml: float, fat_g: float, fat_water_pct: float = 0.0, loss_pct: float = 8.0, spirit_abv: float = 40.0) -> dict:
    water_ml = fat_g * fat_water_pct / 100  # e.g. whole butter ~16% water; brown butter/ghee ~0
    gross = spirit_ml + water_ml
    out_ml = gross * (1 - loss_pct / 100)
    abv = spirit_ml * spirit_abv / gross
    return {"spirit_ml": spirit_ml, "fat_g": fat_g, "fat_w_v_pct": round(fat_g / spirit_ml * 100, 1),
            "fat_g_per_750ml": round(fat_g / spirit_ml * 750, 1),
            "water_from_fat_ml": round(water_ml, 1), "est_abv_pct": round(abv, 1),
            "est_yield_ml": round(out_ml), "loss_pct_assumed": loss_pct,
            "note": "Yield/loss is an ESTIMATE until recorded on the bench (weigh in, weigh out)."}

ACID_SPLITS = {"lime": {"citric": 2/3, "malic": 1/3}, "lemon": {"citric": 1.0}, "citric_only": {"citric": 1.0}}
def acid_adjust(juice_ml: float, current_ta: float, target_ta: float, profile: str = "lime", citric_form: str = "anhydrous") -> dict:
    """TA in g/100 ml (citric-equivalent working model). Returns grams to dissolve."""
    delta = target_ta - current_ta
    if delta <= 0:
        return {"add_g_total": 0, "note": "Juice already at/above target TA; do not add acid."}
    total = delta * 10 * juice_ml / 1000  # g/L * L
    split = ACID_SPLITS[profile]
    adds = {k: round(total * v, 1) for k, v in split.items()}
    if citric_form == "monohydrate" and "citric" in adds:
        adds["citric"] = round(adds["citric"] / 0.9143, 1)  # anhydrous MW 192.12 / monohydrate 210.14
    return {"juice_ml": juice_ml, "current_ta_g_100ml": current_ta, "target_ta_g_100ml": target_ta,
            "add_g": adds, "add_g_total": round(sum(adds.values()), 1), "profile": profile,
            "note": "Weigh to 0.1 g. Dissolve fully. Changes sourness, not aroma. Verify TA by titration if available."}

def cost_preview(recipe: dict) -> dict:
    rows, total, missing = [], 0.0, []
    for ln in recipe["lines"]:
        ml = _ml(ln)
        if not all(ln.get(k) is not None for k in ("pack_cost", "pack_size", "pack_unit")):
            missing.append(ln["name"]); continue
        u = ln["pack_unit"].lower()
        if u in UNIT_ML:
            pack_ml = ln["pack_size"] * UNIT_ML[u]
        elif u in UNIT_G and ln.get("density"):
            pack_ml = ln["pack_size"] * UNIT_G[u] / ln["density"]
        else:
            missing.append(ln["name"] + " (unit)"); continue
        y = (ln.get("yield_pct") or 100) / 100
        c = ln["pack_cost"] / (pack_ml * y) * ml
        total += c
        rows.append({"name": ln["name"], "ml": round(ml, 1), "cost": round(c, 4)})
    price = recipe.get("menu_price")
    out = {"PREVIEW_ONLY": "Not the cost of record. Use phg_recipe_cost for books.",
           "lines": rows, "cost_per_serve": round(total, 2), "complete": not missing, "missing": missing}
    if price:
        out["pour_cost_pct"] = round(total / price * 100, 1)
        out["gross_profit"] = round(price - total, 2)
    tgt = recipe.get("target_cogs_pct")
    if tgt:
        out["price_at_target"] = round(total / (tgt / 100), 2)
    return out

DEMO = {"name": "Daiquiri (demo)", "technique": "shaken", "menu_price": 14, "target_cogs_pct": 20, "lines": [
    {"name": "White rum", "ml": 60, "abv": 40, "sugar_g_100ml": 0, "ta_g_100ml": 0, "density": 0.948,
     "pack_cost": 22.0, "pack_size": 1000, "pack_unit": "ml"},
    {"name": "Lime juice", "ml": 22.5, "abv": 0, "sugar_g_100ml": 1.73, "ta_g_100ml": 6.0, "density": 1.023,
     "pack_cost": 1.20, "pack_size": 1, "pack_unit": "lb", "yield_pct": 40},
    {"name": "Simple 1:1 (w/w)", "ml": 22.5, "abv": 0, "sugar_g_100ml": 61.49, "ta_g_100ml": 0, "density": 1.2298,
     "pack_cost": 0.90, "pack_size": 1000, "pack_unit": "ml"}]}

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("demo")
    r = sp.add_parser("recipe"); r.add_argument("file")
    b = sp.add_parser("batch"); b.add_argument("file"); b.add_argument("--servings", type=float)
    b.add_argument("--volume-ml", type=float); b.add_argument("--container-ml", type=float)
    b.add_argument("--no-dilution", action="store_true"); b.add_argument("--overage-pct", type=float, default=0)
    f = sp.add_parser("fatwash"); f.add_argument("--spirit-ml", type=float, required=True); f.add_argument("--fat-g", type=float, required=True)
    f.add_argument("--fat-water-pct", type=float, default=0); f.add_argument("--loss-pct", type=float, default=8); f.add_argument("--spirit-abv", type=float, default=40)
    a = sp.add_parser("acid"); a.add_argument("--juice-ml", type=float, required=True); a.add_argument("--current-ta", type=float, required=True)
    a.add_argument("--target-ta", type=float, required=True); a.add_argument("--profile", default="lime", choices=list(ACID_SPLITS))
    a.add_argument("--citric-form", default="anhydrous", choices=["anhydrous", "monohydrate"])
    c = sp.add_parser("cost"); c.add_argument("file")
    x = p.parse_args(argv)
    load = lambda fn: json.load(open(fn))
    if x.cmd == "demo":
        res = {"analyse": analyse(DEMO), "batch_750": batch(DEMO, volume_ml=750, container_ml=750),
               "batch_40": batch(DEMO, servings=40, include_dilution=False),
               "fatwash_brown_butter": fatwash(750, 113), "acid_oj_to_lime": acid_adjust(1000, 1.0, 6.0, "lime"),
               "cost_preview": cost_preview(DEMO)}
    elif x.cmd == "recipe": res = analyse(load(x.file))
    elif x.cmd == "batch": res = batch(load(x.file), x.servings, x.volume_ml, x.container_ml, not x.no_dilution, x.overage_pct)
    elif x.cmd == "fatwash": res = fatwash(x.spirit_ml, x.fat_g, x.fat_water_pct, x.loss_pct, x.spirit_abv)
    elif x.cmd == "acid": res = acid_adjust(x.juice_ml, x.current_ta, x.target_ta, x.profile, x.citric_form)
    else: res = cost_preview(load(x.file))
    json.dump(res, sys.stdout, indent=2); print()

if __name__ == "__main__":
    main()
