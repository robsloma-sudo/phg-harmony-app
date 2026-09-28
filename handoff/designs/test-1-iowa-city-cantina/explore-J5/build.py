#!/usr/bin/env python3
"""TEST-1 explore-J5 "Horizon", round 5 (checkpoint: ../explore-J4).

ART (raster, text-free, generated here with numpy/PIL at full print resolution, two screen-print inks + paper):
  navy dusk field (top band + the right column down to the ground line), a true-profile Iowa grain elevator
  left as unprinted paper (headhouse + leg housing, gallery bridge, a row of domed cylindrical bins cropped by
  the page edge), standing on an amber ground band whose lower edge is cut like the border of a papel picado
  banner (picos + pierced rombos). Riso-style grain and a 0.25 mm misregistration of the amber pass, both
  suppressed behind the wordmark.
TEXT: HTML over the art. Cocktails on columns 1-2; lower tier in three max-content columns spread flush to both
  frame edges. Descriptions are broken at ingredient boundaries (never after a middot, no orphan garnish).

Content: ../build/draft_doc.json + garnish from phg.recipe_versions (cited in ../round-17/proposal.md) + spirits
lines from public.beverage_categories (gateway log ids 225, 226). Nothing invented.
Usage: python3 build.py [before|after]    (env J5_ABL=a,b removes named devices)
"""
import json, sys, html, io, re, os, glob
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
DRAFT = json.load(open(HERE.parent / "build" / "draft_doc.json"))
FONTDIR = HERE.parent / "build" / "fonts"
FONTS = FONTDIR.as_uri()
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "after"
BEFORE = VARIANT == "before"
esc = html.escape
NB = " "

NAVY, AMBER = (0x1E, 0x21, 0x47), (0xD9, 0x8A, 0x2E)
PAPER = (0xF4, 0xED, 0xE1)
HEX = lambda c: "#%02X%02X%02X" % c
AMBER_INK, INK, MUTED = "#8F4F10", "#221C22", "#5B5058"

# ---- content ---------------------------------------------------------------------------------------------------
# Lists of ingredient phrases (cocktails) or single phrases. Cocktail garnish from phg.recipe_versions.
PARTS = {
    "beta_margarita": ["Tequila blanco", "fresh lime juice", "orange liqueur", "agave syrup", "lime wheel"],  # rv f06abb74
    "beta_manhattan": ["Rye whiskey", "sweet vermouth", "cocktail cherry"],                 # bitters hidden; rv 9fb77eaa
    "beta_daiquiri": ["White rum", "fresh lime juice", "demerara syrup", "lime coin"],      # rv 14d45e57
    "beta_old_fashioned": ["Brown butter-washed bourbon", "demerara syrup", "aromatic bitters", "orange peel"],  # rv 7095fd3d
    "beta_czech_pilsner": ["Crisp pale lager"],
    "beta_dry_hopped_ipa": ["Hop-forward draft IPA"],       # draft text kept (brief section 5 keeps the style words)
    "beta_amber_lager": ["Toasty amber lager"],
    "beta_malbec": ["Dry red wine"],
    "beta_pinot_grigio": ["Dry white wine"],
    "beta_brut_rose": ["Dry sparkling rosé"],
    # public.beverage_categories (via phg_designer_query, log 225/226):
    "beta_blanco_tequila": ["Blanco-class agave spirit", "pour"],   # spirits.agave_spirits.tequila.blanco (NOM-006-SCFI-2012 §5 clase)
    "beta_anejo_tequila": ["Añejo-class agave spirit", "pour"],     # spirits.agave_spirits.tequila.anejo (NOM-006-SCFI-2012 §5 clase)
    "beta_cognac_vsop": ["Grape brandy from Cognac", "pour"],       # spirits.brandy_fruit_spirits.grape_brandy.cognac.vsop
    "beta_dry_cider": ["Dry sparkling cider"],
}
NOTE = {"beta_margarita": "Bright and citrus-forward."}   # the only draft that supplies a tasting note
ORDER_FIRST = {"sub_cocktails_classics": ["beta_margarita", "beta_manhattan"]}
SEC = {s["id"]: s for s in DRAFT["sections"]}
ALL_IDS = {it["id"] for s in DRAFT["sections"] for sb in s["subs"] for it in sb["items"]} | \
          {it["id"] for s in DRAFT["sections"] for it in s["items"]}
assert len(ALL_IDS) == 14 and set(PARTS) == ALL_IDS

_F = ImageFont.truetype(str(FONTDIR / "DMSans-400-normal.ttf"), 400)


def textw(t, px):
    return _F.getlength(t) * px / 400


