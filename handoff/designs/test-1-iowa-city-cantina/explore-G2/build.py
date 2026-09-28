#!/usr/bin/env python3
"""Direction G2 "Monument" (round 2) for TEST-1, the Iowa City cantina bar menu.

The one gesture: CANTINA drawn as structure (glyphs.py). It is a wood-type-cut block letter with rótulo forms,
pulled in two plates. The black key sits over a chile-red plate that is deliberately misregistered, so the red reads
both as a sign painter's shadow and as a letterpress register slip. The word runs up the right edge, cropped by the
trim. The venue line "& Cocktail Bar / Iowa City, Iowa" continues along the monument's baseline at its foot.

  python3 build.py                    -> menu.html, preview-letter.png (2550x3300), preview-phone.png (1170 wide), geometry.json
  python3 build.py --variant before   -> preview-letter-before.png, geometry-before.json (pre-subtraction)
"""
import glob, html, json, sys
from pathlib import Path

import glyphs

HERE = Path(__file__).resolve().parent
DRAFT = HERE.parent / "build" / "draft_doc.json"
FONTS = (HERE / "fonts").as_uri()

PAPER, INK, INK2, CHILE = "#EFE7D8", "#1B1815", "#4D453D", "#9B2D1F"

# Garnish from phg.recipe_versions.garnish (designer gateway query log_id 213, 2026-09-28)
GARNISH = {"beta_manhattan": "Cocktail cherry", "beta_margarita": "Lime wheel",
           "beta_daiquiri": "Lime coin", "beta_old_fashioned": "Orange peel"}
# Style sentences kept from the draft desc (brief section 5): only the Margarita has one
STYLE = {"beta_margarita": "Bright and citrus-forward."}

# Reading order: Cocktails, Beer | Spirits, Wine, Cider (Spirits/Agave before Wine; brief section 5)
ORDER = ["sec_cocktails", "sec_beer", "sec_spirits", "sec_wine", "sec_cider"]
FIRST = {"sub_cocktails_classics": ["beta_margarita", "beta_manhattan"]}  # Margarita first

VARIANTS = {
    "before": dict(rules=True, reg=(-3.0, 4.0), beer_inline=False),
    "after": dict(rules=False, reg=(-2.0, 3.0), beer_inline=True),
}


def esc(s):
    return html.escape(s, quote=True)


def sentence(parts):
    s = " · ".join(p.lower() for p in parts)
    return s[:1].upper() + s[1:]


def describe(it):
    """(lines, provenance). Cocktails: visible components in recipe order, full names, no quantities, then garnish."""
    comps = it.get("components") or []
    if comps:
        hidden = {k for k, v in (it["meta"].get("public_components") or {}).items() if v is False}
        names = [c["name"] for c in comps if c["name"].lower().replace(" ", "-") not in hidden]
        g = GARNISH.get(it["id"])
        if g and g.lower() not in (n.lower() for n in names):
            names.append(g)
        lines = [sentence(names)]
        if it["id"] in STYLE:
            lines.append(STYLE[it["id"]])
        prov = "components (hidden removed) + garnish from recipe_versions"
        if it["meta"]["public_visibility"].get("house_recipe") is False:
            prov += "; house_recipe=false so names only"
        return lines, prov
    d = (it.get("desc") or "").strip().rstrip(".")
    return ([d] if d else []), "draft desc, full text"


def price(it):
    v = it["prices"][0]["value"]
    return str(int(v)) if float(v) == int(v) else f"{v:g}"


def item_html(it):
    lines, _ = describe(it)
    ds = "".join(f'<div class="ds">{esc(l)}</div>' for l in lines)
    return (f'<div class="it" data-id="{it["id"]}"><div class="row"><span class="nm">{esc(it["name"])}</span>'
            f'<span class="pr">{price(it)}</span></div>{ds}</div>')


def ordered(items, sub_id):
    if sub_id in FIRST:
        rank = {k: i for i, k in enumerate(FIRST[sub_id])}
        return sorted(items, key=lambda x: rank.get(x["id"], 99))
    return items


