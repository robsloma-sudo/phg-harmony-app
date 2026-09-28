#!/usr/bin/env python3
"""TEST-1 explore-J2 "Horizon" (round 2; explore-J is the checkpoint).

The dusk field is now two flat inks (indigo sky, amber horizon glow) broken by ONE flat plum silhouette:
an adobe stepped parapet (Mexico) that climbs, step by step, into an Iowa grain elevator (headhouse + silos)
bleeding off the right edge. The stair also descends below the horizon, pointing into the Cocktails column.

Content: ../build/draft_doc.json (names, prices, desc, components) + garnish from phg.recipe_versions
(as cited in ../round-17/proposal.md). Nothing invented.
Usage: python3 build.py [before|after]
"""
import json, sys, html, io, re, os, glob
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFT = json.load(open(HERE.parent / "build" / "draft_doc.json"))
FONTS = (HERE.parent / "build" / "fonts").as_uri()
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "after"
BEFORE = VARIANT == "before"
esc = html.escape

INDIGO, PLUM, AMBER = "#1E2147", "#5A2B4F", "#D98A2E"   # dusk inks: field + silhouette only
AMBER_INK = "#8F4F10"                                     # amber darkened: section heads only (5.5:1 on paper)
PAPER, INK, MUTED = "#F4EDE1", "#221C22", "#5B5058"

# ---- content --------------------------------------------------------------------------------------------------
# Cocktails: full component names (hidden components omitted) + garnish from phg.recipe_versions.
# Everything else: the draft's full desc text (trailing period dropped).
DESC = {
    "beta_margarita": ["Tequila blanco · fresh lime juice · orange liqueur · agave syrup · lime wheel",
                       "Bright and citrus-forward"],          # rv f06abb74 garnish; draft desc sentence 2
    "beta_manhattan": ["Rye whiskey · sweet vermouth · cocktail cherry"],   # bitters hidden; rv 9fb77eaa garnish
    "beta_daiquiri": ["White rum · fresh lime juice · demerara syrup · lime coin"],          # rv 14d45e57
    "beta_old_fashioned": ["Brown butter-washed bourbon · demerara syrup · aromatic bitters · orange peel"],  # rv 7095fd3d
    "beta_czech_pilsner": ["Crisp pale lager"],
    "beta_dry_hopped_ipa": ["Hop-forward draft IPA"],
    "beta_amber_lager": ["Toasty amber lager"],
    "beta_malbec": ["Dry red wine"],
    "beta_pinot_grigio": ["Dry white wine"],
    "beta_brut_rose": ["Dry sparkling rosé"],
    "beta_blanco_tequila": ["Blanco tequila pour"],
    "beta_anejo_tequila": ["Añejo tequila pour"],
    "beta_cognac_vsop": ["VSOP Cognac pour"],
    "beta_dry_cider": ["Dry sparkling cider"],
}
ORDER_FIRST = {"sub_cocktails_classics": ["beta_margarita", "beta_manhattan"]}   # Margarita first

SEC = {s["id"]: s for s in DRAFT["sections"]}
ALL_IDS = {it["id"] for s in DRAFT["sections"] for sb in s["subs"] for it in sb["items"]} | \
          {it["id"] for s in DRAFT["sections"] for it in s["items"]}
assert len(ALL_IDS) == 14 and set(DESC) == ALL_IDS


def price(it):
    v = it["prices"][0]["value"]
    return str(int(v)) if float(v).is_integer() else f"{v:.2f}"


def item_html(it):
    ds = "".join(f'<div class="ds">{esc(d)}</div>' for d in DESC[it["id"]])
    return (f'<div class="it" data-id="{it["id"]}"><div class="nm"><span class="n">{esc(it["name"])}</span>'
            f'<span class="p">{price(it)}</span></div>{ds}</div>')


