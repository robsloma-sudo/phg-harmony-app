#!/usr/bin/env python3
"""Explore H - "Sun & Terrace". TEST-1 Iowa City cantina bar menu.

One gesture: a flat terracotta disc (cropped by the top-right trim) and a stepped ink terrace
(cropped at the lower-right corner), composed as one right-hand band. CANTINA collides with the
disc; where it crosses, the letters knock out to cream (clip-path circle = the disc).

Renders menu.html, preview-letter.png (2550x3300) and preview-phone.png (1170 wide),
plus contrast.json (worst-pixel contrast for every text run) and layout.json (geometry).
"""
import glob, io, json, os, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFT = HERE.parent / "build" / "draft_doc.json"
FONTS = (HERE / "fonts").as_uri()

# ---- palette: ground + ink + one accent ------------------------------------------------------
CREAM = "#F3EBDD"   # ground
INK = "#1E1A17"     # names, prices, wordmark, terrace
INK2 = "#5B5149"    # descriptions, sub heads, sub-line, tagline (same ink, lighter value)
TERRA = "#A6472A"   # accent: disc + section heads only

# ---- content: every item from the draft; descriptions only from components / existing desc ----
# Descriptions are ingredient-first, sentence case, one line, no quantities. Rules applied:
#  * hidden components dropped (Manhattan aromatic bitters: public_components aromatic-bitters=false)
#  * house_recipe=false (Brown Butter Old Fashioned): ingredient names only (taken from its desc)
#  * descs that only echo the item name are dropped (tequila x2, cognac); echoed words are
#    deleted, never replaced (IPA, amber lager, rose, cider). Nothing is added.
DESC = {
    "beta_manhattan": "Rye whiskey · sweet vermouth · cocktail cherry",        # components minus hidden
    "beta_margarita": "Tequila blanco · lime · orange liqueur · agave",         # draft desc, sentence 1
    "beta_daiquiri": "White rum · lime · house demerara syrup",                # draft desc
    "beta_old_fashioned": "Brown butter-washed bourbon · demerara · bitters",  # draft desc (names only)
    "beta_czech_pilsner": "Crisp pale lager",                                  # draft desc
    "beta_dry_hopped_ipa": "Hop-forward",                                      # draft desc minus echo "draft IPA"
    "beta_amber_lager": "Toasty",                                              # draft desc minus echo "amber lager"
    "beta_malbec": "Dry red wine",                                             # draft desc
    "beta_pinot_grigio": "Dry white wine",                                     # draft desc
    "beta_brut_rose": "Dry sparkling",                                         # draft desc minus echo "rosé"
    "beta_blanco_tequila": "",                                                 # "Blanco tequila pour." = echo
    "beta_anejo_tequila": "",                                                  # "Añejo tequila pour." = echo
    "beta_cognac_vsop": "",                                                    # "VSOP Cognac pour." = echo
    "beta_dry_cider": "Sparkling",                                             # draft desc minus echo "dry cider"
}
# Column split (sections stay whole, draft order kept inside each column)
# Subtraction pass: Spirits' "Agave" / "Brandy" sub heads merged into SPIRITS (items stay in
# draft order and in their section; the names Tequila / Cognac already carry the grouping).
MERGE_SUBS = {"sec_spirits"}
COLUMNS = [["sec_cocktails", "sec_beer"], ["sec_wine", "sec_spirits", "sec_cider"]]


def fmt_price(v):
    return f"{v:.2f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))


def load():
    doc = json.loads(DRAFT.read_text())
    secs = {s["id"]: s for s in doc["sections"]}
    seen = []
    cols = []
    for ids in COLUMNS:
        blocks = []
        for sid in ids:
            s = secs[sid]
            groups = [(None, s.get("items", []))] if s.get("items") else []
            if sid in MERGE_SUBS:  # subtraction pass: sub heads merged into the section head
                groups += [(None, [i for sub in s.get("subs", []) for i in sub["items"]])]
            else:
                groups += [(sub["name"], sub["items"]) for sub in s.get("subs", [])]
            gs = []
            for sub, items in groups:
                rows = []
                for it in items:
                    assert it["meta"]["public_visibility"]["item"]
                    assert len(it["prices"]) == 1
                    seen.append(it["id"])
                    rows.append({"id": it["id"], "name": it["name"], "desc": DESC[it["id"]],
                                 "price": fmt_price(it["prices"][0]["value"])})
                gs.append({"sub": sub, "rows": rows})
            blocks.append({"name": s["name"], "groups": gs})
        cols.append(blocks)
    all_ids = [i["id"] for s in doc["sections"] for i in s.get("items", [])] + \
              [i["id"] for s in doc["sections"] for sub in s.get("subs", []) for i in sub["items"]]
    assert sorted(seen) == sorted(all_ids), "item coverage mismatch"
    return cols


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;")