def section_html(sec, v):
    subs = sec.get("subs") or []
    out = [f'<section class="sec" data-id="{sec["id"]}">']
    if v["beer_inline"] and len(subs) == 1:
        out.append(f'<h2>{esc(sec["name"])}<span class="h2sub">{esc(subs[0]["name"])}</span></h2>')
        out += [item_html(it) for it in ordered(subs[0]["items"], subs[0]["id"])]
    else:
        out.append(f'<h2>{esc(sec["name"])}</h2>')
        out += [item_html(it) for it in sec.get("items", [])]
        for sb in subs:
            out.append(f'<h3>{esc(sb["name"])}</h3>')
            out += [item_html(it) for it in ordered(sb["items"], sb["id"])]
    out.append("</section>")
    return "\n".join(out)


def build(variant, split):
    v = VARIANTS[variant]
    doc = json.loads(DRAFT.read_text())
    secs = {s["id"]: s for s in doc["sections"]}
    assert sorted(ORDER) == sorted(secs)
    cols = [ORDER[:split], ORDER[split:]]
    cols_html = "\n".join(f'<div class="col col{i}">' + "\n".join(section_html(secs[s], v) for s in c) + "</div>"
                          for i, c in enumerate(cols))
    L, word = glyphs.word()
    rx, ry = v["reg"]
    rules_css = f"h2{{padding-bottom:6px;border-bottom:1px solid {INK2}}}" if v["rules"] else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Cantina · Bar menu</title><style>
@font-face{{font-family:Lab;font-weight:500;src:url({FONTS}/Oswald-500.ttf)}}
@font-face{{font-family:Nr;font-weight:400;src:url({FONTS}/Newsreader-400.ttf)}}
@font-face{{font-family:Nr;font-weight:500;src:url({FONTS}/Newsreader-500.ttf)}}
@font-face{{font-family:Nr;font-weight:400;font-style:italic;src:url({FONTS}/Newsreader-400i.ttf)}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:{PAPER}}}
.page{{position:relative;overflow:hidden;background:{PAPER};color:{INK};font-family:Nr;-webkit-font-smoothing:antialiased;
  font-variant-numeric:lining-nums tabular-nums}}
svg.mon{{position:absolute;left:0;top:0;pointer-events:none;overflow:visible}}
.plate-red{{fill:{CHILE}}} .plate-key{{fill:{INK}}}
.foot{{position:absolute;font-family:Lab;font-weight:500;text-transform:uppercase;font-size:13px;letter-spacing:.3em;
  line-height:1.55;white-space:nowrap;color:{INK}}}
.foot .l2{{color:{INK2}}}
h2,h3,.h2sub{{font-family:Lab;font-weight:500;text-transform:uppercase}}
h2{{font-size:18px;letter-spacing:.3em;color:{CHILE};line-height:1;margin:0 0 calc(var(--u)*1.1)}}
{rules_css}
.h2sub{{font-size:13px;letter-spacing:.3em;color:{INK2};margin-left:1.1em}}
h3{{font-size:13px;letter-spacing:.3em;color:{INK2};line-height:1;margin:calc(var(--u)*1.15) 0 calc(var(--u)*.6)}}
h2+h3{{margin-top:0}}
.sec+.sec{{margin-top:var(--gap)}}
.it{{margin-bottom:var(--u)}} .it:last-child{{margin-bottom:0}}
.row{{display:block;line-height:1.2}}
.nm{{font-size:24px;font-weight:500;letter-spacing:.005em}}
.pr{{font-size:24px;font-weight:400;color:{INK2};margin-left:.9em;font-variant-numeric:lining-nums tabular-nums}}
.ds{{font-size:16px;font-style:italic;line-height:1.32;color:{INK2};margin-top:2px}}
.ds+.ds{{margin-top:0}}
.list{{position:absolute;display:grid;align-items:start}}

body.letter .page{{width:816px;height:1056px;--u:16px;--gap:44px}}
body.letter .list{{left:56px;top:56px;grid-template-columns:252px 208px;column-gap:32px}}

