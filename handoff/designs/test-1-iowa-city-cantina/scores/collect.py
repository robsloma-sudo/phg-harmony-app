"""collect.py <round> <agentId>... : pull each finished reviewer's final JSON from its task output into r<round>.jsonl"""
import json, sys, re, pathlib
T = pathlib.Path('/tmp/claude-0/-home-user-phg-harmony-app/c0df8ae8-562c-5574-b6e9-9bdd13434505/tasks')
r, ids = sys.argv[1], sys.argv[2:]
out = pathlib.Path(__file__).parent / f'r{r}.jsonl'
got, missing = [], []
for i in ids:
    p = T / f'{i}.output'
    last = None
    if p.exists():
        for line in p.read_text().splitlines():
            try: d = json.loads(line)
            except Exception: continue
            if d.get('type') == 'assistant':
                for c in d.get('message', {}).get('content', []):
                    if c.get('type') == 'text' and '"scores"' in c['text']: last = c['text']
                    if c.get('type') == 'tool_use' and c.get('name') == 'SubagentHandback':
                        m0 = (c.get('input') or {}).get('message', '')
                        if '"scores"' in m0: last = m0
    m = re.search(r'\{.*"scores".*\}', last or '', re.S)
    if not m: missing.append(i); continue
    txt = m.group(0)
    # trim trailing prose after the JSON object
    depth = 0
    for k, ch in enumerate(txt):
        depth += ch == '{'; depth -= ch == '}'
        if depth == 0: txt = txt[:k+1]; break
    got.append(json.loads(txt))
out.write_text(''.join(json.dumps(g) + '\n' for g in got))
print(f'{len(got)} collected, missing: {missing}')
