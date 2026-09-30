"""Round 16: one face per row (shared band line), card feet close the row difference. Tries La Botella top-right first."""
import json, pathlib
HERE = pathlib.Path(__file__).parent
M = json.loads((HERE / "measure.json").read_text())["M"]; H = json.loads((HERE / "heights.json").read_text())
PT = 0.75; MINF = 99; DECK = 630; GAP = 12; FOOTMIN = 24   # a foot needs 6 pt + rule + 5.25 pt + 12 pt line
content = {}
for c in M["cards"]:   # card height without face and foot = border 3 + 12 + list + 9 + 3
    content[c["ref"]] = round((c["content_bottom"] - c["box"]["y"] - c["face"]["h"]) * PT + 12)
def plan(order):
    r1, r2 = {"agave_top": (("sec_cocktails", "sec_spirits"), ("sec_beer", "sec_wine")), "beer_top": (("sec_cocktails", "sec_beer"), ("sec_wine", "sec_spirits"))}[order]
    m1, m2 = max(content[x] for x in r1), max(content[x] for x in r2)
    spare = DECK - GAP - m1 - m2 - 2 * MINF          # extra height to share between the two faces
    if spare < 0: return None, f"{order}: needs {m1 + m2 + 2 * MINF + GAP} pt with {MINF} pt faces; deck is {DECK} pt"
    f1 = MINF + (spare // 12) * 6; f2 = MINF + spare - (spare // 12) * 6
    assert (f1 + 3) % 6 == 0 and (f2 + 3) % 6 == 0, (f1, f2)
    foot = {x: (m1 if x in r1 else m2) - content[x] for x in content}
    if any(0 < v < FOOTMIN for v in foot.values()): return None, f"{order}: foot below {FOOTMIN} pt {foot}"
    return {"order": order, "row1": m1 + f1, "row2": m2 + f2, "deck": DECK, "face": {"row1": f1, "row2": f2}, "foot": foot}, f"{order}: fits"
a, why_a = plan("agave_top"); b, why_b = plan("beer_top")
res = a or b; res["order_note"] = f"content heights (no face, no foot) {content}; {why_a}; {why_b}"
H = res; (HERE / "heights.json").write_text(json.dumps(H))
print(json.dumps(H, indent=1, ensure_ascii=False))
