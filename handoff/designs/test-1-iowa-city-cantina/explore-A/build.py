"""Explore-A: brutalist typographic poster. Builds menu.html from draft_doc.json, renders letter + phone PNGs,
checks contrast pairs and overflow. Fonts: system Liberation Sans / Liberation Mono (no Google)."""
import json, pathlib, html
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
DOC = json.load(open(HERE.parent / "build" / "draft_doc.json"))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
E = html.escape

INK, PAPER, ACC = "#0D0D0D", "#F1EEE6", "#FF5A1F"   # black, off-white, safety orange (field only, never text colour)

# garnish / glass / method: phg.recipe_versions rows cited in ../round-17/proposal.md
SERVE = {
    "beta_margarita": ("rocks", "lime wheel", "shaken"),
    "beta_manhattan": ("coupe", "cocktail cherry", "stirred"),
    "beta_old_fashioned": ("rocks · large cube", "orange peel", "stirred"),
    "beta_daiquiri": ("coupe", "lime coin", "shaken"),
}
FR = {0.25: "¼", 0.5: "½", 0.75: "¾"}
def qty(q):
    return FR.get(q, str(int(q)) if float(q).is_integer() else str(q))

def lum(h):
    c = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def cr(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True); return (la + 0.05) / (lb + 0.05)
PAIRS = {"ink on paper": cr(INK, PAPER), "ink on orange": cr(INK, ACC), "paper on ink": cr(PAPER, INK)}
assert all(v >= 4.5 for v in PAIRS.values()), PAIRS

def spec_lines(it):
    hidden = {k for k, v in it["meta"].get("public_components", {}).items() if v is False}
    show_qty = it["meta"]["public_visibility"].get("house_recipe", True)
    out = []
    for c in it["components"]:
        slug = c["name"].lower().replace(" ", "-")
        if slug in hidden or c["role"] == "Garnish":
            continue
        q = f'{qty(c["quantity"])} {c["unit"]}' if show_qty else ""
        name = c["name"].lower()
        if it["id"] == "beta_daiquiri" and c["name"] == "Demerara Syrup":
            name = "house demerara syrup"          # draft desc wording
        out.append((q, name))
    return out

def cocktail(it):
    glass, garnish, method = SERVE[it["id"]]
    rows = "".join(f'<div class="sl"><span class="q">{E(q)}</span><span>{E(n)}</span></div>' for q, n in spec_lines(it))
    return f'''<div class="ck"><div class="big">{it["prices"][0]["value"]}</div>
<div class="ckb"><div class="nm">{E(it["name"].upper())}</div><div class="spec">{rows}</div></div>
<dl class="meta"><dt>glass</dt><dd>{E(glass)}</dd><dt>garnish</dt><dd>{E(garnish)}</dd><dt>method</dt><dd>{E(method)}</dd></dl></div>'''

def small(it):
    return f'''<div class="sm"><div class="mid">{it["prices"][0]["value"]}</div><div><div class="snm">{E(it["name"].upper())}</div><div class="sd">{E(it["desc"])}</div></div></div>'''

S = {s["id"]: s for s in DOC["sections"]}
def lower(sid, idx):
    s = S[sid]; body = ""
    for sb in s["subs"]:
        if len(s["subs"]) > 1: body += f'<div class="sub">{E(sb["name"].upper())}</div>'
        body += "".join(small(i) for i in sb["items"])
    body += "".join(small(i) for i in s["items"])
    return f'<section class="lc"><div class="lh"><span class="ix">{idx}</span>{E(s["name"].upper())}</div>{body}</section>'

ck = S["sec_cocktails"]; ckhtml = ""
for sb in ck["subs"]:
    ckhtml += f'<div class="ckrule"><span>{E(sb["name"].upper())}</span></div>' + "".join(cocktail(i) for i in sb["items"])

