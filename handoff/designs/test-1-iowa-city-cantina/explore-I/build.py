#!/usr/bin/env python3
"""TEST-1 explore-I "Night Field": one engineered gold line agave on bottle green.

Every item, price and description comes from ../build/draft_doc.json (see DESC_RULES below).
The only drawing is a rosette of tapered leaf outlines computed here in Python, one stroke weight,
cropped by the bottom and right trim.

Usage: python3 build.py [--variant before|after]
Outputs (after): menu.html, preview-letter.png, preview-phone.png, render_report.json
Outputs (before): preview-letter-before.png (the pre-subtraction checkpoint)
"""
import json, math, os, sys, io, re, glob
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFT = json.load(open(HERE.parent / "build" / "draft_doc.json"))
FONTS = (HERE / "fonts").as_uri()
VARIANT = sys.argv[sys.argv.index("--variant") + 1] if "--variant" in sys.argv else "after"
BEFORE = VARIANT == "before"

# ---- palette (3 inks) ------------------------------------------------------------------
GREEN = "#10291F"      # ground: deep bottle green
IVORY = "#EFE6D2"      # reading ink
IVORY2 = "#C9C2AF"     # descriptions / sub-labels (ivory mixed toward ground, still > 7:1)
GOLD = "#C8A765"       # the single accent: wordmark, section heads, the agave line

# ---- content --------------------------------------------------------------------------
# Description sources (never invented; no quantities; never echo the name):
#   comp  = component names, hidden components removed
#   desc  = the draft desc reduced to its ingredient / style words (no added words)
#   none  = the draft desc only echoes the name -> dropped
DESC_RULES = {
    "beta_manhattan": ("comp", None),                       # Aromatic Bitters hidden (public_components false)
    "beta_margarita": ("desc", "Tequila blanco · lime · orange liqueur · agave"),
    "beta_daiquiri": ("desc", "White rum · lime · demerara syrup"),
    "beta_old_fashioned": ("desc", "Brown butter-washed bourbon · demerara · bitters"),  # house_recipe=false: names only
    "beta_czech_pilsner": ("desc", "Crisp pale lager"),
    "beta_dry_hopped_ipa": ("desc", "Hop-forward"),           # "draft IPA" echoes name/section
    "beta_amber_lager": ("desc", "Toasty"),                   # "amber lager" echoes name
    "beta_malbec": ("desc", "Dry red"),                       # "wine" echoes section
    "beta_pinot_grigio": ("desc", "Dry white"),
    "beta_brut_rose": ("none", None),                         # "Dry sparkling rosé" = Brut + Sparkling + Rosé: echo
    "beta_blanco_tequila": ("none", None),                    # "Blanco tequila pour." echo
    "beta_anejo_tequila": ("none", None),                     # "Añejo tequila pour." echo
    "beta_cognac_vsop": ("none", None),                       # "VSOP Cognac pour." echo
    "beta_dry_cider": ("desc", "Sparkling"),                  # "dry ... cider" echoes name
}


def description(it):
    kind, txt = DESC_RULES[it["id"]]
    if kind == "none":
        return ""
    if kind == "comp":
        hidden = {k for k, v in it["meta"].get("public_components", {}).items() if v is False}
        names = [c["name"] for c in it["components"]
                 if c["name"].lower().replace(" ", "-") not in hidden]
        s = " · ".join(n.lower() for n in names)
        return s[0].upper() + s[1:]
    # verify every word of the reduced desc exists in the draft desc (no invention)
    src = re.sub(r"[^\w\s-]", " ", it["desc"].lower())
    for w in re.findall(r"[\w-]+", txt.lower()):
        assert w in src.split() or w in src, (it["id"], w)
    return txt


def price(it):
    v = it["prices"][0]["value"]
    return f"{v:g}" if float(v).is_integer() else f"{v:.2f}"


SEC = {s["id"]: s for s in DRAFT["sections"]}
# Section heads from the draft. Beer's single sub "Draft" is merged into its head ("Draft Beer");
# every other sub is kept as a quiet label.
GROUPS = {
    "sec_cocktails": ("Cocktails", True),
    "sec_beer": ("Draft Beer", False),
    "sec_wine": ("Wine", True),
    "sec_spirits": ("Spirits", True),
    "sec_cider": ("Cider", False),
}
LEFT = ["sec_cocktails", "sec_beer", "sec_cider"]
RIGHT = ["sec_wine", "sec_spirits"]


def item_html(it):
    d = description(it)
    ds = f'<div class="ds">{d}</div>' if d else ""
    return (f'<div class="it" data-id="{it["id"]}"><div class="row"><span class="nm">{it["name"]}</span>'
            f'<span class="pr">{price(it)}</span></div>{ds}</div>')


