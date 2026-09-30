"""Coa Cantina drinks menu, round 2. Writes doc.json and menu.html into the parent folder."""
import json, base64, html, unicodedata, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from source import ALL, fix, fix_cite

OUT = os.path.dirname(HERE)
SRC = {r[0]: r for r in ALL}
E = html.escape

# ---------------------------------------------------------------- content model
# Printed descriptions carry ONLY what venue rows state. Standard specs live in proposal.md, not on the menu.
# (printed desc or '', components [(name, role, source)], missing ingredients)
MARG_BASE = [('Blanco tequila', 'base', 'venue')]
COCKTAILS = {
 173909: ('', MARG_BASE, ['all modifiers (citrus, sweetener, liqueur), rim, garnish']),
 173910: ('Made with Banhez mezcal', [('Banhez mezcal', 'base', 'venue')], ['all modifiers, rim, garnish']),
 173911: ('', MARG_BASE + [('Cucumber', 'flavour', 'name'), ('Jalapeno', 'flavour', 'name')], ['form of cucumber / jalapeno; modifiers; rim']),
 173912: ('', MARG_BASE + [('Mango', 'flavour', 'name')], ['form of mango; modifiers; rim']),
 173908: ('', MARG_BASE + [('Blackberry', 'flavour', 'name')], ['form of blackberry; modifiers; rim']),
 173913: ('', MARG_BASE + [('Peach', 'flavour', 'name')], ['form of peach; modifiers; rim']),
 173914: ('', MARG_BASE + [('Pineapple', 'flavour', 'name')], ['form of pineapple; modifiers; rim']),
 173915: ('', MARG_BASE + [('Strawberry', 'flavour', 'name')], ['form of strawberry; modifiers; rim']),
 173918: ('Blanco tequila, fresh lime, grapefruit, Aperol, grapefruit soda, salted rim',
          [('Blanco tequila', 'base', 'venue'), ('Fresh lime', 'citrus', 'venue'), ('Grapefruit', 'citrus', 'venue'), ('Aperol', 'modifier', 'venue'),
           ('Grapefruit soda', 'lengthener', 'venue'), ('Salted rim', 'garnish', 'venue')], []),
 173921: ('Blanco tequila, fresh lime juice, Topo Chico sparkling water',
          [('Blanco tequila', 'base', 'venue'), ('Fresh lime juice', 'citrus', 'venue'), ('Topo Chico sparkling water', 'lengthener', 'venue')], ['garnish']),
 173916: ('', [('Blanco tequila', 'base', 'venue')], ['tomato base, citrus, seasonings, rim, garnish (standard Bloody Mary spec in proposal.md, not printed)']),
 173920: ('Made with Dos Equis', [('Dos Equis', 'base', 'venue')], ['michelada mix / seasonings, citrus, rim, garnish']),
 173917: ('', [('Blanco tequila', 'base', 'venue')], ['all modifiers, mixers, rim, garnish']),
 173919: ('', [('Tequila', 'base', 'venue')], ['all modifiers and garnish']),
 173923: ('', MARG_BASE + [('Mango', 'flavour', 'name')], ['frozen base / mix']),
 173924: ('', MARG_BASE + [('Strawberry', 'flavour', 'name')], ['frozen base / mix']),
 173925: ('', MARG_BASE, ['which tropical fruits; frozen base / mix']),
 173922: ('', MARG_BASE, ['all flavours and mixers']),
 173975: ('Zero-proof alternatives to tequila, gin or whiskey', [('Ritual Zero Proof (tequila, gin or whiskey alternative)', 'base', 'venue')], []),
}
UPGRADE = {173918: (184680, 'Upgrade to Don Julio Blanco', 4), 173921: (184681, 'Upgrade to Deleon Platinum', 2)}
INTRO = {'sec_margaritas': 'Made with blanco tequila, except the Coa Mezcal Margarita.',
         'sec_frozen': 'Made with blanco tequila.'}
KNOWN_BEER = {173932: 'American light lager', 173933: 'American light lager', 173941: 'International pale lager',
              173930: 'Golden ale', 173931: 'IPA'}           # doc.json only (brand_products.declared_style / the name)
