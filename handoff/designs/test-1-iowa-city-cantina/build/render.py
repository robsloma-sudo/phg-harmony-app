import json, pathlib, subprocess, sys
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path("/home/user/phg-harmony-app/handoff/designs/test-1-iowa-city-cantina")
URL = (OUT / "menu.html").as_uri()
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
PT = 0.75; MM = 25.4 / 72
r2 = lambda v: round(v, 2)

PROBE = r"""
(sel) => {
  const pg = document.querySelector('.page').getBoundingClientRect();
  const bl = (el) => { const s=document.createElement('span'); s.style.cssText='display:inline-block;width:0;height:0;vertical-align:baseline'; el.appendChild(s); const y=s.getBoundingClientRect().top-pg.top; s.remove(); return y; };
  const top = (el) => el.getBoundingClientRect().top - pg.top;
  const pairs = {
    title: [document.querySelector('.title'), document.querySelector('.title')],
    loc: [document.querySelector('.loc'), document.querySelector('.loc')],
    h2: [...document.querySelectorAll('.hrow')].map(h => [h.querySelector('h2'), h]),
    h3: [...document.querySelectorAll('.sub')].map(s => [s.querySelector('h3'), s]),
    name: [...document.querySelectorAll('.row')].map(r => [r.querySelector('.name'), r]),
    desc: [...document.querySelectorAll('.desc')].map(d => [d, d]),
  };
  const out = {};
  for (const [k, v] of Object.entries(pairs)) {
    const list = Array.isArray(v[0]) ? v : [v];
    out[k] = list.map(([t, slot]) => ({baseline: bl(t), slot_top: top(slot)}));
  }
  return out;
}
"""
SLOT_TARGET = {"title": 33, "loc": 9, "h2": 21, "h3": 9, "name": 9, "desc": 9}  # baseline = slot top + target (pt)

def build():
    subprocess.run([sys.executable, str(HERE / "build.py")], check=True)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    # ---- pass 1: natural baselines (no shifts)
    (HERE / "shifts.json").unlink(missing_ok=True); build()
    pg = b.new_page(viewport={"width": 816, "height": 1056})
    pg.goto(URL, wait_until="load"); pg.evaluate("document.fonts.ready")
    nat = pg.evaluate(PROBE, None)
    shifts = {}
    for k, lst in nat.items():
        offs = {r2(((x["baseline"] - x["slot_top"]) * PT) % 12) if k == "desc" else r2((x["baseline"] - x["slot_top"]) * PT) for x in lst}
        assert len(offs) == 1, (k, offs)
        shifts[k] = r2(SLOT_TARGET[k] - offs.pop())
    (HERE / "shifts.json").write_text(json.dumps(shifts))
    build()
    # ---- pass 2: final render + measurement
    pg = b.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=3.125)
    pg.goto(URL, wait_until="load"); pg.evaluate("document.fonts.ready")
    fonts = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').length")
    fin = pg.evaluate(PROBE, None)
    M = pg.evaluate((HERE / "measure.js").read_text())
    pg.locator(".page").screenshot(path=str(OUT / "preview-letter.png"))
    pg.pdf(path=str(OUT / "menu.pdf"), width="8.5in", height="11in", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
    ph = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    ph.goto(URL, wait_until="load"); ph.evaluate("document.fonts.ready")
    ph_w = ph.evaluate("document.documentElement.scrollWidth")
    PH = ph.evaluate(r"""() => { const t=e=>e.getBoundingClientRect(); const out=[];
       document.querySelectorAll('.hrow').forEach(h=>{ const n=h.nextElementSibling; out.push({sec:h.parentElement.dataset.id, gap_px: +(t(n).top - t(h).bottom).toFixed(2), next:n.className}); }); return out; }""")
    ph.screenshot(path=str(OUT / "preview-phone.png"), full_page=True)
    b.close()

# ---- ink scan of the 300 dpi preview: true printed margins
im = Image.open(OUT / "preview-letter.png").convert("RGB")
bg = Image.new("RGB", im.size, (0xF6, 0xEE, 0xDF))
diff = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 24 else 0)
bx = diff.getbbox(); sx = im.size[0] / 612; sy = im.size[1] / 792
ink = {"left": r2(bx[0] / sx), "top": r2(bx[1] / sy), "right": r2(612 - bx[2] / sx), "bottom": r2(792 - bx[3] / sy)}

json.dump({"shifts": shifts, "nat": nat, "fin": fin, "M": M, "ph": PH, "ph_w": ph_w, "ink": ink, "fonts": fonts,
           "png": list(im.size), "phone_png": list(Image.open(OUT / "preview-phone.png").size)},
          open(HERE / "measure.json", "w"), indent=1, ensure_ascii=False)
print("shifts", shifts, "fonts", fonts, "ink", ink, "phone scrollWidth", ph_w)
