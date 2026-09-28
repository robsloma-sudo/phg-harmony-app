"""Round 5 render: letter PNG (300 dpi, full resolution), PDF, phone PNG, and per-card measurement -> measure.json."""
import json, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path("/home/user/phg-harmony-app/handoff/designs/test-1-iowa-city-cantina")
URL = (OUT / "menu.html").as_uri()
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
r2 = lambda v: round(v, 2)

MEASURE = r"""() => {
  const pg = document.querySelector('.page').getBoundingClientRect();
  const box = b => ({x: b.left - pg.left, y: b.top - pg.top, w: b.width, h: b.height});
  const tight = el => { const r = document.createRange(); r.selectNodeContents(el); const rs = [...r.getClientRects()].filter(a => a.width > 0);
    if (!rs.length) return box(el.getBoundingClientRect());
    const x = Math.min(...rs.map(a => a.left)), y = Math.min(...rs.map(a => a.top)), R = Math.max(...rs.map(a => a.right)), B = Math.max(...rs.map(a => a.bottom));
    return {x: x - pg.left, y: y - pg.top, w: R - x, h: B - y, lines: new Set(rs.map(a => Math.round(a.top))).size}; };
  const T = (el) => Object.assign({text: (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 160)}, tight(el));
  const cards = [...document.querySelectorAll('.card')].map(c => {
    const cs = getComputedStyle(c), body = c.querySelector('.body');
    return {n: +c.dataset.n, ref: c.dataset.id, featured: c.classList.contains('featured'), box: box(c.getBoundingClientRect()),
      padding_px: {left: parseFloat(cs.paddingLeft), right: parseFloat(cs.paddingRight), top: parseFloat(cs.paddingTop), bottom: parseFloat(cs.paddingBottom)},
      border_px: parseFloat(cs.borderLeftWidth),
      content_bottom: Math.max(...[...body.children].map(e => e.getBoundingClientRect().bottom)) - pg.top,
      cardno: T(c.querySelector('.cardno')), banner: box(c.querySelector('.bannerband').getBoundingClientRect()),
      name: T(c.querySelector('h2')), kicker: T(c.querySelector('.kicker')), eyebrow: c.querySelector('.eyebrow') ? T(c.querySelector('.eyebrow')) : null,
      icon: box(c.querySelector('.icon').getBoundingClientRect()),
      subs: [...c.querySelectorAll('.sub')].map(s => ({ref: s.dataset.id, h3: T(s.querySelector('h3')), es: T(s.querySelector('.es'))})),
      items: [...c.querySelectorAll('.item')].map(it => ({ref: it.dataset.ref, name: T(it.querySelector('.name')), price: T(it.querySelector('.price')), desc: T(it.querySelector('.desc'))}))};
  });
  return {page: {w: pg.width, h: pg.height}, cards, banner: box(document.querySelector('.banner').getBoundingClientRect()),
          title: T(document.querySelector('.title')), loc: T(document.querySelector('.loc')), deck: box(document.querySelector('.deck').getBoundingClientRect()),
          foot: box(document.querySelector('.foot').getBoundingClientRect())};
}"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=3.125)
    pg.goto(URL, wait_until="load"); pg.evaluate("document.fonts.ready")
    fonts = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').length")
    M = pg.evaluate(MEASURE)
    pg.locator(".page").screenshot(path=str(OUT / "preview-letter.png"))
    pg.pdf(path=str(OUT / "menu.pdf"), width="8.5in", height="11in", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
    ph = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    ph.goto(URL, wait_until="load"); ph.evaluate("document.fonts.ready")
    PH = ph.evaluate("""() => ({scrollWidth: document.documentElement.scrollWidth, tabs: getComputedStyle(document.querySelector('.tabs')).position,
        tab_count: document.querySelectorAll('.tab').length, cards: [...document.querySelectorAll('.card')].map(c => { const r = c.getBoundingClientRect(); return {n: +c.dataset.n, x: r.left, w: r.width, y: r.top + scrollY}; })})""")
    ph.screenshot(path=str(OUT / "preview-phone.png"), full_page=True)
    b.close()

im = Image.open(OUT / "preview-letter.png").convert("RGB")
diff = ImageChops.difference(im, Image.new("RGB", im.size, (0xF6, 0xEE, 0xDF))).convert("L").point(lambda v: 255 if v > 24 else 0)
bx = diff.getbbox(); sx = im.size[0] / 612; sy = im.size[1] / 792
ink = {"left": r2(bx[0] / sx), "top": r2(bx[1] / sy), "right": r2(612 - bx[2] / sx), "bottom": r2(792 - bx[3] / sy)}
json.dump({"M": M, "ph": PH, "ink": ink, "fonts": fonts, "png": list(im.size), "phone_png": list(Image.open(OUT / "preview-phone.png").size)},
          open(HERE / "measure.json", "w"), indent=1, ensure_ascii=False)
print("fonts", fonts, "ink", ink, "png", im.size, "phone", PH["scrollWidth"], PH["tabs"])
