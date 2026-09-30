#!/usr/bin/env python3
"""Automated KB visual tests on rendered menu PNGs (phg_design.validation_tests).

  thumbnail_test / blur_squint_test / salience_budget_test / focal_dominance_test
  grayscale_test (value range), palette_role_map (accent share), visual_moment_test,
  variant_silhouette_test (when several files are given).

Usage: python3 visual_tests.py a.png [b.png ...]  -> JSON on stdout
Proxies only: they measure structure, not taste. Read with the render.
"""
import json, sys
import numpy as np
from PIL import Image, ImageFilter


def lum(img):
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2], a


def components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    sizes = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                stack, n = [(y, x)], 0
                seen[y, x] = True
                while stack:
                    cy, cx = stack.pop()
                    n += 1
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                sizes.append(n)
    return sorted(sizes, reverse=True)


def analyse(path):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    # squint: blur sigma ~1% of width, then thumbnail to 200 px wide
    sq = im.filter(ImageFilter.GaussianBlur(radius=W * 0.01))
    th = sq.resize((200, max(1, round(200 * H / W))), Image.LANCZOS)
    L, rgb = lum(th)
    ground = float(np.median(L))
    dev = np.abs(L - ground)
    salient = dev > 0.18  # strongly differs from the ground after squinting
    comps = [c for c in components(salient) if c >= 12]
    area = L.size
    primary = comps[0] / area if comps else 0.0
    secondary = comps[1] / area if len(comps) > 1 else 0.0
    # accent share: saturated pixels on the full-res image (downsampled for speed)
    small = im.resize((400, round(400 * H / W)))
    a = np.asarray(small, dtype=np.float32) / 255.0
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    accent = float(((sat > 0.45) & (mx > 0.25)).mean())
    # visual moment: luminance-contrast-weighted centroid vs centre
    wts = dev + 1e-6
    ys, xs = np.mgrid[0:L.shape[0], 0:L.shape[1]]
    cx = float((xs * wts).sum() / wts.sum() / L.shape[1])
    cy = float((ys * wts).sum() / wts.sum() / L.shape[0])
    Lf, _ = lum(small)
    return {
        "file": path,
        "squint_salient_regions": len(comps),
        "primary_area_pct": round(primary * 100, 2),
        "primary_to_secondary": round(primary / secondary, 2) if secondary else None,
        "ground_luminance": round(ground, 3),
        "value_range_p5_p95": [round(float(np.percentile(Lf, 5)), 3), round(float(np.percentile(Lf, 95)), 3)],
        "accent_area_pct": round(accent * 100, 2),
        "visual_centroid": [round(cx, 3), round(cy, 3)],
        "_sil": np.asarray(im.convert("L").filter(ImageFilter.GaussianBlur(W * 0.02)).resize((40, 52)), dtype=np.float32),
    }


def main(paths):
    res = [analyse(p) for p in paths]
    sims = []
    for i in range(len(res)):
        for j in range(i + 1, len(res)):
            a, b = res[i]["_sil"].ravel(), res[j]["_sil"].ravel()
            a, b = a - a.mean(), b - b.mean()
            r = float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-6))
            sims.append({"a": res[i]["file"], "b": res[j]["file"], "silhouette_corr": round(r, 3)})
    for r in res:
        del r["_sil"]
    print(json.dumps({"results": res, "variant_silhouette": sims,
                      "notes": "silhouette_corr > 0.8 = structurally similar directions (variant_silhouette_test fails)"}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
