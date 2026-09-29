#!/usr/bin/env python3
"""Turn data/product_knowledge/*.jsonl (handoff/agents/PRODUCT_KNOWLEDGE_CONTRACT.md) into idempotent SQL for the
phg_know schema (draft 09). Prints SQL to stdout (or writes chunks with --out DIR --chunk N). Never touches the DB.
Sources are keyed by a hash of their URL (or title). Brand profiles are soft-linked to public.brands by name and to
public.organizations by NOM at load time."""
import glob, hashlib, json, os, re, sys

STYLES = {'blanco', 'joven', 'reposado', 'anejo', 'extra_anejo', 'cristalino', 'other'}
CATS = {'tequila', 'mezcal', 'raicilla', 'sotol', 'bacanora', 'whiskey', 'rum', 'gin', 'vodka', 'brandy', 'liqueur', 'other'}

def q(v):
    if v is None or v == '': return 'null'
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, (int, float)): return repr(v)
    return "'" + str(v).replace("'", "''") + "'"
def arr(xs):
    xs = [x for x in (xs or []) if x not in (None, '')]
    return "'{}'::text[]" if not xs else 'array[' + ','.join(q(str(x)) for x in xs) + ']::text[]'
def num(v):
    try: return repr(float(v)) if v not in (None, '') else 'null'
    except (TypeError, ValueError): return 'null'
def skey(s):
    base = (s.get('url') or s.get('title') or '').strip().lower()
    return 'src_' + hashlib.md5(base.encode()).hexdigest()[:12] if base else None
def norm_style(x):
    x = (x or '').lower().replace('ñ', 'n').replace('-', '_').replace(' ', '_')
    return {'extra_añejo': 'extra_anejo', 'plata': 'blanco', 'silver': 'blanco', 'gold': 'joven'}.get(x, x) if x else 'other'

def main():
    files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', 'data', 'product_knowledge', '*.jsonl')))
    brands, exps, srcs, warn = {}, {}, {}, []
    for f in files:
        for n, line in enumerate(open(f), 1):
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except Exception as e: warn.append(f'{os.path.basename(f)}:{n} bad json {e}'); continue
            keys = []
            for s in r.get('sources') or []:
                k = skey(s)
                if k:
                    keys.append(k)
                    srcs.setdefault(k, s)
            r['_src'] = sorted(set(keys))
            if not keys: warn.append(f'{os.path.basename(f)}:{n} {r.get("key")} has no source - skipped'); continue
            if r.get('type') == 'brand': brands[r['key']] = r
            elif r.get('type') == 'expression': exps[r['key']] = r
    out = ['begin;', "set local lock_timeout = '3s';"]
    for k, s in srcs.items():
        tier = s.get('tier') if isinstance(s.get('tier'), int) and 1 <= s.get('tier') <= 5 else None
        out.append(f"insert into phg_know.sources (key,url,title,kind,tier) values ({q(k)},{q(s.get('url'))},{q(s.get('title'))},{q(s.get('kind'))},{q(tier)}) on conflict (key) do update set url=excluded.url,title=excluded.title,kind=excluded.kind,tier=excluded.tier;")
    for k, b in brands.items():
        cat = (b.get('category') or 'other').lower()
        if cat not in CATS: cat = 'other'
        fy = b.get('founded_year') if isinstance(b.get('founded_year'), int) and 1500 <= b['founded_year'] <= 2100 else None
        nom = re.sub(r'[^0-9]', '', str(b.get('nom') or '')) or None
        out.append(f"""insert into phg_know.brand_profiles (key,name,aka,category,nom,producer,owner,region,founded_year,history,verification,source_keys,updated_at) values ({q(k)},{q(b.get('name'))},{arr(b.get('aka'))},{q(cat)},{q(nom)},{q(b.get('producer'))},{q(b.get('owner'))},{q(b.get('region'))},{q(fy)},{arr(b.get('history'))},{q(b.get('verification') if b.get('verification') in ('page','excerpt','unverified') else 'unverified')},{arr(b['_src'])},now())
 on conflict (key) do update set name=excluded.name,aka=excluded.aka,category=excluded.category,nom=excluded.nom,producer=excluded.producer,owner=excluded.owner,region=excluded.region,founded_year=excluded.founded_year,history=excluded.history,verification=excluded.verification,source_keys=excluded.source_keys,updated_at=now();""")
    for k, e in exps.items():
        if e.get('brand_key') not in brands: warn.append(f'{k}: unknown brand {e.get("brand_key")} - skipped'); continue
        st = norm_style(e.get('style'))
        if st not in STYLES: st = 'other'
        abv = e.get('abv'); abv = abv if isinstance(abv, (int, float)) and 0 < abv <= 100 else None
        af = e.get('additive_free') if isinstance(e.get('additive_free'), bool) else None
        cols = dict(key=q(k), brand_key=q(e['brand_key']), name=q(e.get('name')), style=q(st), abv=num(abv),
                    aging_months_min=num(e.get('aging_months_min')), aging_months_max=num(e.get('aging_months_max')),
                    barrels=q(e.get('barrels')), agave=q(e.get('agave')), agave_species=q(e.get('agave_species')),
                    agave_region=q(e.get('agave_region')), cooking=q(e.get('cooking')), milling=q(e.get('milling')),
                    fermentation=q(e.get('fermentation')), distillation=q(e.get('distillation')),
                    water_source=q(e.get('water') or e.get('water_source')), additive_free=q(af),
                    tasting=arr(e.get('tasting')), price_usd_750=num(e.get('price_usd_750')), awards=arr(e.get('awards')),
                    mezcal_category=q(e.get('mezcal_category') or (e.get('category') if e.get('category') != 'tequila' else None)),
                    maestro=q(e.get('maestro')), village=q(e.get('village')),
                    verification=q(e.get('verification') if e.get('verification') in ('page','excerpt','unverified') else 'unverified'),
                    source_keys=arr(e['_src']))
        names = ','.join(cols); vals = ','.join(cols.values())
        upd = ','.join(f'{c}=excluded.{c}' for c in cols if c != 'key')
        out.append(f"insert into phg_know.expressions ({names},updated_at) values ({vals},now()) on conflict (key) do update set {upd},updated_at=now();")
    out.append("""update phg_know.brand_profiles p set brand_id = b.brand_id from (select distinct on (lower(brand_name)) lower(brand_name) n, brand_id from public.brands order by lower(brand_name), brand_id) b where p.brand_id is null and b.n = lower(p.name);""")
    out.append("""update phg_know.brand_profiles p set organization_id = o.organization_id from public.organizations o where p.organization_id is null and p.nom is not null and o.nom = p.nom;""")
    out.append('commit;')
    for w in warn: print('-- WARN ' + w, file=sys.stderr)
    print(f'-- {len(srcs)} sources, {len(brands)} brands, {len(exps)} expressions', file=sys.stderr)
    if '--out' in sys.argv:
        d = sys.argv[sys.argv.index('--out') + 1]; size = int(sys.argv[sys.argv.index('--chunk') + 1]) if '--chunk' in sys.argv else 60
        os.makedirs(d, exist_ok=True); body = out[2:-1]
        for i in range(0, len(body), size):
            open(os.path.join(d, f'pk_{i // size + 1:02d}.sql'), 'w').write('\n'.join(out[:2] + body[i:i + size] + ['commit;']))
    else:
        print('\n'.join(out))

if __name__ == '__main__':
    main()
