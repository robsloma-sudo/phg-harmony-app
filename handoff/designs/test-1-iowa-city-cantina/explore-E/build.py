#!/usr/bin/env python3
"""Explore-E  RÓTULO: hand-painted Mexican street-sign lettering, CSS/SVG only.

Builds menu.html from ../build/draft_doc.json (items/prices verbatim), renders
preview-letter.png (2550x3300) and preview-phone.png (1170 wide), and runs a
worst-pixel contrast check (text-free render vs. each text line's ink box).
"""
import json, math, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DOC = json.loads((ROOT / "build" / "draft_doc.json").read_text())
FONTS = (ROOT / "build" / "fonts").as_uri()

# Palette (flat sign-paint enamels)
RED, YEL, COB, GRN, INK, WHT, WALL = "#B8102A", "#FFC414", "#173E9A", "#0B6135", "#1B1512", "#FFFFFF", "#F4EAD3"

# Garnish / glass / method: phg.recipe_versions as cited in ../round-17/proposal.md
SERVE = {
    "beta_margarita":     "SHAKEN · ON THE ROCKS · LIME WHEEL",
    "beta_manhattan":     "STIRRED · COUPE · COCKTAIL CHERRY",
    "beta_old_fashioned": "STIRRED · ROCKS · LARGE CUBE · ORANGE PEEL",
    "beta_daiquiri":      "SHAKEN · COUPE · LIME COIN",
}
FRAC = {0.25: "¼", 0.5: "½", 0.75: "¾"}


def qty(c):
    q, u = c.get("quantity"), c.get("unit")
    if q is None or u in (None, "each"):
        return ""
    n = FRAC.get(q, ("%g" % q))
    if u == "dash":
        return f"{n} DASH{'ES' if q != 1 else ''} "
    return f"{n} {u.upper()} "


def spec_line(item):
    """Short punchy line from draft components. Garnish components are moved to the
    serve line; hidden components (meta.public_components false) are dropped; quantities
    are only shown when public_visibility.house_recipe is true."""
    hidden = {k for k, v in item["meta"].get("public_components", {}).items() if v is False}
    show_q = item["meta"].get("public_visibility", {}).get("house_recipe", True)
    parts = []
    for c in item["components"]:
        slug = c["name"].lower().replace(" ", "-")
        if slug in hidden or c.get("role") == "Garnish":
            continue
        name = c["name"].upper().replace(" JUICE", "")
        if item["id"] == "beta_daiquiri" and name == "DEMERARA SYRUP":
            name = "HOUSE DEMERARA SYRUP"  # draft desc: 'house demerara syrup'
        parts.append((qty(c) if show_q else "") + name)
    return " + ".join(parts)


def burst(value, fill=YEL, size=78):
    pts, n = [], 14
    for i in range(n * 2):
        r = 38 if i % 2 == 0 else 31
        a = math.pi * i / n - math.pi / 2
        pts.append(f"{40 + r * math.cos(a):.1f},{40 + r * math.sin(a):.1f}")
    return (f'<span class="burst" style="width:{size}px;height:{size}px">'
            f'<svg viewBox="0 0 80 80" aria-hidden="true"><polygon points="{" ".join(pts)}" '
            f'fill="{fill}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/></svg>'
            f'<b class="t price">{value:g}</b></span>')


def oval(value):
    return f'<span class="oval"><b class="t price">{value:g}</b></span>'


def sec(sid):
    return next(s for s in DOC["sections"] if s["id"] == sid)


def items_of(s):
    for sub in s["subs"]:
        yield sub["name"], sub["items"]
    if s["items"]:
        yield None, s["items"]


def cocktail_card(it):
    p = it["prices"][0]["value"]
    return f'''<div class="ck">
  <div class="ckhead"><h3 class="t name">{it["name"].upper()}</h3>{burst(p)}</div>
  <p class="t spec">{spec_line(it)}</p>
  <p class="t serve">— {SERVE[it["id"]]}</p>
</div>'''


def row(it):
    return f'''<div class="row"><div class="rt"><h3 class="t name">{it["name"].upper()}</h3>
<p class="t spec">{it["desc"].upper()}</p></div>{oval(it["prices"][0]["value"])}</div>'''


def board(title, color, body, cls="", tab_color=None):
    return f'''<section class="board {cls}" style="--bg:{color}">
  <h2 class="sign"><span class="t signtxt">{title}</span></h2>
  {body}
</section>'''


def build_html():
    ck = sec("sec_cocktails")
    ck_body = ""
    for subname, its in items_of(ck):
        ck_body += f'<div class="sub"><span class="t tab">{subname.upper()}</span></div><div class="ckgrid">'
        ck_body += "".join(cocktail_card(i) for i in its) + "</div>"

    def simple(sid):
        out = ""
        for subname, its in items_of(sec(sid)):
            if subname:
                out += f'<div class="sub"><span class="t tab">{subname.upper()}</span></div>'
            out += "".join(row(i) for i in its)
        return out

    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cantina &amp; Cocktail Bar · Bar menu</title>
