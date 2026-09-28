#!/usr/bin/env python3
"""TEST-1 explore-J3 "Horizon", round 3 (checkpoints: ../explore-J, ../explore-J2).

ART (text-free inline SVG, flat screen-print inks): an indigo dusk sky, a thin amber horizon glow, a stepped
(escalonado) amber glow rising behind the right edge, and in front of it one plum Iowa grain elevator
(headhouse + gallery + bin cluster) standing on the page bottom and running up the right trim, through the
reading area and across the horizon. Materiality: a two-pass misregistration (indigo underprint offset) and a
paper tooth, both clipped to the art shapes only (never under reading text).
TEXT: one flush-left grid. CANTINA and its sub-line, Cocktails and the three lower columns share the left text edge.

Content: ../build/draft_doc.json + garnish from phg.recipe_versions (cited in ../round-17/proposal.md). Nothing invented.
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
NB = " "

INDIGO, PLUM, AMBER = "#1E2147", "#5A2B4F", "#D98A2E"
AMBER_INK = "#8F4F10"     # section heads only (5.5:1 on paper)
PRICE_INK = PLUM          # prices: plum dusk ink, distinct from the muted description ink (9.4:1 on paper)
PAPER, INK, MUTED = "#F4EDE1", "#221C22", "#5B5058"


def ingr(*parts):
    """Ingredient line: non-breaking spaces inside each multi-word ingredient, breaks only after the middots."""
    return " · ".join(p.replace(" ", NB) for p in parts)


DESC = {
    "beta_margarita": ingr("Tequila blanco", "fresh lime juice", "orange liqueur", "agave syrup", "lime wheel")
                      + ". \x00Bright and citrus-forward\x01",   # \x00..\x01 = kept together (nowrap)                                    # rv f06abb74 + draft desc
    "beta_manhattan": ingr("Rye whiskey", "sweet vermouth", "cocktail cherry"),         # bitters hidden; rv 9fb77eaa
    "beta_daiquiri": ingr("White rum", "fresh lime juice", "demerara syrup", "lime coin"),            # rv 14d45e57
    "beta_old_fashioned": ingr("Brown butter-washed bourbon", "demerara syrup", "aromatic bitters", "orange peel"),  # rv 7095fd3d
    "beta_czech_pilsner": "Crisp pale lager",
    "beta_dry_hopped_ipa": "Hop-forward draft IPA",
    "beta_amber_lager": "Toasty amber lager",
    "beta_malbec": "Dry red wine",
    "beta_pinot_grigio": "Dry white wine",
    "beta_brut_rose": "Dry sparkling rosé",
    "beta_blanco_tequila": "Blanco tequila pour",
    "beta_anejo_tequila": "Añejo tequila pour",
    "beta_cognac_vsop": "VSOP Cognac pour",
    "beta_dry_cider": "Dry sparkling cider",
}
ORDER_FIRST = {"sub_cocktails_classics": ["beta_margarita", "beta_manhattan"]}
SEC = {s["id"]: s for s in DRAFT["sections"]}
ALL_IDS = {it["id"] for s in DRAFT["sections"] for sb in s["subs"] for it in sb["items"]} | \
          {it["id"] for s in DRAFT["sections"] for it in s["items"]}
assert len(ALL_IDS) == 14 and set(DESC) == ALL_IDS


def price(it):
    v = it["prices"][0]["value"]
    return str(int(v)) if float(v).is_integer() else f"{v:.2f}"


def dtext(i):
    return esc(DESC[i]).replace(chr(0), '<span class="nw">').replace(chr(1), "</span>")


def item_html(it):
    return (f'<div class="it" data-id="{it["id"]}"><div class="nm"><span class="n">{esc(it["name"])}</span>'
            f'{NB}<span class="p">{price(it)}</span></div><div class="ds">{dtext(it["id"])}</div></div>')


def section_html(sec, head=None, show_subs=True, cls="sec"):
    out = [f'<section class="{cls}" id="{sec["id"]}"><h2>{esc(head or sec["name"])}</h2>']
    for sb in sec["subs"]:
        items = sb["items"]
        if sb["id"] in ORDER_FIRST:
            items = sorted(items, key=lambda i: ORDER_FIRST[sb["id"]].index(i["id"]))
        out.append('<div class="grp">' + (f'<h3>{esc(sb["name"])}</h3>' if show_subs else "")
                   + "".join(item_html(it) for it in items) + "</div>")
    if sec["items"]:
        out.append('<div class="grp">' + "".join(item_html(it) for it in sec["items"]) + "</div>")
    out.append("</section>")
    return "".join(out)


# ---- ART ---------------------------------------------------------------------------------------------------------
def art_svg(W, H, Hz, s, ex, band, tooth=True, offset=True, glow_band=True, gallery_windows=True, spout=True, hh_window=True, tag="l"):
    """W,H page; Hz horizon; s scale; ex = elevator left edge (headhouse). Everything bleeds 12 px past trim."""
    u = lambda v: v * s
    B = 12
    # stepped amber glow behind the elevator: rises from the horizon in escalonado steps to bleed off the top
    gx = ex - u(96)
    steps = 7
    rise = (Hz + B) / steps
    run = u(20)
    pts = [(gx, Hz)]
    x, y = gx, Hz
    for _ in range(steps):
        y -= rise; pts.append((x, y)); x += run; pts.append((x, y))
    pts += [(W + B, y), (W + B, Hz)]
    glow = "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + " Z"
    # elevator (one flat ink): gabled headhouse, loading spout, windowed gallery, bin cluster to the page bottom.
    hw = u(58)
    hh_top = u(58)
    gal_y, gal_h = u(128), u(22)
    bins_x = ex + hw
    bins_top = gal_y + gal_h
    nb = 3
    gap = u(7)
    bw = (W + B - bins_x) / nb
    shapes = [f'<rect x="{ex:.1f}" y="{hh_top:.1f}" width="{hw:.1f}" height="{H + B - hh_top:.1f}"/>',
              f'<path d="M{ex - u(4):.1f},{hh_top + 1:.1f} L{ex + hw / 2:.1f},{hh_top - u(30):.1f} L{ex + hw + u(4):.1f},{hh_top + 1:.1f} Z"/>',
              f'<rect x="{ex + hw - 1:.1f}" y="{gal_y:.1f}" width="{W + B - ex - hw + 1:.1f}" height="{gal_h:.1f}"/>']
    if spout:
        sx0, sy0, sx1, sy1 = ex + 1, gal_y + u(34), ex - u(78), Hz
        shapes.append(f'<path d="M{sx0:.1f},{sy0:.1f} L{sx1:.1f},{sy1:.1f} L{sx1 + u(7):.1f},{sy1:.1f} L{sx0:.1f},{sy0 + u(9):.1f} Z"/>')
    for i in range(nb):
        bx = bins_x + i * bw + gap
        shapes.append(f'<rect x="{bx:.1f}" y="{bins_top - 1:.1f}" width="{bw - gap:.1f}" height="{H + B - bins_top:.1f}"/>')
    elev = "".join(shapes)
    # cut-outs (negative space, background shows through): gallery windows + headhouse slits
    holes = ""
    if gallery_windows:
        wx = ex + hw + u(10)
        while wx + u(8) < W:
            holes += f'<rect x="{wx:.1f}" y="{gal_y + u(7):.1f}" width="{u(8):.1f}" height="{u(8):.1f}"/>'
            wx += u(18)
    if hh_window:
        holes += f'<rect x="{ex + hw / 2 - u(4):.1f}" y="{hh_top - u(16):.1f}" width="{u(8):.1f}" height="{u(10):.1f}"/>'
    mask = (f'<mask id="m{tag}"><rect x="-20" y="-20" width="{W + 40}" height="{H + 40}" fill="#fff"/>'
            f'<g fill="#000">{holes}</g></mask>')
    tooth_f = (f'<filter id="t{tag}" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" '
               f'baseFrequency="1.6" numOctaves="1" seed="7"/><feColorMatrix type="matrix" values="0 0 0 0 0.96  0 0 0 0 0.93  0 0 0 0 0.88  0 0 0 -2.2 1.25"/></filter>')
    clip = f'<clipPath id="c{tag}"><path d="{glow}"/>{elev}</clipPath>'
    out = [f'<svg class="art" width="{W}" height="{H}" viewBox="0 0 {W} {H}" aria-hidden="true" '
           f'style="position:absolute;left:0;top:0;overflow:visible"><defs>{mask}{tooth_f}{clip}</defs>',
           f'<rect x="{-B}" y="{-B}" width="{W + 2 * B}" height="{Hz + B}" fill="{INDIGO}"/>']
    if glow_band:
        out.append(f'<rect x="{-B}" y="{Hz - band}" width="{W + 2 * B}" height="{band}" fill="{AMBER}"/>')
    out.append(f'<path d="{glow}" fill="{AMBER}"/>')
    if offset:   # second pass misregistered: indigo underprint 3 px down-right of the plum
        out.append(f'<g fill="{INDIGO}" mask="url(#m{tag})" transform="translate({u(3):.1f},{u(3):.1f})">{elev}</g>')
    out.append(f'<g fill="{PLUM}" mask="url(#m{tag})">{elev}</g>')
    if tooth:
        out.append(f'<g clip-path="url(#c{tag})"><rect x="{-B}" y="{-B}" width="{W + 2 * B}" height="{H + 2 * B}" '
                   f'filter="url(#t{tag})" opacity=".22"/></g>')
    out.append("</svg>")
    return "".join(out)


def art_flags():
    """Device switches. 'after' = the subtraction pass (see proposal.md); J3_ABL env removes extra devices for ablation."""
    f = dict(tooth=True, offset=True, glow_band=True, gallery_windows=True, spout=True, hh_window=True)
    if not BEFORE:
        f.update(glow_band=False, tooth=False, hh_window=False, spout=False)
    for k in filter(None, os.environ.get("J3_ABL", "").split(",")):
        f[k] = False
    return f


def build():
    flags = art_flags()
    letter_art = art_svg(816, 1056, 238, 1.0, ex=648, band=14, tag="l", **flags)
    phone_art = art_svg(390, 1, 190, 0.6, ex=340, band=10, tag="p", **flags)
    cocktails = section_html(SEC["sec_cocktails"], cls="sec main")
    spirits = section_html(SEC["sec_spirits"])
    beer = section_html(SEC["sec_beer"], head="Draft Beer", show_subs=False)   # single sub "Draft" merged into head
    cider = section_html(SEC["sec_cider"], cls="sec last")
    wine = section_html(SEC["sec_wine"])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Cantina — bar menu (explore-J3 Horizon)</title>
<style>
@font-face{{font-family:Fr;font-weight:400 900;src:url({FONTS}/fraunces.woff2) format("woff2")}}
@font-face{{font-family:Fr;font-style:italic;font-weight:400 700;src:url({FONTS}/fraunces-i.woff2) format("woff2")}}
@font-face{{font-family:Dm;font-weight:400 800;src:url({FONTS}/dmsans.woff2) format("woff2")}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{PAPER}}}
.page{{position:relative;background:{PAPER};color:{INK};overflow:hidden}}
.art-l,.art-p{{display:none}} body.letter .art-l,body.phone .art-p{{display:block}}
.mast{{position:absolute;left:var(--m);color:{PAPER}}}
.wm{{font:430 var(--wm)/1 Fr;letter-spacing:.14em;margin-left:var(--wmfix);font-variation-settings:"opsz" 144,"SOFT" 0,"WONK" 0}}
.sub{{font:400 var(--subsz)/1 Dm;letter-spacing:.2em;margin-top:var(--subgap);color:#E9E1D6}}
.read{{position:absolute;left:var(--m);width:var(--tw);display:flex;flex-direction:column;justify-content:space-between}}
h2{{font:600 var(--h2)/16px Dm;letter-spacing:.3em;text-transform:uppercase;color:{AMBER_INK};margin-bottom:16px}}
h3{{font:italic 400 var(--h3)/24px Fr;color:{MUTED};margin-bottom:8px}}
.nw{{white-space:nowrap}}
.main .it+.it{{margin-top:20px}} .main .grp+.grp{{margin-top:24px}}
.grp+.grp{{margin-top:16px}}
.it+.it{{margin-top:var(--itgap)}}
.nm{{font:500 var(--nm)/24px Fr;font-variation-settings:"opsz" 18;color:{INK};font-variant-numeric:lining-nums tabular-nums}}
.nm .p{{font-weight:400;color:{PRICE_INK};margin-left:.7em}}
.ds{{font:400 var(--ds)/16px Dm;color:{MUTED}}}
.row{{display:grid;grid-template-columns:repeat(3,1fr);column-gap:var(--gut);align-items:stretch}}
.col{{display:flex;flex-direction:column}}
.col .sec{{display:flex;flex-direction:column;flex:1}}
.col .sec .grp:last-child{{margin-top:auto}}
.col .sec.last{{flex:0;margin-top:32px}}
body.letter .page{{width:816px;height:1056px;
  --m:60px;--tw:560px;--wm:90px;--wmfix:-3px;--subsz:12.5px;--subgap:20px;--h2:12.5px;--h3:15px;
  --nm:17.5px;--ds:13px;--itgap:16px;--gut:20px;--mt:47px}}
body.letter .mast{{top:var(--mt)}}
body.letter .read{{top:290px;bottom:60px}}
body.letter .main .ds{{max-width:560px}}
.nm{{white-space:nowrap}}
body.phone .page{{width:390px;
  --m:24px;--tw:300px;--wm:44px;--wmfix:-1.5px;--subsz:10.5px;--subgap:12px;--h2:12px;--h3:14.5px;
  --nm:17px;--ds:13px;--itgap:14px;--gut:0px}}
body.phone .art-p svg{{height:100%}}
body.phone .art-p{{position:absolute;inset:0}}
body.phone .mast{{top:44px}}
body.phone .read{{position:relative;left:0;padding:238px 0 48px;display:block;margin-left:24px}}
body.phone .nm{{white-space:normal}}
body.phone .row{{display:block;margin-top:44px}}
body.phone .col+.col{{margin-top:40px}}
body.phone .col .sec.last{{margin-top:40px}}
body.phone .col .sec .grp:last-child{{margin-top:16px}}
body.phone .col .sec .grp:first-of-type{{margin-top:0}}
</style></head><body class="{{BODYCLASS}}"><div class="page">
<div class="art-l">{letter_art}</div><div class="art-p">{{PHONEART}}</div>
<header class="mast"><div class="wm">CANTINA</div><div class="sub">&amp; cocktail bar · Iowa City, Iowa</div></header>
<main class="read">
{cocktails}
<div class="row"><div class="col">{spirits}</div><div class="col">{beer}{cider}</div><div class="col">{wine}</div></div>
</main></div></body></html>""", phone_art