def section_html(sec, head=None, show_subs=True, cls="sec"):
    out = [f'<section class="{cls}" id="{sec["id"]}"><h2>{esc(head or sec["name"])}</h2>']
    for sb in sec["subs"]:
        items = sb["items"]
        if sb["id"] in ORDER_FIRST:
            items = sorted(items, key=lambda i: ORDER_FIRST[sb["id"]].index(i["id"]))
        if show_subs:
            out.append(f'<h3>{esc(sb["name"])}</h3>')
        out += [item_html(it) for it in items]
    out += [item_html(it) for it in sec["items"]]
    out.append("</section>")
    return "".join(out)


# ---- ART layer: the silhouette (text-free SVG, one flat ink) ----------------------------------------------------
def silhouette(W, Hz, s, x0, crown=True, cupola=True, bleed=12):
    """One skyline, left to right, standing on the horizon:
    adobe block whose left edge descends in parapet steps toward the Cocktails column (x0 = lowest step),
    a stepped adobe crown (escalonado parapet), then the same wall line rising into an Iowa grain-elevator
    headhouse (with a cupola) and a run of domed silos bleeding off the right edge. s = scale."""
    u = lambda v: v * s
    pts = [(x0, Hz)]
    x, y = x0, Hz
    for _ in range(3):                       # descending parapet steps (the pointer)
        y -= u(14); pts.append((x, y)); x += u(22); pts.append((x, y))
    roof = y                                 # adobe roof line
    if crown:                                # stepped crown centred on the adobe facade
        cx = x + u(40)
        pts.append((cx, roof))
        for _ in range(3):
            y -= u(10); pts.append((cx, y)); cx += u(12); pts.append((cx, y))
        cx += u(14); pts.append((cx, y))
        for _ in range(3):
            y += u(10); cx_ = cx; pts.append((cx_, y)); cx += u(12); pts.append((cx, y))
        x = cx
    hx = x + u(40)                           # headhouse
    hw, htop = u(60), u(34)
    pts += [(hx, roof), (hx, htop)]
    if cupola:
        c0 = hx + u(16)
        pts += [(c0, htop), (c0, htop - u(20)), (c0 + u(28), htop - u(20)), (c0 + u(28), htop)]
    pts += [(hx + hw, htop)]
    silo_top = u(104)
    pts.append((hx + hw, silo_top))
    d = "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts)
    sx, n = hx + hw, 3
    sw = (W + bleed - sx) / n
    for _ in range(n):
        d += f" A{sw/2:.1f},{sw*0.28:.1f} 0 0 1 {sx + sw:.1f},{silo_top:.1f}"
        sx += sw
    d += f" L{W + bleed:.1f},{Hz:.1f} Z"
    return d, ""


def field_svg(W, H_field, Hz, amber_top, sil, extra_below):
    d, vg = sil
    return (f'<svg class="art" width="{W}" height="{H_field + extra_below}" viewBox="0 0 {W} {H_field + extra_below}" '
            f'aria-hidden="true" style="position:absolute;left:0;top:0;overflow:visible">'
            f'<rect x="-12" y="-12" width="{W + 24}" height="{amber_top + 12}" fill="{INDIGO}"/>'
            f'<rect x="-12" y="{amber_top}" width="{W + 24}" height="{Hz - amber_top}" fill="{AMBER}"/>'
            f'<path d="{d}" fill="{PLUM}"/>{vg}</svg>')


