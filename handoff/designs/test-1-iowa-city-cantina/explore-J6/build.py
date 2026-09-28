#!/usr/bin/env python3
"""TEST-1 explore-J6 "Horizon", round 6 (checkpoint J4; art pipeline from J5).

ART (raster, text-free, generated at full print resolution): flat navy dusk (top band + right column) with ONE
cut-paper Iowa grain elevator left as unprinted paper: gabled-free headhouse with a narrow offset leg housing, a
gallery beam that runs from the left trim (CANTINA stands on it) through the headhouse and across the bin cones,
and a row of cylindrical bins (half-round tone in a second paper value) whose conical caps are the picos of a
papel-picado edge and whose walls are pierced with rombos. The amber dusk shows only through the cuts (and as a
thin ground line), printed as a second pass misregistered by 0.25 mm.
TEXT: one grid. x 60 | 264 | 468 (= navy column edge). Cocktails on columns 1-2; Spirits and Wine below them;
Beer & Cider hangs from the elevator's ground line in column 3. Every column ends on the bottom margin.

Content: ../build/draft_doc.json + garnish from phg.recipe_versions (cited in ../round-17/proposal.md). Nothing invented.
Usage: python3 build.py [before|after]      (env J6_ABL=a,b removes named devices)
"""
import json, sys, html, io, re, os, glob, itertools
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
DRAFT = json.load(open(HERE.parent / "build" / "draft_doc.json"))
FONTDIR = HERE.parent / "build" / "fonts"
FONTS = FONTDIR.as_uri()
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "after"
BEFORE = VARIANT == "before"
esc = html.escape
NB = " "

NAVY, AMBER, PAPER, PAPER2 = (0x1E, 0x21, 0x47), (0xD9, 0x8A, 0x2E), (0xF4, 0xED, 0xE1), (0xE2, 0xD6, 0xC2)
HEX = lambda c: "#%02X%02X%02X" % c
AMBER_INK, INK, MUTED = "#8F4F10", "#221C22", "#5B5058"

PARTS = {
    "beta_margarita": ["Tequila blanco", "fresh lime juice", "orange liqueur", "agave syrup", "lime wheel"],  # rv f06abb74
    "beta_manhattan": ["Rye whiskey", "sweet vermouth", "cocktail cherry"],                 # bitters hidden; rv 9fb77eaa
    "beta_daiquiri": ["White rum", "fresh lime juice", "house demerara syrup", "lime coin"],  # draft desc "house demerara syrup"; rv 14d45e57
    "beta_old_fashioned": ["Brown butter-washed bourbon", "demerara syrup", "aromatic bitters", "orange peel"],  # rv 7095fd3d
    "beta_czech_pilsner": ["Crisp pale lager"],
    "beta_dry_hopped_ipa": ["Hop-forward draft IPA"],
    "beta_amber_lager": ["Toasty amber lager"],
    "beta_malbec": ["Dry red wine"],
    "beta_pinot_grigio": ["Dry white wine"],
    "beta_brut_rose": ["Dry sparkling rosé"],
    "beta_blanco_tequila": ["Blanco tequila pour"],    # draft desc
    "beta_anejo_tequila": ["Añejo tequila pour"],      # draft desc
    "beta_cognac_vsop": ["VSOP Cognac pour"],          # draft desc
    "beta_dry_cider": ["Dry sparkling cider"],
}
NOTE = {"beta_margarita": "Bright and citrus-forward."}   # draft-supplied tasting note (draft desc, sentence 2)
ORDER_FIRST = {"sub_cocktails_classics": ["beta_margarita", "beta_manhattan"]}
SEC = {s["id"]: s for s in DRAFT["sections"]}
ALL_IDS = {it["id"] for s in DRAFT["sections"] for sb in s["subs"] for it in sb["items"]} | \
          {it["id"] for s in DRAFT["sections"] for it in s["items"]}
assert len(ALL_IDS) == 14 and set(PARTS) == ALL_IDS
_F = ImageFont.truetype(str(FONTDIR / "DMSans-400-normal.ttf"), 400)
SEP = " · "


def textw(t, px):
    return _F.getlength(t) * px / 400


