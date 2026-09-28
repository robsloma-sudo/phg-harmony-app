import json,sys
def avg(r): return r.get('average') or round(sum(r['scores'].values())/len(r['scores']),1)
for n in sys.argv[1:]:
    rows=[json.loads(l) for l in open(f'r{n}.jsonl')]
    g={};f=0
    for r in rows:
        k=r['reviewer'].lower(); t='critic' if 'critic' in k else 'content' if 'content' in k else 'accuracy'
        g.setdefault(t,[]).append(avg(r)); f+=any(v!='pass' for v in r['gates'].values())
    m={t:round(sum(v)/len(v),1) for t,v in g.items()}; print(n,len(rows),g,m,round(sum(m.values())/3,1),'gatefails',f)
