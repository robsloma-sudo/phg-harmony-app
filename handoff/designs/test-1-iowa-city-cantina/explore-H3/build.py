#!/usr/bin/env python3
"""Explore H3 - "Sun & Furrow", round 3. TEST-1 Iowa City cantina bar menu.

The ploughed field IS the menu's structure:
  * one continuous single-weight line ploughs furrows DOWN the right side of the page at the
    baseline pitch U (13 css px on letter). Every text baseline in both columns sits on a furrow's
    grid line, so rows register across columns and the field is the visible baseline grid.
  * at the left headland the plough turns in squared greca hooks: each unit of six furrows nests
    three hairpins (outer, middle, inner, 13 px apart), a square step-fret with an inward return.
  * the top furrow is the horizon: it starts at the sun's edge; the sun is clipped by it.
  * beyond the hooks the furrows bend with the land (contour ploughing), flat where they meet the
    hooks so the grid stays exact next to the text.
CANTINA is in Chango (after lettering by Mexican illustrator Ernesto "Chango" Garcia Cabral); the
sun's edge is placed in the measured gap between T and I, so it never cuts a glyph.

Outputs: menu.html, preview-letter.png (2550x3300), preview-phone.png (1170 wide),
contrast.json, layout.json (geometry, grid registration, eye travel).
"""
import glob, io, json, math, os, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFT = HERE.parent / "build" / "draft_doc.json"
FONTS = (HERE / "fonts").as_uri()
CREAM, INK, INK2, TERRA = "#F3EBDD", "#1E1A17", "#5B5149", "#A6472A"

# ------------------------------------------------------------------ content (unchanged from H2)
DESC = {
    "beta_margarita": "Tequila blanco · fresh lime juice · orange liqueur · agave syrup · lime wheel. Bright and citrus-forward.",
    "beta_manhattan": "Rye whiskey · sweet vermouth · cocktail cherry",
    "beta_daiquiri": "White rum · fresh lime juice · demerara syrup · lime coin",
    "beta_old_fashioned": "Brown butter-washed bourbon · demerara syrup · aromatic bitters · orange peel",
    "beta_czech_pilsner": "Crisp pale lager",
    "beta_dry_hopped_ipa": "Hop-forward draft IPA",
    "beta_amber_lager": "Toasty amber lager",
    "beta_blanco_tequila": "Blanco tequila pour",
    "beta_anejo_tequila": "Añejo tequila pour",
    "beta_cognac_vsop": "VSOP Cognac pour",
    "beta_malbec": "Dry red wine",
    "beta_pinot_grigio": "Dry white wine",
    "beta_brut_rose": "Dry sparkling rosé",
    "beta_dry_cider": "Dry sparkling cider",
}
ITEM_ORDER = {"sub_cocktails_classics": ["beta_margarita", "beta_manhattan"]}
# Reading order: Cocktails, Beer | Cider (next to Beer), Spirits (Agave, Brandy), Wine.
COLUMNS = [["sec_cocktails", "sec_beer"], ["sec_cider", "sec_spirits", "sec_wine"]]


def fmt_price(v):
    return str(int(v)) if v == int(v) else f"{v:.2f}"


def load():
    doc = json.loads(DRAFT.read_text())
    secs = {s["id"]: s for s in doc["sections"]}
    seen, cols = [], []
    for ids in COLUMNS:
        blocks = []
        for sid in ids:
            s = secs[sid]
            groups = [(None, s["items"])] if s.get("items") else []
            for sub in s.get("subs", []):
                items = sub["items"]
                if sub["id"] in ITEM_ORDER:
                    by = {i["id"]: i for i in items}
                    items = [by[k] for k in ITEM_ORDER[sub["id"]]]
                    assert len(items) == len(sub["items"])
                groups.append((sub["name"], items))
            gs = []
            for name, items in groups:
                rows = []
                for it in items:
                    assert len(it["prices"]) == 1
                    seen.append(it["id"])
                    rows.append({"name": it["name"], "desc": DESC[it["id"]],
                                 "price": fmt_price(it["prices"][0]["value"])})
                gs.append({"sub": name, "rows": rows})
            blocks.append({"name": s["name"], "groups": gs})
        cols.append(blocks)
    all_ids = [i["id"] for s in doc["sections"] for i in s.get("items", [])] + \
              [i["id"] for s in doc["sections"] for sub in s.get("subs", []) for i in sub["items"]]
    assert sorted(seen) == sorted(all_ids), "item coverage mismatch"
    return cols


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;")