body.phone .page{{width:390px;--u:14px;--gap:38px;padding:0 28px 44px}}
body.phone svg.mon{{position:relative;display:block;margin-left:-28px}}
body.phone .foot{{position:relative;margin-top:10px}}
body.phone .list{{position:relative;margin-top:40px;grid-template-columns:1fr}}
body.phone .col1{{margin-top:var(--gap)}}
body.phone .nm,body.phone .pr{{font-size:19px}} body.phone .ds{{font-size:14px}} body.phone h2{{font-size:16px}}
</style></head>
<body class="{{BODYCLASS}}"><div class="page">
<svg class="mon" aria-label="Cantina"><g id="mon"><g class="plate-red" fill-rule="evenodd" transform="translate({rx},{ry})">{word}</g><g class="plate-key" fill-rule="evenodd">{word}</g></g></svg>
<div class="foot"><div>&amp; Cocktail Bar</div><div class="l2">Iowa City, Iowa</div></div>
<div class="list">
{cols_html}
</div>
</div>
<script>
const WORD_LEN={L:.3f};
async function layout(){{
  await document.fonts.ready;
  const page=document.querySelector('.page'), phone=document.body.classList.contains('phone');
  const svg=document.querySelector('svg.mon'), g=document.getElementById('mon'), foot=document.querySelector('.foot');
  const W=page.offsetWidth;
  if(!phone){{
    const H=page.offsetHeight, M=56, crop=0.08, top=-H*0.012;
    // the venue line runs on after the word along the same baseline; it ends on the bottom margin
    foot.style.transformOrigin='0 0';
    const fw=foot.offsetWidth, fh=foot.offsetHeight;       // unrotated: fw = line length, fh = two line depth
    const footLen=fw, footGap=26;
    const wordEnd=H-M-footLen-footGap;                     // page y where the word's last glyph ends
    const S=(wordEnd-top)/WORD_LEN, cap=100*S, xTop=W+crop*cap, xBase=xTop-cap;
    svg.setAttribute('width',W); svg.setAttribute('height',H);
    // glyph x -> page +y, glyph y (cap line 0 .. baseline 100) -> page -x
    g.setAttribute('transform',`translate(${{xTop.toFixed(2)}},${{top.toFixed(2)}}) rotate(90) scale(${{S.toFixed(4)}})`);
    // foot: rotated 90deg cw, first line's baseline sits on the monument baseline, reading on down the page
    const fs=parseFloat(getComputedStyle(foot).fontSize), lh=parseFloat(getComputedStyle(foot).lineHeight);
    const firstBase=(lh-fs)/2+fs*0.93;                     // approx baseline of line 1 inside the block
    foot.style.left=(xBase+firstBase).toFixed(2)+'px';
    foot.style.top=(wordEnd+footGap).toFixed(2)+'px';
    foot.style.transform='rotate(90deg)';
    window.__mon={{scale:S,cap_height:cap,x_top:xTop,x_baseline:xBase,crop_pct:crop*100,y_start:top,y_end:wordEnd,
                  red_plate_offset_units:[{rx},{ry}],visible_width:W-xBase}};
    // fill: one unit u drives item spacing and gaps (gap = 2.75u) so the longer column lands on the bottom margin;
    // the shorter column then takes its remainder in its own section gaps (no dead field under a column)
    // fill: each column solves its own unit u (item spacing; section gap = 2.75u) so both columns land on the
    // bottom margin: no dead field under either column, and no stretched holes between sections
    const cols=[...document.querySelectorAll('.col')], us={{}}, gaps={{}};
    cols.forEach((c,i)=>{{
      const setU=x=>{{c.style.setProperty('--u',x.toFixed(2)+'px');c.style.setProperty('--gap',(2.75*x).toFixed(2)+'px')}};
      const nIt=c.querySelectorAll('.it').length, nSec=c.querySelectorAll('.sec').length, nH3=c.querySelectorAll('h3').length;
      const slots=(nIt-nSec)+2.75*(nSec-1)+1.75*nH3+1.1*nSec;
      let u=16;
      for(let k=0;k<8;k++){{ setU(u); u=Math.max(10,Math.min(34,u+((H-M)-c.getBoundingClientRect().bottom)/slots)); }}
      setU(u); us['col'+i]=+u.toFixed(2); gaps['col'+i]=+(2.75*u).toFixed(2);
    }});
    const u=us;
    window.__u=u; window.__gaps=gaps;
  }} else {{
    // phone: same two plates, horizontal, spanning the width, cap tops cropped 8% by the top trim
    const crop=0.08, S=(W*1.0)/WORD_LEN, cap=100*S, pad=W*0.0;
    svg.setAttribute('width',W); svg.setAttribute('height',(cap*(1-crop)+8).toFixed(2));
    g.setAttribute('transform',`translate(${{pad.toFixed(2)}},${{(-crop*cap).toFixed(2)}}) scale(${{S.toFixed(4)}})`);
    window.__mon={{scale:S,cap_height:cap,crop_pct:crop*100}};
  }}
  window.__ready=true;
}}
layout();
</script>
</body></html>"""


GEOM_JS = """() => {
  const R=e=>{const b=e.getBoundingClientRect();return [+b.left.toFixed(1),+b.top.toFixed(1),+b.right.toFixed(1),+b.bottom.toFixed(1)]};
  const page=document.querySelector('.page'), W=page.offsetWidth, H=page.offsetHeight, phone=document.body.classList.contains('phone');
  const out={page:R(page),monument:window.__mon,u:window.__u||null,gaps:window.__gaps||null,foot:R(document.querySelector('.foot')),
    columns:[...document.querySelectorAll('.col')].map(R),sections:{},items:{},rows:{},problems:[]};
  document.querySelectorAll('.sec').forEach(s=>{out.sections[s.dataset.id]=R(s.querySelector('h2'))});
  document.querySelectorAll('.it').forEach(it=>{
    const nm=it.querySelector('.nm'),pr=it.querySelector('.pr'),ds=[...it.querySelectorAll('.ds')];
    const col=it.closest('.col').getBoundingClientRect(), n=nm.getBoundingClientRect(), p=pr.getBoundingClientRect();
    out.items[it.dataset.id]={name:R(nm),price:R(pr),desc:ds.map(R),desc_lines:ds.map(d=>Math.round(d.getBoundingClientRect().height/(16*1.32)))};
    // eye travel: gap from end of name to start of price, as a share of the column (row) width
    const travel=(p.left-n.right)/col.width; out.rows[it.dataset.id]=+(travel*100).toFixed(1);
    if(travel>0.40) out.problems.push(it.dataset.id+': eye travel '+(travel*100).toFixed(0)+'%');
    if(Math.abs(p.bottom-n.bottom)>2) out.problems.push(it.dataset.id+': price not on the last line of the name');
  });
  if(!phone){
    const mon=window.__mon, M=48;
    const textR=Math.max(...[...document.querySelectorAll('.col')].map(c=>c.getBoundingClientRect().right));
    out.channel_px=+(mon.x_baseline-2*mon.scale - textR).toFixed(1); // red plate reaches 2 units past the baseline
    out.gutter_px=parseFloat(getComputedStyle(document.querySelector('.list')).columnGap);
    if(out.channel_px<2*out.gutter_px) out.problems.push('channel narrower than 2x gutter');
    document.querySelectorAll('.nm,.pr,.ds,h2,h3').forEach(e=>{const b=e.getBoundingClientRect();
      if(b.left<M||b.top<M||b.bottom>H-M||b.right>mon.x_baseline-2*mon.scale-24) out.problems.push('text outside safe area: '+e.textContent)});
    const f=document.querySelector('.foot').getBoundingClientRect();
    if(f.bottom>H-M||f.right>W-M) out.problems.push('foot line outside 0.5in safe area');
  }
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
    variant = "before" if sys.argv[-1] == "before" else "after"
    split = 2  # left: Cocktails, Beer | right: Spirits, Wine, Cider
    doc = build(variant, split)
    sfx = "-before" if variant == "before" else ""
    if variant == "after":
        (HERE / "menu.html").write_text(doc.replace("{BODYCLASS}", "letter"))
    rep = {"variant": variant, "contrast_on_paper": {"ink": contrast(INK, PAPER), "ink2": contrast(INK2, PAPER),
                                                     "chile": contrast(CHILE, PAPER)}}
    exe = next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe)
        jobs = [("letter", 816, 1056, 3.125, f"preview-letter{sfx}.png")]
        if variant == "after":
            jobs.append(("phone", 390, 844, 3, "preview-phone.png"))
        for cls, w, h, dsf, name in jobs:
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            tmp = HERE / f".render-{cls}.html"; tmp.write_text(doc.replace("{BODYCLASS}", cls))
            pg.goto(tmp.as_uri()); pg.wait_for_function("window.__ready===true"); pg.wait_for_timeout(300); tmp.unlink()
            rep[cls] = pg.evaluate(GEOM_JS)
            if cls == "letter":
                pg.locator(".page").screenshot(path=str(HERE / name))
            else:
                pg.screenshot(path=str(HERE / name), full_page=True)
            pg.close()
        b.close()
    (HERE / f"geometry{sfx}.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    for k in ("letter", "phone"):
        if k in rep:
            r = rep[k]
            print(k, "problems:", r["problems"], "u:", r["u"], "gaps:", r["gaps"], "cols:", r["columns"],
                  "channel:", r.get("channel_px"), "max travel %:", max(r["rows"].values()))
    print("monument:", rep["letter"]["monument"])


if __name__ == "__main__":
    main()