HTML = f'''<!doctype html><html><head><meta charset="utf-8"><title>Cantina — Bar menu (explore A)</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#777}}
.page{{width:816px;height:1056px;background:{PAPER};color:{INK};font-family:"Liberation Sans",Arial,sans-serif;position:relative;overflow:hidden;padding:48px 48px 48px 48px}}
.mast{{display:grid;grid-template-columns:repeat(12,1fr);column-gap:12px;align-items:end;border-bottom:10px solid {INK};padding-bottom:6px}}
.word{{grid-column:1/10;font-weight:700;font-size:108px;line-height:.78;letter-spacing:-.065em}}
.kick{{grid-column:10/13;font-weight:700;font-size:11px;letter-spacing:.14em;line-height:1.45;text-align:right}}
.band{{background:{ACC};margin:14px -48px 0;padding:10px 48px 6px;position:relative}}
.bh{{display:flex;justify-content:space-between;align-items:baseline;font-weight:700;font-size:12px;letter-spacing:.16em;border-bottom:3px solid {INK};padding-bottom:5px}}
.bh .t{{font-size:30px;letter-spacing:-.02em}} .ix{{font-family:"Liberation Mono",monospace;margin-right:10px;font-weight:700}}
.bh .d{{font-family:"Liberation Mono",monospace;font-weight:400;letter-spacing:0;font-size:12px}}
.ckrule{{font-size:11px;font-weight:700;letter-spacing:.2em;padding:6px 0 0;margin-left:244px}}
.ck{{display:grid;grid-template-columns:232px 1fr 214px;column-gap:12px;border-bottom:2px solid {INK};padding:0 0 4px;align-items:start}}
.ck:last-child{{border-bottom:0}}
.big{{font-weight:700;font-size:122px;line-height:.74;letter-spacing:-.07em;text-align:right;padding-top:9px;padding-right:10px;border-right:6px solid {INK};height:100%}}
.ckb{{padding-top:8px}}
.nm{{font-weight:700;font-size:19px;letter-spacing:.05em;line-height:1.1;margin-bottom:5px}}
.spec{{font-family:"Liberation Mono",monospace;font-size:13px;line-height:1.3}}
.sl{{display:grid;grid-template-columns:52px 1fr}} .q{{font-weight:700}}
.meta{{display:grid;grid-template-columns:62px 1fr;font-family:"Liberation Mono",monospace;font-size:12px;line-height:1.35;padding-top:10px;border-left:2px solid {INK};padding-left:9px;align-self:stretch;align-content:start}}
.meta dt{{font-weight:700;text-transform:uppercase;font-size:10.5px;letter-spacing:.06em;padding-top:1px}}
.low{{display:grid;grid-template-columns:repeat(3,1fr);column-gap:12px;margin-top:12px}}
.lc{{border-top:10px solid {INK};padding-top:4px}} .stack .lc+.lc{{margin-top:6px}} .low{{align-items:start}}
.lh{{font-weight:700;font-size:21px;letter-spacing:-.01em;margin-bottom:4px}}
.sub{{font-size:10.5px;font-weight:700;letter-spacing:.2em;margin:6px 0 1px}}
.sm{{display:grid;grid-template-columns:52px 1fr;column-gap:8px;border-top:2px solid {INK};padding:3px 0 4px;align-items:start}}
.mid{{font-weight:700;font-size:40px;line-height:.8;letter-spacing:-.06em;padding-top:3px}}
.snm{{font-weight:700;font-size:13px;letter-spacing:.05em;line-height:1.15}}
.sd{{font-family:"Liberation Mono",monospace;font-size:12px;line-height:1.3}}
.foot{{position:absolute;left:48px;right:48px;bottom:48px;display:flex;justify-content:space-between;align-items:end;font-weight:700;font-size:11px;letter-spacing:.16em;border-top:3px solid {INK};padding-top:6px}}
.foot .m{{font-family:"Liberation Mono",monospace;letter-spacing:0;font-weight:400}}
@media (max-width:500px){{
 .page{{width:390px;height:auto;padding:24px 20px 28px}}
 .word{{grid-column:1/13;font-size:88px}} .kick{{grid-column:1/13;text-align:left;margin-top:10px}}
 .band{{margin:14px -20px 0;padding:10px 20px 6px}} .bh{{flex-wrap:wrap}} .bh .d{{width:100%}}
 .ckrule{{margin-left:0}}
 .ck{{grid-template-columns:112px 1fr;row-gap:6px}} .big{{font-size:82px;padding-right:8px;border-right-width:4px}}
 .meta{{grid-column:1/3;border-left:0;border-top:2px solid {INK};padding:4px 0 0}}
 .low{{grid-template-columns:1fr}} .lc{{margin-bottom:12px}}
 .foot{{position:static;margin-top:10px;flex-wrap:wrap;gap:6px}}
}}
</style></head><body><div class="page">
<header class="mast"><div class="word">CANTINA</div><div class="kick">&amp; COCKTAIL BAR<br>IOWA CITY, IOWA<br>{E(DOC["title"].upper())}</div></header>
<section class="band"><div class="bh"><span class="t"><span class="ix">01</span>{E(ck["name"].upper())}</span><span class="d">{E(ck["desc"])}</span></div>{ckhtml}</section>
<div class="low"><div class="stack">{lower("sec_beer","02")}{lower("sec_cider","03")}</div>{lower("sec_wine","04")}{lower("sec_spirits","05")}</div>
<footer class="foot"><span>GOOD DRINKS / GOOD COMPANY</span><span class="m">{E(DOC.get("subtitle",""))}</span></footer>
</div></body></html>'''
(HERE / "menu.html").write_text(HTML)

CHECK = r"""() => { const pg=document.querySelector('.page').getBoundingClientRect(); const bad=[];
 document.querySelectorAll('.page *').forEach(e=>{ if(!e.childElementCount && e.textContent.trim()){ const b=e.getBoundingClientRect();
  if(e.closest('.band')&&!e.closest('.big')) {} 
  if(b.left<pg.left+47.5||b.right>pg.right-47.5||b.bottom>pg.bottom-47.5||b.top<pg.top+47.5) bad.push([e.textContent.trim().slice(0,30),Math.round(b.left-pg.left),Math.round(b.top-pg.top),Math.round(b.right-pg.left),Math.round(b.bottom-pg.top)]);
  if(e.scrollWidth>e.clientWidth+1 && getComputedStyle(e).display!='inline') bad.push(['overflow',e.textContent.slice(0,30)]); }});
 const low=document.querySelector('.low').getBoundingClientRect(), f=document.querySelector('.foot').getBoundingClientRect();
 const lcs=[...document.querySelectorAll('.lc')].map(x=>x.getBoundingClientRect().bottom-pg.top);
 return {bad, low_bottom:Math.max(...lcs), foot_top:f.top-pg.top}; }"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=3.125)
    pg.goto((HERE / "menu.html").as_uri()); pg.wait_for_timeout(300)
    print("contrast", {k: round(v, 2) for k, v in PAIRS.items()})
    print("letter check", pg.evaluate(CHECK))
    pg.locator(".page").screenshot(path=str(HERE / "preview-letter.png"))
    ph = b.new_page(viewport={"width": 390, "height": 800}, device_scale_factor=3)
    ph.goto((HERE / "menu.html").as_uri()); ph.wait_for_timeout(300)
    ph.locator(".page").screenshot(path=str(HERE / "preview-phone.png"))
    b.close()
from PIL import Image
for f in ("preview-letter.png", "preview-phone.png"):
    print(f, Image.open(HERE / f).size)
