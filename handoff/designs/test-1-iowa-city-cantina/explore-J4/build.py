#!/usr/bin/env python3
"""TEST-1 explore-J4 "Horizon", round 4 (checkpoint: ../explore-J3).

ART (text-free inline SVG, three flat inks: navy, amber, paper):
  a navy dusk sky cut on its right by an amber glow in escalonado steps (Mexican stepped parapet as the shape
  of the light), and ONE navy prairie grain elevator (gabled headhouse + wide slip-form bin block) standing in
  that glow. The elevator crosses the horizon and comes down beside the Cocktails column to a ground line;
  the lower tier hangs from that same line.
TEXT: one three-column grid (x 60-756). Cocktails on columns 1-2 beside the elevator; lower tier on 1-3.

Content: ../build/draft_doc.json + garnish from phg.recipe_versions (cited in ../round-17/proposal.md). Nothing invented.
Usage: python3 build.py [before|after]   (env J4_ABL=a,b removes named art devices for ablation)
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

NAVY, AMBER = "#1E2147", "#D98A2E"
AMBER_INK = "#8F4F10"            # the amber, darkened for text on paper: section heads only (5.5:1)
PAPER, INK, MUTED = "#F4EDE1", "#221C22", "#5B5058"


def ingr(*parts):
    return " · ".join(p.replace(" ", NB) for p in parts)


DESC = {
    "beta_margarita": ingr("Tequila blanco", "fresh lime juice", "orange liqueur", "agave syrup", "lime wheel")
                      + ". \x00Bright and citrus-forward\x01",          # rv f06abb74 garnish + draft desc sentence
    "beta_manhattan": ingr("Rye whiskey", "sweet vermouth", "cocktail cherry"),       # bitters hidden; rv 9fb77eaa
    "beta_daiquiri": ingr("White rum", "fresh lime juice", "demerara syrup", "lime coin"),          # rv 14d45e57
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
    return esc(DESC[i]).replace("\x00", '<span class="nw">').replace("\x01", "</span>")


def item_html(it):
    return (f'<div class="it" data-id="{it["id"]}"><div class="nm"><span class="n">{esc(it["name"])}</span>'
            f'{NB}<span class="p">{price(it)}</span></div><div class="ds">{dtext(it["id"])}</div></div>')


def grp(name, items, sid=""):
    idattr = f' id="{sid}"' if sid else ""
    return f'<div class="grp"{idattr}><h3>{esc(name)}</h3>' + "".join(item_html(i) for i in items) + "</div>"


def section_html(sec, cls="sec"):
    out = [f'<section class="{cls}" id="{sec["id"]}"><h2>{esc(sec["name"])}</h2>']
    for sb in sec["subs"]:
        items = sb["items"]
        if sb["id"] in ORDER_FIRST:
            items = sorted(items, key=lambda i: ORDER_FIRST[sb["id"]].index(i["id"]))
        out.append(grp(sb["name"], items))
    out.append("</section>")
    return "".join(out)


def beer_cider_html():
    """Beer (sub: Draft) and Cider share one column under 'Beer & Cider'; each keeps its own draft group."""
    beer, cider = SEC["sec_beer"], SEC["sec_cider"]
    draft = beer["subs"][0]
    return (f'<section class="sec" id="sec_beer_cider"><h2>Beer &amp; Cider</h2>'
            + grp(draft["name"], draft["items"], "sec_beer") + grp(cider["name"], cider["items"], "sec_cider")
            + "</section>")


# ---- ART -------------------------------------------------------------------------------------------------------
def art_flags():
    f = dict(setback=True, bin_arcs=True, ground_rule=True, glow_band=True)
    if not BEFORE:
        f.update(ground_rule=False, glow_band=False)
    for k in filter(None, os.environ.get("J4_ABL", "").split(",")):
        f[k] = False
    return f


def art_svg(W, H, Hz, G, P, flags, rule_x0=None):
    """W,H page; Hz horizon (bottom of the sky); G ground line (elevator base); P geometry dict."""
    B = 12
    o = [f'<svg class="art" width="{W}" height="{H}" viewBox="0 0 {W} {H}" aria-hidden="true" '
         f'style="position:absolute;left:0;top:0;overflow:visible">',
         f'<rect x="{-B}" y="{-B}" width="{W + 2 * B}" height="{Hz + B}" fill="{NAVY}"/>']
    # escalonado glow: steps descend from the top-right to the horizon, moving left by `run` per step
    n, run, x0 = P["steps"], P["run"], P["glow_x_top"]
    h = (Hz + B) / n
    pts = [(W + B, -B), (x0, -B)]
    y = -B
    for k in range(n):
        y += h
        pts.append((x0 - run * k, y))
        if k < n - 1:
            pts.append((x0 - run * (k + 1), y))
    pts.append((W + B, Hz))
    o.append(f'<path d="M' + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f' Z" fill="{AMBER}"/>')
    if flags["glow_band"]:
        o.append(f'<rect x="{-B}" y="{Hz - P["band"]}" width="{W + 2 * B}" height="{P["band"]}" fill="{AMBER}"/>')
    # the elevator: one navy silhouette = a wide slip-form bin block (its top reads as the crowns of the
    # cylinders) with a taller headhouse rising from its left end; the headhouse roofline steps up once
    # (leg housing), echoing the escalonado of the sky.
    hx, hw, ht = P["hx"], P["hw"], P["h_top"]
    bt, n, dep = P["bins_top"], P["bins_n"], P["arc_d"]
    d = f"M{hx:.1f},{G:.1f} L{hx:.1f},{ht:.1f} "
    if flags["setback"]:
        sw, sh = P["set_w"], P["set_h"]
        d += f"L{hx:.1f},{ht - sh:.1f} L{hx + sw:.1f},{ht - sh:.1f} L{hx + sw:.1f},{ht:.1f} "
    d += f"L{hx + hw:.1f},{ht:.1f} L{hx + hw:.1f},{bt:.1f} "
    bw = (W + B - hx - hw) / n
    x = hx + hw
    for _ in range(n):
        if flags["bin_arcs"]:
            d += f"A{bw / 2:.1f},{dep:.1f} 0 0 1 {x + bw:.1f},{bt:.1f} "
        else:
            d += f"L{x + bw:.1f},{bt:.1f} "
        x += bw
    d += f"L{W + B:.1f},{G:.1f} Z"
    o.append(f'<path d="{d}" fill="{NAVY}"/>')
    if flags["ground_rule"] and rule_x0 is not None:
        o.append(f'<rect x="{rule_x0}" y="{G - 1}" width="{hx - rule_x0}" height="1.5" fill="{NAVY}"/>')
    o.append("</svg>")
    return "".join(o)


LETTER = dict(steps=6, run=16, glow_x_top=520, band=10, hx=556, hw=74, h_top=64, set_w=44, set_h=30,
              bins_top=300, bins_n=3, arc_d=16)
PHONE = dict(steps=6, run=8, glow_x_top=286, band=8, hx=284, hw=36, h_top=92, set_w=22, set_h=18,
             bins_top=170, bins_n=2, arc_d=10)
HZ_L, HZ_P = 204, 250


def page_html():
    cocktails = section_html(SEC["sec_cocktails"], cls="sec main")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Cantina — bar menu (explore-J4 Horizon)</title>
<style>
@font-face{{font-family:Fr;font-weight:400 900;src:url({FONTS}/fraunces.woff2) format("woff2")}}
@font-face{{font-family:Fr;font-style:italic;font-weight:400 700;src:url({FONTS}/fraunces-i.woff2) format("woff2")}}
@font-face{{font-family:Dm;font-weight:400 800;src:url({FONTS}/dmsans.woff2) format("woff2")}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{PAPER}}}
.page{{position:relative;background:{PAPER};color:{INK};overflow:hidden}}
.mast{{position:absolute;left:var(--m);top:var(--mt);color:{PAPER};z-index:1}}
.wm{{font:430 var(--wm)/1 Fr;letter-spacing:.14em;margin-left:var(--wmfix);font-variation-settings:"opsz" 144,"SOFT" 0,"WONK" 0}}
.sub{{font:400 var(--subsz)/1 Dm;letter-spacing:.2em;margin-top:var(--subgap);color:#E9E1D6}}
.read{{position:absolute;left:var(--m);top:var(--rt);width:var(--tw);z-index:1}}
h2{{font:600 var(--h2)/16px Dm;letter-spacing:.3em;text-transform:uppercase;color:{AMBER_INK};margin-bottom:20px}}
h3{{font:italic 400 var(--h3)/26px Fr;color:{MUTED};margin-bottom:6px}}
.nw{{white-space:nowrap}}
.grp+.grp{{margin-top:var(--grpgap)}}
.it+.it{{margin-top:var(--itgap)}}
.nm{{font:500 var(--nm)/26px Fr;font-variation-settings:"opsz" 18;color:{INK};font-variant-numeric:lining-nums tabular-nums}}
.nm .p{{font-weight:400;color:{MUTED};margin-left:.75em}}
.ds{{font:400 var(--ds)/18px Dm;color:{MUTED}}}
.row{{display:grid;grid-template-columns:repeat(3,1fr);column-gap:24px;align-items:start;margin-top:var(--tiergap)}}
body.letter .page{{width:816px;height:1056px;
  --m:60px;--mt:50px;--tw:696px;--rt:{HZ_L + 32}px;--wm:76px;--wmfix:-3px;--subsz:12.5px;--subgap:22px;--h2:12.5px;--h3:15.5px;
  --nm:18.5px;--ds:13.5px;--itgap:18px;--grpgap:26px;--tiergap:{{TIERGAP}}px}}
body.letter .main{{width:456px}}
body.letter .nm{{white-space:nowrap}}
body.phone .page{{width:390px;
  --m:24px;--mt:44px;--tw:342px;--rt:{HZ_P + 36}px;--wm:44px;--wmfix:-1.5px;--subsz:10.5px;--subgap:12px;--h2:12px;--h3:15px;
  --nm:17.5px;--ds:13.5px;--itgap:16px;--grpgap:26px;--tiergap:44px}}
body.phone .read{{position:relative;top:0;padding:{HZ_P + 36}px 0 52px;left:0;margin-left:24px}}
body.phone .row{{display:block}}
body.phone .col+.col{{margin-top:44px}}
</style></head><body class="{{BODYCLASS}}"><div class="page">
{{ART}}
<header class="mast"><div class="wm">CANTINA</div><div class="sub">&amp; cocktail bar · Iowa City, Iowa</div></header>
<main class="read">
{cocktails}
<div class="row"><div class="col">{section_html(SEC["sec_spirits"])}</div><div class="col">{beer_cider_html()}</div><div class="col">{section_html(SEC["sec_wine"])}</div></div>
</main></div></body></html>"""


