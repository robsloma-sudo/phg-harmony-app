#!/usr/bin/env python3
"""TEST-1 explore-J "Horizon".

One flat horizon splits the page: a posterised dusk field (indigo / plum / thin amber, hard edges)
carries the only display word; below it, on paper, one centred reading column (cocktails) and a
quiet three-up row (beer + cider / wine / spirits).

Every item, price and description comes from ../build/draft_doc.json (see TEXT below; nothing invented).
Usage: python3 build.py [before|after]     (default: after = the subtracted version)
Outputs: menu.html, preview-letter.png (2550x3300), preview-phone.png (1170 wide), contrast.json, geometry.json
"""
import json, sys, html, io, re, os, glob
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFT = json.load(open(HERE.parent / "build" / "draft_doc.json"))
FONTS = (HERE.parent / "build" / "fonts").as_uri()
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "after"
esc = html.escape

# ---- palette -------------------------------------------------------------------------------
INDIGO, PLUM, AMBER = "#1E2147", "#5A2B4F", "#D98A2E"   # dusk inks: field only (+ indigo heads)
PAPER, INK, MUTED = "#F4EDE1", "#221C22", "#5B5058"

# ---- content --------------------------------------------------------------------------------
# Descriptions: ingredient-first, built only from components (cocktails) or the existing desc.
# Echoes of the item name are removed; if nothing but the echo remains, the description is dropped.
DESC = {
    # Manhattan: aromatic bitters hidden (meta.public_components['aromatic-bitters'] = false)
    "beta_manhattan": "Rye whiskey · sweet vermouth · cocktail cherry",
    "beta_margarita": "Tequila blanco · fresh lime juice · orange liqueur · agave syrup",
    "beta_daiquiri": "White rum · fresh lime juice · demerara syrup",
    # house_recipe = false -> ingredient names only (no quantities anywhere on this menu anyway)
    "beta_old_fashioned": "Brown butter-washed bourbon · demerara syrup · aromatic bitters",
    "beta_czech_pilsner": "Crisp pale lager",            # draft desc "Crisp pale lager."
    "beta_dry_hopped_ipa": "Hop-forward",                 # "Hop-forward draft IPA." minus name echo
    "beta_amber_lager": "Toasty",                         # "Toasty amber lager." minus name echo
    "beta_malbec": "Dry red wine",                        # "Dry red wine."
    "beta_pinot_grigio": "Dry white wine",                # "Dry white wine."
    "beta_brut_rose": "Dry sparkling",                    # "Dry sparkling rosé." minus name echo
    "beta_blanco_tequila": None,                          # "Blanco tequila pour." = pure echo -> dropped
    "beta_anejo_tequila": None,                           # "Añejo tequila pour." = pure echo -> dropped
    "beta_cognac_vsop": None,                             # "VSOP Cognac pour." = pure echo -> dropped
    "beta_dry_cider": "Sparkling",                        # "Dry sparkling cider." minus name echo
}


def price(it):
    v = it["prices"][0]["value"]
    return str(int(v)) if float(v).is_integer() else f"{v:.2f}"


SEC = {s["id"]: s for s in DRAFT["sections"]}
count = sum(len(sb["items"]) for s in DRAFT["sections"] for sb in s["subs"]) + sum(len(s["items"]) for s in DRAFT["sections"])
assert count == 14 and set(DESC) == {it["id"] for s in DRAFT["sections"] for sb in s["subs"] for it in sb["items"]} | {it["id"] for s in DRAFT["sections"] for it in s["items"]}


def item_html(it):
    d = DESC[it["id"]]
    dh = f'<div class="ds">{esc(d)}</div>' if d else ""
    return (f'<div class="it" data-id="{it["id"]}"><div class="nm"><span class="n">{esc(it["name"])}</span>'
            f'<span class="p">{price(it)}</span></div>{dh}</div>')


def section_html(sec, head=None, show_subs=True, cls="sec"):
    out = [f'<section class="{cls}" id="{sec["id"]}"><h2>{esc(head or sec["name"])}</h2>']
    for sb in sec["subs"]:
        if show_subs:
            out.append(f'<h3>{esc(sb["name"])}</h3>')
        out += [item_html(it) for it in sb["items"]]
    out += [item_html(it) for it in sec["items"]]
    out.append("</section>")
    return "".join(out)