def menu_html(cols):
    out = []
    for i, blocks in enumerate(cols):
        out.append(f'<div class="col col{i+1}">')
        for b in blocks:
            out.append(f'<section><h2>{esc(b["name"])}</h2>')
            for g in b["groups"]:
                if g["sub"]:
                    out.append(f'<h3>{esc(g["sub"])}</h3>')
                for r in g["rows"]:
                    d = f'<span class="d">{esc(r["desc"])}</span>' if r["desc"] else ""
                    out.append(f'<div class="it"><span class="n">{esc(r["name"])}</span>'
                               f'<span class="p">{r["price"]}</span>{d}</div>')
            out.append('</section>')
        out.append('</div>')
    return "\n".join(out)


# Terrace: seven contour steps, each STEP_W wide and STEP_H tall, rising to the right,
# drawn 12 css px (3.2 mm) past the right and bottom trim (bleed).
def terrace_svg(n, sw, sh, bleed=12):
    W, H = n * sw + bleed, n * sh + bleed
    pts = [(W, 0), (W - bleed - sw, 0)]
    for k in range(1, n):
        x = W - bleed - k * sw
        pts += [(x, k * sh), (x - sw, k * sh)]
    pts += [(W - bleed - n * sw, H), (W, H)]
    path = " ".join(f"{x},{y}" for x, y in pts)
    return (f'<svg class="terrace" width="{W}" height="{H}" viewBox="0 0 {W} {H}" aria-hidden="true">'
            f'<polygon points="{path}" fill="{INK}"/></svg>')


def build():
    cols = load()
    items = menu_html(cols)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Cantina - bar menu (explore H, Sun &amp; Terrace)</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@font-face{{font-family:Cz;font-weight:400;src:url({FONTS}/Cinzel-400.ttf)}}
@font-face{{font-family:Gd;font-weight:400;src:url({FONTS}/EBGaramond-400.ttf)}}
@font-face{{font-family:Gd;font-weight:500;src:url({FONTS}/EBGaramond-500.ttf)}}
@font-face{{font-family:Gd;font-weight:400;font-style:italic;src:url({FONTS}/EBGaramond-400i.ttf)}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{CREAM}}}
.page{{position:relative;overflow:hidden;background:{CREAM};color:{INK};font-family:Gd}}
/* ---------- the gesture ---------- */
.disc{{position:absolute;border-radius:50%;background:{TERRA}}}
.terrace{{position:absolute;display:block}}
/* ---------- wordmark (only display type) ---------- */
.wm{{position:absolute;inset:0;pointer-events:none}}
.wm span{{position:absolute;font-family:Cz;font-weight:400;line-height:1;white-space:nowrap}}
.wm.ink span{{color:{INK}}}
.wm.knock span{{color:{CREAM}}}
.sub{{position:absolute;font-family:Gd;font-weight:500;color:{INK2};text-transform:uppercase;white-space:nowrap}}
/* ---------- reading layer ---------- */
.col{{position:absolute}}
h2{{font-family:Gd;font-weight:500;color:{TERRA};text-transform:uppercase;letter-spacing:.28em}}
h3{{font-family:Gd;font-weight:500;color:{INK2};text-transform:uppercase;letter-spacing:.24em}}
.it{{display:grid;grid-template-columns:var(--nw) 24px;column-gap:0;align-items:baseline}}
.n{{font-weight:500}}
.p{{font-weight:500;font-variant-numeric:lining-nums tabular-nums;text-align:right}}
.d{{grid-column:1 / span 2;white-space:nowrap;font-style:italic;color:{INK2}}}
.tag{{position:absolute;font-family:Gd;font-weight:500;color:{INK2};text-transform:uppercase;letter-spacing:.34em}}

