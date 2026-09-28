#!/usr/bin/env python3
"""Direction G3 "Monument" (round 3) for TEST-1, the Iowa City cantina bar menu.

The one gesture: CANTINA as a letterpress pull (press.py) of wood-type-cut rótulo letters (glyphs.py). The key plate
carries wood grain and bites into the sheet; the chile plate is a true multiply overprint, skewed out of register.
The reading layer is quiet (14 pt names, 10 pt descriptions) on one shared 22 px row grid across both columns.

  python3 build.py                    -> menu.html, preview-letter.png (2550x3300), preview-phone.png (1170 wide), geometry.json
  python3 build.py before             -> preview-letter-before.png, geometry-before.json (pre-subtraction)
"""
import glob, html, json, sys
from pathlib import Path

import glyphs, press

HERE = Path(__file__).resolve().parent
DRAFT = HERE.parent / "build" / "draft_doc.json"
FONTS = (HERE / "fonts").as_uri()
PAPER, INK, INK2, CHILE = "#EFE7D8", "#1B1815", "#4D453D", "#9B2D1F"
NB = " "

# Garnish: phg.recipe_versions.garnish (designer gateway log_id 213). Style sentence: draft desc (Margarita only).
GARNISH = {"beta_manhattan": "Cocktail cherry", "beta_margarita": "Lime wheel",
           "beta_daiquiri": "Lime coin", "beta_old_fashioned": "Orange peel"}
STYLE = {"beta_margarita": "Bright and citrus-forward."}

# Reading order: Cocktails, Spirits | Beer, Cider, Wine.
# Agave spirits sit straight under the cocktails in the first column; Spirits precede Wine; Cider sits next to Beer.
COLUMNS = [["sec_cocktails", "sec_spirits"], ["sec_beer", "sec_cider", "sec_wine"]]
FIRST = {"sub_cocktails_classics": ["beta_margarita", "beta_manhattan"]}

# Pacing on the row grid (in rows): item gap, gap before a sub head, gap between sections
PACE = dict(item=1, sub=2, sec=3)

VARIANTS = {
    # pre-subtraction: every candidate device on
    "before": dict(grain=True, bite=True, red=True, skew=0.9, slip=1.6, rules=True, subgrey=True),
    # after the subtraction pass (proposal.md section 3)
    "after": dict(grain=True, bite=False, red=True, skew=0.9, slip=1.6, rules=False, subgrey=True),
}


def esc(s):
    return html.escape(s, quote=False)


def ing_span(name, last):
    words = esc(name).replace(" ", NB)
    sep = "" if last else f"{NB}·"
    return f'<span class="u">{words}{sep}</span>'


def describe(it):
    """HTML for the description paragraph and a plain-text copy for the content log."""
    comps = it.get("components") or []
    if comps:
        hidden = {k for k, v in (it["meta"].get("public_components") or {}).items() if v is False}
        names = [c["name"] for c in comps if c["name"].lower().replace(" ", "-") not in hidden]
        g = GARNISH.get(it["id"])
        if g and g.lower() not in (n.lower() for n in names):
            names.append(g)
        names = [n.lower() for n in names]
        names[0] = names[0][:1].upper() + names[0][1:]
        parts = [ing_span(n, i == len(names) - 1) for i, n in enumerate(names)]
        plain = " · ".join(names)
        htm = " ".join(parts)
        if it["id"] in STYLE:  # joined into the same line flow
            st = STYLE[it["id"]]
            htm += ". " + " ".join(f'<span class="u">{esc(w)}</span>' for w in st.split(" "))
            plain += ". " + st
        return htm, plain
    d = (it.get("desc") or "").strip().rstrip(".")
    return (" ".join(f'<span class="u">{esc(w)}</span>' for w in d.split(" ")), d) if d else ("", "")


def price(it):
    v = it["prices"][0]["value"]
    return str(int(v)) if float(v) == int(v) else f"{v:g}"


def item_html(it):
    htm, _ = describe(it)
    ds = f'<p class="ds">{htm}</p>' if htm else ""
    return (f'<div class="it" data-id="{it["id"]}"><p class="row"><span class="nm">{esc(it["name"])}</span>'
            f'{NB}<span class="pr">{price(it)}</span></p>{ds}</div>')


def ordered(items, sub_id):
    if sub_id in FIRST:
        rank = {k: i for i, k in enumerate(FIRST[sub_id])}
        return sorted(items, key=lambda x: rank.get(x["id"], 99))
    return items


