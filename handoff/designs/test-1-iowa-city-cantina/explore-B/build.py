"""Explore-B: Mexican modernism / courtyard of flat colour planes. Builds menu.html, renders previews, checks contrast + fit."""
import json, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
DRAFT = json.loads((HERE.parent / "build" / "draft_doc.json").read_text())
FONTS = (HERE.parent / "build" / "fonts").as_uri()

# Palette (flat planes; no texture, so the plane colour IS the worst pixel)
C = dict(plaster="#F5EEE2", rosa="#C2185B", shadow="#7E0E3E", marigold="#F2A93B",
         cobalt="#1D3A8A", water="#A9D0CF", ink="#1B1A2B", cream="#FBF6EC", rosa_ink="#A3124C", water_ink="#12306A")

# Calm sentences built only from draft components + phg.recipe_versions glass/garnish/method (see round-17/proposal.md).
# Manhattan: aromatic bitters hidden per meta.public_components. Quantities are not printed (Old Fashioned house_recipe=false);
# they set the order (base spirit first, then by quantity/role).
COCKTAIL_DESC = {
 "beta_margarita": "Shaken with tequila blanco, fresh lime, orange liqueur and agave syrup; served on the rocks with a lime wheel.",
 "beta_manhattan": "Stirred with rye whiskey and sweet vermouth; served up in a coupe with a cocktail cherry.",
 "beta_daiquiri": "Shaken with white rum, fresh lime and house demerara syrup; served up in a coupe with a lime coin.",
 "beta_old_fashioned": "Stirred with brown butter-washed bourbon, demerara syrup and aromatic bitters; served in a rocks glass over a large cube with an orange peel.",
}

def price(it):
    v = it["prices"][0]["value"]; return f"{v:g}"

def item_html(it, cocktail=False):
    d = COCKTAIL_DESC[it["id"]] if cocktail else it["desc"]
    return (f'<div class="item" data-id="{it["id"]}"><div class="row"><span class="nm">{it["name"]}</span>'
            f'<span class="ld"></span><span class="pr">{price(it)}</span></div><p class="ds">{d}</p></div>')

def section_html(sec, cls=""):
    out = [f'<section class="sec {cls}"><h2><i class="sq"></i>{sec["name"]}</h2>']
    for sub in sec["subs"]:
        out.append(f'<h3>{sub["name"]}</h3>')
        out += [item_html(i, sec["id"] == "sec_cocktails") for i in sub["items"]]
    out += [item_html(i) for i in sec["items"]]
    out.append("</section>")
    return "\n".join(out)

S = {s["id"]: s for s in DRAFT["sections"]}
n_items = sum(len(s["items"]) + sum(len(b["items"]) for b in s["subs"]) for s in DRAFT["sections"])
assert n_items == 14, n_items