def build():
    before = VARIANT == "before"
    cocktails = section_html(SEC["sec_cocktails"], cls="sec main")
    # Beer has a single sub (Draft): merged into the head "Draft Beer" (every item stays in its group).
    beer = section_html(SEC["sec_beer"], head="Draft Beer", show_subs=False)
    cider = section_html(SEC["sec_cider"])
    wine = section_html(SEC["sec_wine"])
    spirits = section_html(SEC["sec_spirits"])
    extras_css = ""
    rule_main = tagline = ""
    if before:
        rule_main = '<div class="tierrule"></div>'
        tagline = '<div class="tag">Good drinks · good company</div>'
        extras_css = f"""
        .main h2::after{{content:"";display:block;width:34px;height:1.5px;background:{AMBER};margin:9px auto 0}}
        .tierrule{{width:120px;height:1px;background:{INDIGO};opacity:.55;margin:0 auto}}
        .row .col+.col{{border-left:1px solid rgba(30,33,71,.25)}}
        .tag{{font:500 10.5px/1 Dm;letter-spacing:.32em;text-transform:uppercase;color:{MUTED};text-align:center;margin-top:14px}}
        """
    GEOM = ("--b1:214px;--b2:78px;--b3:25px;--mt:62px;--rt:363px" if before
            else "--b1:236px;--b2:50px;--b3:17px;--mt:74px;--rt:352px")
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Cantina — bar menu (explore-J Horizon)</title>
<style>
@font-face{{font-family:Fr;font-weight:400 900;src:url({FONTS}/fraunces.woff2) format("woff2")}}
@font-face{{font-family:Fr;font-style:italic;font-weight:400 700;src:url({FONTS}/fraunces-i.woff2) format("woff2")}}
@font-face{{font-family:Dm;font-weight:400 800;src:url({FONTS}/dmsans.woff2) format("woff2")}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{PAPER}}}
.page{{position:relative;background:{PAPER};color:{INK};overflow:hidden}}
/* ART layer: three posterised dusk bands, hard edges, no gradient. Print: field bleeds 3 mm past trim. */
.field{{position:absolute;left:0;right:0;top:0}}
.b1{{background:{INDIGO}}} .b2{{background:{PLUM}}} .b3{{background:{AMBER}}}
.field div{{width:100%}}
.mast{{position:absolute;left:0;right:0;text-align:center;color:{PAPER}}}
.wm{{font:420 var(--wm)/1 Fr;letter-spacing:.2em;margin-right:-.2em;font-variation-settings:"opsz" 144,"SOFT" 0,"WONK" 0}}
.sub{{font:400 var(--subsz)/1 Dm;letter-spacing:.24em;margin-top:var(--subgap);margin-right:-.24em;color:#E9E1D6}}
/* TEXT layer */
.read{{position:absolute;left:var(--mx);right:var(--mx);display:flex;flex-direction:column;justify-content:space-between}}
h2{{font:600 var(--h2)/1 Dm;letter-spacing:.3em;margin-right:-.3em;text-transform:uppercase;color:{INDIGO};text-align:center;margin-bottom:var(--h2gap)}}
h3{{font:italic 400 var(--h3)/1 Fr;color:{MUTED};text-align:center;margin:var(--h3top) 0 var(--h3gap)}}
h2+h3{{margin-top:0}}
.it{{text-align:center;margin-bottom:var(--itgap)}}
.nm{{font:500 var(--nm)/1.2 Fr;font-variation-settings:"opsz" 18;color:{INK};font-variant-numeric:lining-nums tabular-nums}}
.nm .p{{margin-left:.62em}}
.ds{{font:400 var(--ds)/1.3 Dm;color:{MUTED};margin-top:var(--dsgap)}}
.row{{display:grid;grid-template-columns:1fr 1fr 1fr;align-items:start}}
.col{{padding:0 10px}}
.col .sec+.sec{{margin-top:var(--secgap)}}
.it:last-child{{margin-bottom:0}}
{extras_css}
body.letter .page{{width:816px;height:1056px;
  --wm:104px;--subsz:12.5px;--subgap:22px;--mx:72px;--h2:12.5px;--h2gap:16px;--h3:15px;--h3top:20px;--h3gap:11px;
  --nm:18.5px;--ds:13px;--dsgap:4px;--itgap:15px;--secgap:30px;{GEOM}}}
body.letter .b1{{height:var(--b1)}} body.letter .b2{{height:var(--b2)}} body.letter .b3{{height:var(--b3)}}
body.letter .mast{{top:var(--mt)}}
body.letter .read{{top:var(--rt);bottom:52px}}
body.letter .main{{width:520px;margin:0 auto}}
body.phone .page{{width:390px;
  --wm:52px;--subsz:10.5px;--subgap:14px;--mx:28px;--h2:12px;--h2gap:14px;--h3:14.5px;--h3top:18px;--h3gap:10px;
  --nm:17.5px;--ds:13px;--dsgap:3px;--itgap:15px;--secgap:40px}}
body.phone .b1{{height:150px}} body.phone .b2{{height:46px}} body.phone .b3{{height:15px}}
body.phone .mast{{top:48px}}
body.phone .read{{position:relative;left:auto;right:auto;padding:44px var(--mx) 56px;display:block}}
body.phone .field{{position:relative}}
body.phone .row{{display:block;margin-top:40px}}
body.phone .col{{padding:0}} body.phone .col+.col{{margin-top:40px;border:0!important}}
body.phone .tierrule{{margin-top:40px}}
</style></head><body class="{{BODYCLASS}}"><div class="page">
<div class="field" aria-hidden="true"><div class="b1"></div><div class="b2"></div><div class="b3"></div></div>
<header class="mast"><div class="wm">CANTINA</div><div class="sub">&amp; cocktail bar · Iowa City, Iowa</div></header>
<main class="read">
{cocktails}
{rule_main}
<div class="row"><div class="col">{beer}{cider}</div><div class="col">{wine}</div><div class="col">{spirits}</div></div>
{tagline}
</main></div></body></html>"""


# ---- contrast: worst pixel behind every text run -------------------------------------------
CONTRAST_JS = """() => { const out=[]; const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 let n; while(n=w.nextNode()){ if(!n.textContent.trim()) continue; const el=n.parentElement;
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
    page.add_style_tag(content="*{color:revert}")
    res = []
    for b in boxes:
        rgb = tuple(int(float(v)) for v in re.findall(r"[\d.]+", b["c"])[:3])
        x0, y0 = int(b["x"] * scale), int(b["y"] * scale)
        x1, y1 = int((b["x"] + b["w"]) * scale), int((b["y"] + b["h"]) * scale)
        px = set(img.crop((x0, y0, max(x0 + 1, x1), max(y0 + 1, y1))).resize((40, 10)).getdata())
        L1 = rl(rgb)
        worst = min((max(L1, rl(p)) + .05) / (min(L1, rl(p)) + .05) for p in px)
        res.append({"text": b["t"], "role": b["role"], "font_px_css": b["fs"],
                    "print_pt": round(b["fs"] * 0.75, 2), "min_contrast": round(worst, 2),
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
            geom[name] = pg.evaluate("""() => { const q=s=>[...document.querySelectorAll(s)].map(e=>{const r=e.getBoundingClientRect();
              return {el:(e.id||e.className||e.tagName), text:(e.innerText||'').split('\\n')[0].slice(0,40), x:+r.left.toFixed(1), y:+r.top.toFixed(1), w:+r.width.toFixed(1), h:+r.height.toFixed(1)}});
              const pgb=document.querySelector('.page').getBoundingClientRect();
              return {page:[pgb.width,pgb.height], field:q('.field > div'), mast:q('.mast,.wm,.sub'), sections:q('section'), heads:q('h2,h3'), items:q('.it'), columns:q('.col,.main')} }""")
            pg.screenshot(path=str(HERE / name), full_page=(cls == "phone"))
            report[name] = contrast(pg, dsf)
            pg.close()
        b.close()
    (HERE / "contrast.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (HERE / "geometry.json").write_text(json.dumps(geom, indent=1, ensure_ascii=False))
    for k, v in report.items():
        worst = sorted(v, key=lambda r: r["min_contrast"])[:3]
        small = sorted(v, key=lambda r: r["font_px_css"])[:2]
        print(k, "worst contrast:", [(r["text"], r["min_contrast"]) for r in worst], "smallest:", [(r["text"], r["print_pt"]) for r in small])


if __name__ == "__main__":
    main()