def section_html(sec):
    out = [f'<section class="sec" data-id="{sec["id"]}">', f'<h2>{esc(sec["name"])}</h2>']
    out += [item_html(it) for it in sec.get("items", [])]
    for sb in sec.get("subs") or []:
        out.append(f'<h3>{esc(sb["name"])}</h3>')
        out += [item_html(it) for it in ordered(sb["items"], sb["id"])]
    out.append("</section>")
    return "\n".join(out)


def build(variant):
    v = VARIANTS[variant]
    doc = json.loads(DRAFT.read_text())
    secs = {s["id"]: s for s in doc["sections"]}
    assert sorted(sum(COLUMNS, [])) == sorted(secs)
    cols = "\n".join(f'<div class="col col{i}">' + "\n".join(section_html(secs[s]) for s in c) + "</div>"
                     for i, c in enumerate(COLUMNS))
    L, word = glyphs.word()
    mon = press.defs() + f'<g id="mon" style="isolation:isolate">' + press.layers(
        word, L, skew_deg=v["skew"], slip=v["slip"], red_on=v["red"], grain_on=v["grain"], bite_on=v["bite"]) + "</g>"
    rules = f"h2{{box-shadow:inset 0 -1px 0 {INK2}}}" if v["rules"] else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Cantina · Bar menu</title><style>
@font-face{{font-family:Lab;font-weight:500;src:url({FONTS}/Oswald-500.ttf)}}
@font-face{{font-family:Nr;font-weight:400;src:url({FONTS}/Newsreader-400.ttf)}}
@font-face{{font-family:Nr;font-weight:500;src:url({FONTS}/Newsreader-500.ttf)}}
@font-face{{font-family:Nr;font-weight:400;font-style:italic;src:url({FONTS}/Newsreader-400i.ttf)}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:{PAPER}}}
.page{{position:relative;overflow:hidden;background:{PAPER};color:{INK};font-family:Nr;-webkit-font-smoothing:antialiased;
  font-variant-numeric:lining-nums tabular-nums;--g:22px}}
svg.mon{{position:absolute;left:0;top:0;pointer-events:none;overflow:visible}}
.plate-key{{fill:{INK}}} .plate-red{{fill:{CHILE}}}
.foot{{position:absolute;font-family:Lab;font-weight:500;text-transform:uppercase;font-size:12px;letter-spacing:.3em;
  line-height:var(--g);white-space:nowrap;color:{INK}}}
.foot .l2{{color:{INK2}}}
/* one row grid: every line box is exactly one row (--g); every gap is a whole number of rows */
.list{{position:absolute;display:grid;align-items:start}}
h2,h3{{font-family:Lab;font-weight:500;text-transform:uppercase;line-height:var(--g)}}
h2{{font-size:15px;letter-spacing:.3em;color:{CHILE};margin-bottom:calc(var(--g)*1)}}
{rules}
h3{{font-size:12px;letter-spacing:.3em;color:{INK2}}}
.it+h3{{margin-top:calc(var(--g)*var(--sub))}}
.sec+.sec{{margin-top:calc(var(--g)*var(--sec))}}
.it+.it{{margin-top:calc(var(--g)*{PACE['item']})}}
.row{{line-height:var(--g)}}
.nm{{font-size:19px;font-weight:500;letter-spacing:.005em}}
.pr{{font-size:19px;font-weight:400;color:{INK2};margin-left:.55em;font-variant-numeric:lining-nums tabular-nums}}
.ds{{font-size:13.5px;font-style:italic;line-height:var(--g);color:{INK2};text-wrap:pretty}}
.u{{white-space:nowrap}}

body.letter .page{{width:816px;height:1056px}}
body.letter .list{{left:56px;grid-template-columns:282px 178px;column-gap:30px}}