def build():
    # letter geometry (css px; 816 x 1056)
    L = dict(W=816, Hz=300, amber=176)
    CROWN = os.environ.get("J2_CROWN", "1") == "1"      # ablation switches
    CUPOLA = os.environ.get("J2_CUPOLA", "1" if BEFORE else "0") == "1"
    L_sil = silhouette(W=816, Hz=300, s=1.0, x0=430, crown=CROWN, cupola=CUPOLA)
    P_sil = silhouette(W=390, Hz=212, s=0.62, x0=196, crown=CROWN, cupola=CUPOLA)
    letter_art = field_svg(816, 300, 300, 224, L_sil, 0)
    phone_art = field_svg(390, 212, 212, 164, P_sil, 0)

    cocktails = section_html(SEC["sec_cocktails"], cls="sec main")
    spirits = section_html(SEC["sec_spirits"])
    wine = section_html(SEC["sec_wine"])
    beer = section_html(SEC["sec_beer"], head="Draft Beer", show_subs=False)   # single sub "Draft" merged
    cider = section_html(SEC["sec_cider"])
    before_css = ""
    if BEFORE:
        before_css = f""".main h3::before,.main h3::after{{content:"—";margin:0 .5em;color:{AMBER_INK}}}
        .row{{border-top:1px solid rgba(34,28,34,.18);padding-top:28px}}"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Cantina — bar menu (explore-J2 Horizon)</title>
<style>
@font-face{{font-family:Fr;font-weight:400 900;src:url({FONTS}/fraunces.woff2) format("woff2")}}
@font-face{{font-family:Fr;font-style:italic;font-weight:400 700;src:url({FONTS}/fraunces-i.woff2) format("woff2")}}
@font-face{{font-family:Dm;font-weight:400 800;src:url({FONTS}/dmsans.woff2) format("woff2")}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{PAPER}}}
.page{{position:relative;background:{PAPER};color:{INK};overflow:hidden}}
.art-l,.art-p{{display:none}}
body.letter .art-l, body.phone .art-p{{display:block}}
.mast{{position:absolute;color:{PAPER}}}
.wm{{font:430 var(--wm)/1 Fr;letter-spacing:.14em;font-variation-settings:"opsz" 144,"SOFT" 0,"WONK" 0}}
.sub{{font:400 var(--subsz)/1 Dm;letter-spacing:.2em;margin-top:var(--subgap);color:#E9E1D6}}
.read{{position:absolute;left:var(--mx);right:var(--mx);display:flex;flex-direction:column;justify-content:space-between}}
h2{{font:600 var(--h2)/16px Dm;letter-spacing:.3em;text-transform:uppercase;color:{AMBER_INK};margin-bottom:var(--h2gap)}}
h3{{font:italic 400 var(--h3)/24px Fr;color:{MUTED};margin:var(--h3top) 0 4px}}
h2+h3{{margin-top:0}}
.it{{margin-bottom:var(--itgap)}}
.it:last-child{{margin-bottom:0}}
.nm{{font:500 var(--nm)/24px Fr;font-variation-settings:"opsz" 18;color:{INK};font-variant-numeric:lining-nums tabular-nums}}
.nm .p{{font-weight:400;color:{MUTED};margin-left:1em}}
.ds{{font:400 var(--ds)/16px Dm;color:{MUTED}}}
.main{{text-align:center}}
.main h2{{margin-right:-.3em}}
.row{{display:grid;grid-template-columns:repeat(3,1fr);column-gap:var(--gut);align-items:start}}
.col .sec+.sec{{margin-top:var(--secgap)}}
{before_css}
body.letter .page{{width:816px;height:1056px;
  --wm:92px;--subsz:12.5px;--subgap:20px;--mx:72px;--h2:12.5px;--h2gap:16px;--h3:15px;--h3top:16px;
  --nm:18.5px;--ds:13px;--itgap:16px;--secgap:24px;--gut:40px}}
body.letter .mast{{left:68px;top:74px}}
body.letter .read{{top:372px;bottom:52px}}
body.letter .main{{width:600px;margin:0 auto}}
body.phone .page{{width:390px;
  --wm:44px;--subsz:10.5px;--subgap:12px;--mx:28px;--h2:12px;--h2gap:14px;--h3:14.5px;--h3top:14px;
  --nm:17.5px;--ds:13px;--itgap:14px;--secgap:40px;--gut:0px}}
body.phone .art-p{{position:relative;height:212px}}
body.phone .mast{{left:26px;top:40px}}
body.phone .read{{position:relative;left:auto;right:auto;padding:68px var(--mx) 56px;display:block}}
body.phone .row{{display:block;margin-top:48px}}
body.phone .col+.col{{margin-top:40px}}
</style></head><body class="{{BODYCLASS}}"><div class="page">
<div class="art-l">{letter_art}</div><div class="art-p">{phone_art}</div>
<header class="mast"><div class="wm">CANTINA</div><div class="sub">&amp; cocktail bar · Iowa City, Iowa</div></header>
<main class="read">
{cocktails}
<div class="row"><div class="col">{spirits}</div><div class="col">{wine}</div><div class="col">{beer}{cider}</div></div>
</main></div></body></html>"""