def desc_html(t):
    """Multi-word ingredients never break; a middot stays at the end of the line it closes.
    Plain sentences (the Margarita's 'Bright and citrus-forward.') keep ordinary spaces."""
    parts = esc(t).split(" · ")
    out = []
    for i, p in enumerate(parts):
        if "." in p:            # 'lime wheel. Bright and citrus-forward.'
            head, tail = p.split(".", 1)
            p = head.replace(" ", "&nbsp;") + "." + tail
        else:
            p = p.replace(" ", "&nbsp;")
        out.append(p)
    return "&nbsp;· ".join(out)


def menu_html(cols):
    out = []
    for i, blocks in enumerate(cols):
        out.append(f'<div class="col col{i+1}">')
        for b in blocks:
            out.append(f'<section><h2>{esc(b["name"])}</h2>')
            for g in b["groups"]:
                if g["sub"]:
                    out.append(f'<h3>{esc(g["sub"])}</h3>')
                for r in g["rows"]:
                    out.append(f'<div class="it"><p class="np"><span class="n">{esc(r["name"])}</span>'
                               f'<span class="p">{r["price"]}</span></p><p class="d">{desc_html(r["desc"])}</p></div>')
            out.append('</section>')
        out.append('</div>')
    return "\n".join(out)


# ------------------------------------------------------------------ layouts
LAYOUTS = {
    "letter": dict(W=816, H=1056, dsf=3.125, m=64, u=13, wm_w=688, cols=[(64, 240), (328, 200)], horizon_min=205,
                   head=552, sun_r=220, bottom=998, top_min=203, sub_gap=30,
                   fs=dict(h2=26, h3=11.5, np=17, d=12, sub=13), amp=14, lam=260, stroke=1.5),
    "phone": dict(W=390, H=None, dsf=3, m=24, u=15, wm_w=342, cols=[(24, 246)], horizon_min=0, hook_dx=8,
                  head=286, sun_r=112, bottom=None, top_min=150, sub_gap=20,
                  fs=dict(h2=22, h3=11.5, np=17, d=13.5, sub=10), amp=8, lam=240, stroke=1.4),
}


def field_path(L, horizon_y, sun, page_h):
    """One continuous path: horizon from the sun's edge, then units of six furrows with nested
    squared hooks (greca) at the headland; off-page turns sit beyond the right trim."""
    u, W, H0 = L["u"], L["W"], L["head"]
    cx, cy, r = sun
    xr = W + 3 * u                      # off-page turn column (bleed)
    hx = L.get("hook_dx", u)             # horizontal pitch of the nested hooks and of the stair
    flat = H0 + 4 * hx                  # contour bending starts after the hooks

    def bend(x, y):
        if x <= flat:
            return y
        s = ((x - flat) / (W - flat)) ** 1.3
        return y + L["amp"] * s * math.sin(2 * math.pi * y / L["lam"])

    def run(y, x0, x1):                 # furrow polyline from x0 to x1 (either direction)
        n = max(2, int(abs(x1 - x0) / 4))
        return [(x0 + (x1 - x0) * i / n, bend(x0 + (x1 - x0) * i / n, y)) for i in range(n + 1)]

    pts = []
    xs = cx - math.sqrt(max(r * r - (horizon_y - cy) ** 2, 0))   # sun meets the horizon here
    pts += run(horizon_y, xs, xr)
    y = horizon_y + u
    unit = 0
    base_h = H0
    while y < page_h + 6 * u:
        H0 = base_h + (unit % 3) * hx     # stair: each hook steps one pitch inward, then resets
        unit += 1
        a, b, c, d, e, f = [y + i * u for i in range(6)]
        pts += [(xr, bend(xr, a))] + run(a, xr, H0) + [(H0, f)] + run(f, H0, xr)[1:]          # outer
        pts += [(xr, bend(xr, e))] + run(e, xr, H0 + hx) + [(H0 + hx, b)] + run(b, H0 + hx, xr)[1:]  # middle
        pts += [(xr, bend(xr, c))] + run(c, xr, H0 + 2*hx) + [(H0 + 2*hx, d)] + run(d, H0 + 2*hx, xr)[1:]  # inner
        y += 6 * u                       # next unit starts on the next furrow: the field is continuous
    return "M" + " L".join(f"{x:.2f},{yy:.2f}" for x, yy in pts)


