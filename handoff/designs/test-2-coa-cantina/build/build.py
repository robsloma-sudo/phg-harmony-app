import json, base64, html, unicodedata, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from source import ALL, fix

HERE = os.path.dirname(__file__)
OUT = '/home/user/phg-harmony-app/handoff/designs/test-2-coa-cantina'
os.makedirs(OUT, exist_ok=True)
SRC = {r[0]: r for r in ALL}
E = html.escape

# ---------------------------------------------------------------- content model
# spec: 'venue' = venue's own notes; 'standard' = public.cocktail_reference; 'name' = stated in the item name
STD_MARG = ['blanco tequila', 'lime', 'orange liqueur']
COCKTAILS = {
 # id: (printed desc, components[(name, role, source)], missing list)
 173909: ('Blanco tequila, lime, orange liqueur', [('Blanco tequila','base','venue'),('Lime','citrus','standard'),('Orange liqueur','modifier','standard')], []),
 173910: ('Banhez mezcal, lime, orange liqueur', [('Banhez mezcal','base','venue'),('Lime','citrus','standard'),('Orange liqueur','modifier','standard')], []),
 173911: ('Blanco tequila, lime, orange liqueur, cucumber, jalapeño', [('Blanco tequila','base','venue'),('Lime','citrus','standard'),('Orange liqueur','modifier','standard'),('Cucumber','flavour','name'),('Jalapeño','flavour','name')], ['form of cucumber and jalapeño (muddled, infused, syrup?)']),
 173912: ('Blanco tequila, lime, orange liqueur, mango', [('Blanco tequila','base','venue'),('Lime','citrus','standard'),('Orange liqueur','modifier','standard'),('Mango','flavour','name')], ['form of mango (purée, syrup, fresh?)']),
 173908: ('Blanco tequila, lime, orange liqueur, blackberry', [('Blanco tequila','base','venue'),('Lime','citrus','standard'),('Orange liqueur','modifier','standard'),('Blackberry','flavour','name')], ['form of blackberry']),
 173913: ('Blanco tequila, lime, orange liqueur, peach', [('Blanco tequila','base','venue'),('Lime','citrus','standard'),('Orange liqueur','modifier','standard'),('Peach','flavour','name')], ['form of peach']),
 173914: ('Blanco tequila, lime, orange liqueur, pineapple', [('Blanco tequila','base','venue'),('Lime','citrus','standard'),('Orange liqueur','modifier','standard'),('Pineapple','flavour','name')], ['form of pineapple']),
 173915: ('Blanco tequila, lime, orange liqueur, strawberry', [('Blanco tequila','base','venue'),('Lime','citrus','standard'),('Orange liqueur','modifier','standard'),('Strawberry','flavour','name')], ['form of strawberry']),
 173918: ('Blanco tequila, fresh lime, grapefruit, Aperol, grapefruit soda, salted rim', [('Blanco tequila','base','venue'),('Fresh lime','citrus','venue'),('Grapefruit','citrus','venue'),('Aperol','modifier','venue'),('Grapefruit soda','lengthener','venue'),('Salted rim','garnish','venue')], []),
 173921: ('Blanco tequila, fresh lime juice, Topo Chico sparkling water', [('Blanco tequila','base','venue'),('Fresh lime juice','citrus','venue'),('Topo Chico sparkling water','lengthener','venue')], ['garnish']),
 173916: ('Blanco tequila, tomato juice, lemon, Worcestershire, hot sauce, celery salt', [('Blanco tequila','base','venue'),('Tomato juice','mixer','standard'),('Lemon','citrus','standard'),('Worcestershire','seasoning','standard'),('Hot sauce','seasoning','standard'),('Celery salt','seasoning','standard')], ['garnish']),
 173920: ('Made with Dos Equis', [('Dos Equis','base','venue')], ['michelada mix / seasonings, citrus, rim, garnish']),
 173917: ('Blanco tequila', [('Blanco tequila','base','venue')], ['all modifiers, mixers and garnish']),
 173919: ('Tequila', [('Tequila','base','venue')], ['all modifiers and garnish']),
 173922: ('Blanco tequila, frozen', [('Blanco tequila','base','venue')], ['all flavours and mixers']),
 173923: ('Blanco tequila, lime, orange liqueur, mango', [('Blanco tequila','base','venue'),('Lime','citrus','standard'),('Orange liqueur','modifier','standard'),('Mango','flavour','name')], ['frozen base / mix']),
 173924: ('Blanco tequila, lime, orange liqueur, strawberry', [('Blanco tequila','base','venue'),('Lime','citrus','standard'),('Orange liqueur','modifier','standard'),('Strawberry','flavour','name')], ['frozen base / mix']),
 173925: ('Blanco tequila, frozen', [('Blanco tequila','base','venue')], ['which tropical fruits; mixers']),
 173975: ('Zero-proof alternatives to tequila, gin or whiskey', [('Ritual Zero Proof (tequila, gin or whiskey alternative)','base','venue')], []),
}
UPGRADE = {173918: (184680, 'Upgrade to Don Julio Blanco', 4), 173921: (184681, 'Upgrade to DeLeón Platinum', 2)}