def break_parts(parts, px, measure):
    """Fewest lines that fit, most even split. Breaks only between ingredients; the separator is kept and
    carried to the START of the continuation line (so no line ends with a middot and no break loses it)."""
    n = len(parts)
    best = None
    for k in range(1, n + 1):
        for cuts in itertools.combinations(range(1, n), k - 1):
            idx = (0,) + cuts + (n,)
            lines = [("· " if i else "") + SEP.join(parts[idx[i]:idx[i + 1]]) for i in range(k)]
            ws = [textw(l, px) for l in lines]
            if max(ws) > measure * 0.97:
                continue
            orphan = k > 1 and (idx[-1] - idx[-2]) == 1 and n > 2
            score = (orphan, max(ws) - min(ws))
            if best is None or score < best[0]:
                best = (score, lines)
        if best:
            return best[1]
    return [SEP.join(parts)]


def price(it):
    v = it["prices"][0]["value"]
    return str(int(v)) if float(v).is_integer() else f"{v:.2f}"


def desc_html(iid, measures):
    out = []
    for cls, (px, m) in measures.items():
        lines = break_parts(PARTS[iid], px, m)
        out.append(f'<span class="ds v-{cls}">' + "".join(
            f'<span class="ln">{esc(l).replace(" ", NB).replace(NB + "·" + NB, " ·" + NB)}</span>' for l in lines) + "</span>")
    note = f'<span class="note">{esc(NOTE[iid])}</span>' if iid in NOTE else ""
    return "".join(out) + note


def item_html(it, measures):
    return (f'<div class="it" data-id="{it["id"]}"><div class="nm"><span class="n">{esc(it["name"])}</span>'
            f'{NB}<span class="p">{price(it)}</span></div>{desc_html(it["id"], measures)}</div>')


def grp(name, items, measures, sid=""):
    idattr = f' id="{sid}"' if sid else ""
    return f'<div class="grp"{idattr}><h3>{esc(name)}</h3>' + "".join(item_html(i, measures) for i in items) + "</div>"


def section_html(sec, measures, cls="sec"):
    out = [f'<section class="{cls}" id="{sec["id"]}"><h2>{esc(sec["name"])}</h2>']
    for sb in sec["subs"]:
        items = sb["items"]
        if sb["id"] in ORDER_FIRST:
            items = sorted(items, key=lambda i: ORDER_FIRST[sb["id"]].index(i["id"]))
        out.append(grp(sb["name"], items, measures))
    return "".join(out) + "</section>"


def beer_cider_html(measures):
    beer, cider = SEC["sec_beer"], SEC["sec_cider"]
    draft = beer["subs"][0]
    return (f'<section class="sec" id="sec_beer_cider"><h2>Beer &amp; Cider</h2>'
            + grp(draft["name"], draft["items"], measures, "sec_beer")
            + grp(cider["name"], cider["items"], measures, "sec_cider") + "</section>")


# ---- ART ---------------------------------------------------------------------------------------------------------
def flags():
    f = dict(misreg=True, rombos=True, rombo_row2=True, shade=True, cones=True, leg=True, beam_left=True,
             ground_line=True, headhouse_rombos=True, cone_shade=True)
    if not BEFORE:
        f.update(rombo_row2=False, headhouse_rombos=False, cone_shade=False)
    for k in filter(None, os.environ.get("J6_ABL", "").split(",")):
        f[k] = False
    return f