<style>
@font-face{{font-family:Fraunces;font-weight:700;src:url({FONTS}/Fraunces-700-normal.ttf)}}
@font-face{{font-family:Fraunces;font-weight:600;src:url({FONTS}/Fraunces-600-normal.ttf)}}
@font-face{{font-family:'DM Sans';font-weight:700;src:url({FONTS}/DMSans-700-normal.ttf)}}
@font-face{{font-family:'DM Sans';font-weight:500;src:url({FONTS}/DMSans-500-normal.ttf)}}
@font-face{{font-family:'DM Sans';font-weight:400;src:url({FONTS}/DMSans-400-normal.ttf)}}
@page{{size:8.5in 11in;margin:0}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{WALL}}}
/* page 816x1056 css px = 612x792 pt; 36 pt safe margin = 48 px */
.page{{width:816px;height:1056px;padding:48px;position:relative;overflow:hidden;
  background:{WALL};display:flex;flex-direction:column;gap:14px;font-family:'DM Sans',sans-serif;color:{INK}}}
/* ART layer: painted wall trim, full bleed (+3 mm past trim handled by bleed box) */
.page::before{{content:"";position:absolute;inset:-12px;border:26px solid {GRN};
  box-shadow:inset 0 0 0 5px {WALL},inset 0 0 0 9px {RED};pointer-events:none}}
.page>*{{position:relative}}
/* header sign */
.marquee{{background:{RED};border:4px solid {WHT};outline:3px solid {INK};border-radius:14px;
  padding:14px 20px 12px;text-align:center}}
.wm{{font-family:Fraunces;font-weight:700;font-size:92px;line-height:.95;letter-spacing:4px;color:{YEL};
  -webkit-text-stroke:2.5px {INK};paint-order:stroke fill;
  text-shadow:2px 2px 0 {INK},4px 4px 0 {INK},6px 6px 0 {INK},8px 8px 0 {WHT},10px 10px 0 {INK}}}
.sub-wm{{display:flex;justify-content:center;gap:14px;margin-top:10px}}
.pill{{display:inline-block;background:{WHT};color:{INK};font-weight:700;font-size:15px;letter-spacing:3px;
  padding:5px 14px;border-radius:30px;border:2.5px solid {INK}}}
/* shop-front boards */
.board{{background:var(--bg);border:4px solid {WHT};outline:3px solid {INK};border-radius:12px;
  padding:0 16px 12px;color:{WHT}}}
.board.yel{{color:{INK}}}
.sign{{margin:-2px -2px 8px;text-align:center;line-height:1}}
.signtxt{{display:inline-block;font-family:Fraunces;font-weight:700;font-size:40px;letter-spacing:3px;
  color:{WHT};-webkit-text-stroke:2px {INK};paint-order:stroke fill;
  text-shadow:2px 2px 0 {INK},4px 4px 0 {INK},5px 5px 0 {INK};
  background:{INK};padding:6px 22px 8px;border-radius:0 0 12px 12px;
  border:3px solid {WHT};border-top:0}}
.signtxt{{background:transparent;border:0;padding:10px 0 2px}}
.sub{{margin:6px 0 4px}}
.tab{{display:inline-block;font-weight:700;font-size:13px;letter-spacing:3px;background:{WHT};color:{INK};
  padding:3px 10px;border-radius:4px}}
.ckgrid{{display:grid;grid-template-columns:1fr 1fr;gap:10px 22px;margin-bottom:6px}}
.ckhead,.row{{display:flex;align-items:center;justify-content:space-between;gap:10px}}
.name{{font-weight:700;font-size:19px;letter-spacing:1.6px;line-height:1.15}}
.spec{{font-weight:500;font-size:13.5px;letter-spacing:.6px;line-height:1.3;margin-top:2px}}
.serve{{font-weight:700;font-size:12.5px;letter-spacing:1px;line-height:1.3;margin-top:3px;color:{YEL}}}
.burst{{position:relative;flex:none;display:inline-flex;align-items:center;justify-content:center;
  filter:drop-shadow(3px 3px 0 {INK})}}
.burst svg{{position:absolute;inset:0;width:100%;height:100%}}
.price{{position:relative;font-family:Fraunces;font-weight:700;font-size:30px;color:{INK};line-height:1}}
.oval{{flex:none;display:inline-flex;align-items:center;justify-content:center;width:60px;height:42px;
  border-radius:50%;background:{YEL};border:2.5px solid {INK};box-shadow:3px 3px 0 {INK}}}