def section_html(sid):
    s = SEC[sid]
    head, show_subs = GROUPS[sid]
    out = [f'<section><h2>{head}</h2>']
    for it in s.get("items", []):
        out.append(item_html(it))
    for sub in s.get("subs", []):
        if show_subs:
            out.append(f'<h3>{sub["name"]}</h3>')
        for it in sub["items"]:
            out.append(item_html(it))
    out.append("</section>")
    return "\n".join(out)


def all_items():
    for s in DRAFT["sections"]:
        yield from s.get("items", [])
        for sub in s.get("subs", []):
            yield from sub["items"]


# ---- the gesture: a geometric agave rosette -------------------------------------------
def leaf_path(bx, by, ang, L, W, bend, n=90):
    """Tapered lanceolate leaf from base (bx,by). ang in degrees from vertical (+ = right).
    Half-width ~ t^0.42 (1-t)^1.05 (widest near 30%), centreline bends outward by bend*L*t^2."""
    a = math.radians(ang)
    dx, dy = math.sin(a), -math.cos(a)
    nx, ny = math.cos(a), math.sin(a)          # right-hand normal of the axis
    p, q = 0.42, 1.05
    peak = (p / (p + q)) ** p * (q / (p + q)) ** q
    cen, hw = [], []
    for i in range(n + 1):
        t = i / n
        off = bend * L * t * t
        cen.append((bx + dx * L * t + nx * off, by + dy * L * t + ny * off))
        hw.append(W * (t ** p) * ((1 - t) ** q) / peak)
    left, right = [], []
    for i, (cx, cy) in enumerate(cen):
        j0, j1 = max(0, i - 1), min(n, i + 1)
        tx, ty = cen[j1][0] - cen[j0][0], cen[j1][1] - cen[j0][1]
        m = math.hypot(tx, ty) or 1
        ux, uy = ty / m, -tx / m               # local normal
        left.append((cx - ux * hw[i], cy - uy * hw[i]))
        right.append((cx + ux * hw[i], cy + uy * hw[i]))
    pts = left + right[::-1]
    outline = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z"
    k = int(n * 0.86)
    rib = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in cen[int(n * 0.06):k])
    # engraving veins: lines at fixed fractions of the half-width, so they converge on the tip
    veins = []
    for u, t1 in VEINS:
        pts = []
        for i in range(int(n * 0.10), int(n * t1)):
            cx, cy = cen[i]; lx, ly = left[i]
            pts.append((cx + (lx - cx) * u, cy + (ly - cy) * u))
        if pts:
            veins.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts))
    return outline, rib + " " + " ".join(veins)


VEINS = json.loads(os.environ.get('AGAVE_VEINS', '[]'))   # (fraction of half-width, end t); negative = right side


# rings from back (tall, upright) to front (short, splayed); drawn in that order, each leaf
# filled with the ground so front leaves occlude back ones like an engraving.
RINGS = [
    # (angles, length factors, width factor, bend) -- each ring sits half a step off the ring behind it
    ([-20, 0, 20], [0.93, 1.00, 0.93], 0.13, 0.04),
    ([-50, -30, -10, 10, 30, 50], [0.78, 0.86, 0.92, 0.92, 0.86, 0.78], 0.145, 0.08),
    ([-66, -44, -22, 0, 22, 44, 66], [0.64, 0.70, 0.74, 0.76, 0.74, 0.70, 0.64], 0.16, 0.08),
    ([-32, -11, 11, 32], [0.54, 0.57, 0.57, 0.54], 0.18, 0.07),
]


def agave_svg(vw, vh, bx, by, L, stroke, ribs=True, css_class="agave"):
    parts = []
    for angs, lf, wf, bend in RINGS:
        for a, f in zip(angs, lf):
            Lx = L * f
            b = bend * (1 if a >= 0 else -1) * min(1.0, abs(a) / 40 + 0.15)
            o, r = leaf_path(bx, by, a, Lx, Lx * wf, b)
            parts.append(f'<path d="{o}" fill="{GREEN}"/>')
            if ribs:
                parts.append(f'<path d="{r}" fill="none"/>')
    return (f'<svg class="{css_class}" viewBox="0 0 {vw} {vh}" width="{vw}" height="{vh}" '
            f'xmlns="http://www.w3.org/2000/svg"><g stroke="{GOLD}" stroke-width="{stroke}" '
            f'stroke-linejoin="round" stroke-linecap="round">{"".join(parts)}</g></svg>')


# ---- page -------------------------------------------------------------------------------
PW, PH = 816, 1056          # letter @ 96 css px/in; rendered at 3.125x = 2550 x 3300
M = 64                      # 0.67 in side margin
COLW = 320
GUT = PW - 2 * M - 2 * COLW  # 72