/* ================= LETTER 816 x 1056 css px (= 8.5 x 11 in; x3.125 = 2550 x 3300) ============ */
body.letter .page{{width:816px;height:1056px}}
body.letter .disc{{width:320px;height:320px;left:512px;top:-34px}}           /* centre 672,126  r 160 */
body.letter .terrace{{right:-12px;bottom:-12px}}
body.letter .wm span{{left:58px;top:186px;font-size:124px;letter-spacing:.075em}}
body.letter .wm.knock{{clip-path:circle(160px at 672px 126px)}}
body.letter .sub{{left:64px;top:334px;font-size:13px;letter-spacing:.3em}}
body.letter .col{{top:410px;width:300px;--nw:206px}}
body.letter .col1{{left:64px}}
body.letter .col2{{left:452px}}
body.letter section+section{{margin-top:34px}}
body.letter h2{{font-size:14px;margin-bottom:12px}}
body.letter h3{{font-size:11px;margin:12px 0 6px}}
body.letter h2+h3{{margin-top:0}}
body.letter .it{{margin-bottom:11px}}
body.letter .n,body.letter .p{{font-size:16px;line-height:1.2}}
body.letter .d{{font-size:13px;line-height:1.3;margin-top:1px}}
body.letter .tag{{left:64px;bottom:62px;font-size:11.5px;line-height:1.9}}