KNOWN_BEER = {173932: 'American light lager', 173933: 'American light lager', 173941: 'International pale lager',
              173930: 'Golden ale', 173931: 'IPA'}  # brand_products.declared_style, or the style stated in the name
SPIRIT_DESC = {173955: 'Cucumber & mint · grapefruit & rose · peach & orange blossom',
               173956: 'Grape · orange · citrus · raspberry · watermelon',
               174103: 'Coffee liqueur', 174104: 'Tequila'}

def names(ids): return [(i, fix(SRC[i][2]), SRC[i][3]) for i in ids]

MARGS = [173909, 173910, 173911, 173912, 173908, 173913, 173914, 173915]
COCKS = [173918, 173921, 173916, 173920, 173917, 173919]
FROZEN = [173923, 173924, 173925, 173922]
AF = [173975]
DRAFT = [173926, 173928, 173927, 173930, 173931, 173929]
BOTTLES = [173937, 173936, 173941, 173942, 173938, 173932, 173933, 173934, 173935, 173940]
SELTZ = [173943, 173944, 173945, 173948, 173949, 173950, 173951, 173946, 173947, 173939]
VODKA = [173952, 173954, 173955, 173957, 173953, 173956]
GIN = [173965, 173962, 173963, 173964]
RUM = [173958, 173959, 173960, 173961]
WHISKEY = [173970, 173969, 173967, 173968, 173966, 173972, 173971]
SCOTCH = [173974, 173973]
OTROS = [174103, 174104]
# sort spirits by price then name for a clean ladder
def ladder(ids): return sorted(ids, key=lambda i: (SRC[i][3] if SRC[i][3] is not None else 999, fix(SRC[i][2])))
VODKA, GIN, RUM, WHISKEY, SCOTCH = map(ladder, (VODKA, GIN, RUM, WHISKEY, SCOTCH))

TEQ = [r for r in ALL if r[1] in ('Blanco', 'Reposado', 'Anejo')]
def is_cris(n): return 'Cristalino' in n or 'Cristalnio' in n
def is_extra(n): return ' Extra' in n
CRIS = [r for r in TEQ if is_cris(r[2])]
EXTRA = [r for r in TEQ if is_extra(r[2])]
CORE = [r for r in TEQ if not is_cris(r[2]) and not is_extra(r[2])]
def skey(n): return unicodedata.normalize('NFKD', n).encode('ascii', 'ignore').decode().lower()
rows = {}
for i, sec, n, p, _ in CORE:
    rows.setdefault(fix(n), {})[sec[0]] = (i, p)
MATRIX = sorted(rows.items(), key=lambda kv: skey(kv[0]))
CRIS = sorted(CRIS, key=lambda r: skey(fix(r[2])))
EXTRA = sorted(EXTRA, key=lambda r: r[3])

# ---------------------------------------------------------------- doc.json
def item(i, desc='', label='', comps=None, missing=None, section_note=None, extra_prices=None, merged=None):
    r = SRC[i]
    prices = [] if r[3] is None else [{'id': f'p_sme_{i}', 'label': label, 'value': r[3], 'source': 'staging_menu_extract'}]
    for (uid, ulabel, uval) in (extra_prices or []):
        prices.append({'id': f'p_sme_{uid}', 'label': ulabel, 'value': uval, 'source': 'staging_menu_extract'})
    meta = {'source_id': i, 'source_section': r[1], 'source_name': r[2]}
    if fix(r[2]) != r[2]: meta['name_normalised_from'] = r[2]
    if merged: meta['merged_from'] = merged
    if missing: meta['missing_ingredients'] = missing
    if r[3] is None: meta['needs_price'] = True
    if section_note: meta['placement_note'] = section_note
    it = {'id': f'sme_{i}', 'name': fix(r[2]), 'brand': '', 'desc': desc, 'badges': [], 'prices': prices,
          'meta': meta, 'origin': {'item_name': r[2], 'venue_key': 'ACC-IA-LIC-LC0049193'}, 'source': 'staging_menu_extract'}
    if comps:
        it['components'] = [{'kind': 'ingredient', 'name': n, 'role': role, 'spec_source': s} for n, role, s in comps]
    return it

