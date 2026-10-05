"""
Step 2 of 2: trace every Libbey glass from its photo, calibrate wall thickness per family, and export the DB load file.

  python3 trace_and_calibrate.py      # needs ./libbey_data/ from pull_libbey_catalogue.py (~10 min on 4 CPUs)

What it does
1. For each family, sweeps an effective wall thickness (0.6-4.4 mm) and keeps the value whose MEDIAN
   capacity error is closest to 0. This is a calibration factor, not a measured thickness.
2. Traces every glass with its family's calibrated wall (trace_glass.trace). Pass = |volume error| <= 7%
   and photo aspect vs published diameter within 10%.
3. Writes the outputs below. Mugs (handles) and 'other_cocktail' are skipped.

Outputs (in ./libbey_data/):
  wall_calibration.json              {family: {wall_mm, median_err_pct, n}}
  libbey_traced_all.json             every trace, including failures and their errors
  libbey_glassware_load.json         verified CORE cocktail glasses, colour variants (sku with '/') collapsed,
                                     shaped for phg.glassware -> load via phg-cocktail-studio glassware_upsert
                                     (write inner_profile only; the DB trigger computes fill_curve)
"""
import collections, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trace_glass
from trace_glass import trace, WALL, STEM

D = "libbey_data"
CORE = {"coupe", "nick_and_nora", "martini", "rocks", "highball", "collins", "pint", "flute", "margarita", "hurricane",
        "snifter", "cordial", "shot", "specialty"}
DB_FAMILY = {"rocks": "double_rocks", "margarita": "other", "cordial": "other", "specialty": "other"}   # phg.glassware family check
STEMF = {"coupe", "nick_and_nora", "martini", "flute", "margarita", "hurricane", "snifter", "cordial"}

def img(r): return f"{D}/img/{(r['sku'] or 'x').replace('/', '_')}.jpg"

def main():
    rows = json.load(open(f"{D}/rows.json")); items = []
    for r in rows:
        f = r["phg_family"]
        if not f or f in ("other_cocktail", "mug") or not (r["capacity_ml"] and r["height_mm"] and r["max_diameter_mm"]) or not os.path.exists(img(r)):
            continue
        tf = f if f in WALL else "highball"
        if f in STEM and "stemless" in r["name"].lower(): tf = "highball"
        items.append((r, tf))
    fams = collections.defaultdict(list)
    for r, tf in items: fams[tf].append(r)

    calib = {}
    for tf, rs in fams.items():
        best = None
        for w in [x / 10 for x in range(6, 46, 2)]:
            trace_glass.WALL[tf] = w; errs = []
            for r in rs:
                try: errs.append(trace(img(r), r["height_mm"], r["max_diameter_mm"], r["capacity_ml"], tf)["capacity_error_pct"])
                except Exception: pass
            med = statistics.median(errs) if errs else 99
            if best is None or abs(med) < abs(best[1]): best = (w, med)
        calib[tf] = dict(wall_mm=best[0], median_err_pct=round(best[1], 1), n=len(rs)); trace_glass.WALL[tf] = best[0]
        print(tf, calib[tf], flush=True)
    json.dump(calib, open(f"{D}/wall_calibration.json", "w"), indent=1)

    out = []
    for r, tf in items:
        try: out.append({**r, "trace_family": tf, **trace(img(r), r["height_mm"], r["max_diameter_mm"], r["capacity_ml"], tf)})
        except Exception as e: out.append({**r, "trace_family": tf, "trace_error": str(e)[:200], "status": "unverified"})
    json.dump(out, open(f"{D}/libbey_traced_all.json", "w"))
    print("traced", len(out), collections.Counter(t["status"] for t in out))

    load = []
    for t in out:
        if not (t["status"] == "spec_sheet" and t["phg_family"] in CORE and "/" not in (t["sku"] or "")): continue
        p = t["inner_profile"]; step = max(1, len(p) // 14); thin = [p[0]] + p[1:-1][::step] + [p[-1]]
        fam = t["phg_family"]; dbfam = DB_FAMILY.get(fam, fam)
        if fam == "rocks" and t["capacity_ml"] < 300: dbfam = "rocks"
        load.append(dict(
            glass_key=f"libbey_{t['sku'].lower()}", name=f"Libbey {t['name']} {t['capacity_oz']:g} oz", family=dbfam,
            manufacturer=t.get("brand") or "Libbey", manufacturer_sku=t["sku"], capacity_ml=t["capacity_ml"], height_mm=t["height_mm"],
            max_diameter_mm=t["max_diameter_mm"], rim_diameter_mm=round(2 * (p[-1]["r_mm"] + t["wall_mm"]), 1),
            wall_thickness_mm=t["wall_mm"], base_thickness_mm=t["base_or_stem_mm"],
            inner_profile=[{"r_mm": round(x["r_mm"], 1), "h_mm": round(x["h_mm"], 1)} for x in thin],
            source_url=t["url"], verification_status="spec_sheet",
            notes=(f"Traced from Libbey product photo; scaled by published height {t['height_mm']} mm. Traced volume {t['traced_volume_ml']} ml vs "
                   f"published {t['capacity_ml']} ml ({t['capacity_error_pct']:+}%). Photo width vs published max diameter {t['aspect_check_pct']:+}%. "
                   f"{'Bowl bottom' if fam in STEMF else 'Base top'} = observed photo edge selected by capacity ({t['base_or_stem_mm']} mm). "
                   f"Wall {t['wall_mm']} mm is an effective family calibration, not a measured thickness. Libbey type: {t['libbey_type']}.")))
    json.dump(load, open(f"{D}/libbey_glassware_load.json", "w"))
    print("load file:", len(load), "glasses ->", f"{D}/libbey_glassware_load.json")

if __name__ == "__main__":
    main()