body.phone .page{{width:390px;padding:0 28px 44px;--g:21px}}
body.phone svg.mon{{position:relative;display:block;margin-left:-28px}}
body.phone .foot{{position:relative;margin-top:6px}}
body.phone .list{{position:relative;margin-top:calc(var(--g)*2);grid-template-columns:1fr}}
body.phone .col1{{margin-top:calc(var(--g)*3)}}
body.phone .nm,body.phone .pr{{font-size:18px}} body.phone .ds{{font-size:13.5px}}
</style></head>
<body class="{{BODYCLASS}}"><div class="page" style="--sub:{PACE['sub']};--sec:{PACE['sec']}">
<svg class="mon" aria-label="Cantina">{mon}</svg>
<div class="foot"><div>&amp; Cocktail Bar</div><div class="l2">Iowa City, Iowa</div></div>
<div class="list">
{cols}
</div>
</div>
<script>
const WORD_LEN={L:.3f}, A_START={glyphs.GLYPHS['C']()[0]+glyphs.GAP}, SKEW={v['skew']}, SLIP={v['slip']};
async function layout(){{
  await document.fonts.ready;
  const page=document.querySelector('.page'), phone=document.body.classList.contains('phone');
  const svg=document.querySelector('svg.mon'), g=document.getElementById('mon'), foot=document.querySelector('.foot');
  const W=page.offsetWidth;
  // worst-case red spill past the key, in glyph units: skew displacement at the word ends + slip
  const spill=Math.abs(Math.sin(SKEW*Math.PI/180))*WORD_LEN/2+Math.abs(SLIP)*0+0.5;
  if(!phone){{
    const H=page.offsetHeight, M=56, crop=0.08, top=-H*0.012;
    const G=parseFloat(getComputedStyle(page).getPropertyValue('--g'));
    const fw=foot.offsetWidth, footGap=G;
    const wordEnd=H-M-fw-footGap;
    const S=(wordEnd-top)/WORD_LEN, cap=100*S, xTop=W+crop*cap, xBase=xTop-cap;
    svg.setAttribute('width',W); svg.setAttribute('height',H);
    g.setAttribute('transform',`translate(${{xTop.toFixed(2)}},${{top.toFixed(2)}}) rotate(90) scale(${{S.toFixed(4)}})`);
    const fs=parseFloat(getComputedStyle(foot).fontSize), lh=G;
    foot.style.transformOrigin='0 0';
    foot.style.left=(xBase+(lh-fs)/2+fs*0.93).toFixed(2)+'px';
    foot.style.top=(wordEnd+footGap).toFixed(2)+'px';
    foot.style.transform='rotate(90deg)';
    window.__mon={{scale:S,cap_height:cap,x_top:xTop,x_baseline:xBase,crop_pct:crop*100,y_start:top,y_end:wordEnd,
                  skew_deg:SKEW,slip_units:SLIP,red_spill_px:spill*S,visible_width:W-xBase}};
    // rows: the list sits on the page's row grid. Both columns start on the same row; the taller column ends on the
    // bottom margin; the shorter one gains whole rows in its pacing gaps (never fractions: rows stay aligned)
    const list=document.querySelector('.list'), cols=[...document.querySelectorAll('.col')];
    list.style.top=M+'px';
    const rows=c=>Math.round(c.getBoundingClientRect().height/G);
    const R=cols.map(rows), N=Math.floor((H-2*M)/G);
    // the list's first row aligns with the head of the A (the C stands alone in the top field beside nothing)
    const yA=top+(A_START)*S, T=Math.max(0,Math.round((yA-M)/G));
    list.style.top=(M+T*G)+'px';
    // leftover rows go into the pacing gaps, whole rows only, section gaps first then sub-head gaps (round robin)
    const extra={{}};
    cols.forEach((c,i)=>{{
      let d=N-T-R[i]; extra['col'+i]=d; if(d<=0) return;
      const secs=[...c.querySelectorAll('.sec+.sec')], subs=[...c.querySelectorAll('.it+h3')];
      const add=el=>{{el.style.marginTop=(parseFloat(getComputedStyle(el).marginTop)+G)+'px'; d--;}};
      while(d>0 && (secs.length||subs.length)){{ for(const el of secs){{ if(d>0) add(el); }} for(const el of subs){{ if(d>0) add(el); }} }}
    }});
    const gapRows=[...document.querySelectorAll('.sec+.sec,.it+h3')].map(e=>[e.tagName==='SECTION'?e.dataset.id:e.textContent,Math.round(parseFloat(getComputedStyle(e).marginTop)/G)]);
    window.__gapRows=gapRows;
    window.__grid={{row_px:G,rows_available:N,rows_used:R,top_offset_rows:T,list_top:M+T*G,extra_rows_added:extra,gap_rows:window.__gapRows}};
  }} else {{
    const crop=0.08, S=W/WORD_LEN, cap=100*S;
    svg.setAttribute('width',W); svg.setAttribute('height',(cap*(1-crop)+spill*S+6).toFixed(2));
    g.setAttribute('transform',`translate(0,${{(-crop*cap).toFixed(2)}}) scale(${{S.toFixed(4)}})`);
    window.__mon={{scale:S,cap_height:cap,crop_pct:crop*100}};
  }}
  window.__ready=true;
}}
layout();
</script>
</body></html>"""


GEOM_JS = r"""() => {
  const R=e=>{const b=e.getBoundingClientRect();return [+b.left.toFixed(1),+b.top.toFixed(1),+b.right.toFixed(1),+b.bottom.toFixed(1)]};
  const page=document.querySelector('.page'), W=page.offsetWidth, H=page.offsetHeight, phone=document.body.classList.contains('phone');
  const out={page:R(page),monument:window.__mon,grid:window.__grid||null,foot:R(document.querySelector('.foot')),
    columns:[...document.querySelectorAll('.col')].map(R),sections:{},subs:[],items:{},rows:{},baselines_off_grid:0,problems:[]};
  document.querySelectorAll('.sec').forEach(s=>{out.sections[s.dataset.id]=R(s.querySelector('h2'))});
  document.querySelectorAll('h3').forEach(h=>out.subs.push([h.textContent,...R(h)]));
  const G=parseFloat(getComputedStyle(page).getPropertyValue('--g')), top0=document.querySelector('.list').getBoundingClientRect().top;
  // word-per-line audit: which words share a line top inside each description
  const lineWords=el=>{const spans=[...el.querySelectorAll('.u')];const lines={};
    spans.forEach(s=>{const t=Math.round(s.getBoundingClientRect().top);(lines[t]=lines[t]||[]).push(s.textContent)});
    return Object.values(lines)};
  document.querySelectorAll('.it').forEach(it=>{
    const nm=it.querySelector('.nm'),pr=it.querySelector('.pr'),ds=it.querySelector('.ds');
    const col=it.closest('.col').getBoundingClientRect(), n=nm.getBoundingClientRect(), p=pr.getBoundingClientRect();
    const lines=ds?lineWords(ds):[];
    out.items[it.dataset.id]={name:R(nm),price:R(pr),desc:ds?R(ds):null,desc_lines:lines.map(l=>l.join(' '))};
    const travel=(p.left-n.right)/col.width; out.rows[it.dataset.id]=+(travel*100).toFixed(1);
    if(travel>0.40) out.problems.push(it.dataset.id+': eye travel '+(travel*100).toFixed(0)+'%');
    if(Math.abs(p.bottom-n.bottom)>2) out.problems.push(it.dataset.id+': price not on the name line');
    if(n.height>G*1.5) out.problems.push(it.dataset.id+': name wraps');
    lines.forEach(l=>{ const words=l.join(' ').split(/[\s ]+/).filter(w=>w&&w!=='·');
      if(lines.length>1 && words.length<2) out.problems.push(it.dataset.id+': one-word line "'+l.join(' ')+'"'); });
  });
  // every line box must start on a row of the grid
  document.querySelectorAll('.list h2,.list h3,.row,.ds').forEach(e=>{const t=e.getBoundingClientRect().top-top0; if(Math.abs(t/G-Math.round(t/G))>0.02) out.baselines_off_grid++});
  if(out.baselines_off_grid) out.problems.push(out.baselines_off_grid+' line boxes off the row grid');
  if(!phone){
    const mon=window.__mon, M=48;
    const textR=Math.max(...[...document.querySelectorAll('.col')].map(c=>c.getBoundingClientRect().right));
    out.channel_px=+(mon.x_baseline-mon.red_spill_px-textR).toFixed(1);
    out.gutter_px=parseFloat(getComputedStyle(document.querySelector('.list')).columnGap);
    if(out.channel_px<2*out.gutter_px) out.problems.push('channel narrower than 2x gutter');
    document.querySelectorAll('.nm,.pr,.ds,h2,h3').forEach(e=>{const b=e.getBoundingClientRect();
      if(b.left<M||b.top<M||b.bottom>H-M) out.problems.push('text outside safe area: '+e.textContent)});
    const f=document.querySelector('.foot').getBoundingClientRect();
    if(f.bottom>H-M||f.right>W-M) out.problems.push('foot outside safe area');
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
    doc = build(variant)
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
            pg.goto(tmp.as_uri()); pg.wait_for_function("window.__ready===true"); pg.wait_for_timeout(400); tmp.unlink()
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
            print(k, "problems:", r["problems"], "grid:", r["grid"], "cols:", r["columns"],
                  "channel:", r.get("channel_px"), "max travel %:", max(r["rows"].values()))
    print("monument:", rep["letter"]["monument"])


if __name__ == "__main__":
    main()
