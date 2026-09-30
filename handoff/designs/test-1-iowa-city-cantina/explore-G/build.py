#!/usr/bin/env python3
"""Direction G "Monument" for TEST-1 (Iowa City cantina bar menu).

Type-as-image: one condensed wordmark, CANTINA, set vertically along the right edge, cropped by the trim.
Reading layer: two short columns in the left ~62% of the page. Two inks + one accent (dry chile red).

  python3 build.py            -> menu.html, preview-letter.png (2550x3300), preview-phone.png (1170 wide), geometry.json
  python3 build.py --variant before   -> the pre-subtraction version (preview-letter-before.png) for the log
"""
import glob, html, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFT = HERE.parent / "build" / "draft_doc.json"
FONTS = (HERE / "fonts").as_uri()

# ---- palette: ground + ink + one accent -------------------------------------------------------------
PAPER = "#EFE7D8"   # warm paper ground
INK = "#1B1815"     # near-black (reading text and the monument)
INK2 = "#4D453D"    # same ink, lighter value, for descriptions and labels (not a new hue)
CHILE = "#9B2D1F"   # dry chile red: section heads only

# ---- descriptions: ingredient-first, sentence case, one line, sourced only --------------------------
# (item id) -> (description or None, provenance). Nothing here is invented; see proposal.md content log.
DESC = {
    "beta_manhattan": ("Rye whiskey · sweet vermouth · cocktail cherry",
                       "components; Aromatic Bitters hidden (public_components aromatic-bitters=false)"),
    "beta_margarita": ("Tequila blanco · lime · orange liqueur · agave",
                       "existing desc ingredient terms; tasting sentence 'Bright and citrus-forward.' dropped"),
    "beta_daiquiri": ("White rum · lime · demerara syrup",
                      "components (White Rum, Fresh Lime Juice, Demerara Syrup) as named in existing desc"),
    "beta_old_fashioned": ("Brown butter-washed bourbon · demerara · bitters",
                           "house_recipe=false: ingredient names only, exactly the existing desc terms"),
    "beta_czech_pilsner": ("Crisp pale lager", "existing desc"),
    "beta_dry_hopped_ipa": ("Hop-forward", "existing desc minus the echo 'draft IPA'"),
    "beta_amber_lager": ("Toasty", "existing desc minus the echo 'amber lager'"),
    "beta_malbec": ("Dry red", "existing desc minus 'wine' (section head says Wine)"),
    "beta_pinot_grigio": ("Dry white", "existing desc minus 'wine'"),
    "beta_brut_rose": (None, "'Dry sparkling rosé' = echo of name + sub head Sparkling; dropped"),
    "beta_blanco_tequila": (None, "'Blanco tequila pour.' is an echo; dropped"),
    "beta_anejo_tequila": (None, "'Añejo tequila pour.' is an echo; dropped"),
    "beta_cognac_vsop": (None, "'VSOP Cognac pour.' is an echo; dropped"),
    "beta_dry_cider": ("Sparkling", "existing desc minus the echo 'dry … cider'"),
}

# columns keep draft order: left = Cocktails, Beer; right = Wine, Spirits, Cider
COLUMNS = [["sec_cocktails", "sec_beer"], ["sec_wine", "sec_spirits", "sec_cider"]]

VARIANTS = {
    # pre-subtraction: includes every device we were tempted by
    "before": dict(track=0, rule=True, mark=True, subheads=True, beer_sub_inline=False, tagline=True, folio=True),
    # after the subtraction pass (see proposal.md)
    "after": dict(track=-0.05, rule=False, mark=False, subheads=True, beer_sub_inline=True, tagline=True, folio=False),
}


def esc(s):
    return html.escape(s, quote=True)


def price(it):
    v = it["prices"][0]["value"]
    return f"{v:g}" if float(v) != int(v) else str(int(v))


def item_html(it):
    d, _ = DESC[it["id"]]
    dhtml = f'<div class="ds">{esc(d)}</div>' if d else ""
    return (f'<div class="it" data-id="{it["id"]}"><div class="row"><span class="nm">{esc(it["name"])}</span>'
            f'<span class="pr">{price(it)}</span></div>{dhtml}</div>')