def cocktail(i):
    d, comps, miss = COCKTAILS[i]
    up = UPGRADE.get(i)
    return item(i, d, comps=comps, missing=miss, extra_prices=[up] if up else None, merged=[up[0]] if up else None)

def simple(i, desc=''):
    miss = None
    return item(i, desc)

doc = {'id': 'menu_coa_drinks', 'title': 'Coa Cantina — Drinks', 'size': 'legal_p', 'sections': [
 {'id': 'sec_margaritas', 'name': 'Margaritas', 'desc': '', 'items': [cocktail(i) for i in MARGS], 'subs': []},
 {'id': 'sec_cocktails', 'name': 'Cocktails', 'desc': '', 'items': [cocktail(i) for i in COCKS], 'subs': []},
 {'id': 'sec_frozen', 'name': 'Frozen Drinks', 'desc': '', 'items': [cocktail(i) for i in FROZEN], 'subs': []},
 {'id': 'sec_beer', 'name': 'Beer', 'desc': '', 'items': [], 'subs': [
   {'id': 'sub_beer_draft', 'name': 'Draft', 'desc': '', 'items': [item(i, KNOWN_BEER.get(i, ''), missing=['style' if i not in KNOWN_BEER else None, 'ABV']) for i in DRAFT]},
   {'id': 'sub_beer_bottles', 'name': 'Bottles & Cans', 'desc': '', 'items': [item(i, KNOWN_BEER.get(i, ''), missing=['style' if i not in KNOWN_BEER else None, 'ABV']) for i in BOTTLES]}]},
 {'id': 'sec_seltzer_cider', 'name': 'Seltzer & Cider', 'desc': '', 'items': [item(i, '', missing=['base spirit / style', 'ABV'], section_note='venue lists under Bottles & Cans') for i in SELTZ], 'subs': []},
 {'id': 'sec_tequila', 'name': 'Tequila', 'desc': 'By expression', 'items': [], 'subs': [
   {'id': 'sub_teq_blanco', 'name': 'Blanco', 'desc': '', 'items': []},
   {'id': 'sub_teq_reposado', 'name': 'Reposado', 'desc': '', 'items': []},
   {'id': 'sub_teq_anejo', 'name': 'Añejo', 'desc': '', 'items': []},
   {'id': 'sub_teq_cristalino', 'name': 'Cristalino', 'desc': '', 'items': []},
   {'id': 'sub_teq_extra', 'name': 'Extra Añejo', 'desc': '', 'items': []}]},
 {'id': 'sec_vodka', 'name': 'Vodka', 'desc': '', 'items': [item(i, SPIRIT_DESC.get(i, 'Vodka')) for i in VODKA], 'subs': []},
 {'id': 'sec_gin', 'name': 'Gin', 'desc': '', 'items': [item(i, 'Gin') for i in GIN], 'subs': []},
 {'id': 'sec_rum', 'name': 'Rum', 'desc': '', 'items': [item(i, 'Rum') for i in RUM], 'subs': []},
 {'id': 'sec_whiskey', 'name': 'Whiskey', 'desc': '', 'items': [item(i, 'Whiskey') for i in WHISKEY], 'subs': []},
 {'id': 'sec_scotch', 'name': 'Scotch', 'desc': '', 'items': [item(i, 'Scotch whisky') for i in SCOTCH], 'subs': []},
 {'id': 'sec_otros', 'name': 'Otros', 'desc': '', 'items': [item(i, SPIRIT_DESC[i], section_note='venue section: Misc') for i in OTROS], 'subs': []},
 {'id': 'sec_alcohol_free', 'name': 'Alcohol Free', 'desc': '', 'items': [cocktail(i) for i in AF], 'subs': []},
]}
for it in (x for s in doc['sections'] for sub in s['subs'] for x in sub['items']):
    if 'missing_ingredients' in it['meta']: it['meta']['missing_ingredients'] = [m for m in it['meta']['missing_ingredients'] if m]
