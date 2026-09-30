"""Tally one round: python3 tally.py <round>. Reads scores/r<round>.jsonl (one reviewer JSON per line)."""
import json, sys, pathlib
KEYS = {'critic': ['1','2','3','4','5','6','7','10','15'], 'content': ['3','5','8','9','10'], 'accuracy': ['10','11','12','13','14']}
here = pathlib.Path(__file__).parent
r = sys.argv[1]
rows = [json.loads(l) for l in open(here / f'r{r}.jsonl') if l.strip()]
out, by = [], {}
for x in rows:
    k = x['reviewer']; vals = [float(x['scores'][c]) for c in KEYS[k] if c in x['scores']]
    avg = sum(vals) / len(vals); by.setdefault(k, []).append(avg)
    sc = ' '.join('%s:%s' % (c, x['scores'].get(c)) for c in KEYS[k])
    out.append('| %s | %s | %s | %.1f |' % (k, x.get('lens','')[:60], sc, avg))
allv = [a for v in by.values() for a in v]
comb = sum(allv) / len(allv)
hist_p = here / 'history.json'
hist = json.loads(hist_p.read_text()) if hist_p.exists() else {}
best = max((v['combined'] for kk, v in hist.items() if kk != r), default=None)
hist[r] = {'combined': round(comb, 1), **{k: round(sum(v)/len(v), 1) for k, v in by.items()}, 'n': len(allv)}
hist_p.write_text(json.dumps(hist, indent=1))
print(f"Round {r}: combined {comb:.1f} over {len(allv)} reviews | " + ' | '.join(f"{k} {sum(v)/len(v):.1f}" for k, v in by.items()))
print(f"pass (>=80): {comb >= 80} | improved over best {best}: {best is None or comb > best}")
print("| reviewer | lens | scores | avg |\n|---|---|---|---|"); print('\n'.join(out))
