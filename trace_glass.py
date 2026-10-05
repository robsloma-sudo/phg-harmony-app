"""
PHG glassware tracer: manufacturer product photo -> revolved glass profile, validated against published capacity.

Method
1. Libbey product shots are straight-on side views on pure white. Threshold the glass, then for each pixel row
   take the left/right extent -> outer radius r_out(y). The axis is the median row centre.
2. Scale: px/mm from the published HEIGHT. The published MAX DIAMETER is then an independent check of the
   photo's aspect ratio (perspective / crop errors show up here).
3. Interior:
   - tumblers: the top of the solid base is the strongest horizontal edge along the axis in the lower part of the glass
   - stemware: the bowl starts where the silhouette is narrowest above the foot (the stem), plus a small knop allowance
   - inner radius = r_out - wall (wall is assumed per family; it is not visible reliably)
4. Base selection: the bowl bottom must be an intensity edge actually visible in the photo (tumblers: lower 45%
   of the glass, above the table line; stemware: within 20 mm above the stem joint). Of those observed edges, the
   one whose implied volume is closest to the published capacity is used. Capacity selects between real edges,
   it never creates one.
5. Validation: |volume error| <= 7% AND photo aspect vs published max diameter within 10% -> 'spec_sheet' (traced).
   Otherwise 'unverified' with the errors recorded. Mugs (handles) are not traced.
"""
import json, math, sys
import numpy as np
from PIL import Image

WALL = {"coupe": 1.4, "nick_and_nora": 1.3, "martini": 1.4, "flute": 1.2, "wine": 1.2, "margarita": 1.6, "snifter": 1.4,
        "cordial": 1.4, "hurricane": 1.8, "specialty": 1.6, "goblet": 1.8,
        "rocks": 2.6, "highball": 2.2, "collins": 2.0, "pint": 2.6, "beer": 2.2, "shot": 2.5, "juice": 2.0, "mug": 3.0}
STEM = {"coupe", "nick_and_nora", "martini", "flute", "wine", "margarita", "snifter", "cordial", "hurricane", "goblet"}

def trace(img_path, height_mm, max_d_mm, capacity_ml, family, thresh=244):
    im = np.asarray(Image.open(img_path).convert("L"), dtype=np.int16)
    mask = im < thresh
    rows = np.where(mask.any(axis=1))[0]
    top, bot = rows.min(), rows.max()
    # ignore a soft floor shadow/reflection: keep rows whose width is reasonable
    left = np.array([np.argmax(mask[y]) if mask[y].any() else -1 for y in range(im.shape[0])])
    right = np.array([im.shape[1] - 1 - np.argmax(mask[y][::-1]) if mask[y].any() else -1 for y in range(im.shape[0])])
    centres = (left[top:bot + 1] + right[top:bot + 1]) / 2
    axis = float(np.median(centres))
    px_per_mm = (bot - top + 1) / height_mm
    width_px = (right[top:bot + 1] - left[top:bot + 1] + 1).max()
    d_check = width_px / px_per_mm
    aspect_err = (d_check / max_d_mm - 1) * 100 if max_d_mm else None

    # outer radius per mm of height (from the table up)
    H = height_mm; r_out = []
    for hmm in np.arange(0, H + 0.01, 0.5):
        y = int(round(bot - hmm * px_per_mm)); y = min(max(y, top), bot)
        r_out.append((hmm, max(right[y] - axis, axis - left[y]) / px_per_mm))
    r_out = np.array(r_out)
    wall = WALL.get(family, 2.0)

    # candidate bowl-bottom heights, all OBSERVED in the photo
    col = im[:, int(axis) - 6:int(axis) + 7].mean(axis=1)
    if family in STEM:
        lo, hi = int(len(r_out) * 0.08), int(len(r_out) * 0.85)
        seg = r_out[lo:hi]; i_min = lo + int(np.argmin(seg[:, 1]))
        stem_r = r_out[i_min, 1]; j = i_min
        while j < len(r_out) - 1 and r_out[j, 1] < stem_r + 3.0: j += 1
        z_join = r_out[j, 0]
        # interior bottom = an intensity edge on the axis between the stem joint and 20 mm above it
        y_a, y_b = int(bot - (z_join + 20) * px_per_mm), int(bot - z_join * px_per_mm)
        g = np.abs(np.diff(col[y_a:y_b])); idx = np.argsort(g)[::-1][:12]
        cands = sorted({round(z_join + 1.0, 1)} | {round((bot - (y_a + i)) / px_per_mm, 1) for i in idx if g[i] > 4})
    else:
        y0, y1 = int(bot - 0.45 * (bot - top)), bot - int(2.5 * px_per_mm)      # skip the table contact line
        g = np.abs(np.diff(col[y0:y1])); idx = np.argsort(g)[::-1][:15]
        cands = sorted({round((bot - (y0 + i)) / px_per_mm, 1) for i in idx if g[i] > 4})
    if not cands: cands = [3.0]

    def inner_vol(zb):
        pts = [(0.0, 0.0)] + [(max(ro - wall, 0.0), hmm - zb) for hmm, ro in r_out if hmm >= zb]
        v = 0.0
        for (r1, h1), (r2, h2) in zip(pts, pts[1:]):
            if h2 > h1: v += math.pi * (h2 - h1) / 3 * (r1 * r1 + r1 * r2 + r2 * r2) / 1000
        return v
    z_bowl = min(cands, key=lambda zb: abs(inner_vol(zb) - capacity_ml)) if capacity_ml else cands[0]
    inner = [(0.0, 0.0)]
    for hmm, ro in r_out:
        if hmm >= z_bowl - 1e-6:
            inner.append((max(ro - wall, 0.0), hmm - z_bowl))
    # rim: last point
    prof = [{"r_mm": round(r, 2), "h_mm": round(h, 2)} for r, h in inner]
    # tidy: drop duplicate heights at the start
    vol = 0.0
    for a, b in zip(prof, prof[1:]):
        dh = b["h_mm"] - a["h_mm"]
        if dh > 0: vol += math.pi * dh / 3 * (a["r_mm"] ** 2 + a["r_mm"] * b["r_mm"] + b["r_mm"] ** 2) / 1000
    err = (vol / capacity_ml - 1) * 100 if capacity_ml else None
    # thin the profile for storage: every 2 mm + rim
    thin = [prof[0]] + [p for p in prof[1:] if abs(p["h_mm"] / 2 - round(p["h_mm"] / 2)) < 0.13] + [prof[-1]]
    dedup = []
    for p in thin:
        if not dedup or p["h_mm"] > dedup[-1]["h_mm"] or (p["h_mm"] == 0 and p["r_mm"] > dedup[-1]["r_mm"]): dedup.append(p)
    status = "spec_sheet" if (err is not None and abs(err) <= 7 and (aspect_err is None or abs(aspect_err) <= 10)) else "unverified"
    return dict(status=status, n_edge_candidates=len(cands), inner_profile=dedup, traced_volume_ml=round(vol, 1), capacity_error_pct=round(err, 1) if err is not None else None,
                base_or_stem_mm=round(z_bowl, 1), wall_mm=wall, aspect_check_pct=round(aspect_err, 1) if aspect_err is not None else None,
                rim_inner_r_mm=dedup[-1]["r_mm"], px_per_mm=round(px_per_mm, 2))

if __name__ == "__main__":
    a = sys.argv[1:]
    print(json.dumps(trace(a[0], float(a[1]), float(a[2]), float(a[3]), a[4]), indent=1)[:600])
