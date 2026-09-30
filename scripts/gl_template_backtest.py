#!/usr/bin/env python3
"""Backtest data/finance/invoice_coding_template.json against an example coded-invoice export (Airtable JSON).
A coded GL on an example invoice counts as covered when the vendor's profile can produce that code, or the code is a
parent of one it can produce (the example often coded to the parent, e.g. 6500 instead of 6515).
usage: gl_template_backtest.py invoices.json vendor_map.json"""
import csv, json, re, sys, collections
root = __file__.rsplit('/scripts/', 1)[0]
t = json.load(open(f'{root}/data/finance/invoice_coding_template.json')); P = {p['key']: p for p in t['profiles']}
parent = {r['code']: r['parent_code'] for r in csv.DictReader(open(f'{root}/data/finance/gl_template_bar_restaurant.csv'))}
def ancestors(c):
    out = set()
    while c:
        out.add(c); c = parent.get(c)
    return out
def norm(g): return re.match(r'(\d{4}(-\d{2})?)', g.replace('5420-N/A', '5420-10')).group(1)
d = json.load(open(sys.argv[1])); vm = json.load(open(sys.argv[2]))
hit = miss = 0; ha = ma = 0.0; misses = collections.Counter(); unm = collections.Counter()
for r in d['records']:
    f = r['fields']; vs = [x['name'] for x in f.get('Distributor/Vendor', [])]
    for g in f.get('Type', []):
        a = abs(f.get(g) or 0); c = norm(g); pk = vm.get(vs[0] if vs else '')
        if not pk: unm[vs[0] if vs else None] += 1; continue
        p = P[pk]; allowed = {p['default_gl']} | {gl for _, gl in p['line_rules']}; allowed.discard(None)
        reach = set().union(*(ancestors(x) for x in allowed)) if allowed else set()
        if c in reach: hit += 1; ha += a
        else: miss += 1; ma += a; misses[(pk, c)] += 1
print(f'coded GL lines covered {hit}/{hit+miss} ({100*hit/max(1,hit+miss):.0f}%), amount {ha:,.0f}/{ha+ma:,.0f} ({100*ha/max(1,ha+ma):.0f}%)')
print('misses', misses.most_common(15)); print('unmapped', sum(unm.values()))