def build():
    left = "\n".join(section_html(s) for s in LEFT)
    right = "\n".join(section_html(s) for s in RIGHT)
    agave_letter = agave_svg(PW, PH, bx=664, by=1122, L=388, stroke=float(os.environ.get('AGAVE_STROKE', '1.7')), ribs=os.environ.get('AGAVE_RIBS', '1') == '1')
    agave_phone = agave_svg(390, 300, bx=300, by=342, L=292, stroke=1.4, ribs=True, css_class="agave-phone")
    frame = '<div class="frame"></div>' if BEFORE else ""
    rule = '<div class="wmrule"></div>' if BEFORE else ""
    sig = '' if '--nosig' in sys.argv else '<div class="sig">Good drinks<br>Good people</div>'
    ff = "".join(
        f"@font-face{{font-family:{fam};font-weight:{w};src:url({FONTS}/{file})}}"
        for fam, w, file in [("CG", 500, "CormorantGaramond-500.ttf"), ("SS", 400, "SourceSerif4-400.ttf"),
                             ("SS", 500, "SourceSerif4-500.ttf"), ("SS", 600, "SourceSerif4-600.ttf"),
                             ("DM", 500, "DMSans-500.ttf"), ("DM", 600, "DMSans-600.ttf")])
    css = f"""{ff}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:{GREEN}}}
.page{{position:relative;overflow:hidden;background:{GREEN};color:{IVORY};font-family:SS;
  -webkit-font-smoothing:antialiased}}
body.letter .page{{width:{PW}px;height:{PH}px}}
.agave{{position:absolute;left:0;top:0;pointer-events:none}}
.agave-phone{{display:none}}
header{{position:absolute;left:0;right:0;top:78px;text-align:center}}
.wm{{font-family:CG;font-weight:500;font-size:92px;line-height:1;letter-spacing:.34em;padding-left:.34em;color:{GOLD}}}
.sub{{font-family:DM;font-weight:500;font-size:12px;letter-spacing:.34em;padding-left:.34em;text-transform:uppercase;color:{IVORY2};line-height:1}}
.sub.a{{margin-top:22px}} .sub.b{{margin-top:10px}}
.wmrule{{width:64px;height:0;border-top:1.2px solid {GOLD};margin:22px auto 0}}
.cols{{position:absolute;top:292px;left:{M}px;display:grid;grid-template-columns:{COLW}px {COLW}px;column-gap:{GUT}px;align-items:start}}
section+section{{margin-top:42px}}
h2{{font-family:DM;font-weight:600;font-size:14px;letter-spacing:.3em;text-transform:uppercase;color:{GOLD};line-height:1;margin-bottom:16px}}
h3{{font-family:DM;font-weight:500;font-size:11px;letter-spacing:.26em;text-transform:uppercase;color:{IVORY2};line-height:1;margin:16px 0 9px}}
h2+h3{{margin-top:0}}
.it+.it{{margin-top:12px}}
.row{{display:grid;grid-template-columns:1fr auto;column-gap:14px;align-items:baseline}}
.nm{{font-weight:500;font-size:17.5px;line-height:1.25;white-space:nowrap}}
.pr{{font-weight:500;font-size:17.5px;line-height:1.25;font-variant-numeric:tabular-nums lining-nums}}
.ds{{font-weight:400;font-size:13px;line-height:1.3;color:{IVORY2};margin-top:2px;white-space:nowrap}}
.sig{{position:absolute;left:{M}px;bottom:66px;font-family:DM;font-weight:500;font-size:11px;letter-spacing:.34em;text-transform:uppercase;color:{IVORY2};line-height:1.9}}
.frame{{position:absolute;inset:26px;border:1.2px solid {GOLD}}}
.frame::after{{content:"";position:absolute;inset:5px;border:1.2px solid {GOLD}}}
/* phone: recomposed to one column, agave closes the page */
body.phone .page{{width:390px;min-height:100px;padding:0 0 0}}
body.phone .agave,body.phone .frame{{display:none}}
body.phone .agave-phone{{display:block;margin-top:8px}}
body.phone header{{position:static;padding-top:48px}}
body.phone .wm{{font-size:50px;letter-spacing:.3em;padding-left:.3em}}
body.phone .sub{{font-size:11px}} body.phone .sub.a{{margin-top:16px}}
body.phone .cols{{position:static;display:block;padding:44px 34px 0}}
body.phone .col+.col{{margin-top:42px}}
body.phone .nm,body.phone .pr{{font-size:18px}} body.phone .ds{{font-size:13.5px}}
body.phone .sig{{position:static;padding:40px 34px 0}}
"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cantina &amp; Cocktail Bar, Iowa City: bar menu (explore-I Night Field)</title>
<style>{css}</style></head>
<body class="{{BODYCLASS}}"><div class="page">
{agave_letter}
{frame}
<header><div class="wm">CANTINA</div><div class="sub a">&amp; Cocktail Bar</div><div class="sub b">Iowa City, Iowa</div>{rule}</header>
<main class="cols"><div class="col">
{left}
</div><div class="col">
{right}
</div></main>
{sig}
{agave_phone}
</div></body></html>"""