def page_html(cls, p):
    """p: dict of computed parameters (wm size/base, sun, horizon, grid shifts, top)."""
    L, fs, u = LAYOUTS[cls], LAYOUTS[cls]["fs"], LAYOUTS[cls]["u"]
    cols = load()
    if cls == "phone":
        cols = [cols[0] + cols[1]]
    W, H = L["W"], p.get("page_h", L["H"] or 2400)
    cx, cy, r = p["sun"]
    hz = p["horizon"]
    show_art = p.get("art", True)
    field = field_path(L, hz, p["sun"], H) if show_art else ""
    art = f"""<svg class="art" width="{W}" height="{H}" viewBox="0 0 {W} {H}" overflow="hidden">
<defs><clipPath id="sky"><rect x="-50" y="-50" width="{W+100}" height="{hz + 50:.2f}"/></clipPath>
<clipPath id="sun"><circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}"/></clipPath></defs>
{'' if not show_art else f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{TERRA}" clip-path="url(#sky)"/>'}
{'' if not show_art else f'<path d="{field}" fill="none" stroke="{INK}" stroke-width="{L["stroke"]}" stroke-linejoin="miter" stroke-miterlimit="10"/>'}
<text class="wmk" x="{L['m']}" y="{p['wm_base']:.2f}" textLength="{L['wm_w']}" lengthAdjust="spacing" fill="{INK}">CANTINA</text>
{'' if not show_art else f'<text class="wmk" x="{L["m"]}" y="{p["wm_base"]:.2f}" textLength="{L["wm_w"]}" lengthAdjust="spacing" fill="{CREAM}" clip-path="url(#sun)" aria-hidden="true">CANTINA</text>'}
</svg>"""
    colcss = "\n".join(f".col{i+1}{{left:{x}px;width:{w}px}}" for i, (x, w) in enumerate(L["cols"]))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Cantina - bar menu (explore H3, Sun &amp; Furrow)</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@font-face{{font-family:Ch;font-weight:400;src:url({FONTS}/Chango-400.ttf)}}
@font-face{{font-family:Gd;font-weight:400;src:url({FONTS}/EBGaramond-400.ttf)}}
@font-face{{font-family:Gd;font-weight:500;src:url({FONTS}/EBGaramond-500.ttf)}}
@font-face{{font-family:Gd;font-weight:400;font-style:italic;src:url({FONTS}/EBGaramond-400i.ttf)}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{CREAM}}}
.page{{position:relative;overflow:hidden;background:{CREAM};color:{INK};font-family:Gd;width:{W}px;height:{H}px}}
.art{{position:absolute;left:0;top:0}}
.wmk{{font-family:Ch;font-size:{p['wm_size']:.2f}px}}
.sub{{position:absolute;left:{L['m']}px;top:{p['sub_top']:.1f}px;font-weight:500;font-size:{fs['sub']}px;letter-spacing:{'.26em' if cls=='letter' else '.14em'};
  color:{INK2};text-transform:uppercase;white-space:nowrap;line-height:1}}
.col{{position:absolute;top:{p['top']}px}}
{colcss}
/* baseline grid: every line box is a multiple of U; baselines are shifted onto the furrow lines */
h2{{font-weight:500;font-size:{fs['h2']}px;line-height:{3*u}px;letter-spacing:.12em;color:{TERRA};text-transform:uppercase;
  position:relative;top:{p['shift']['h2']:.2f}px;margin-bottom:{u}px}}
h3{{font-weight:500;font-size:{fs['h3']}px;line-height:{u}px;letter-spacing:.22em;color:{INK2};text-transform:uppercase;
  position:relative;top:{p['shift']['h3']:.2f}px;margin-bottom:{u}px}}