def section_html(sec, v):
    out = [f'<section class="sec" data-id="{sec["id"]}">']
    subs = sec.get("subs") or []
    if v["beer_sub_inline"] and len(subs) == 1:
        # one-sub section: the sub label rides on the head line instead of taking its own row
        out.append(f'<h2>{esc(sec["name"])}<span class="h2sub">{esc(subs[0]["name"])}</span></h2>')
        out += [item_html(it) for it in subs[0]["items"]]
    else:
        out.append(f'<h2>{esc(sec["name"])}</h2>')
        out += [item_html(it) for it in sec.get("items", [])]
        for sb in subs:
            if v["subheads"]:
                out.append(f'<h3>{esc(sb["name"])}</h3>')
            out += [item_html(it) for it in sb["items"]]
    out.append("</section>")
    return "\n".join(out)


def build(variant="after"):
    v = VARIANTS[variant]
    doc = json.loads(DRAFT.read_text())
    secs = {s["id"]: s for s in doc["sections"]}
    assert sorted(sum(COLUMNS, [])) == sorted(secs), "every section placed exactly once"
    cols = "\n".join(
        f'<div class="col col{i}">' + "\n".join(section_html(secs[sid], v) for sid in col) + "</div>"
        for i, col in enumerate(COLUMNS))
    rule = '<div class="rule"></div>' if v["rule"] else ""
    mark = '<span class="mark"></span>' if v["mark"] else ""
    tagline = '<div class="tag">Good drinks<br>Good people</div>' if v["tagline"] else ""
    folio = '<div class="folio">Bar menu</div>' if v["folio"] else ""
    TRACK = v.get("track", 0)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Cantina · Bar menu</title><style>
@font-face{{font-family:Mon;font-weight:700;src:url({FONTS}/Oswald-700.ttf)}}
@font-face{{font-family:Lab;font-weight:500;src:url({FONTS}/Oswald-500.ttf)}}
@font-face{{font-family:Nr;font-weight:400;src:url({FONTS}/Newsreader-400.ttf)}}
@font-face{{font-family:Nr;font-weight:500;src:url({FONTS}/Newsreader-500.ttf)}}
@font-face{{font-family:Nr;font-weight:400;font-style:italic;src:url({FONTS}/Newsreader-400i.ttf)}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:{PAPER}}}
.page{{position:relative;overflow:hidden;background:{PAPER};color:{INK};font-family:Nr;
  font-variant-numeric:lining-nums tabular-nums;-webkit-font-smoothing:antialiased}}
/* the one gesture */
svg.mon{{position:absolute;left:0;top:0;pointer-events:none}}
svg.mon text{{font-family:Mon;font-weight:700;fill:{INK}}}
/* labels: tracked caps, 3 words or fewer */
.lab,.tag,h2,h3,.h2sub,.folio{{font-family:Lab;font-weight:500;text-transform:uppercase}}
.head{{position:absolute}}
.lab{{font-size:12px;letter-spacing:.34em;line-height:1.75;color:{INK}}}
.lab .l2{{color:{INK2}}}
.mark{{display:inline-block;width:7px;height:7px;border-radius:50%;background:{CHILE};margin-left:.6em;vertical-align:1px}}
.rule{{height:1px;background:{INK};opacity:.55;margin-top:22px;width:96px}}
.list{{position:absolute;display:grid}}
h2{{font-size:15px;letter-spacing:.3em;color:{CHILE};line-height:1;margin:0 0 calc(var(--u)*1.25)}}
.h2sub{{font-size:12px;letter-spacing:.3em;color:{INK2};margin-left:1.1em}}
h3{{font-size:12px;letter-spacing:.3em;color:{INK2};line-height:1;margin:calc(var(--u)*1.2) 0 calc(var(--u)*.75)}}
h2+h3{{margin-top:0}}
.sec+.sec{{margin-top:var(--gap)}}
.it{{margin-bottom:var(--u)}}
.it:last-child{{margin-bottom:0}}
.row{{display:flex;align-items:baseline;justify-content:space-between;gap:14px}}
.nm{{font-size:18px;font-weight:500;line-height:1.2;letter-spacing:.005em}}
.pr{{font-size:18px;font-weight:500;line-height:1.2;font-variant-numeric:lining-nums tabular-nums}}
.ds{{font-size:13px;font-style:italic;line-height:1.3;color:{INK2};margin-top:2px;white-space:nowrap}}
.tag{{position:absolute;font-size:12px;letter-spacing:.34em;line-height:1.75;color:{INK2}}}
.folio{{position:absolute;font-size:12px;letter-spacing:.3em;color:{INK2}}}