def draw_art(W, H, s, Hz, col_x, Gr, gal_y, P, F):
    """Flat two-ink print. Hz: bottom of the navy top band. col_x: navy column edge (letter) or None.
    Gr: ground line (elevator base / bottom of the navy column). gal_y: top of the gallery beam."""
    Wp, Hp = int(round(W * s)), int(round(H * s))
    S = lambda v: v * s
    B = 12
    navy = Image.new("L", (Wp, Hp), 0); dn = ImageDraw.Draw(navy)
    ko = Image.new("L", (Wp, Hp), 0); dk = ImageDraw.Draw(ko)          # elevator (unprinted paper)
    sh = Image.new("L", (Wp, Hp), 0); ds = ImageDraw.Draw(sh)          # second paper value (half-round tone)
    holes = Image.new("L", (Wp, Hp), 0); dh = ImageDraw.Draw(holes)    # cuts that show the amber dusk
    dn.rectangle([S(-B), S(-B), S(W + B), S(Hz)], fill=255)
    if col_x is not None:
        dn.rectangle([S(col_x), S(-B), S(W + B), S(Gr)], fill=255)
    hx, hw, ht = P["hx"], P["hw"], P["h_top"]
    gh = P["gal_h"]
    # headhouse + leg housing (narrow, offset to the right edge of the roof)
    dk.rectangle([S(hx), S(ht), S(hx + hw), S(Gr)], fill=255)
    if F["leg"]:
        lw, lh = P["leg_w"], P["leg_h"]
        lx = hx + hw - P["leg_inset"] - lw
        dk.rectangle([S(lx), S(ht - lh), S(lx + lw), S(ht)], fill=255)
    # gallery beam: right arm across the bin cones; left arm to the left trim under the wordmark
    dk.rectangle([S(hx + hw - 1), S(gal_y), S(W + B), S(gal_y + gh)], fill=255)
    if F["beam_left"]:
        dk.rectangle([S(-B), S(gal_y), S(hx + 1), S(gal_y + gh)], fill=255)
    # bins: cylinders with conical caps (the picos), half-round tone, rombos cut through the walls
    bx0, bw, ch = hx + hw + P["hgap"], P["bin_w"], P["cone_h"]
    apex = gal_y + gh
    shoulder = apex + ch
    x = bx0
    bins = []
    while x < W + B:
        bins.append(x)
        dk.rectangle([S(x), S(shoulder), S(x + bw), S(Gr)], fill=255)
        if F["cones"]:
            dk.polygon([(S(x), S(shoulder + 1)), (S(x + bw / 2), S(apex - 1)), (S(x + bw), S(shoulder + 1))], fill=255)
        else:
            dk.rectangle([S(x), S(apex), S(x + bw), S(shoulder + 1)], fill=255)
        if F["shade"]:
            f0 = P["shade_from"]
            ds.rectangle([S(x + bw * f0), S(shoulder), S(x + bw), S(Gr)], fill=255)
            if F["cone_shade"] and F["cones"]:
                ds.polygon([(S(x + bw / 2), S(apex)), (S(x + bw), S(shoulder + 1)), (S(x + bw / 2), S(shoulder + 1))], fill=255)
        x += bw
    if F["rombos"]:
        rows = [P["rombo_row1"]] + ([P["rombo_row2"]] if F["rombo_row2"] else [])
        for fr in rows:
            cy = shoulder + (Gr - shoulder) * fr
            r = P["rombo"]
            for bx in bins:
                cx = bx + bw * 0.36
                dh.polygon([(S(cx), S(cy - r)), (S(cx + r * 0.6), S(cy)), (S(cx), S(cy + r)), (S(cx - r * 0.6), S(cy))], fill=255)
        if F["headhouse_rombos"]:
            for k in range(3):
                cx, cy, r = hx + hw / 2, ht + 40 + k * 28, P["rombo"] * 0.8
                dh.polygon([(S(cx), S(cy - r)), (S(cx + r * 0.6), S(cy)), (S(cx), S(cy + r)), (S(cx - r * 0.6), S(cy))], fill=255)
    amber = holes.copy()
    if F["ground_line"] and col_x is not None:
        ImageDraw.Draw(amber).rectangle([S(col_x), S(Gr - P["ground"]), S(W + B), S(Gr)], fill=255)
    elif F["ground_line"]:
        ImageDraw.Draw(amber).rectangle([S(-B), S(Gr - P["ground"]), S(W + B), S(Gr)], fill=255)
    k = np.asarray(ko, np.float32) / 255
    n = np.asarray(navy, np.float32) / 255 * (1 - k)
    shade = np.asarray(sh, np.float32) / 255 * k
    hole = np.asarray(holes, np.float32) / 255
    a = np.asarray(amber, np.float32) / 255
    if F["misreg"]:
        dx, dy = int(round(s * 0.95)), int(round(s * 0.65))     # shift without wrap-around
        sh_a = np.zeros_like(a); sh_a[dy:, dx:] = a[:a.shape[0] - dy, :a.shape[1] - dx]; a = sh_a
    # holes are cut through the paper: the navy never prints there, the paper shows what the amber pass leaves
    n = n * (1 - hole)
    img = np.ones((Hp, Wp, 3), np.float32) * (np.array(PAPER, np.float32) / 255)
    img = img * (1 - shade[..., None]) + (np.array(PAPER2, np.float32) / 255) * shade[..., None]
    for cov, ink in ((a, AMBER), (n, NAVY)):
        inkf = np.array(ink, np.float32) / 255
        img = img * (1 - cov[..., None]) + img * inkf * cov[..., None]
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))