# ---- checks -----------------------------------------------------------------------------
def rl(c):
    c = [v / 255 for v in c]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


PROBE_JS = """() => {
 const pg=document.querySelector('.page').getBoundingClientRect(); const out=[];
 document.querySelectorAll('.wm,.sub,h2,h3,.nm,.pr,.ds,.sig').forEach(e=>{
   const r=document.createRange(); r.selectNodeContents(e); const b=r.getBoundingClientRect();
   const cs=getComputedStyle(e);
   out.push({t:e.textContent.trim().slice(0,40),cls:e.className||e.tagName,c:cs.color,fs:cs.fontSize,
     x:b.left-pg.left,y:b.top-pg.top,w:b.width,h:b.height,over:e.scrollWidth>e.clientWidth+1});});
 const g=s=>{const e=document.querySelector(s); if(!e) return null; const b=e.getBoundingClientRect();
   return [Math.round(b.left-pg.left),Math.round(b.top-pg.top),Math.round(b.right-pg.left),Math.round(b.bottom-pg.top)]};
 const cols=[...document.querySelectorAll('.col')].map(e=>{const b=e.getBoundingClientRect();return [Math.round(b.left-pg.left),Math.round(b.top-pg.top),Math.round(b.right-pg.left),Math.round(b.bottom-pg.top)]});
 return {boxes:out, geometry:{page:[pg.width,pg.height],header:g('header'),wordmark:g('.wm'),cols,sig:g('.sig')}};
}"""


def check(pg, scale):
    from PIL import Image
    data = pg.evaluate(PROBE_JS)
    pg.add_style_tag(content="*{color:transparent!important}")
    img = Image.open(io.BytesIO(pg.screenshot(full_page=True))).convert("RGB")
    rows = []
    for b in data["boxes"]:
        rgb = tuple(int(float(v)) for v in re.findall(r"[\d.]+", b["c"])[:3])
        L1 = rl(rgb)
        x0, y0 = max(0, int(b["x"] * scale)), max(0, int(b["y"] * scale))
        x1, y1 = min(img.width, int((b["x"] + b["w"]) * scale)), min(img.height, int((b["y"] + b["h"]) * scale))
        worst = 99
        if x1 > x0 and y1 > y0:
            for px in set(img.crop((x0, y0, x1, y1)).get_flattened_data()):
                L2 = rl(px)
                worst = min(worst, (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05))
        rows.append({"text": b["t"], "role": b["cls"], "font_px_css": b["fs"], "min_contrast": round(worst, 2),
                     "overflow": b["over"], "box_css": [round(b["x"]), round(b["y"]), round(b["x"] + b["w"]), round(b["y"] + b["h"])]})
    pg.reload(); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
    return rows, data["geometry"]


def main():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    doc = build()
    # integrity: every draft item present with its exact price
    for it in all_items():
        assert f'data-id="{it["id"]}"' in doc and f'<span class="pr">{price(it)}</span>' in doc, it["id"]
    tag = "-before" if BEFORE else ("-nosig" if "--nosig" in sys.argv else os.environ.get("TAG", ""))
    if not tag:
        (HERE / "menu.html").write_text(doc.replace("{BODYCLASS}", "letter"))
    report = {"variant": VARIANT}
    exe = next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=exe)
        jobs = [(f"preview-letter{tag}.png", "letter", PW, PH, 3.125)]
        if not tag:
            jobs.append(("preview-phone.png", "phone", 390, 800, 3))
        for name, cls, w, h, dsf in jobs:
            pg = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            tmp = HERE / f".render-{cls}.html"
            tmp.write_text(doc.replace("{BODYCLASS}", cls))
            pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(600)
            pg.screenshot(path=str(HERE / name), full_page=(cls == "phone"))
            rows, geo = check(pg, dsf)
            tmp.unlink()
            report[name] = {"geometry_css_px": geo, "text": rows}
            pg.close()
        br.close()
    (HERE / f"render_report{tag}.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    for k, v in report.items():
        if isinstance(v, dict):
            worst = sorted(v["text"], key=lambda r: r["min_contrast"])[:3]
            print(k, v["geometry_css_px"], [(r["text"], r["min_contrast"]) for r in worst],
                  "overflow:", [r["text"] for r in v["text"] if r["overflow"]])


if __name__ == "__main__":
    main()