CONTRAST_JS = """() => { const out=[]; const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 let n; while(n=w.nextNode()){ if(!n.textContent.trim()) continue; const el=n.parentElement;
  if(el.closest('style,title')) continue;
  const r=document.createRange(); r.selectNodeContents(n); for(const b of r.getClientRects()){ if(b.width<1) continue;
   const cs=getComputedStyle(el); out.push({t:n.textContent.trim().slice(0,48),c:cs.color,fs:parseFloat(cs.fontSize),
   role:el.className||el.tagName,x:b.x,y:b.y,w:b.width,h:b.height});}} return out;}"""


def rl(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast(page, scale):
    from PIL import Image
    boxes = page.evaluate(CONTRAST_JS)
    page.add_style_tag(content="*{color:transparent!important}")
    img = Image.open(io.BytesIO(page.screenshot(full_page=True))).convert("RGB")
    res = []
    for b in boxes:
        rgb = tuple(int(float(v)) for v in re.findall(r"[\d.]+", b["c"])[:3])
        x0, y0 = int(b["x"] * scale), int(b["y"] * scale)
        x1, y1 = int((b["x"] + b["w"]) * scale), int((b["y"] + b["h"]) * scale)
        px = set(img.crop((x0, y0, max(x0 + 1, x1), max(y0 + 1, y1))).resize((60, 12)).get_flattened_data()
                 if hasattr(Image.Image, "get_flattened_data") else
                 img.crop((x0, y0, max(x0 + 1, x1), max(y0 + 1, y1))).resize((60, 12)).getdata())
        L1 = rl(rgb)
        worst = min((max(L1, rl(p)) + .05) / (min(L1, rl(p)) + .05) for p in px)
        res.append({"text": b["t"], "role": b["role"], "font_px_css": b["fs"], "print_pt": round(b["fs"] * 0.75, 2),
                    "min_contrast": round(worst, 2),
                    "box_css": [round(b["x"], 1), round(b["y"], 1), round(b["w"], 1), round(b["h"], 1)]})
    return res


def main():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    doc = build()
    (HERE / "menu.html").write_text(doc.replace("{BODYCLASS}", "letter"))
    report, geom = {}, {}
    exe = next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"), None)
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        for name, cls, w, h, dsf in [("preview-letter.png", "letter", 816, 1056, 3.125),
                                     ("preview-phone.png", "phone", 390, 900, 3)]:
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            tmp = HERE / f".render-{cls}.html"
            tmp.write_text(doc.replace("{BODYCLASS}", cls))
            pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(600); tmp.unlink()
            geom[name] = pg.evaluate("""() => { const q=s=>[...document.querySelectorAll(s)].filter(e=>e.offsetParent!==null||e.tagName==='svg').map(e=>{const r=e.getBoundingClientRect();
              return {el:(e.id||(typeof e.className==='string'?e.className:'')||e.tagName), text:(e.innerText||'').split('\\n')[0].slice(0,40), x:+r.left.toFixed(1), y:+r.top.toFixed(1), w:+r.width.toFixed(1), h:+r.height.toFixed(1)}});
              const pgb=document.querySelector('.page').getBoundingClientRect();
              return {page:[pgb.width,pgb.height], mast:q('.wm,.sub'), sections:q('section'), heads:q('h2,h3'), items:q('.it'), prices:q('.p'), columns:q('.col,.main')} }""")
            pg.screenshot(path=str(HERE / name), full_page=(cls == "phone"))
            report[name] = contrast(pg, dsf)
            pg.close()
        b.close()
    (HERE / "contrast.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (HERE / "geometry.json").write_text(json.dumps(geom, indent=1, ensure_ascii=False))
    for k, v in report.items():
        worst = sorted(v, key=lambda r: r["min_contrast"])[:3]
        small = sorted(v, key=lambda r: r["font_px_css"])[:2]
        print(k, "worst:", [(r["text"], r["min_contrast"]) for r in worst], "smallest:", [(r["text"], r["print_pt"]) for r in small])


if __name__ == "__main__":
    main()
