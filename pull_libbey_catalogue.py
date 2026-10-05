"""
Step 1 of 2: pull the Libbey foodservice beverageware catalogue and download product photos.

  python3 pull_libbey_catalogue.py            # all pages (~811 items, ~2 min) + photos (~5 min)
  python3 pull_libbey_catalogue.py --pages 2  # quick test

Source: libbeyfoodservice.com server-rendered listing pages (__NEXT_DATA__ JSON). Reads public pages only,
1.5 s between pages and 0.25 s between photos. Does NOT use Libbey's Algolia search key (it is referrer-
restricted to their site).

Outputs (in ./libbey_data/):
  libbey_beverageware.json          raw product records
  rows.json                         normalised rows (sku, family, capacity_ml, height_mm, ...)
  libbey_beverageware_catalogue.csv same rows as CSV
  img/<sku>.jpg                     first product photo per item (straight-on side view on white)
"""
import argparse, csv, json, os, re, time, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (PHG glassware catalogue research)"}
OUT = "libbey_data"
FAM = {"Coupe Cocktail": "coupe", "Martini Cocktail": "martini", "Dof/Rocks Tumbler": "rocks", "Hi-Ball Tumbler": "highball",
       "Cooler Tumbler": "collins", "Flute Cocktail": "flute", "Margarita Cocktail": "margarita", "Hurricane Cocktail": "hurricane",
       "Shot/Shooter Cocktail": "shot", "Brandy Cocktail": "snifter", "Cordial Cocktail": "cordial", "Specialty Cocktail": "specialty",
       "Other Cocktail": "other_cocktail", "Beer": "beer", "Cold Mug": "mug", "Goblet": "goblet", "All Purpose Wine": "wine",
       "Red Wine": "wine", "White Wine": "wine", "Juice Tumbler": "juice"}

def page(n):
    url = f"https://libbeyfoodservice.com/products/beverageware?page={n}"
    h = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode()
    d = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S).group(1))
    r = d["props"]["pageProps"]["serverState"]["initialResults"]["shopify_products"]["results"][0]
    return r["hits"], r["nbPages"], r["nbHits"]

def num(s):
    m = re.search(r"[\d.]+", s or ""); return float(m.group()) if m else None

def normalise(x):
    d = x["meta"]["details"]; m = x["meta"].get("measurements") or {}
    cap, H = num(m.get("capacity")), num(m.get("height")); D = num(m.get("diameter")) or num(m.get("width"))
    t, name = d.get("type", ""), x["title"]; fam = FAM.get(t, "")
    if re.search(r"nick\s*&?\s*nora", name, re.I): fam = "nick_and_nora"
    if fam == "beer" and re.search(r"pint|mixing", name, re.I): fam = "pint"
    if fam == "mug" and re.search(r"mule|moscow", name, re.I): fam = "mule_mug"
    imgs = (x["meta"].get("images") or {}).get("all", "").split(", ")
    return dict(sku=d.get("itemno"), name=name, brand=d.get("brand"), pattern=d.get("pattern"), libbey_type=t, phg_family=fam,
                capacity_oz=cap, capacity_ml=round(cap * 29.5735, 1) if cap else None, height_in=H, max_diameter_in=D,
                height_mm=round(H * 25.4, 1) if H else None, max_diameter_mm=round(D * 25.4, 1) if D else None,
                price_low=d.get("price_low"), price_high=d.get("price_high"),
                case_pack=(x["meta"].get("packaging") or {}).get("case_pack"), sample_eligible=d.get("sample_eligible"),
                image=imgs[0] if imgs and imgs[0] else x.get("product_image"),
                url=f"https://libbeyfoodservice.com/product/{x['handle']}")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--pages", type=int, default=0); ap.add_argument("--no-images", action="store_true")
    a = ap.parse_args(); os.makedirs(f"{OUT}/img", exist_ok=True)
    hits, n_pages, n_hits = page(1); allp = {x["id"]: x for x in hits}
    last = min(n_pages, a.pages) if a.pages else n_pages
    print(f"{n_hits} items over {n_pages} pages; fetching {last}")
    for n in range(2, last + 1):
        time.sleep(1.5)
        try:
            for x in page(n)[0]: allp[x["id"]] = x
        except Exception as e: print("page", n, "error", e)
        print(f"page {n}/{last}: {len(allp)} items", flush=True)
    raw = list(allp.values()); json.dump(raw, open(f"{OUT}/libbey_beverageware.json", "w"))
    rows = sorted((normalise(x) for x in raw), key=lambda r: (r["phg_family"] or "zz", r["capacity_ml"] or 0))
    json.dump(rows, open(f"{OUT}/rows.json", "w"))
    with open(f"{OUT}/libbey_beverageware_catalogue.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} rows -> {OUT}/libbey_beverageware_catalogue.csv")
    if a.no_images: return
    got = 0
    for r in rows:
        p = f"{OUT}/img/{(r['sku'] or 'x').replace('/', '_')}.jpg"
        if r["image"] and not os.path.exists(p):
            try: urllib.request.urlretrieve(r["image"], p); got += 1; time.sleep(0.25)
            except Exception as e: print("img", r["sku"], e)
    print(f"downloaded {got} photos -> {OUT}/img/")

if __name__ == "__main__":
    main()