for s in doc['sections']:
    for x in s['items']:
        if 'missing_ingredients' in x['meta']: x['meta']['missing_ingredients'] = [m for m in x['meta']['missing_ingredients'] if m]
teq = {s['id']: s for s in doc['sections'][5]['subs']}
LAB = {'Blanco': 'Blanco', 'Reposado': 'Reposado', 'Anejo': 'Añejo'}
for r in sorted(CORE, key=lambda r: skey(fix(r[2]))):
    sub = {'Blanco': 'sub_teq_blanco', 'Reposado': 'sub_teq_reposado', 'Anejo': 'sub_teq_anejo'}[r[1]]
    teq[sub]['items'].append(item(r[0], f'{LAB[r[1]]} tequila', label=LAB[r[1]]))
for r in CRIS:
    teq['sub_teq_cristalino']['items'].append(item(r[0], f'{LAB[r[1]]} cristalino', label=LAB[r[1]], section_note=f'venue lists under {LAB[r[1]]}'))
for r in EXTRA:
    teq['sub_teq_extra']['items'].append(item(r[0], 'Extra añejo', label='Añejo', section_note='venue lists under Añejo; name states Extra'))
json.dump(doc, open(f'{OUT}/doc.json', 'w'), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- HTML
def b64(f): return base64.b64encode(open(f'{HERE}/fonts/{f}', 'rb').read()).decode()
FONTS = f"""
@font-face{{font-family:'Fraunces';font-style:normal;font-weight:400 900;src:url(data:font/woff2;base64,{b64('fraunces.woff2')}) format('woff2');}}
@font-face{{font-family:'Fraunces';font-style:italic;font-weight:400 700;src:url(data:font/woff2;base64,{b64('fraunces-i.woff2')}) format('woff2');}}
@font-face{{font-family:'DM Sans';font-style:normal;font-weight:400 800;src:url(data:font/woff2;base64,{b64('dmsans.woff2')}) format('woff2');}}
@font-face{{font-family:'DM Sans';font-style:italic;font-weight:400;src:url(data:font/woff2;base64,{b64('dmsans-i.woff2')}) format('woff2');}}
"""

def price_txt(v): return '—' if v is None else str(v)

def papel(width_pt=540, h=20):
    # papel picado banner: a string with alternating cut-paper flags
    cols = ['#B03A26', '#E3A33B', '#145A55']
    n = 15; fw = width_pt / n
    parts = [f'<svg class="papel" data-k="ornament" viewBox="0 0 {width_pt} {h}" width="{width_pt}pt" height="{h}pt" aria-hidden="true">',
             f'<path d="M0 1.2 H{width_pt}" stroke="#1F1B18" stroke-width="0.6"/>']
    for k in range(n):
        x0 = k * fw + 3; x1 = (k + 1) * fw - 3; c = cols[k % 3]; mid = (x0 + x1) / 2
        zig = ' '.join(f'L{x1 - j * (x1 - x0) / 6:.2f} {h - (0 if j % 2 == 0 else 3.2):.2f}' for j in range(7))
        parts.append(f'<path d="M{x0:.2f} 1.2 L{x1:.2f} 1.2 L{x1:.2f} {h:.2f} {zig} Z" fill="{c}"/>')
        parts.append(f'<circle cx="{mid:.2f}" cy="{h*0.42:.2f}" r="2.6" fill="#F5EEDF"/>')
        parts.append(f'<path d="M{mid-7:.2f} {h*0.42:.2f} l2.4 -2.4 l2.4 2.4 l-2.4 2.4 Z M{mid+2.2:.2f} {h*0.42:.2f} l2.4 -2.4 l2.4 2.4 l-2.4 2.4 Z" fill="#F5EEDF"/>')
    parts.append('</svg>')
    return ''.join(parts)

AGAVE = '''<svg class="agave" viewBox="0 0 60 34" aria-hidden="true"><g fill="none" stroke-linecap="round">
<path d="M30 32 C29 20 28 10 30 1" stroke="#145A55" stroke-width="2.2"/>
<path d="M30 32 C25 22 19 14 11 8" stroke="#145A55" stroke-width="2"/><path d="M30 32 C35 22 41 14 49 8" stroke="#145A55" stroke-width="2"/>
<path d="M30 32 C22 26 12 22 2 21" stroke="#E3A33B" stroke-width="2"/><path d="M30 32 C38 26 48 22 58 21" stroke="#E3A33B" stroke-width="2"/>
<path d="M30 32 C27 24 23 17 20 5" stroke="#B03A26" stroke-width="1.6"/><path d="M30 32 C33 24 37 17 40 5" stroke="#B03A26" stroke-width="1.6"/>
</g></svg>'''

def divider():
    return f'<div class="divider" data-k="divider"><span class="rule"></span>{AGAVE}<span class="rule"></span></div>'

def mast(kicker, title):
    return f'''<header class="mast">{papel()}
<div class="mastrow"><div class="wordmark" data-k="header" data-lvl="0">Coa Cantina</div>
<div class="mastright"><div class="masttitle" data-k="header" data-lvl="0b">{E(title)}</div><div class="kicker" data-k="description">{E(kicker)}</div></div></div>
<div class="doublerule" data-k="divider"></div></header>'''

def footer(n):
    return f'''<footer class="foot" data-k="description"><span>Coa Cantina · Iowa City</span><span class="fdot">{AGAVE}</span><span>coacantinaiowacity.com · {n}/2</span></footer>'''

def h1(txt, ref=''):
    return f'<h2 class="h1" data-k="header" data-ref="{ref}"><span>{E(txt)}</span></h2>'
def h2(txt, ref=''):
    return f'<h3 class="h2" data-k="subheader" data-ref="{ref}">{E(txt)}</h3>'

def rich(i, feature=False):
    r = SRC[i]; d, _, miss = COCKTAILS[i]
    up = UPGRADE.get(i)
    cls = 'ritem feature' if feature else 'ritem'
    s = f'<div class="{cls}" data-item="sme_{i}">'
    s += f'<div class="line"><span class="nm" data-k="item_name" data-ref="sme_{i}">{E(fix(r[2]))}</span><span class="pr" data-k="price" data-ref="sme_{i}">{price_txt(r[3])}</span></div>'
    s += f'<div class="line"><span class="ds" data-k="description" data-ref="sme_{i}">{E(d)}</span></div>'
    if up:
        s += f'<div class="line up"><span class="ds" data-k="description" data-ref="sme_{i}">{E(up[1])}</span><span class="pr small" data-k="price" data-ref="sme_{i}">+{up[2]}</span></div>'
    return s + '</div>'

def row(i, desc=None):
    r = SRC[i]
    muted = ' na' if r[3] is None else ''
    s = f'<div class="row" data-item="sme_{i}"><div class="line"><span class="nm" data-k="item_name" data-ref="sme_{i}">{E(fix(r[2]))}</span><span class="pr{muted}" data-k="price" data-ref="sme_{i}">{price_txt(r[3])}</span></div>'
    if desc: s += f'<div class="line"><span class="ds" data-k="description" data-ref="sme_{i}">{E(desc)}</span></div>'
    return s + '</div>'

def block(title, ids, lvl=1, descs=None, ref=''):
    hd = h1(title, ref) if lvl == 1 else h2(title, ref)
    return f'<section class="blk">{hd}<div class="rows">' + ''.join(row(i, (descs or {}).get(i)) for i in ids) + '</div></section>'

# ---- page 1
p1_left = (f'<section class="blk">{h1("Margaritas","sec_margaritas")}<div class="rows">' + rich(MARGS[0], True) + ''.join(rich(i) for i in MARGS[1:]) + '</div></section>'
           + f'<section class="blk">{h1("Alcohol Free","sec_alcohol_free")}<div class="rows">' + rich(AF[0]) + '</div></section>')
p1_right = (f'<section class="blk">{h1("Cocktails","sec_cocktails")}<div class="rows">' + rich(COCKS[0], True) + ''.join(rich(i) for i in COCKS[1:]) + '</div></section>'
            + f'<section class="blk">{h1("Frozen","sec_frozen")}<div class="rows">' + ''.join(rich(i) for i in FROZEN) + '</div></section>')
beer = (f'<div class="band">{h1("Beer, Seltzer & Cider","sec_beer")}<div class="thirds">'
        f'<div class="col">{block("Draft", DRAFT, 2, ref="sub_beer_draft")}</div>'
        f'<div class="col">{block("Bottles & Cans", BOTTLES, 2, ref="sub_beer_bottles")}</div>'
        f'<div class="col">{block("Seltzer & Cider", SELTZ, 2, ref="sec_seltzer_cider")}</div></div></div>')
page1 = (f'<article class="page" id="page-1">{mast("Iowa City · Bebidas", "Drinks")}'
         f'<main class="body"><div class="halves"><div class="col">{p1_left}{divider()}</div><div class="col">{p1_right}</div></div>'
         f'{beer}</main>{footer(1)}</article>')

# ---- page 2: tequila matrix
def mrow(name, cells):
    ref = ' '.join(f'sme_{c[0]}' for c in cells.values())
    s = f'<div class="mrow" data-item="{ref}"><span class="nm" data-k="item_name" data-ref="{ref}">{E(name)}</span>'
    for k in 'BRA':
        if k in cells:
            s += f'<span class="mc pr" data-k="price" data-col="{k}" data-ref="sme_{cells[k][0]}">{cells[k][1]}</span>'
        else:
            s += f'<span class="mc empty" data-col="{k}" aria-hidden="true">·</span>'
    return s + '</div>'

def mhead():
    return ('<div class="mhead"><span class="nm">&nbsp;</span>'
            '<span class="mc" data-k="subheader">Blanco</span><span class="mc" data-k="subheader">Reposado</span><span class="mc" data-k="subheader">Añejo</span></div>')

half = (len(MATRIX) + len(CRIS) + len(EXTRA) + 2) // 2
# split: left gets first N matrix rows + cristalino group; right gets the rest + extra group
nL = half - len(CRIS) - 1
left_rows = MATRIX[:nL]; right_rows = MATRIX[nL:]
def grp(title, rs, ref):
    out = f'<div class="mgroup">{h2(title, ref)}'
    for r in rs:
        k = {'Blanco': 'B', 'Reposado': 'R', 'Anejo': 'A'}[r[1]]
        out += mrow(fix(r[2]), {k: (r[0], r[3])})
    return out + '</div>'
mleft = f'<div class="col matrix">{mhead()}' + ''.join(mrow(n, c) for n, c in left_rows) + grp('Cristalino', CRIS, 'sub_teq_cristalino') + '</div>'
mright = f'<div class="col matrix">{mhead()}' + ''.join(mrow(n, c) for n, c in right_rows) + grp('Extra Añejo', EXTRA, 'sub_teq_extra') + '</div>'

sp = (f'<div class="band">{h1("Spirits","sec_spirits")}<div class="quarters">'
      f'<div class="col">{block("Vodka", VODKA, 2, SPIRIT_DESC, "sec_vodka")}</div>'
      f'<div class="col">{block("Gin", GIN, 2, ref="sec_gin")}{block("Rum", RUM, 2, ref="sec_rum")}</div>'
      f'<div class="col">{block("Whiskey", WHISKEY, 2, ref="sec_whiskey")}</div>'
      f'<div class="col">{block("Scotch", SCOTCH, 2, ref="sec_scotch")}{block("Otros", OTROS, 2, SPIRIT_DESC, "sec_otros")}</div></div></div>')
page2 = (f'<article class="page" id="page-2">{mast("Blanco · Reposado · Añejo", "Agave & Spirits")}'
         f'<main class="body"><div class="band">{h1("Tequila","sec_tequila")}<div class="halves">{mleft}{mright}</div></div>{sp}</main>{footer(2)}</article>')

CSS = open(f'{HERE}/menu.css').read()
doc_html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Coa Cantina — Drinks (US Legal 8.5 × 14 in, 2 pages)</title>
<!-- Print size: US Legal 8.5 x 14 in (215.9 x 355.6 mm), portrait, 2 pages (duplex). Margins 0.5 in (12.7 mm) all sides. No bleed required: all colour sits inside the margins. -->
<style>{FONTS}{CSS}</style></head><body>
{page1}
{page2}
</body></html>'''
open(f'{OUT}/menu.html', 'w').write(doc_html)
print('matrix rows', len(MATRIX), 'left', len(left_rows), '+', len(CRIS), 'right', len(right_rows), '+', len(EXTRA))
print('tequila items', sum(len(s['items']) for s in doc['sections'][5]['subs']))
print('total items', sum(len(s['items']) + sum(len(x['items']) for x in s['subs']) for s in doc['sections']))
