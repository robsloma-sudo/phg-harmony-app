import json, os
from collections import defaultdict
HERE = os.path.dirname(__file__)
OUT = '/home/user/phg-harmony-app/handoff/designs/test-2-coa-cantina'
els = json.load(open(f'{HERE}/els.json'))
MM = 25.4 / 96; PT = 0.75
r2 = lambda v: round(v, 2)
W_MM, H_MM = 215.9, 355.6

def lum(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def cr(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True); return round((la + 0.05) / (lb + 0.05), 2)

PAL = {'background': '#F5EEDF', 'text': '#1F1B18', 'accent': '#A8361F', 'price_and_subheader': '#135651',
       'muted_text': '#57504A', 'ornament_only': '#E3A33B', 'zebra_tint': '#EEE3CD', 'leader_dots': '#B9A98F'}
pairs = [('text', 'background'), ('muted_text', 'background'), ('accent', 'background'), ('price_and_subheader', 'background'),
         ('text', 'zebra_tint'), ('price_and_subheader', 'zebra_tint')]
contrast = {f'{a} on {b}': cr(PAL[a], PAL[b]) for a, b in pairs}

kindmap = {'footer': 'footer'}
elements = []
for e in els:
    k = e['kind']
    if k == 'header' and e.get('lvl') in ('0', '0b'): k2 = 'header'  # masthead
    else: k2 = k
    el = {'kind': k2, 'page': e['page'], 'x_mm': r2(e['x'] * MM), 'y_mm': r2(e['y'] * MM), 'w_mm': r2(e['w'] * MM), 'h_mm': r2(e['h'] * MM),
          'x_pt': r2(e['x'] * PT), 'y_pt': r2(e['y'] * PT), 'w_pt': r2(e['w'] * PT), 'h_pt': r2(e['h'] * PT), 'text': e['text']}
    if e.get('ref'): el['ref'] = e['ref']
    if e.get('col'): el['column'] = e['col']
    if e.get('mcol'): el['price_column'] = {'B': 'Blanco', 'R': 'Reposado', 'A': 'Añejo'}[e['mcol']]
    if e.get('size'): el['font'] = e['font']; el['size_pt'] = r2(e['size'] * PT)
    if e.get('tw'): el['text_w_mm'] = r2(e['tw'] * MM)
    if e.get('lvl'): el['level'] = 'masthead'
    elif k == 'subheader' and e['text'] in ('Blanco', 'Reposado', 'Añejo') and e.get('col') in ('p2c0', 'p2c1'): el['level'] = 'column_label'
    elif k == 'header': el['level'] = 1
    elif k == 'subheader': el['level'] = 2
    elements.append(el)

# ------------------------------------------------ measured checks
checks = {}
for pg in (1, 2):
    P = [e for e in elements if e['page'] == pg]
    left = min(e['x_mm'] for e in P); top = min(e['y_mm'] for e in P)
    right = W_MM - max(e['x_mm'] + e['w_mm'] for e in P); bottom = H_MM - max(e['y_mm'] + e['h_mm'] for e in P)
    checks[f'page{pg}_margins_mm'] = {'top': r2(top), 'right': r2(right), 'bottom': r2(bottom), 'left': r2(left)}

def spread(v): return r2(max(v) - min(v)) if v else 0
cols = defaultdict(list)
for e in elements:
    if e.get('column'): cols[e['column']].append(e)
left_edges, price_edges, h_x = {}, {}, {}
for c, E in sorted(cols.items()):
    names = [e['x_mm'] for e in E if e['kind'] == 'item_name']
    left_edges[c] = {'x_mm': r2(min(names)) if names else None, 'spread_mm': spread(names), 'n': len(names)}
    groups = defaultdict(list)
    for e in E:
        if e['kind'] == 'price': groups[e.get('price_column', 'price')].append(r2(e['x_mm'] + e['w_mm']))
    price_edges[c] = {g: {'right_mm': r2(max(v)), 'spread_mm': spread(v), 'n': len(v)} for g, v in groups.items()}
    for lvl in (1, 2):
        hx = [e['x_mm'] for e in E if e.get('level') == lvl and e['kind'] in ('header', 'subheader') and e['text'] not in ('Blanco', 'Reposado', 'Añejo')]
        if hx: h_x[f'{c} L{lvl}'] = {'x_mm': r2(min(hx)), 'spread_mm': spread(hx), 'n': len(hx)}
checks['item_name_left_edges'] = left_edges
checks['price_right_edges'] = price_edges
checks['header_x_per_column'] = h_x
sizes = defaultdict(set)
for e in elements:
    if e.get('level') in (1, 2): sizes[e['level']].add(e['size_pt'])
checks['header_sizes_pt'] = {f'L{k}': sorted(v) for k, v in sizes.items()}

# spacing between consecutive items: an item runs from its name's top to the bottom of its last text line
gaps = {}
from collections import Counter
for c, E in sorted(cols.items()):
    seq = sorted([e for e in E if e['kind'] in ('item_name', 'description', 'price', 'header', 'subheader')], key=lambda e: (round(e['y_mm'], 1), e['x_mm']))
    items, cur = [], None
    for e in seq:
        if e['kind'] in ('header', 'subheader'):
            cur = None; items.append(None); continue
        if e['kind'] == 'item_name':
            cur = {'top': e['y_mm'], 'bot': e['y_mm'] + e['h_mm']}; items.append(cur)
        elif cur is not None:
            cur['bot'] = max(cur['bot'], e['y_mm'] + e['h_mm'])
    g = [r2(b['top'] - a['bot']) for a, b in zip(items, items[1:]) if a and b]
    if g:
        mode = Counter(g).most_common(1)[0][0]
        gaps[c] = {'typical_gap_mm': mode, 'spread_mm': spread(g), 'n': len(g), 'off_by_more_than_0.5mm': [x for x in g if abs(x - mode) > 0.5]}
# header spacing: gap from each L1/L2 header bottom to the first item top, and from previous item to header top
hsp = defaultdict(list)
for c, E in sorted(cols.items()):
    seq = sorted([e for e in E if e['kind'] in ('item_name', 'description', 'price', 'header', 'subheader') and e.get('level') != 'column_label'], key=lambda e: (round(e['y_mm'], 1), e['x_mm']))
    for a, b in zip(seq, seq[1:]):
        if a['kind'] in ('header', 'subheader') and b['kind'] == 'item_name':
            hsp[f"below L{a['level']}"].append(r2(b['y_mm'] - (a['y_mm'] + a['h_mm'])))
checks['header_spacing_below_mm'] = {k: {'values': sorted(set(v)), 'spread_mm': spread(v)} for k, v in hsp.items()}
checks['item_gaps'] = gaps
checks['contrast'] = contrast

# content: every item_name has a description element?
refs_name = {e['ref'] for e in elements if e['kind'] == 'item_name'}
refs_desc = {e['ref'] for e in elements if e['kind'] == 'description' and e.get('ref')}
# rows without their own description line are described by their column label (tequila grid) or list header (beer, spirits)
lastL2 = {}
for e in sorted(elements, key=lambda e: (e['page'], e.get('column') or '', e['y_mm'])):
    if e['kind'] == 'subheader' and e.get('level') == 2: lastL2[e.get('column')] = e['text']
    if e['kind'] == 'item_name' and e['ref'] not in refs_desc:
        if e.get('column') in ('p2c0', 'p2c1'):
            e['described_by'] = 'tequila grid column label(s) Blanco / Reposado / Añejo' + (f' + group header {lastL2[e["column"]]}' if e.get('column') in lastL2 and e['y_mm'] > 0 and lastL2[e['column']] in ('Cristalino', 'Extra Añejo') else '')
        else:
            e['described_by'] = f'list header: {lastL2.get(e.get("column"))}'
no_desc = [e for e in elements if e['kind'] == 'item_name' and e['ref'] not in refs_desc]
checks['item_names_without_own_description_line'] = {'count': len(no_desc), 'all_have_described_by': all('described_by' in e for e in no_desc),
   'cocktails_without_description': [e['text'] for e in no_desc if e['page'] == 1 and e.get('column') in ('p1c0', 'p1c1')]}

layout = {
 'page': {'size': 'US Legal portrait', 'width_mm': W_MM, 'height_mm': H_MM, 'width_pt': 612, 'height_pt': 1008, 'pages': 2,
          'margins_mm': {'top': 12.7, 'right': 12.7, 'bottom': 12.7, 'left': 12.7}, 'bleed_mm': 0,
          'note': 'Duplex on one sheet: page 1 Cocktails/Beer, page 2 Agave & Spirits.'},
 'grid': {'columns': 12, 'column_width_pt': 28.5, 'gutter_pt': 18, 'gutter_mm': 6.35, 'baseline_pt': 1,
          'spans': {'halves': '6 cols = 261pt (92.08mm)', 'thirds': '4 cols = 168pt (59.27mm)', 'quarters': '3 cols = 121.5pt (42.86mm)'},
          'rhythm_pt': {'cocktail_name_line': 16, 'cocktail_desc_line': 12, 'cocktail_item_gap': 12, 'list_row': 14, 'matrix_row': 13, 'section_gap': 21},
          'note': 'Leading is set per text role (16/12/14/13pt) on a 1pt grid; each role is constant everywhere it appears.'},
 'palette': PAL,
 'type': {'masthead': {'font': 'Fraunces 900', 'size_pt': 40}, 'page_title': {'font': 'Fraunces 600 italic', 'size_pt': 20},
          'header': {'font': 'Fraunces 800', 'size_pt': 18, 'colour': '#A8361F'},
          'subheader': {'font': 'DM Sans 800 caps +0.18em', 'size_pt': 8, 'colour': '#135651'},
          'item': {'font': 'Fraunces 650 (cocktails) / DM Sans 500 (lists)', 'size_pt': [12.5, 9.5, 9], 'feature_size_pt': 14},
          'description': {'font': 'DM Sans 400', 'size_pt': [9, 8], 'colour': '#57504A'},
          'price': {'font': 'DM Sans 700 tabular lining', 'size_pt': [12, 9.5, 9], 'colour': '#135651', 'format': 'whole dollars, no $ sign, no decimals; upgrades as +N'}},
 'elements': elements,
 'measured_checks': checks,
}
json.dump(layout, open(f'{OUT}/layout.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(checks, ensure_ascii=False, indent=1))
