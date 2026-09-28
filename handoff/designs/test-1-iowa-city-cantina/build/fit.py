"""Round 15: fit the face heights. Every card keeps one item pitch; the shorter card in each row takes the row difference in its face."""
import json, pathlib
HERE = pathlib.Path(__file__).parent
M = json.loads((HERE / "measure.json").read_text())["M"]; H = json.loads((HERE / "heights.json").read_text())
PT = 0.75; MINF = 105; DECK = 630; GAP = 12
face = {int(k): v for k, v in H.get("face", {}).items()} or {n: MINF for n in (1, 2, 3, 4)}
content = {}
for c in M["cards"]:
    h = c["box"]["h"] * PT; inner_bottom = (c["box"]["y"] + c["box"]["h"]) * PT - (c["padding_px"]["bottom"] + c["border_px"]) * PT
    empty = inner_bottom - c["content_bottom"] * PT
    content[c["n"]] = round(h - empty - face[c["n"]])      # card height without the face at one item pitch
row1 = max(content[1], content[2]) + MINF; row2 = DECK - GAP - row1
assert row2 >= max(content[3], content[4]) + MINF, ("rows do not fit", content, row1, row2)
face = {n: (row1 if n in (1, 2) else row2) - content[n] for n in (1, 2, 3, 4)}
assert all((f + 3) % 6 == 0 for f in face.values()), face
H.update({"row1": row1, "row2": row2, "deck": DECK, "xg": {str(n): 0 for n in (1, 2, 3, 4)}, "face": {str(n): f for n, f in face.items()}})
(HERE / "heights.json").write_text(json.dumps(H))
print("content", content, "rows", row1, row2, "face", face)