/* ---- letter: 816x1056 css px = 8.5x11 in; x3.125 = 2550x3300 ---- */
body.letter .page{{width:816px;height:1056px;--u:15px;--gap:40px}}
body.letter .head{{left:56px;top:56px}}
body.letter .list{{left:56px;top:190px;grid-template-columns:262px 170px;column-gap:36px;align-items:start}}
body.letter .tag{{left:56px;bottom:56px}}
body.letter .folio{{left:306px;bottom:56px}}

/* ---- phone: 390 css px x3 = 1170, one column, monument turns horizontal at the top ---- */
body.phone .page{{width:390px;--u:14px;--gap:36px;padding:0 28px 40px}}
body.phone .head{{position:relative;padding-top:18px}}
body.phone .list{{position:relative;margin-top:34px;grid-template-columns:1fr;row-gap:var(--gap)}}
body.phone .sec+.sec{{margin-top:var(--gap)}}
body.phone .it{{max-width:300px}}
body.phone .rule{{margin-top:18px}}
body.phone .tag{{position:relative;margin-top:44px}}
body.phone .folio{{display:none}}
body.phone .ds{{white-space:normal}}
</style></head>
<body class="{{BODYCLASS}}"><div class="page">
<svg class="mon" aria-label="Cantina"><text id="monw">CANTINA</text></svg>
<div class="head"><div class="lab">&amp; cocktail bar{mark}<br><span class="l2">Iowa City, Iowa</span></div>{rule}</div>
<div class="list">
{cols}
</div>
{tagline}{folio}
</div>
<script>
async function layout(){{
  await document.fonts.ready;
  const page=document.querySelector('.page'), phone=document.body.classList.contains('phone');
  const svg=document.querySelector('svg.mon'), t=document.getElementById('monw');
  const c=document.createElement('canvas').getContext('2d');
  c.font='700 100px Mon'; const m=c.measureText('CANTINA');
  const capR=m.actualBoundingBoxAscent/100, natR=m.width/100;
  const W=page.offsetWidth;
  if(!phone){{
    const H=page.offsetHeight;
    // monument: Oswald 700 at its natural set width runs the full page height (+1.2% overshoot each end);
    // letter tops cropped 7% by the right trim (the T crossbar stays readable)
    const L=H*1.024, crop=0.07, TR={TRACK}, F=L/(natR+6*TR), cap=capR*F;
    const xb=W-cap*(1-crop);
    svg.setAttribute('width',W); svg.setAttribute('height',H);
    t.setAttribute('font-size',F.toFixed(2));
    t.setAttribute('textLength',L.toFixed(2)); t.setAttribute('lengthAdjust','spacing');
    t.setAttribute('transform',`translate(${{xb.toFixed(2)}},${{(-H*0.012).toFixed(2)}}) rotate(90)`);
    t.setAttribute('x',0); t.setAttribute('y',0);
    window.__mon={{font_size:F,cap_height:cap,baseline_x:xb,visible_left:xb,visible_width:W-xb,crop_pct:crop*100,
                  top:-H*0.012,bottom:H*1.012,text_length:L,natural_length:natR*F,tracking_em:TR}};
    // fill: one spacing unit u drives item spacing and section gaps (gap = 2.6u) so the longer column
    // ends one band above the tagline; spacing is scaled, never ornament added
    const tag=document.querySelector('.tag');
    const target=(tag?tag.getBoundingClientRect().top:H-56)-64;
    let u=15;
    const setU=x=>{{page.style.setProperty('--u',x.toFixed(2)+'px');page.style.setProperty('--gap',(2.6*x).toFixed(2)+'px')}};
    for(let k=0;k<6;k++){{
      setU(u);
      const bottom=Math.max(...[...document.querySelectorAll('.col')].map(e=>e.getBoundingClientRect().bottom));
      const slots=Math.max(...[...document.querySelectorAll('.col')].map(e=>e.querySelectorAll('.it').length+2.6*(e.querySelectorAll('.sec').length-1)+e.querySelectorAll('h3').length*1.95));
      u=Math.max(12,Math.min(26,u+(target-bottom)/slots));
    }}
    setU(u); const gap=2.6*u; window.__u=u;
    window.__gap=gap;
  }} else {{
    // phone: the same word horizontal, spanning the width, cap tops cropped 6% by the top trim
    const F=(W*1.035)/natR, cap=capR*F, crop=0.06, yb=cap*(1-crop);
    const hb=yb+Math.max(0,m.actualBoundingBoxDescent/100*F);
    svg.setAttribute('width',W); svg.setAttribute('height',hb+4);
    svg.style.position='relative'; svg.style.display='block'; svg.style.marginLeft='-28px';
    t.setAttribute('font-size',F.toFixed(2)); t.setAttribute('x',(-W*0.0175).toFixed(2)); t.setAttribute('y',yb.toFixed(2));
    window.__mon={{font_size:F,cap_height:cap,baseline_y:yb,crop_pct:crop*100}};
  }}
  window.__ready=true;
}}
layout();
</script>
</body></html>"""


GEOM_JS = """() => {
  const R=e=>{const b=e.getBoundingClientRect();return [+b.left.toFixed(1),+b.top.toFixed(1),+b.right.toFixed(1),+b.bottom.toFixed(1)]};
  const out={page:R(document.querySelector('.page')),monument:window.__mon,gap:window.__gap||null,u:window.__u||null,
    head:R(document.querySelector('.head')),tag:document.querySelector('.tag')?R(document.querySelector('.tag')):null,
    columns:[...document.querySelectorAll('.col')].map(R),sections:{},items:{},problems:[]};
  document.querySelectorAll('.sec').forEach(s=>{out.sections[s.dataset.id]=R(s.querySelector('h2'))});
  document.querySelectorAll('.it').forEach(it=>{
    const nm=it.querySelector('.nm'),pr=it.querySelector('.pr'),ds=it.querySelector('.ds'),row=it.querySelector('.row');
    out.items[it.dataset.id]={name:R(nm),price:R(pr),desc:ds?R(ds):null};
    if(row.getBoundingClientRect().height>30) out.problems.push(it.dataset.id+': name row wraps');
    if(ds && (ds.getBoundingClientRect().height>20 || ds.scrollWidth>ds.parentElement.getBoundingClientRect().width+0.5))
      out.problems.push(it.dataset.id+': description exceeds one line/column');
  });
  const mon=window.__mon;
  if(mon && mon.visible_left){ document.querySelectorAll('.nm,.pr,.ds,h2,h3,.lab,.tag').forEach(e=>{
      if(e.getBoundingClientRect().right>mon.visible_left-24) out.problems.push('text within 24px of monument: '+e.textContent)});
    const W=816,H=1056,M=48; document.querySelectorAll('.nm,.pr,.ds,h2,h3,.lab,.tag,.folio').forEach(e=>{const b=e.getBoundingClientRect();
      if(b.left<M||b.top<M||b.bottom>H-M) out.problems.push('text inside 0.5in margin: '+e.textContent)}); }
  return out;}"""


def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


def main():
    from playwright.sync_api import sync_playwright
    variant = "before" if "--variant" in sys.argv and sys.argv[-1] == "before" else "after"
    doc = build(variant)
    suffix = "-before" if variant == "before" else ""
    if variant == "after":
        (HERE / "menu.html").write_text(doc.replace("{BODYCLASS}", "letter"))
    report = {"variant": variant,
              "contrast_on_paper": {"ink": contrast(INK, PAPER), "ink2": contrast(INK2, PAPER), "chile": contrast(CHILE, PAPER)}}
    exe = next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe)
        jobs = [("letter", 816, 1056, 3.125, f"preview-letter{suffix}.png")]
        if variant == "after":
            jobs.append(("phone", 390, 844, 3, "preview-phone.png"))
        for cls, w, h, dsf, name in jobs:
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            tmp = HERE / f".render-{cls}.html"
            tmp.write_text(doc.replace("{BODYCLASS}", cls))
            pg.goto(tmp.as_uri()); pg.wait_for_function("window.__ready===true"); pg.wait_for_timeout(300)
            tmp.unlink()
            report[cls] = pg.evaluate(GEOM_JS)
            if cls == "letter":
                pg.locator(".page").screenshot(path=str(HERE / name))
            else:
                pg.screenshot(path=str(HERE / name), full_page=True)
            pg.close()
        b.close()
    (HERE / f"geometry{suffix}.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps({k: (v if k != "letter" and k != "phone" else {"problems": v["problems"], "gap": v["gap"],
                                                                     "columns": v["columns"], "monument": v["monument"]})
                      for k, v in report.items()}, indent=1))


if __name__ == "__main__":
    main()