HTML = f"""<!doctype html><html><head><meta charset="utf-8"><title>Cantina &amp; Cocktail Bar — courtyard</title>
<style>
@font-face{{font-family:DMS;src:url({FONTS}/DMSans-400-normal.ttf);font-weight:400}}
@font-face{{font-family:DMS;src:url({FONTS}/DMSans-500-normal.ttf);font-weight:500}}
@font-face{{font-family:DMS;src:url({FONTS}/DMSans-700-normal.ttf);font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#ddd;font-family:DMS,sans-serif;color:{C['ink']}}}
.page{{position:relative;width:816px;height:1056px;overflow:hidden;background:{C['plaster']}}}
/* ART layer: flat architectural planes (CSS). Full-bleed planes run 12px (~3.2mm) past trim. */
.wall{{position:absolute;left:-12px;top:-12px;width:840px;height:282px;background:{C['rosa']}}}
.sun{{position:absolute;right:-12px;top:-12px;width:240px;height:184px;background:{C['marigold']}}}
.shadow{{position:absolute;left:0;top:0;width:816px;height:270px;background:{C['shadow']};
  clip-path:polygon(576px 172px,816px 172px,816px 270px,674px 270px)}}
.blue{{position:absolute;left:528px;top:270px;width:300px;height:690px;background:{C['cobalt']}}}
.water{{position:absolute;left:-12px;top:960px;width:840px;height:108px;background:{C['water']}}}
.water::before{{content:"";position:absolute;left:12px;right:12px;top:22px;height:1px;background:{C['cream']};opacity:.8}}
/* TEXT layer */
.title{{position:absolute;left:48px;top:72px;color:{C['cream']}}}
.title h1{{font-weight:500;font-size:74px;letter-spacing:.2em;line-height:1}}
.title p{{margin-top:18px;font-size:13px;font-weight:500;letter-spacing:.34em;text-transform:uppercase}}
.motto{{position:absolute;left:600px;top:48px;width:168px;font-size:12px;font-weight:700;letter-spacing:.3em;line-height:1.9;color:{C['ink']};text-transform:uppercase}}
.colL{{position:absolute;left:48px;top:304px;width:444px}}
.colR{{position:absolute;left:560px;top:304px;width:208px;color:{C['cream']}}}
.sec + .sec{{margin-top:22px}}
h2{{font-size:15px;font-weight:700;letter-spacing:.32em;text-transform:uppercase;display:flex;align-items:center;gap:12px;margin-bottom:6px}}
.sq{{display:inline-block;width:14px;height:14px;background:{C['marigold']}}}
h3{{font-size:11.5px;font-weight:700;letter-spacing:.28em;text-transform:uppercase;color:{C['rosa_ink']};margin:12px 0 5px}}
.colR h3{{color:{C['marigold']}}}
.item{{margin:0 0 10px}}
.row{{display:flex;align-items:baseline;gap:10px}}
.nm{{font-size:16px;font-weight:700;letter-spacing:.12em;text-transform:uppercase}}
.ld{{flex:1;border-bottom:1px solid currentColor;opacity:.35;transform:translateY(-4px)}}
.pr{{font-size:17px;font-weight:700;font-variant-numeric:tabular-nums}}
.ds{{font-size:14px;line-height:1.4;margin-top:2px;max-width:420px}}
.colR .ds{{font-size:13.5px}}
.foot{{position:absolute;left:48px;right:48px;top:1000px;display:flex;justify-content:space-between;font-size:11.5px;font-weight:700;letter-spacing:.32em;text-transform:uppercase;color:{C['water_ink']}}}
/* PHONE: the courtyard read as a walk, one plane after another */
@media (max-width:500px){{
 body{{background:{C['plaster']}}}
 .page{{width:390px;height:auto;overflow:visible}}
 .wall,.sun,.shadow,.blue,.water{{display:none}}
 .title{{position:relative;left:0;top:0;background:{C['rosa']};padding:44px 24px 40px}}
 .title h1{{font-size:44px}} .title p{{font-size:11.5px;letter-spacing:.26em;line-height:1.7}}
 .motto{{position:relative;left:0;top:0;width:auto;background:{C['marigold']};padding:16px 24px;font-size:11.5px;line-height:1.7}}
 .colL,.colR{{position:relative;left:0;top:0;width:auto;padding:32px 24px}}
 .colR{{background:{C['cobalt']}}}
 .ds{{max-width:none}} .colR .ds{{font-size:14px}}
 .foot{{position:relative;left:0;right:0;top:0;background:{C['water']};padding:28px 24px;display:block;line-height:2}}
 .foot span{{display:block}}
}}
</style></head><body><div class="page">
<div class="wall"></div><div class="sun"></div><div class="shadow"></div><div class="blue"></div><div class="water"></div>
<div class="title"><h1>CANTINA</h1><p>&amp; Cocktail Bar · Iowa City, Iowa</p></div>
<div class="motto">Good drinks<br>Good company</div>
<div class="colL">{section_html(S['sec_cocktails'])}{section_html(S['sec_spirits'])}</div>
<div class="colR">{section_html(S['sec_beer'])}{section_html(S['sec_wine'])}{section_html(S['sec_cider'])}</div>
<div class="foot"><span>Sit in the light</span><span>Salud</span></div>
</div></body></html>"""
(HERE / "menu.html").write_text(HTML)

def lum(h):
    h = h.lstrip("#"); rgb = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    r, g, b = map(f, rgb); return .2126*r + .7152*g + .0722*b
def cr(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True); return round((la + .05) / (lb + .05), 2)
PAIRS = {"title/subtitle cream on rosa": ("cream", "rosa"), "motto ink on marigold": ("ink", "marigold"),
         "left text ink on plaster": ("ink", "plaster"), "left subheads rosa_ink on plaster": ("rosa_ink", "plaster"),
         "right text cream on cobalt": ("cream", "cobalt"), "right subheads marigold on cobalt": ("marigold", "cobalt"),
         "footer water_ink on water": ("water_ink", "water")}
contrast = {k: cr(C[a], C[b]) for k, (a, b) in PAIRS.items()}

CHECK = r"""() => { const pg=document.querySelector('.page').getBoundingClientRect(); const out=[];
 for (const sel of ['.colL','.colR']) { const b=document.querySelector(sel).getBoundingClientRect(); out.push([sel,b.left-pg.left,b.top-pg.top,b.right-pg.left,b.bottom-pg.top]); }
 const f=document.querySelector('.foot').getBoundingClientRect(); out.push(['.foot',f.left-pg.left,f.top-pg.top,f.right-pg.left,f.bottom-pg.top]);
 const t=document.querySelector('.title').getBoundingClientRect(); out.push(['.title',t.left-pg.left,t.top-pg.top,t.right-pg.left,t.bottom-pg.top]);
 const m=document.querySelector('.motto').getBoundingClientRect(); out.push(['.motto',m.left-pg.left,m.top-pg.top,m.right-pg.left,m.bottom-pg.top]);
 const rows=[...document.querySelectorAll('.row')].map(r=>{const n=r.querySelector('.nm').getBoundingClientRect(),p=r.querySelector('.pr').getBoundingClientRect(); return [r.parentNode.dataset.id, Math.round(p.left-n.right), Math.round(Math.abs(p.top-n.top))];});
 return {boxes:out, rows}; }"""
with sync_playwright() as p:
    br = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    pg = br.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=3.125)
    pg.goto((HERE / "menu.html").as_uri()); pg.wait_for_timeout(400)
    geo = pg.evaluate(CHECK)
    pg.locator(".page").screenshot(path=str(HERE / "preview-letter.png"))
    ph = br.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3)
    ph.goto((HERE / "menu.html").as_uri()); ph.wait_for_timeout(400)
    ph.screenshot(path=str(HERE / "preview-phone.png"), full_page=True)
    br.close()
print(json.dumps({"contrast": contrast, **geo}, indent=1))