/* ================= PHONE 390 css px wide (x3 = 1170) - recomposed to one column ============ */
body.phone .page{{width:390px;height:var(--ph,1640px)}}
body.phone .disc{{width:220px;height:220px;left:236px;top:-44px}}            /* centre 346,66 r 110 */
body.phone .terrace{{right:-12px;bottom:-12px}}
body.phone .wm span{{left:26px;top:104px;font-size:60px;letter-spacing:.07em}}
body.phone .wm.knock{{clip-path:circle(110px at 346px 66px)}}
body.phone .sub{{left:28px;top:180px;font-size:11px;letter-spacing:.24em}}
body.phone .col{{position:static;width:auto;--nw:calc(100% - 44px)}}
body.phone .cols{{position:absolute;left:28px;right:28px;top:232px}}
body.phone .col+.col{{margin-top:34px}}
body.phone section+section{{margin-top:34px}}
body.phone h2{{font-size:14px;margin-bottom:12px}}
body.phone h3{{font-size:11px;margin:12px 0 6px}}
body.phone h2+h3{{margin-top:0}}
body.phone .it{{margin-bottom:11px}}
body.phone .n,body.phone .p{{font-size:17px;line-height:1.2}}
body.phone .d{{font-size:14px;line-height:1.3;margin-top:1px}}
body.phone .tag{{left:28px;bottom:40px;font-size:11px;line-height:1.9}}
</style></head>
<body class="{{BODYCLASS}}"><div class="page">
<div class="disc" aria-hidden="true"></div>
{{TERRACE}}
<h1 class="wm ink"><span>CANTINA</span></h1>
<div class="wm knock" aria-hidden="true"><span>CANTINA</span></div>
<p class="sub">&amp; cocktail bar &#183; Iowa City, Iowa</p>
<div class="cols">
{items}
</div>
<p class="tag">Good drinks<br>Good people</p>
</div></body></html>"""


TERRACES = {"letter": terrace_svg(7, 48, 26), "phone": terrace_svg(6, 30, 18)}

CONTRAST_JS = """() => { const out=[]; const walker=document.createTreeWalker(document.querySelector('.page'),NodeFilter.SHOW_TEXT);
  let n; while(n=walker.nextNode()){ if(!n.textContent.trim()) continue; const el=n.parentElement;
    if(el.closest('.wm')) continue;
    const r=document.createRange(); r.selectNodeContents(n); for(const b of r.getClientRects()){
      if(b.width<1) continue; out.push({t:n.textContent.trim().slice(0,40),c:getComputedStyle(el).color,
      role:el.className||el.tagName,x:b.x,y:b.y,w:b.width,h:b.height});}}
  return out;}"""

GEOM_JS = """() => { const q=s=>[...document.querySelectorAll(s)].map(e=>{const b=e.getBoundingClientRect();
  return {sel:s,text:(e.textContent||'').trim().slice(0,30),x:+b.left.toFixed(1),y:+b.top.toFixed(1),w:+b.width.toFixed(1),h:+b.height.toFixed(1)}});
  const digits=[...'0123456789'].map(d=>{const s=document.createElement('span');s.className='p';s.textContent=d;
    s.style.display='inline-block';s.style.position='absolute';document.querySelector('.it').appendChild(s);const w=s.getBoundingClientRect().width;s.remove();return +w.toFixed(2)});
  return {page:q('.page')[0],disc:q('.disc')[0],terrace:q('.terrace')[0],wordmark:q('.wm.ink span')[0],sub:q('.sub')[0],
    columns:q('.col'),section_heads:q('h2'),sub_heads:q('h3'),items:q('.it'),tagline:q('.tag')[0],digit_widths:digits,
    text_ext:(()=>{let x0=1e9,y0=1e9,x1=0,y1=0;document.querySelectorAll('.sub,.col,.tag').forEach(e=>{const b=e.getBoundingClientRect();
      x0=Math.min(x0,b.left);y0=Math.min(y0,b.top);x1=Math.max(x1,b.right);y1=Math.max(y1,b.bottom)});return [x0,y0,x1,y1]})()} }"""


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast_check(page, scale):
    from PIL import Image
    boxes = page.evaluate(CONTRAST_JS)
    page.add_style_tag(content=".page *{color:transparent !important}")
    img = Image.open(io.BytesIO(page.screenshot(full_page=True))).convert("RGB")
    page.evaluate("() => document.querySelectorAll('style')[1].remove()")
    res = []
    for b in boxes:
        rgb = tuple(int(float(v)) for v in re.findall(r"[\d.]+", b["c"])[:3])
        L1 = lum(rgb)
        x0, y0 = max(0, int(b["x"] * scale)), max(0, int(b["y"] * scale))
        x1, y1 = min(img.width, int((b["x"] + b["w"]) * scale)), min(img.height, int((b["y"] + b["h"]) * scale))
        worst = 99
        for px in set(img.crop((x0, y0, x1, y1)).getdata()):
            L2 = lum(px)
            worst = min(worst, (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05))
        res.append({"text": b["t"], "role": b["role"], "min": round(worst, 2)})
    res.sort(key=lambda r: r["min"])
    return res


def main():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    doc = build()
    (HERE / "menu.html").write_text(doc.replace("{BODYCLASS}", "letter").replace("{TERRACE}", TERRACES["letter"]))
    report, layout = {}, {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")))
        for name, cls, w, h, dsf in [("preview-letter.png", "letter", 816, 1056, 3.125),
                                     ("preview-phone.png", "phone", 390, 844, 3)]:
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            tmp = HERE / f".render-{cls}.html"
            tmp.write_text(doc.replace("{BODYCLASS}", cls).replace("{TERRACE}", TERRACES[cls]))
            pg.goto(tmp.as_uri())
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(400)
            if cls == "phone":  # page height = content + room for tagline and terrace
                bottom = pg.evaluate("() => document.querySelector('.cols').getBoundingClientRect().bottom")
                pg.evaluate(f"() => document.querySelector('.page').style.setProperty('--ph', '{int(bottom + 190)}px')")
            layout[name] = pg.evaluate(GEOM_JS)
            pg.screenshot(path=str(HERE / name), full_page=True,
                          clip=None if cls == "phone" else {"x": 0, "y": 0, "width": 816, "height": 1056})
            report[name] = contrast_check(pg, dsf)
            tmp.unlink()
            pg.close()
        b.close()
    (HERE / "contrast.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (HERE / "layout.json").write_text(json.dumps(layout, indent=1, ensure_ascii=False))
    for k, v in report.items():
        print(k, "worst:", v[:3])
    for k, v in layout.items():
        print(k, "text extent:", v["text_ext"], "digits:", sorted(set(v["digit_widths"])))


if __name__ == "__main__":
    main()