CONTRAST_JS = """() => { const out=[]; const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 let n; while(n=w.nextNode()){ if(!n.textContent.trim()) continue; const el=n.parentElement;
  if(el.closest('style,title,svg')) continue;
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
        crop = img.crop((x0, y0, max(x0 + 1, x1), max(y0 + 1, y1)))
        px = set(crop.get_flattened_data() if hasattr(crop, "get_flattened_data") else crop.getdata())
        L1 = rl(rgb)
        worst = min((max(L1, rl(p)) + .05) / (min(L1, rl(p)) + .05) for p in px)
        res.append({"text": b["t"], "role": b["role"], "font_px_css": b["fs"], "print_pt": round(b["fs"] * 0.75, 2),
                    "min_contrast": round(worst, 2),
                    "box_css": [round(b["x"], 1), round(b["y"], 1), round(b["w"], 1), round(b["h"], 1)]})
    return res, img


def ink_bbox(img, box, scale, bg):
    """Glyph ink extent of a text box (pixels differing from its background), in css px."""
    import numpy as np
    x, y, w, h = [int(v * scale) for v in box]
    a = np.asarray(img.crop((x, y, x + w, y + h)).convert("RGB"), dtype=int)
    m = np.abs(a - np.array(bg)).sum(-1) > 60
    ys, xs = np.nonzero(m)
    if not len(xs):
        return None
    return [round((x + xs.min()) / scale, 1), round((y + ys.min()) / scale, 1),
            round((x + xs.max() + 1) / scale, 1), round((y + ys.max() + 1) / scale, 1)]


def main():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    from PIL import Image
    doc, _ = build()
    report, geom = {}, {}
    exe = next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"), None)
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        for name, cls, w, h, dsf in [("preview-letter.png", "letter", 816, 1056, 3.125),
                                     ("preview-phone.png", "phone", 390, 900, 3)]:
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            d = doc.replace("{BODYCLASS}", cls)
            if cls == "phone":
                # phone art is sized to the full scroll height: render once to measure, then rebuild the art
                tmp = HERE / ".render-phone.html"; tmp.write_text(d.replace("{PHONEART}", ""))
                pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
                H = pg.evaluate("document.querySelector('.page').scrollHeight")
                flags = art_flags()
                d = d.replace("{PHONEART}", art_svg(390, H, 190, 0.6, ex=340, band=10, tag="p", **flags))
                pg.evaluate(f"document.querySelector('.page').style.height='{H}px'")
                tmp.write_text(d.replace('<div class="page">', f'<div class="page" style="height:{H}px">'))
            else:
                d = d.replace("{PHONEART}", "")
                (HERE / "menu.html").write_text(d)
                tmp = HERE / ".render-letter.html"; tmp.write_text(d)
            pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(600); tmp.unlink()
            geom[name] = pg.evaluate("""() => { const q=s=>[...document.querySelectorAll(s)].filter(e=>e.offsetParent!==null).map(e=>{const r=e.getBoundingClientRect();
              return {el:(e.id||(typeof e.className==='string'?e.className:'')||e.tagName), text:(e.innerText||'').split('\\n')[0].slice(0,40), x:+r.left.toFixed(1), y:+r.top.toFixed(1), w:+r.width.toFixed(1), h:+r.height.toFixed(1)}});
              const pgb=document.querySelector('.page').getBoundingClientRect();
              return {page:[pgb.width,pgb.height], mast:q('.wm,.sub'), sections:q('section'), heads:q('h2,h3'), items:q('.it'), names:q('.nm .n'), prices:q('.p'), descs:q('.ds'), columns:q('.col,.main')} }""")
            pg.screenshot(path=str(HERE / name), full_page=(cls == "phone"))
            full = Image.open(HERE / name).convert("RGB")
            g = geom[name]
            g["ink"] = {
                "wordmark": ink_bbox(full, [g["mast"][0][k] for k in "xywh"], dsf, (0x1E, 0x21, 0x47)),
                "subline": ink_bbox(full, [g["mast"][1][k] for k in "xywh"], dsf, (0x1E, 0x21, 0x47)),
                "first_head": ink_bbox(full, [g["heads"][0][k] for k in "xywh"], dsf, (0xF4, 0xED, 0xE1)),
                "names_left": min(n["x"] for n in g["names"]),
                "text_right": max(dd["x"] + dd["w"] for dd in g["descs"] + g["prices"]),
                "last_desc_bottom_per_column": [max(dd["y"] + dd["h"] for dd in g["descs"] if c["x"] <= dd["x"] < c["x"] + c["w"]) for c in g["columns"]],
            }
            report[name], _ = contrast(pg, dsf)
            pg.close()
        b.close()
    (HERE / "contrast.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (HERE / "geometry.json").write_text(json.dumps(geom, indent=1, ensure_ascii=False))
    for k, v in report.items():
        worst = sorted(v, key=lambda r: r["min_contrast"])[:3]
        small = sorted(v, key=lambda r: r["font_px_css"])[:2]
        print(k, "worst:", [(r["text"], r["min_contrast"]) for r in worst], "smallest:", [(r["text"], r["print_pt"]) for r in small])
        print("  ink:", geom[k]["ink"])


if __name__ == "__main__":
    main()