CONTRAST_JS = """() => { const out=[]; const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 let n; while(n=w.nextNode()){ if(!n.textContent.trim()) continue; const el=n.parentElement;
  if(el.closest('style,title,svg')) continue;
  const r=document.createRange(); r.selectNodeContents(n); for(const b of r.getClientRects()){ if(b.width<1) continue;
   const cs=getComputedStyle(el); out.push({t:n.textContent.trim().slice(0,48),c:cs.color,fs:parseFloat(cs.fontSize),
   role:el.className||el.tagName,x:b.x,y:b.y,w:b.width,h:b.height});}} return out;}"""

GEOM_JS = """() => { const q=s=>[...document.querySelectorAll(s)].filter(e=>e.offsetParent!==null).map(e=>{const r=e.getBoundingClientRect();
  return {el:(e.id||(typeof e.className==='string'?e.className:'')||e.tagName), text:(e.innerText||'').split('\\n')[0].slice(0,40), x:+r.left.toFixed(1), y:+r.top.toFixed(1), w:+r.width.toFixed(1), h:+r.height.toFixed(1)}});
  const pgb=document.querySelector('.page').getBoundingClientRect();
  return {page:[pgb.width,pgb.height], mast:q('.wm,.sub'), sections:q('section'), groups:q('.grp'), heads:q('h2,h3'), items:q('.it'), names:q('.nm .n'), prices:q('.p'), descs:q('.ds'), columns:q('.col,.main')} }"""


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
    return res