section+section{{margin-top:{4*u}px}}
.it+h3{{margin-top:{u}px}}
.it+.it{{margin-top:{2*u}px}}
.np{{font-weight:500;font-size:{fs['np']}px;line-height:{2*u}px;position:relative;top:{p['shift']['np']:.2f}px}}
.p{{font-weight:400;color:{INK2};font-variant-numeric:lining-nums tabular-nums;margin-left:.9em}}
.d{{font-style:italic;font-size:{fs['d']}px;line-height:{u}px;color:{INK2};position:relative;top:{p['shift']['d']:.2f}px}}
</style></head>
<body class="{cls}"><div class="page">
{art}
<h1 style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">Cantina</h1>
<p class="sub">&amp; cocktail bar &#183; Iowa City, Iowa</p>
{menu_html(cols)}
</div></body></html>"""


# ------------------------------------------------------------------ browser helpers
FIT_JS = """() => { const c=document.createElement('canvas').getContext('2d'); c.font='100px Ch';
  const m=c.measureText('CANTINA'); return {w100:m.width, asc100:m.actualBoundingBoxAscent}; }"""

BASELINE_JS = """() => { const r={}; for (const sel of ['h2','h3','.np','.d']) { const el=document.querySelector(sel);
  const s=document.createElement('span'); s.style.cssText='display:inline-block;width:0;height:0;vertical-align:baseline';
  el.prepend(s); r[sel.replace('.','')]= s.getBoundingClientRect().top - el.getBoundingClientRect().top + 0; s.remove(); }
  // remove the relative shift already applied so offsets are raw
  for (const k in r) { const el=document.querySelector(k==='np'||k==='d'?'.'+k:k); r[k]-=parseFloat(getComputedStyle(el).top)||0; }
  return r; }"""

# Balance: add whole units to gaps (section gaps first, then item gaps) until every column's
# last line box ends exactly on the bottom line; returns per-column feet.
# Balance + field rhythm. Each column must end exactly on the bottom line. Extra whole units go
# (a) to section margins so every section head's baseline lands on a greca-unit key furrow
#     (the unit's top furrow or its inner return, i.e. every 3U from phase unitTop0), and (b) evenly to the item gaps inside each section.
# Brute force over the (small) space of unit allocations; prefer all heads aligned, then even gaps.
BALANCE_JS = """([u, bottom, unitTop0]) => { const out=[]; const U6=6*u;
  const probe=el=>{const s=document.createElement('span');s.style.cssText='display:inline-block;width:0;height:0;vertical-align:baseline';
    el.prepend(s);const y=s.getBoundingClientRect().top;s.remove();return y;};
  document.querySelectorAll('.col').forEach(col => {
    const secs=[...col.querySelectorAll('section')];
    const foot=()=>col.lastElementChild.lastElementChild.getBoundingClientRect().bottom;
    const E=Math.round((bottom - foot())/u);
    const bl=secs.map(s=>probe(s.querySelector('h2')));
    const slots=secs.map(s=>[...s.querySelectorAll('.it+.it, .it+h3')]);
    const n=secs.length; let best=null;
    const rec=(i, used, xs, ms)=>{
      if(i===n){ if(used!==E) return;
        let aligned=0, shift=0;
        for(let k=0;k<n;k++){ if(k>0) shift+=xs[k-1]+ms[k];
          const y=bl[k]+shift*u; const r=(((y-unitTop0)%(U6/2))+U6/2)%(U6/2); if(r<0.5 || r>U6/2-0.5) aligned++; }
        // evenness: variance of the added units per item gap across the whole column (+ a small
        // penalty on section-margin units), so no section's items float apart from the rest
        const loads=[]; xs.forEach((x,k)=>{ const nS=slots[k].length; for(let j=0;j<nS;j++) loads.push(Math.floor(x/nS)+(j<x%nS?1:0)); });
        const mean=loads.reduce((a,b)=>a+b,0)/Math.max(loads.length,1);
        let v=loads.reduce((a,q)=>a+(q-mean)**2,0)/Math.max(loads.length,1);
        v+=0.15*ms.reduce((a,m)=>a+m*m,0);
        const msum=ms.reduce((a,b)=>a+b,0);
        const score=[-aligned, v, msum];
        if(!best || score[0]<best.score[0] || (score[0]===best.score[0] && (score[1]<best.score[1]-1e-9 || (Math.abs(score[1]-best.score[1])<1e-9 && score[2]<best.score[2]))))
          best={score, xs:[...xs], ms:[...ms], aligned};
        return; }
      const maxX = slots[i].length ? E-used : 0;
      for(let m=0; m<=(i===0?0:11); m++) for(let x=0; x<=maxX-m; x++){
        if(used+m+x>E) break; xs[i]=x; ms[i]=m; rec(i+1, used+m+x, xs, ms); } };
    rec(0,0,new Array(n).fill(0),new Array(n).fill(0));
    secs.forEach((s,k)=>{ if(k>0 && best.ms[k]) s.style.marginTop=(parseFloat(getComputedStyle(s).marginTop)+best.ms[k]*u)+'px';
      for(let j=0;j<best.xs[k];j++){ const el=slots[k][j%slots[k].length]; el.style.marginTop=(parseFloat(getComputedStyle(el).marginTop)+u)+'px'; } });
    out.push({foot:foot(), extra_units:E, section_margin_units:best.ms, item_units:best.xs, heads_on_unit_tops:best.aligned+'/'+n}); });
  return out; }"""

HEAD_BASELINE_JS = """() => { const el=document.querySelector('h2'); const s=document.createElement('span');
  s.style.cssText='display:inline-block;width:0;height:0;vertical-align:baseline'; el.prepend(s);
  const y=s.getBoundingClientRect().top; s.remove(); return y; }"""

CONTRAST_JS = """() => { const out=[]; const walker=document.createTreeWalker(document.querySelector('.page'),NodeFilter.SHOW_TEXT);
  let n; while(n=walker.nextNode()){ if(!n.textContent.trim()) continue; const el=n.parentElement;
    if(el.closest('svg')||el.tagName==='H1') continue;
    const r=document.createRange(); r.selectNodeContents(n); for(const b of r.getClientRects()){
      if(b.width<1) continue; out.push({t:n.textContent.trim().slice(0,40),c:getComputedStyle(el).color,
      role:el.className||el.tagName,x:b.x,y:b.y,w:b.width,h:b.height});}}
  return out;}"""

GEOM_JS = """() => { const q=s=>[...document.querySelectorAll(s)].map(e=>{const b=e.getBoundingClientRect();
  return {sel:s,text:(e.textContent||'').trim().slice(0,30),x:+b.left.toFixed(1),y:+b.top.toFixed(1),w:+b.width.toFixed(1),h:+b.height.toFixed(1)}});
  const W=document.querySelector('.page').getBoundingClientRect().width;
  const travel=[...document.querySelectorAll('.np')].map(e=>{const n=e.querySelector('.n').getBoundingClientRect(),
    p=e.querySelector('.p').getBoundingClientRect(); return {item:e.querySelector('.n').textContent,
    gap_px:+(p.left-n.right).toFixed(1), gap_pct:+(100*(p.left-n.right)/W).toFixed(2),
    name_start_to_price_end_pct:+(100*(p.right-n.left)/W).toFixed(1)}});
  // baselines of every line of reading text (for the grid-registration check)
  const bl=[], bld=[]; document.querySelectorAll('h2,h3,.np,.d').forEach(el=>{ const s=document.createElement('span');
    s.style.cssText='display:inline-block;width:0;height:0;vertical-align:baseline'; el.prepend(s);
    (el.classList.contains('d')?bld:bl).push(+s.getBoundingClientRect().top.toFixed(2)); s.remove(); });
  const cols=[...document.querySelectorAll('.col')].map(c=>{const l=c.lastElementChild.lastElementChild.querySelector('.d')||c.lastElementChild.lastElementChild;
    const r=document.createRange(); r.selectNodeContents(l); const rs=[...r.getClientRects()]; const b=c.getBoundingClientRect();
    return {x:b.left,y:b.top,w:b.width,last_line_box_bottom:+c.lastElementChild.lastElementChild.getBoundingClientRect().bottom.toFixed(2),
            last_glyph_bottom:+Math.max(...rs.map(x=>x.bottom)).toFixed(2)}});
  return {wordmark:q('.wmk')[0],sub:q('.sub')[0],columns:cols,section_heads:q('h2'),sub_heads:q('h3'),
    eye_travel:travel,baselines:bl,desc_baselines:bld} }"""


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast_check(page, scale):
    from PIL import Image
    boxes = page.evaluate(CONTRAST_JS)
    page.add_style_tag(content=".page p, .page h2, .page h3, .page span{color:transparent !important}")
    img = Image.open(io.BytesIO(page.screenshot(full_page=True))).convert("RGB")
    res = []
    for b in boxes:
        rgb = tuple(int(float(v)) for v in re.findall(r"[\d.]+", b["c"])[:3])
        L1 = lum(rgb)
        x0, y0 = max(0, int(b["x"] * scale)), max(0, int(b["y"] * scale))
        x1, y1 = min(img.width, int((b["x"] + b["w"]) * scale)), min(img.height, int((b["y"] + b["h"]) * scale))
        worst = 99
        for px in set(img.crop((x0, y0, x1, y1)).getdata()):
            worst = min(worst, (max(L1, lum(px)) + 0.05) / (min(L1, lum(px)) + 0.05))
        res.append({"text": b["t"], "role": b["role"], "min": round(worst, 2)})
    res.sort(key=lambda r: r["min"])
    return res


def glyph_gap(page, L, size, base, cap):
    """Measure the ink gap between T (glyph 4) and I (glyph 5) of the fitted wordmark."""
    from PIL import Image
    import numpy as np
    dsf = L["dsf"]
    top, bot = base - cap * 0.9, base - cap * 0.1
    shot = page.screenshot(clip={"x": 0, "y": top, "width": L["W"], "height": bot - top})
    a = np.asarray(Image.open(io.BytesIO(shot)).convert("L"), dtype=np.float32) / 255
    ink = (a < 0.5).any(axis=0)
    runs, inrun = [], False
    for x, v in enumerate(ink):
        if v and not inrun:
            start, inrun = x, True
        elif not v and inrun:
            runs.append((start, x - 1)); inrun = False
    if inrun:
        runs.append((start, len(ink) - 1))
    assert len(runs) == 7, runs
    return runs[3][1] / dsf, runs[4][0] / dsf     # T right ink edge, I left ink edge (css px)


def render(b, cls):
    L = LAYOUTS[cls]
    u, m = L["u"], L["m"]
    pg = b.new_page(viewport={"width": L["W"], "height": L["H"] or 844}, device_scale_factor=L["dsf"])
    tmp = HERE / f".render-{cls}.html"

    def load(p):
        tmp.write_text(page_html(cls, p))
        pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)

    zero = {"h2": 0, "h3": 0, "np": 0, "d": 0}
    p = dict(wm_size=100, wm_base=200, sun=(0, 0, 1), horizon=0, sub_top=0, top=400, shift=zero, art=False)
    load(p)
    fit = pg.evaluate(FIT_JS)
    size = 100 * L["wm_w"] / (fit["w100"] * 1.08)   # ~8% added spacing opens the T|I gap for the sun's edge
    cap = fit["asc100"] * size / 100
    base = m + cap                                      # cap top on the top margin
    p.update(wm_size=size, wm_base=base, sub_top=base + L["sub_gap"])
    load(p)
    t_right, i_left = glyph_gap(pg, L, size, base, cap)
    # sun: centre on the cap middle; its edge stays inside the T|I gap over the whole cap height
    r = L["sun_r"]; cy = base - cap / 2; h = cap / 2
    sag = r - math.sqrt(r * r - h * h)                  # how far the edge moves right at cap top/bottom
    cx = (t_right + i_left) / 2 - sag / 2 + r
    edge = (cx - r, cx - r + sag)
    # baseline offsets -> shifts so every style's baseline lands on the .d grid (mod u)
    raw = pg.evaluate(BASELINE_JS)
    ref = raw["d"]
    shift = {}
    for k, v in raw.items():
        s = (ref - v) % u
        shift[k] = s - u if s > u / 2 else s
    # names: baseline on the FIRST grid line of their 2U box
    shift["np"] = ref - raw["np"]
    shift["d"] = shift["d"] - u / 2      # descriptions sit on the half-grid: name->description = 1.5U
    # column top: whole units above the bottom line, below the horizon
    if L["bottom"]:
        n_units = int((L["bottom"] - L["top_min"]) // u)
        top = L["bottom"] - n_units * u
    else:
        top = int(math.ceil((base + 50) / u) * u)       # phone: horizon + sub-line sit between wordmark and list
    p.update(sun=(cx, cy, r), horizon=top, top=top, shift=shift, art=True)
    load(p)
    # field phase: a greca unit's top furrow = the first section head's baseline; the horizon is
    # the furrow directly above that unit (or a whole unit higher, if that stays below horizon_min)
    b0 = pg.evaluate(HEAD_BASELINE_JS)
    if cls == "phone":   # phone: horizon just under the wordmark, sub-line under it, first head one unit + 1U lower
        off = b0 - top
        top = int(math.ceil((base + 10 + 7 * u - off) / u) * u)
        p["top"] = top
        load(p)
        b0 = pg.evaluate(HEAD_BASELINE_JS)
    horizon = b0 - u
    hmin = L["horizon_min"] if cls == "letter" else base + 8
    while horizon - 6 * u >= hmin:
        horizon -= 6 * u
    p["horizon"] = horizon
    if cls == "phone":
        p["sub_top"] = horizon + 11                   # sub-line under the horizon, left of the field
    load(p)
    feet = None
    if L["bottom"]:
        feet = pg.evaluate("(a) => (" + BALANCE_JS + ")(a)", [u, L["bottom"], horizon + u])
    else:  # phone: page height = content + bottom margin, snapped to the grid
        bottom = pg.evaluate("() => Math.max(...[...document.querySelectorAll('.col')].map(c=>c.getBoundingClientRect().bottom))")
        p["page_h"] = int(bottom + m)
        load(p)
    geo = pg.evaluate(GEOM_JS)
    grid0 = top + ref
    geo["grid"] = {"u": u, "first_baseline": round(grid0, 2), "horizon": round(p["horizon"], 2),
                   "heads_subheads_names_off_grid_max_px": round(max(abs(((y - grid0 + u / 2) % u) - u / 2) for y in geo["baselines"]), 3),
                   "descriptions_off_half_grid_max_px": round(max(abs(((y - grid0 + u / 4) % (u / 2)) - u / 4) for y in geo["desc_baselines"]), 3),
                   "n_baselines": len(geo["baselines"]), "n_desc_baselines": len(geo["desc_baselines"])}
    del geo["baselines"], geo["desc_baselines"]
    geo["wordmark_font_px"] = round(size, 2)
    geo["cap"] = [round(base - cap, 2), round(base, 2)]
    geo["t_i_gap_css"] = [round(t_right, 2), round(i_left, 2)]
    geo["sun"] = {"cx": round(cx, 2), "cy": round(cy, 2), "r": r, "edge_x_range_in_cap_band": [round(e, 2) for e in edge]}
    geo["column_top"] = top
    geo["feet_line_box"] = feet
    geo["shift"] = {k: round(v, 2) for k, v in shift.items()}
    name = f"preview-{cls}.png"
    if cls == "letter":
        (HERE / "menu.html").write_text(tmp.read_text())
    pg.screenshot(path=str(HERE / name), full_page=True)
    con = contrast_check(pg, L["dsf"])
    tmp.unlink()
    pg.close()
    return name, geo, con


def main():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    report, layout = {}, {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=next(glob.iglob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")))
        for cls in ("letter", "phone"):
            name, geo, con = render(b, cls)
            layout[name], report[name] = geo, con
        b.close()
    (HERE / "contrast.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (HERE / "layout.json").write_text(json.dumps(layout, indent=1, ensure_ascii=False))
    for k, v in report.items():
        r = {}
        for e in v:
            r[e["role"]] = min(r.get(e["role"], 99), e["min"])
        print(k, "contrast by role:", r)
    for k, v in layout.items():
        et = v["eye_travel"]
        print(k, "feet:", v["feet_line_box"], [c["last_line_box_bottom"] for c in v["columns"]],
              "grid:", v["grid"], "gap:", v["t_i_gap_css"], "sun:", v["sun"],
              "max gap px:", max(e["gap_px"] for e in et), "max name->price %:", max(e["name_start_to_price_end_pct"] for e in et))


if __name__ == "__main__":
    main()