SPIRIT_DESC = {173955: 'Cucumber & mint · grapefruit & rose · peach & orange blossom',     # venue notes
               173956: 'Grape · orange · citrus · raspberry · watermelon',                 # venue notes
               174104: 'Joven tequila'}   # products d760d665-2d53-42a9-bdad-700bff970dc0 "Ha Clase Azul Gold Tequila", class joven
NOT_PRINTED = {173971: "no price in the source; kept in doc.json, left off print and phone until priced"}

MARGS = [173909, 173910, 173911, 173912, 173908, 173913, 173914, 173915]
COCKS = [173918, 173921, 173916, 173920, 173917, 173919]
FROZEN = [173923, 173924, 173925, 173922]
AF = [173975]
DRAFT = [173926, 173928, 173927, 173930, 173931, 173929]
BOTTLES = [173937, 173936, 173941, 173942, 173938, 173932, 173933, 173934, 173935, 173940]
SELTZ = [173943, 173944, 173945, 173948, 173949, 173950, 173951, 173946, 173947]
CIDER = [173939]
def ladder(ids): return sorted(ids, key=lambda i: (SRC[i][3] if SRC[i][3] is not None else 999, fix(SRC[i][2])))
VODKA = ladder([173952, 173954, 173955, 173957, 173953, 173956])
GIN = ladder([173965, 173962, 173963, 173964])
RUM = ladder([173958, 173959, 173960, 173961])
WHISKEY = ladder([173970, 173969, 173967, 173968, 173966, 173972, 173971])
SCOTCH = ladder([173974, 173973])
OTROS = [174103, 174104]

TEQ = [r for r in ALL if r[1] in ('Blanco', 'Reposado', 'Anejo')]
def is_cris(n): return 'Cristalino' in n or 'Cristalnio' in n
CRIS = [r for r in TEQ if is_cris(r[2])]
CORE = [r for r in TEQ if not is_cris(r[2])]   # extra anejos stay in the Anejo column (round-2 rule 11)
def skey(n): return unicodedata.normalize('NFKD', n).encode('ascii', 'ignore').decode().lower()
rows = {}
for i, sec, n, p, _ in CORE:
    rows.setdefault(fix(n), {})[sec[0]] = (i, p)
MATRIX = sorted(rows.items(), key=lambda kv: skey(kv[0]))
CRIS = sorted(CRIS, key=lambda r: skey(fix(r[2])))
CRIS_CITE = {174018: 'products 2a635ebb-ba30-4be9-9ef4-de957a258457 "Casamigos Cristalino" class cristalino',
             174079: 'products 9952863c-16f6-4a4d-81b8-3c8d142adbc7 "Espolon Cristalino" class cristalino',
             174037: 'products 5bc87a16-7b10-48d8-8d13-bfb63548fbf2 "Gran Coramino Reposado Cristalino" class cristalino'}
EXTRA_CITE = {174097: 'products 9a28ff7a-d1af-40ad-859d-a5ead6d74ae6 "Patron Extra Anejo" class extra_anejo',
              174071: 'products 2f16596f-5fcd-44eb-a02d-bde282f3f718 "Corralejo Extra Anejo" class extra_anejo'}

# ---------------------------------------------------------------- doc.json
def item(i, desc='', label='', comps=None, missing=None, note=None, extra_prices=None, merged=None, cite=None):
    r = SRC[i]
    prices = [] if r[3] is None else [{'id': f'p_sme_{i}', 'label': label, 'value': r[3], 'source': 'staging_menu_extract'}]
    for (uid, ulabel, uval) in (extra_prices or []):
        prices.append({'id': f'p_sme_{uid}', 'label': ulabel, 'value': uval, 'source': 'staging_menu_extract'})
    meta = {'source_id': i, 'source_section': r[1], 'source_name': r[2]}
    if fix(r[2]) != r[2]: meta['name_normalised_from'] = r[2]; meta['name_normalisation_cite'] = fix_cite(r[2])
    if merged: meta['merged_from'] = merged
    if missing: meta['missing_ingredients'] = [m for m in missing if m]
    if r[3] is None: meta['needs_price'] = True
    if i in NOT_PRINTED: meta['print'] = False; meta['print_note'] = NOT_PRINTED[i]
    if note: meta['placement_note'] = note
    if cite: meta['class_cite'] = cite
    it = {'id': f'sme_{i}', 'name': fix(r[2]), 'brand': '', 'desc': desc, 'badges': [], 'prices': prices,
          'meta': meta, 'origin': {'item_name': r[2], 'venue_key': 'ACC-IA-LIC-LC0049193'}, 'source': 'staging_menu_extract'}
    if comps: it['components'] = [{'kind': 'ingredient', 'name': n, 'role': role, 'spec_source': s} for n, role, s in comps]
    return it