def ink_bbox(img, box, scale, bg):
    import numpy as np
    x, y, w, h = [int(v * scale) for v in box]
    a = np.asarray(img.crop((x, y, x + w, y + h)).convert("RGB"), dtype=int)
    m = np.abs(a - np.array(bg)).sum(-1) > 60
    ys, xs = np.nonzero(m)
    if not len(xs):
        return None
    return [round(float(x + xs.min()) / scale, 1), round(float(y + ys.min()) / scale, 1),
            round(float(x + xs.max() + 1) / scale, 1), round(float(y + ys.max() + 1) / scale, 1)]


def main():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    from PIL import Image
    base = page_html()
    flags = art_flags()
    report, geom = {}, {}
    exe = next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"), None)
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))

        def load(pg, html_text, cls):
            tmp = HERE / f".render-{cls}.html"
            tmp.write_text(html_text)
            pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(500); tmp.unlink()

        for name, cls, w, h, dsf in [("preview-letter.png", "letter", 816, 1056, 3.125),
                                     ("preview-phone.png", "phone", 390, 900, 3)]:
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            d0 = base.replace("{BODYCLASS}", cls)
            if cls == "letter":
                # pass 1: measure the cocktail column, put the ground line G half a tier-gap below it
                tiergap = 48
                load(pg, d0.replace("{ART}", "").replace("{TIERGAP}", str(tiergap)), cls)
                mb = pg.evaluate("() => { const d=[...document.querySelectorAll('.main .ds')].pop().getBoundingClientRect(); return d.bottom }")
                G = round(mb + tiergap / 2)
                art = art_svg(816, 1056, HZ_L, G, LETTER, flags, rule_x0=60)
                d = d0.replace("{ART}", art).replace("{TIERGAP}", str(tiergap))
                (HERE / "menu.html").write_text(d)
            else:
                load(pg, d0.replace("{ART}", ""), cls)
                H = pg.evaluate("document.querySelector('.page').scrollHeight")
                G = HZ_P
                art = art_svg(390, H, HZ_P, G, PHONE, dict(flags, ground_rule=False))
                d = d0.replace("{ART}", art).replace('<div class="page">', f'<div class="page" style="height:{H}px">')
            load(pg, d, cls)
            g = pg.evaluate(GEOM_JS)
            g["ground_line_G"] = G
            g["horizon_Hz"] = HZ_L if cls == "letter" else HZ_P
            pg.screenshot(path=str(HERE / name), full_page=(cls == "phone"))
            full = Image.open(HERE / name).convert("RGB")
            nv, pa = (0x1E, 0x21, 0x47), (0xF4, 0xED, 0xE1)
            g["ink"] = {
                "wordmark": ink_bbox(full, [g["mast"][0][k] for k in "xywh"], dsf, nv),
                "subline": ink_bbox(full, [g["mast"][1][k] for k in "xywh"], dsf, nv),
                "cocktails_h2": ink_bbox(full, [g["heads"][0][k] for k in "xywh"], dsf, pa),
                "names_left": min(n["x"] for n in g["names"]),
                "text_right": max(dd["x"] + dd["w"] for dd in g["descs"] + g["prices"]),
                "column_bottoms": [max((dd["y"] + dd["h"] for dd in g["descs"] if c["x"] <= dd["x"] < c["x"] + c["w"] and dd["y"] >= c["y"]), default=None) for c in g["columns"]],
                "first_item_y_per_column": [min((it["y"] for it in g["items"] if c["x"] <= it["x"] < c["x"] + c["w"] and it["y"] >= c["y"]), default=None) for c in g["columns"]],
            }
            geom[name] = g
            report[name] = contrast(pg, dsf)
            pg.close()
        b.close()
    (HERE / "contrast.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (HERE / "geometry.json").write_text(json.dumps(geom, indent=1, ensure_ascii=False))
    for k, v in report.items():
        worst = sorted(v, key=lambda r: r["min_contrast"])[:3]
        print(k, "worst:", [(r["text"], r["min_contrast"]) for r in worst], "G", geom[k]["ground_line_G"])
        print("  ink:", geom[k]["ink"])


if __name__ == "__main__":
    main()