.oval .price{{font-size:24px}}
.row{{padding:5px 0;border-bottom:2px dashed rgba(255,255,255,.55)}}
.row:last-child{{border-bottom:0}}
.yel .row{{border-bottom-color:rgba(27,21,18,.45)}}
.yel .tab{{background:{INK};color:{YEL}}}
.yel .signtxt{{color:{RED};-webkit-text-stroke-color:{INK}}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.foot{{display:flex;justify-content:center;margin-top:auto}}
.foot .pill{{background:{YEL};font-size:14px}}
/* phone */
@media (max-width:600px){{
  .page{{width:390px;height:auto;padding:22px 18px 30px;gap:14px}}
  .page::before{{border-width:10px;box-shadow:inset 0 0 0 3px {WALL},inset 0 0 0 5px {RED}}}
  .wm{{font-size:58px;letter-spacing:2px}}
  .sub-wm{{flex-wrap:wrap;gap:6px}} .pill{{font-size:12px;letter-spacing:2px}}
  .ckgrid,.pair{{grid-template-columns:1fr}}
  .signtxt{{font-size:34px}}
  .name{{font-size:17px}} .spec{{font-size:14px}} .serve{{font-size:13px}}
}}
</style></head><body><main class="page">
<header class="marquee">
  <h1 class="t wm">CANTINA</h1>
  <div class="sub-wm"><span class="t pill">&amp; COCKTAIL BAR</span><span class="t pill">IOWA CITY, IOWA</span></div>
</header>
{board("COCKTAILS", COB, ck_body)}
<div class="pair">
{board("BEER", GRN, simple("sec_beer"))}
{board("WINE", RED, simple("sec_wine"))}
</div>
<div class="pair">
{board("SPIRITS", INK, simple("sec_spirits"))}
{board("CIDER", YEL, simple("sec_cider"), cls="yel")}
</div>
<div class="foot"><span class="t pill">¡SALUD! · GOOD DRINKS · GOOD COMPANY</span></div>
</main></body></html>'''


# ---------- contrast ----------
def lum(rgb):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def cr(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def parse_rgb(s):
    return tuple(int(float(x)) for x in s[s.index("(") + 1:s.index(")")].split(",")[:3])


def render():
    from playwright.sync_api import sync_playwright
    from PIL import Image
    html = HERE / "menu.html"
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
        # letter: 816 css px * 3.125 = 2550
        pg = b.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=3.125)
        pg.goto(html.as_uri()); pg.wait_for_timeout(400)
        ov = pg.evaluate("()=>{const m=document.querySelector('.page');return [m.scrollHeight,m.clientHeight]}")
        pg.screenshot(path=str(HERE / "preview-letter.png"), clip={"x": 0, "y": 0, "width": 816, "height": 1056})
        boxes = pg.evaluate("""()=>[...document.querySelectorAll('.t')].map(e=>{
          const r=document.createRange();r.selectNodeContents(e);const q=r.getBoundingClientRect();
          return {cls:e.className,txt:e.textContent.slice(0,30),x:q.x,y:q.y,w:q.width,h:q.height,
                  col:getComputedStyle(e).color}})""")
        # bleed/margin check: every text box inside 48px margin
        bad_margin = [bx for bx in boxes if bx["x"] < 48 or bx["y"] < 48 or bx["x"] + bx["w"] > 768 or bx["y"] + bx["h"] > 1008]
        pg.add_style_tag(content=".t{color:transparent!important;-webkit-text-stroke:0!important;text-shadow:none!important}")
        pg.wait_for_timeout(100)
        pg.screenshot(path="/tmp/claude-0/e_textfree.png", clip={"x": 0, "y": 0, "width": 816, "height": 1056})
        # phone
        ph = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3)
        ph.goto(html.as_uri()); ph.wait_for_timeout(400)
        ph.screenshot(path=str(HERE / "preview-phone.png"), full_page=True)
        b.close()
    im = Image.open("/tmp/claude-0/e_textfree.png").convert("RGB")
    s = 3.125
    worst = {}
    for bx in boxes:
        col = parse_rgb(bx["col"])
        x0, y0 = int((bx["x"] - 2) * s), int((bx["y"] - 2) * s)
        x1, y1 = int((bx["x"] + bx["w"] + 2) * s), int((bx["y"] + bx["h"] + 2) * s)
        crop = im.crop((x0, y0, x1, y1))
        cols = crop.getcolors(10_000_000)
        m = min(cr(col, c) for _, c in cols)
        key = bx["cls"].replace("t ", "")
        if key not in worst or m < worst[key][0]:
            worst[key] = (round(m, 2), bx["txt"])
    print("overflow scroll/client:", ov)
    print("text outside 36pt margin:", [(b_["txt"], round(b_["x"]), round(b_["y"])) for b_ in bad_margin])
    for k, v in sorted(worst.items(), key=lambda kv: kv[1][0]):
        print(f"  {k:10s} worst {v[0]:6.2f}  e.g. {v[1]!r}")
    print("letter size:", Image.open(HERE / "preview-letter.png").size,
          "phone size:", Image.open(HERE / "preview-phone.png").size)


if __name__ == "__main__":
    (HERE / "menu.html").write_text(build_html())
    os.makedirs("/tmp/claude-0", exist_ok=True)
    render()