LETTER = dict(hx=538, hw=62, h_top=58, leg_w=16, leg_h=40, leg_inset=6, gal_h=12, hgap=0, bin_w=76, cone_h=24,
              shade_from=0.62, rombo=9, rombo_row1=0.22, rombo_row2=0.62, ground=4)
PHONE = dict(hx=262, hw=40, h_top=50, leg_w=10, leg_h=26, leg_inset=4, gal_h=8, hgap=0, bin_w=48, cone_h=15,
             shade_from=0.62, rombo=6, rombo_row1=0.3, rombo_row2=0.7, ground=3)
COL = [60, 264, 468]           # grid: column 3 starts on the navy column edge
COLW = [180, 180, 288]


HZ_L, GAL_H = 186, LETTER["gal_h"]


def page_html():
    MC = {"L": (13.5, 384), "P": (13.5, 342)}
    ML = {"L": (13.5, 180), "P": (13.5, 342)}
    MB = {"L": (13.5, 288), "P": (13.5, 342)}
    cocktails = section_html(SEC["sec_cocktails"], MC, cls="sec main")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Cantina — bar menu (explore-J6 Horizon)</title>
<style>
@font-face{{font-family:Fr;font-weight:400 900;src:url({FONTS}/fraunces.woff2) format("woff2")}}
@font-face{{font-family:Fr;font-style:italic;font-weight:400 700;src:url({FONTS}/fraunces-i.woff2) format("woff2")}}
@font-face{{font-family:Dm;font-weight:400 800;src:url({FONTS}/dmsans.woff2) format("woff2")}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{HEX(PAPER)}}}
.page{{position:relative;background:{HEX(PAPER)} var(--art) 0 0/100% auto no-repeat;color:{INK};overflow:hidden}}
.mast{{position:absolute;left:var(--m);top:var(--mt);color:{HEX(PAPER)}}}
.wm{{font:430 var(--wm)/1 Fr;letter-spacing:.14em;margin-left:var(--wmfix);font-variation-settings:"opsz" 144,"SOFT" 0,"WONK" 0}}
.sub{{font:400 var(--subsz)/1 Dm;letter-spacing:.2em;margin-top:var(--subgap);color:#E9E1D6}}
h2{{font:600 var(--h2)/16px Dm;letter-spacing:.3em;text-transform:uppercase;color:{AMBER_INK};margin-bottom:16px}}
h3{{font:italic 400 var(--h3)/26px Fr;color:{MUTED};margin-bottom:6px}}
.grp+.grp{{margin-top:var(--grpgap)}}
.it+.it{{margin-top:var(--itgap)}}
.main .grp+.grp{{margin-top:var(--grc)}}
.main .it+.it{{margin-top:var(--itc)}}
.nm{{font:500 var(--nm)/26px Fr;font-variation-settings:"opsz" 18;color:{INK};font-variant-numeric:lining-nums tabular-nums;white-space:nowrap}}
.nm .p{{font-weight:400;color:{MUTED};margin-left:.75em}}
.ds{{display:block;font:400 var(--ds)/18px Dm;color:{MUTED}}}
.ds .ln{{display:block;white-space:nowrap}}
.note{{display:block;font:italic 400 var(--ds)/18px Fr;color:{MUTED}}}
.v-P{{display:none}} body.phone .v-L{{display:none}} body.phone .v-P{{display:block}}
body.letter .page{{width:816px;height:1056px;
  --m:60px;--mt:50px;--wm:76px;--wmfix:-3px;--subsz:12.5px;--subgap:22px;--h2:12.5px;--h3:15.5px;
  --nm:18.5px;--ds:13.5px;--itgap:14px;--grpgap:22px}}
body.letter .blk{{position:absolute}}
body.letter #b0{{left:{COL[0]}px;top:{HZ_L + 32}px;width:384px}}
body.letter #b1{{left:{COL[0]}px;top:var(--y0);width:{COLW[0]}px}}
body.letter #b2{{left:{COL[1]}px;top:var(--y0);width:{COLW[1]}px}}
body.letter #b3{{left:{COL[2]}px;top:var(--yb);width:{COLW[2]}px}}
body.phone .page{{width:390px;
  --m:24px;--mt:44px;--wm:44px;--wmfix:-1.5px;--subsz:10.5px;--subgap:20px;--h2:12px;--h3:15px;
  --nm:17.5px;--ds:13.5px;--itgap:16px;--grpgap:26px;--itc:16px;--grc:26px}}
body.phone .read{{position:relative;margin-left:24px;padding:var(--rt) 0 52px;width:342px}}
body.phone .blk+.blk{{margin-top:44px}}
</style></head><body class="{{BODYCLASS}}"><div class="page" style="{{PAGESTYLE}}">
<header class="mast"><div class="wm">CANTINA</div><div class="sub">&amp; cocktail bar · Iowa City, Iowa</div></header>
<main class="read">
<div class="blk" id="b0">{cocktails}</div>
<div class="blk" id="b1">{section_html(SEC["sec_spirits"], ML)}</div>
<div class="blk" id="b2">{section_html(SEC["sec_wine"], ML)}</div>
<div class="blk" id="b3">{beer_cider_html(MB)}</div>
</main></div></body></html>"""

CONTRAST_JS = """() => { const out=[]; const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 let n; while(n=w.nextNode()){ if(!n.textContent.trim()) continue; const el=n.parentElement;
  if(el.closest('style,title')) continue; if(!el.offsetParent && el.tagName!=='BODY') continue;
  const r=document.createRange(); r.selectNodeContents(n); for(const b of r.getClientRects()){ if(b.width<1) continue;
   const cs=getComputedStyle(el); out.push({t:n.textContent.trim().slice(0,48),c:cs.color,fs:parseFloat(cs.fontSize),
   role:el.className||el.tagName,x:b.x,y:b.y,w:b.width,h:b.height});}} return out;}"""

GEOM_JS = """() => { const vis=e=>e.offsetParent!==null; const q=s=>[...document.querySelectorAll(s)].filter(vis).map(e=>{const r=e.getBoundingClientRect();
  return {el:(e.id||(typeof e.className==='string'?e.className:'')||e.tagName), text:(e.innerText||'').split('\\n')[0].slice(0,48), x:+r.left.toFixed(1), y:+r.top.toFixed(1), w:+r.width.toFixed(1), h:+r.height.toFixed(1)}});
  const pgb=document.querySelector('.page').getBoundingClientRect();
  return {page:[pgb.width,pgb.height], mast:q('.wm,.sub'), sections:q('section'), groups:q('.grp'), heads:q('h2,h3'), items:q('.it'), names:q('.nm .n'), prices:q('.p'), lines:q('.ln,.note'), columns:q('.col,.main')} }"""


def rl(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast(page, scale):
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
    x, y, w, h = [int(v * scale) for v in box]
    a = np.asarray(img.crop((x, y, x + w, y + h)).convert("RGB"), dtype=int)
    m = np.abs(a - np.array(bg)).sum(-1) > 90
    ys, xs = np.nonzero(m)
    if not len(xs):
        return None
    return [round(float(x + xs.min()) / scale, 1), round(float(y + ys.min()) / scale, 1),
            round(float(x + xs.max() + 1) / scale, 1), round(float(y + ys.max() + 1) / scale, 1)]




def main():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    base = page_html()
    F = flags()
    report, geom = {}, {}
    exe = next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"), None)
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))

        def load(pg, text, cls):
            tmp = HERE / f".render-{cls}.html"
            tmp.write_text(text)
            pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(500); tmp.unlink()

        H_JS = "id => { const e=document.getElementById(id); const ls=[...e.querySelectorAll('.ln,.note,h2')].filter(x=>x.offsetParent); const t=e.getBoundingClientRect().top; return Math.max(...ls.map(x=>x.getBoundingClientRect().bottom))-t }"
        for name, cls, w, h, dsf in [("preview-letter.png", "letter", 816, 1056, 3.125),
                                     ("preview-phone.png", "phone", 390, 900, 3)]:
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            d0 = base.replace("{BODYCLASS}", cls)
            if cls == "letter":
                css = "--y0:600px;--yb:600px;--itc:16px;--grc:26px"
                load(pg, d0.replace("{PAGESTYLE}", css), cls)
                hc, hs, hw_, hb = [pg.evaluate(H_JS, i) for i in ("b0", "b1", "b2", "b3")]
                wm_bottom = pg.evaluate("() => { const r=document.querySelector('.wm').getBoundingClientRect(); return r.bottom }")
                BOTTOM = 996
                y0 = BOTTOM - max(hs, hw_)
                yb = BOTTOM - hb
                Gr = yb - 26
                c_top = HZ_L + 32
                target = y0 - 40                        # cocktails end one tier gap above Spirits / Wine
                extra = target - (c_top + hc)
                e = max(0.0, min(extra / 3, 14))        # 3 flexible gaps inside Cocktails
                css = f"--y0:{y0:.1f}px;--yb:{yb:.1f}px;--itc:{16 + e:.1f}px;--grc:{26 + e:.1f}px"
                # the wordmark stands on the gallery beam: beam top = CANTINA's baseline (no descenders)
                gal_y = wm_bottom - 76 * 0.129        # Fraunces descender share below the baseline in a 1.0 line box
                art = draw_art(816, 1056, dsf, HZ_L, COL[2], Gr, gal_y, LETTER, F)
                art_name = "art-letter.png"
                G = Gr
            else:
                load(pg, d0.replace("{PAGESTYLE}", "--rt:0px"), cls)
                wm_bottom = pg.evaluate("() => document.querySelector('.wm').getBoundingClientRect().bottom")
                Gp = 236
                H = pg.evaluate("document.querySelector('.page').scrollHeight") + Gp + 60
                gal_y = wm_bottom - 44 * 0.129
                art = draw_art(390, H, dsf, Gp, None, Gp, gal_y, PHONE, F)
                art_name = "art-phone.png"
                css = f"--rt:{Gp + 40}px"
                G = Gp
            art.save(HERE / art_name)
            d = d0.replace("{PAGESTYLE}", css + f";--art:url({(HERE / art_name).as_uri()})")
            if cls == "letter":
                (HERE / "menu.html").write_text(d.replace((HERE / art_name).as_uri(), art_name))
            load(pg, d, cls)
            if cls == "phone":
                Hreal = pg.evaluate("document.querySelector('.read').getBoundingClientRect().bottom")
                pg.evaluate(f"document.querySelector('.page').style.height='{Hreal:.0f}px'")
            g = pg.evaluate(GEOM_JS)
            g["ground_line_G"] = G
            g["gallery_top"] = round(gal_y, 1)
            pg.screenshot(path=str(HERE / name), full_page=(cls == "phone"))
            full = Image.open(HERE / name).convert("RGB")
            g["ink"] = {
                "wordmark": ink_bbox(full, [g["mast"][0][k] for k in "xywh"], dsf, NAVY),
                "subline": ink_bbox(full, [g["mast"][1][k] for k in "xywh"], dsf, NAVY),
                "names_left": min(n["x"] for n in g["names"]),
                "block_bottoms": {bid: pg.evaluate("id => { const e=document.getElementById(id); return Math.max(...[...e.querySelectorAll('.ln,.note')].filter(x=>x.offsetParent).map(x=>x.getBoundingClientRect().bottom)) }", bid) for bid in ("b0", "b1", "b2", "b3")},
                "block_tops": {bid: pg.evaluate("id => document.getElementById(id).getBoundingClientRect().top", bid) for bid in ("b0", "b1", "b2", "b3")},
                "lines_ending_with_middot": pg.evaluate("() => [...document.querySelectorAll('.ln')].filter(e=>e.offsetParent && e.textContent.trim().endsWith('·')).map(e=>e.textContent)"),
                "continuation_lines": pg.evaluate("() => [...document.querySelectorAll('.ln')].filter(e=>e.offsetParent && e.textContent.trim().startsWith('·')).map(e=>e.textContent)"),
            }
            geom[name] = g
            report[name] = contrast(pg, dsf)
            pg.close()
        b.close()
    (HERE / "contrast.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (HERE / "geometry.json").write_text(json.dumps(geom, indent=1, ensure_ascii=False))
    for k, v in report.items():
        worst = sorted(v, key=lambda r: r["min_contrast"])[:3]
        print(k, "worst:", [(r["text"], r["min_contrast"]) for r in worst], "G", geom[k]["ground_line_G"], "gal", geom[k]["gallery_top"])
        print("  ink:", geom[k]["ink"])


if __name__ == "__main__":
    main()