def cocktail(i):
    d, comps, miss = COCKTAILS[i]; up = UPGRADE.get(i)
    return item(i, d, comps=comps, missing=miss, extra_prices=[up] if up else None, merged=[up[0]] if up else None)
def beer(i): return item(i, KNOWN_BEER.get(i, ''), missing=[None if i in KNOWN_BEER else 'style', 'ABV'])
LAB = {'Blanco': 'Blanco', 'Reposado': 'Reposado', 'Anejo': 'Añejo'}

teq_subs = {'Blanco': [], 'Reposado': [], 'Anejo': []}
for r in sorted(CORE, key=lambda r: skey(fix(r[2]))):
    teq_subs[r[1]].append(item(r[0], f'{LAB[r[1]]} tequila', label=LAB[r[1]], cite=EXTRA_CITE.get(r[0]),
                               note='name says Extra; kept under Añejo as listed by the venue (round-2 rule 11)' if ' Extra' in r[2] else None))
cris_items = [item(r[0], f'{LAB[r[1]]} cristalino', label=LAB[r[1]], note=f'venue lists under {LAB[r[1]]}', cite=CRIS_CITE.get(r[0])) for r in CRIS]

doc = {'id': 'menu_coa_drinks', 'title': 'Coa Cantina — Drinks', 'size': 'legal_p', 'sections': [
 {'id': 'sec_margaritas', 'name': 'Margaritas', 'desc': INTRO['sec_margaritas'], 'items': [cocktail(i) for i in MARGS], 'subs': []},
 {'id': 'sec_cocktails', 'name': 'Cocktails', 'desc': '', 'items': [cocktail(i) for i in COCKS], 'subs': []},
 {'id': 'sec_frozen', 'name': 'Frozen Drinks', 'desc': INTRO['sec_frozen'], 'items': [cocktail(i) for i in FROZEN], 'subs': []},
 {'id': 'sec_beer', 'name': 'Beer', 'desc': '', 'items': [], 'subs': [
   {'id': 'sub_beer_draft', 'name': 'Draft', 'desc': '', 'items': [beer(i) for i in DRAFT]},
   {'id': 'sub_beer_bottles', 'name': 'Bottles & Cans', 'desc': '', 'items': [beer(i) for i in BOTTLES]}]},
 {'id': 'sec_seltzer_cider', 'name': 'Seltzer & Cider', 'desc': '', 'items': [], 'subs': [
   {'id': 'sub_seltzer', 'name': 'Seltzer', 'desc': '', 'items': [item(i, '', missing=['base spirit / style', 'ABV'], note='venue lists under Bottles & Cans') for i in SELTZ]},
   {'id': 'sub_cider', 'name': 'Cider', 'desc': '', 'items': [item(i, '', missing=['style', 'ABV'], note='venue lists under Bottles & Cans') for i in CIDER]}]},
 {'id': 'sec_tequila', 'name': 'Tequila', 'desc': 'By expression', 'items': [], 'subs': [
   {'id': 'sub_teq_blanco', 'name': 'Blanco', 'desc': '', 'items': teq_subs['Blanco']},
   {'id': 'sub_teq_reposado', 'name': 'Reposado', 'desc': '', 'items': teq_subs['Reposado']},
   {'id': 'sub_teq_anejo', 'name': 'Añejo', 'desc': '', 'items': teq_subs['Anejo']},
   {'id': 'sub_teq_cristalino', 'name': 'Cristalino', 'desc': '', 'items': cris_items}]},
 {'id': 'sec_vodka', 'name': 'Vodka', 'desc': '', 'items': [item(i, SPIRIT_DESC.get(i, '')) for i in VODKA], 'subs': []},
 {'id': 'sec_gin', 'name': 'Gin', 'desc': '', 'items': [item(i) for i in GIN], 'subs': []},
 {'id': 'sec_rum', 'name': 'Rum', 'desc': '', 'items': [item(i) for i in RUM], 'subs': []},
 {'id': 'sec_whiskey', 'name': 'Whiskey', 'desc': '', 'items': [item(i) for i in WHISKEY], 'subs': []},
 {'id': 'sec_scotch', 'name': 'Scotch', 'desc': '', 'items': [item(i) for i in SCOTCH], 'subs': []},
 {'id': 'sec_otros', 'name': 'Otros', 'desc': '', 'items': [item(i, SPIRIT_DESC.get(i, ''), note='venue section: Misc',
      cite='products d760d665-2d53-42a9-bdad-700bff970dc0 class joven' if i == 174104 else None) for i in OTROS], 'subs': []},
 {'id': 'sec_alcohol_free', 'name': 'Alcohol Free', 'desc': '', 'items': [cocktail(i) for i in AF], 'subs': []},
]}
json.dump(doc, open(f'{OUT}/doc.json', 'w'), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- HTML helpers
def b64(f): return base64.b64encode(open(f'{HERE}/fonts/{f}', 'rb').read()).decode()
FONTS = f"""
@font-face{{font-family:'Fraunces';font-style:normal;font-weight:400 900;src:url(data:font/woff2;base64,{b64('fraunces.woff2')}) format('woff2');}}
@font-face{{font-family:'Fraunces';font-style:italic;font-weight:400 700;src:url(data:font/woff2;base64,{b64('fraunces-i.woff2')}) format('woff2');}}
@font-face{{font-family:'DM Sans';font-style:normal;font-weight:400 800;src:url(data:font/woff2;base64,{b64('dmsans.woff2')}) format('woff2');}}
@font-face{{font-family:'DM Sans';font-style:italic;font-weight:400;src:url(data:font/woff2;base64,{b64('dmsans-i.woff2')}) format('woff2');}}
"""
def printed(i): return i not in NOT_PRINTED

def papel(width_pt=540, h=20):
    cols = ['#A8361F', '#E3A33B', '#135651']; n = 15; fw = width_pt / n
    parts = [f'<svg class="papel" data-k="ornament" viewBox="0 0 {width_pt} {h}" width="{width_pt}pt" height="{h}pt" preserveAspectRatio="none" aria-hidden="true">',
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
<path d="M30 32 C29 20 28 10 30 1" stroke="#135651" stroke-width="2.2"/>
<path d="M30 32 C25 22 19 14 11 8" stroke="#135651" stroke-width="2"/><path d="M30 32 C35 22 41 14 49 8" stroke="#135651" stroke-width="2"/>
<path d="M30 32 C22 26 12 22 2 21" stroke="#E3A33B" stroke-width="2"/><path d="M30 32 C38 26 48 22 58 21" stroke="#E3A33B" stroke-width="2"/>
<path d="M30 32 C27 24 23 17 20 5" stroke="#A8361F" stroke-width="1.6"/><path d="M30 32 C33 24 37 17 40 5" stroke="#A8361F" stroke-width="1.6"/>
</g></svg>'''

def mast(kicker, title, order):
    return f'''<header class="mast" style="--o:{order}">{papel()}
<div class="mastrow"><div class="wordmark" data-k="header" data-lvl="0">Coa Cantina</div>
<div class="mastright"><div class="masttitle" data-k="header" data-lvl="0b">{E(title)}</div><div class="kicker" data-k="description">{E(kicker)}</div></div></div>
<div class="doublerule" data-k="divider"></div></header>'''

def footer(n, order):
    return f'''<footer class="foot" data-k="description" style="--o:{order}"><span>Coa Cantina · Iowa City</span><span class="fdot">{AGAVE}</span><span>coacantinaiowacity.com<span class="pg"> · {n}/2</span></span></footer>'''

def h1(txt, ref='', es=''):
    k = f'<em class="es">{E(es)}</em>' if es else ''
    return f'<h2 class="h1" data-k="header" data-ref="{ref}"><span>{E(txt)}</span>{k}</h2>'
def h2(txt, ref=''): return f'<h3 class="h2" data-k="subheader" data-ref="{ref}">{E(txt)}</h3>'
def intro(ref): return f'<p class="intro" data-k="description" data-ref="{ref}">{E(INTRO[ref])}</p>'

def rich(i, feature=False):
    r = SRC[i]; d, _, _ = COCKTAILS[i]; up = UPGRADE.get(i)
    s = f'<div class="{"ritem feature" if feature else "ritem"}" data-item="sme_{i}">'
    s += f'<div class="line"><span class="nm" data-k="item_name" data-ref="sme_{i}">{E(fix(r[2]))}</span><span class="pr" data-k="price" data-ref="sme_{i}">{r[3]}</span></div>'
    if d: s += f'<div class="line"><span class="ds" data-k="description" data-ref="sme_{i}">{E(d)}</span></div>'
    if up: s += f'<div class="line up"><span class="ds" data-k="description" data-ref="sme_{i}">{E(up[1])}</span><span class="pr small" data-k="price" data-ref="sme_{i}">+{up[2]}</span></div>'
    return s + '</div>'

def row(i, desc=None):
    r = SRC[i]
    s = f'<div class="row" data-item="sme_{i}"><div class="line"><span class="nm" data-k="item_name" data-ref="sme_{i}">{E(fix(r[2]))}</span><span class="pr" data-k="price" data-ref="sme_{i}">{r[3]}</span></div>'
    if desc: s += f'<div class="line"><span class="ds" data-k="description" data-ref="sme_{i}">{E(desc)}</span></div>'
    return s + '</div>'

def block(title, ids, descs=None, ref='', po=0):
    return (f'<section class="blk" style="--po:{po}">{h2(title, ref)}<div class="rows">'
            + ''.join(row(i, (descs or {}).get(i)) for i in ids if printed(i)) + '</div></section>')

# ---------------------------------------------------------------- page 1
top = (f'<div class="halves top">'
       f'<div class="col"><section class="blk" style="--o:1">{h1("Margaritas", "sec_margaritas", "Margaritas")}{intro("sec_margaritas")}<div class="rows">'
       + rich(MARGS[0], True) + ''.join(rich(i) for i in MARGS[1:]) + '</div></section></div>'
       f'<div class="col" style="--igap:{os.environ.get("COA_IGAP_R","22.1pt")}"><section class="blk" style="--o:2">{h1("Cocktails", "sec_cocktails", "Cócteles")}<div class="rows">'
       + rich(COCKS[0], True) + ''.join(rich(i) for i in COCKS[1:]) + '</div></section></div></div>')
frozen = (f'<div class="band" style="--o:3">{h1("Frozen", "sec_frozen", "Congelados")}{intro("sec_frozen")}<div class="halves">'
          f'<div class="col">{"".join(rich(i) for i in FROZEN[:2])}</div><div class="col">{"".join(rich(i) for i in FROZEN[2:])}</div></div></div>')
beerband = (f'<div class="band" style="--o:4">{h1("Beer, Seltzer & Cider", "sec_beer", "Cervezas")}<div class="thirds">'
            f'<div class="col">{block("Draft", DRAFT, ref="sub_beer_draft", po=1)}{block("Cider", CIDER, ref="sub_cider", po=4)}</div>'
            f'<div class="col">{block("Bottles & Cans", BOTTLES, ref="sub_beer_bottles", po=2)}</div>'
            f'<div class="col">{block("Seltzer", SELTZ, ref="sub_seltzer", po=3)}</div></div></div>')
afband = (f'<div class="band" style="--o:8">{h1("Alcohol Free", "sec_alcohol_free", "Sin Alcohol")}'
          f'<div class="single"><div class="col">{rich(AF[0])}</div></div></div>')
page1 = (f'<article class="page" id="page-1">{mast("Iowa City · Bebidas", "Drinks", 0)}'
         f'<main class="body">{top}{frozen}{beerband}{afband}</main>{footer(1, 99)}</article>')

# ---------------------------------------------------------------- page 2: tequila grid
def mrow(name, cells):
    ref = ' '.join(f'sme_{c[0]}' for c in cells.values())
    s = f'<div class="mrow" data-item="{ref}"><span class="nm" data-k="item_name" data-ref="{ref}">{E(name)}</span>'
    for k in 'BRA':
        if k in cells: s += f'<span class="mc pr" data-k="price" data-col="{k}" data-ref="sme_{cells[k][0]}">{cells[k][1]}</span>'
        else: s += f'<span class="mc empty" data-col="{k}" aria-hidden="true">·</span>'
    return s + '</div>'
def mhead(extra=''):
    return (f'<div class="mhead{extra}"><span class="nm">&nbsp;</span>'
            '<span class="mc" data-k="subheader" data-lvl2="label">Blanco</span><span class="mc" data-k="subheader" data-lvl2="label">Reposado</span><span class="mc" data-k="subheader" data-lvl2="label">Añejo</span></div>')
def crisrows():
    out = ''
    for r in CRIS:
        k = {'Blanco': 'B', 'Reposado': 'R', 'Anejo': 'A'}[r[1]]
        out += mrow(fix(r[2]), {k: (r[0], r[3])})
    return out

NL = int(os.environ.get('COA_NL', 39))
left_rows, right_rows = MATRIX[:NL], MATRIX[NL:]
mleft = f'<div class="col matrix">{mhead()}' + ''.join(mrow(n, c) for n, c in left_rows) + '</div>'
mright = (f'<div class="col matrix">{mhead()}' + ''.join(mrow(n, c) for n, c in right_rows)
          + f'<div class="mgroup">{h2("Cristalino", "sub_teq_cristalino")}{mhead(" rep")}{crisrows()}</div></div>')
phone_grid = (f'<div class="tq-phone">{mhead(" sticky")}' + ''.join(mrow(n, c) for n, c in MATRIX)
              + f'<div class="mgroup">{h2("Cristalino", "")}{crisrows()}</div></div>')
tequila = (f'<div class="band" style="--o:5">{h1("Tequila", "sec_tequila")}'
           f'<div class="halves tq-print">{mleft}{mright}</div>{phone_grid}</div>')

# spirits: four quarters; column assignment chosen by build/balance (see proposal.md)
SPB = {'V': lambda po: block("Vodka", VODKA, SPIRIT_DESC, "sec_vodka", po), 'G': lambda po: block("Gin", GIN, ref="sec_gin", po=po),
       'R': lambda po: block("Rum", RUM, ref="sec_rum", po=po), 'W': lambda po: block("Whiskey", WHISKEY, ref="sec_whiskey", po=po),
       'S': lambda po: block("Scotch", SCOTCH, ref="sec_scotch", po=po), 'O': lambda po: block("Otros", OTROS, SPIRIT_DESC, "sec_otros", po)}
PO = {'V': 1, 'G': 2, 'R': 3, 'W': 4, 'S': 5, 'O': 6}
SPCOLS = os.environ.get('COA_SPCOLS', 'V|GO|RS|W').split('|')
spirits = (f'<div class="band" style="--o:6">{h1("Spirits", "sec_spirits", "Licores")}<div class="quarters">'
           + ''.join('<div class="col">' + ''.join(SPB[k](PO[k]) for k in col) + '</div>' for col in SPCOLS) + '</div></div>')
page2 = (f'<article class="page" id="page-2">{mast("Iowa City · Tequila y Licores", "Tequila & Spirits", 50)}'
         f'<main class="body">{tequila}{spirits}</main>{footer(2, 100)}</article>')

CSS = open(f'{HERE}/menu.css').read()
open(f'{OUT}/menu.html', 'w').write(f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Coa Cantina — Drinks (US Legal 8.5 × 14 in, 2 pages)</title>
<!-- Print size: US Legal 8.5 x 14 in (215.9 x 355.6 mm), portrait, 2 pages (duplex). Margins 0.5 in (12.7 mm) all sides. No bleed. Round 2. -->
<style>{FONTS}{CSS}</style></head><body>
{page1}
{page2}
</body></html>''')
print('matrix rows', len(MATRIX), 'left', len(left_rows), 'right', len(right_rows), '+ cristalino', len(CRIS))
print('items', sum(len(s['items']) + sum(len(x['items']) for x in s['subs']) for s in doc['sections']))