def break_parts(parts, px, measure):
    """Fewest lines that fit; among those, the most even split. Breaks only between ingredients and the
    separator at a break is dropped, so no line ends (or starts) with a middot; no lone last ingredient
    when it can be avoided."""
    SEP = " · "
    n = len(parts)
    best = None
    for k in range(1, n + 1):
        import itertools
        for cuts in itertools.combinations(range(1, n), k - 1):
            idx = (0,) + cuts + (n,)
            lines = [SEP.join(parts[idx[i]:idx[i + 1]]) for i in range(k)]
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
            f'<span class="ln">{esc(l).replace(" ", NB).replace(NB + "·" + NB, " · ")}</span>' for l in lines) + "</span>")
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


# ---- ART (raster) ----------------------------------------------------------------------------------------------
def flags():
    f = dict(grain=True, misreg=True, density=True, piercings=True, picos=True, seams=True, posts=True,
             leg=True, gallery=True, caps=True, headhouse_gap=True, band_top_rule=True)
    if not BEFORE:
        f.update(density=False, band_top_rule=False, posts=False)
    for k in filter(None, os.environ.get("J5_ABL", "").split(",")):
        f[k] = False
    return f


def draw_art(W, H, s, Hz, G, P, F, safe_boxes, seed=5):
    """W,H css px; s = device px per css px. Returns an RGB image W*s x H*s.
    Hz: bottom of the navy top band; G: ground line (top of the amber band); P: geometry."""
    Wp, Hp = int(round(W * s)), int(round(H * s))
    S = lambda v: v * s
    navy = Image.new("L", (Wp, Hp), 0)
    amber = Image.new("L", (Wp, Hp), 0)
    dn, da = ImageDraw.Draw(navy), ImageDraw.Draw(amber)
    B = 12
    # navy: top band + right column down to the ground line
    dn.rectangle([S(-B), S(-B), S(W + B), S(Hz)], fill=255)
    dn.rectangle([S(P["col_x"]), S(-B), S(W + B), S(G)], fill=255)
    # amber ground band: straight top at G (the elevator stands on it), papel-picado lower edge
    bh, pico = P["band_h"], P["pico"]
    da.rectangle([S(-B), S(G), S(W + B), S(G + bh)], fill=255)
    if F["picos"]:
        x = -B
        while x < W + B:
            da.polygon([(S(x), S(G + bh)), (S(x + pico), S(G + bh)), (S(x + pico / 2), S(G + bh + pico * 0.55))], fill=255)
            x += pico
    if F["piercings"]:   # pierced rombos and dots, alternating, on the band's centre line
        x, k = -B + pico / 2, 0
        cy = G + bh * 0.52
        while x < W + B:
            if k % 2 == 0:
                r = P["rombo"]
                da.polygon([(S(x), S(cy - r)), (S(x + r * 0.62), S(cy)), (S(x), S(cy + r)), (S(x - r * 0.62), S(cy))], fill=0)
            else:
                r = P["dot"]
                da.ellipse([S(x - r), S(cy - r), S(x + r), S(cy + r)], fill=0)
            x += pico
            k += 1
    # elevator: knocked out of the navy (unprinted paper)
    hx, hw, ht = P["hx"], P["hw"], P["h_top"]
    ko = Image.new("L", (Wp, Hp), 0)
    dk = ImageDraw.Draw(ko)
    dk.rectangle([S(hx), S(ht), S(hx + hw), S(G)], fill=255)                               # headhouse
    if F["leg"]:
        lx, lw, lh = hx + P["leg_off"], P["leg_w"], P["leg_h"]
        dk.rectangle([S(lx), S(ht - lh), S(lx + lw), S(ht)], fill=255)                    # leg housing
        dk.polygon([(S(lx - 2), S(ht - lh)), (S(lx + lw / 2), S(ht - lh - P["leg_roof"])), (S(lx + lw + 2), S(ht - lh))], fill=255)
    bx0 = hx + hw + (P["hgap"] if F["headhouse_gap"] else 0)
    bw, bt, cap = P["bin_w"], P["bin_top"], P["cap_h"]
    x = bx0
    tops = []
    while x < W + B:
        dk.rectangle([S(x), S(bt), S(x + bw), S(G)], fill=255)
        if F["caps"]:
            dk.pieslice([S(x), S(bt - cap), S(x + bw), S(bt + cap)], 180, 360, fill=255)
        tops.append(x + bw / 2)
        x += bw
    if F["seams"]:
        x = bx0 + bw
        while x < W + B:
            dk.rectangle([S(x - P["seam"] / 2), S(bt - cap), S(x + P["seam"] / 2), S(G)], fill=0)
            x += bw
    if F["gallery"]:
        gy, gh = P["gal_y"], P["gal_h"]
        dk.rectangle([S(hx + hw - 1), S(gy), S(W + B), S(gy + gh)], fill=255)
        if F["posts"]:
            for cx in tops:
                dk.rectangle([S(cx - 2), S(gy + gh - 1), S(cx + 2), S(bt - cap + 1)], fill=255)
    if F["band_top_rule"]:
        da.rectangle([S(-B), S(G - 3), S(W + B), S(G)], fill=255)
    n = np.asarray(navy, dtype=np.float32) / 255 * (1 - np.asarray(ko, dtype=np.float32) / 255)
    a = np.asarray(amber, dtype=np.float32) / 255
    rng = np.random.default_rng(seed)
    if F["misreg"]:   # the amber pass lands 0.25 mm (3 px at 300 dpi) right and 2 px down
        a = np.roll(np.roll(a, int(round(s * 0.95)), axis=1), int(round(s * 0.65)), axis=0)
    safe = np.zeros((Hp, Wp), dtype=np.float32)
    for (x0, y0, x1, y1) in safe_boxes:
        safe[int(S(y0)):int(S(y1)), int(S(x0)):int(S(x1))] = 1
    soft = Image.fromarray((safe * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(S(28)))
    safe = np.clip(np.asarray(soft, np.float32) / 255 * 2.2, 0, 1)      # 1 over the type, smooth fade outside

    def grain(cov, p_void, amp):
        """Riso-like ink: fine mottling of ink density + sparse ink-starved pinholes. Both fade to ~25%
        within a very soft zone around the display type (no visible box)."""
        from scipy.ndimage import gaussian_filter
        k = 1 - safe
        fine = gaussian_filter(rng.standard_normal(cov.shape).astype(np.float32), 0.9)
        fine /= fine.std() + 1e-6
        mott = gaussian_filter(rng.standard_normal(cov.shape).astype(np.float32), 2.2)
        mott /= mott.std() + 1e-6
        dens = np.clip(0.93 + amp * k * 0.5 * mott, 0, 1)     # mean-neutral mottling around 93% ink
        voids = (fine < np.quantile(fine, p_void)).astype(np.float32) * k
        out = cov * dens * (1 - 0.9 * voids)
        if F["density"]:
            low = gaussian_filter(rng.standard_normal((cov.shape[0] // 16 + 1, cov.shape[1] // 16 + 1)).astype(np.float32), 3)
            low = np.kron(low, np.ones((16, 16), np.float32))[:cov.shape[0], :cov.shape[1]]
            out *= 1 - 0.05 * k * (low - low.min()) / (np.ptp(low) + 1e-6)
        return out

    if F["grain"]:
        n = grain(n, 0.005, 0.09)
        a = grain(a, 0.008, 0.10)
    paper = np.array(PAPER, np.float32) / 255
    img = np.ones((Hp, Wp, 3), np.float32) * paper
    for cov, ink in ((a, AMBER), (n, NAVY)):     # multiply overprint, amber pass first
        inkf = np.array(ink, np.float32) / 255
        img = img * (1 - cov[..., None]) + img * inkf * cov[..., None]
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))


LETTER = dict(col_x=452, band_h=28, pico=22, rombo=6.5, dot=3, hx=496, hw=92, h_top=128, leg_off=12, leg_w=34,
              leg_h=46, leg_roof=10, hgap=6, bin_w=62, bin_top=280, cap_h=17, seam=3, gal_y=236, gal_h=15)
PHONE = dict(col_x=0, band_h=26, pico=18, rombo=5, dot=2.4, hx=236, hw=56, h_top=150, leg_off=8, leg_w=22,
             leg_h=30, leg_roof=7, hgap=4, bin_w=40, bin_top=228, cap_h=11, seam=2, gal_y=200, gal_h=10)
HZ_L = 180


def page_html():
    ML = {"L": (13.5, 372), "P": (13.5, 342)}      # cocktails measure (letter cols 1-2 / phone)
    MS = {"L": (13.5, 250), "P": (13.5, 342)}      # lower tier (max-content columns; generous cap)
    cocktails = section_html(SEC["sec_cocktails"], ML, cls="sec main")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Cantina — bar menu (explore-J5 Horizon)</title>
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
.read{{position:absolute;left:var(--m);top:var(--rt);width:var(--tw)}}
h2{{font:600 var(--h2)/16px Dm;letter-spacing:.3em;text-transform:uppercase;color:{AMBER_INK};margin-bottom:16px}}
h3{{font:italic 400 var(--h3)/26px Fr;color:{MUTED};margin-bottom:6px}}
.grp+.grp{{margin-top:var(--grpgap)}}
.it+.it{{margin-top:var(--itgap)}}
.nm{{font:500 var(--nm)/26px Fr;font-variation-settings:"opsz" 18;color:{INK};font-variant-numeric:lining-nums tabular-nums;white-space:nowrap}}
.nm .p{{font-weight:400;color:{MUTED};margin-left:.75em}}
.ds{{display:block;font:400 var(--ds)/18px Dm;color:{MUTED}}}
.ds .ln{{display:block;white-space:nowrap}}
.note{{display:block;font:italic 400 var(--ds)/18px Fr;color:{MUTED}}}
.v-P{{display:none}} body.phone .v-L{{display:none}} body.phone .v-P{{display:block}}
.row{{display:grid;grid-template-columns:max-content max-content max-content;justify-content:space-between;align-items:start}}
body.letter .page{{width:816px;height:1056px;
  --m:60px;--mt:50px;--tw:696px;--rt:{HZ_L + 32}px;--wm:76px;--wmfix:-3px;--subsz:12.5px;--subgap:22px;--h2:12.5px;--h3:15.5px;
  --nm:18.5px;--ds:13.5px;--itgap:14px;--grpgap:22px}}
body.letter .main{{width:380px}}
body.letter .row{{margin-top:var(--tiergap)}}
body.phone .page{{width:390px;
  --m:24px;--mt:44px;--tw:342px;--wm:44px;--wmfix:-1.5px;--subsz:10.5px;--subgap:12px;--h2:12px;--h3:15px;
  --nm:17.5px;--ds:13.5px;--itgap:16px;--grpgap:26px}}
body.phone .read{{position:relative;top:0;left:0;margin-left:24px;padding:var(--rt) 0 52px}}
body.phone .row{{display:block;margin-top:44px}}
body.phone .col+.col{{margin-top:44px}}
</style></head><body class="{{BODYCLASS}}"><div class="page" style="{{PAGESTYLE}}">
<header class="mast"><div class="wm">CANTINA</div><div class="sub">&amp; cocktail bar · Iowa City, Iowa</div></header>
<main class="read">
{cocktails}
<div class="row"><div class="col">{section_html(SEC["sec_spirits"], MS)}</div><div class="col">{beer_cider_html(MS)}</div><div class="col">{section_html(SEC["sec_wine"], MS)}</div></div>
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

        for name, cls, w, h, dsf in [("preview-letter.png", "letter", 816, 1056, 3.125),
                                     ("preview-phone.png", "phone", 390, 900, 3)]:
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            d0 = base.replace("{BODYCLASS}", cls)
            if cls == "letter":
                gap, band = 22, LETTER["band_h"] + LETTER["pico"] * 0.55
                css = f"--tiergap:{gap * 2 + band:.0f}px"
                load(pg, d0.replace("{PAGESTYLE}", css), cls)
                mb = pg.evaluate("() => { const e=[...document.querySelectorAll('.main .ln,.main .note')].filter(x=>x.offsetParent).pop().getBoundingClientRect(); return e.bottom }")
                G = round(mb + gap)
                wm = pg.evaluate("() => { const r=document.querySelector('.mast').getBoundingClientRect(); return [r.left-18,r.top-18,r.right+18,r.bottom+18] }")
                art = draw_art(816, 1056, dsf, HZ_L, G, LETTER, F, [wm])
                art_name = "art-letter.png"
            else:
                css = "--rt:0px"
                load(pg, d0.replace("{PAGESTYLE}", css), cls)
                wm = pg.evaluate("() => { const r=document.querySelector('.mast').getBoundingClientRect(); return [r.left-18,r.top-18,r.right+18,r.bottom+18] }")
                Gp = 300
                H = pg.evaluate("document.querySelector('.page').scrollHeight") + Gp + 72
                art = draw_art(390, H, dsf, Gp, Gp, PHONE, F, [wm])
                art_name = "art-phone.png"
                G = Gp
                css = f"--rt:{Gp + PHONE['band_h'] + PHONE['pico'] * 0.55 + 36:.0f}px;height:{H}px"
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
            pg.screenshot(path=str(HERE / name), full_page=(cls == "phone"))
            full = Image.open(HERE / name).convert("RGB")
            g["ink"] = {
                "wordmark": ink_bbox(full, [g["mast"][0][k] for k in "xywh"], dsf, NAVY),
                "subline": ink_bbox(full, [g["mast"][1][k] for k in "xywh"], dsf, NAVY),
                "names_left": min(n["x"] for n in g["names"]),
                "lower_tier_right": max(l["x"] + l["w"] for l in g["lines"] + g["prices"] if l["y"] > G),
                "lower_tier_left": min(n["x"] for n in g["names"] if n["y"] > G),
                "column_bottoms": [max(l["y"] + l["h"] for l in g["lines"] if c["x"] <= l["x"] < c["x"] + c["w"] and l["y"] >= c["y"]) for c in g["columns"]],
                "line_ends_with_middot": pg.evaluate("() => [...document.querySelectorAll('.ln')].filter(e=>e.offsetParent && e.textContent.trim().endsWith('·')).map(e=>e.textContent)"),
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
