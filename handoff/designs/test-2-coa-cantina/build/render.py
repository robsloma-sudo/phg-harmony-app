import json, os, statistics
from collections import defaultdict
from playwright.sync_api import sync_playwright
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', '/opt/pw-browsers')
OUT = '/home/user/phg-harmony-app/handoff/designs/test-2-coa-cantina'
URL = f'file://{OUT}/menu.html'
PX2MM = 25.4 / 96; PX2PT = 0.75
SCALE = 3.125  # 816 css px * 3.125 = 2550 px = 300 dpi at 8.5 in

JS = r'''
() => {
  const out = [];
  document.querySelectorAll('.page').forEach((pg, pi) => {
    const P = pg.getBoundingClientRect();
    const cols = [...pg.querySelectorAll('.halves > .col, .thirds > .col, .quarters > .col')];
    pg.querySelectorAll('[data-k]').forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.width === 0) return;
      let col = cols.findIndex(c => c.contains(el));
      let colbox = col >= 0 ? cols[col].getBoundingClientRect() : null;
      let blk = el.closest('.blk, .mgroup, .matrix');
      let text = el.textContent.trim().replace(/\s+/g, ' ');
      // for names with a dotted leader, measure the text itself
      let tw = null;
      if (el.classList.contains('nm')) { const rg = document.createRange(); rg.selectNodeContents(el); tw = rg.getBoundingClientRect().width; }
      const cs = getComputedStyle(el);
      out.push({page: pi + 1, kind: el.dataset.k, ref: el.dataset.ref || null, col: col >= 0 ? `p${pi+1}c${col}` : null,
        colx: colbox ? colbox.left - P.left : null, colw: colbox ? colbox.width : null,
        block: blk ? (blk.querySelector('[data-k=header],[data-k=subheader]')||{}).textContent || blk.className : null,
        x: r.left - P.left, y: r.top - P.top, w: r.width, h: r.height, tw, text: text.slice(0, 90),
        font: cs.fontFamily.split(',')[0].replace(/"/g,''), size: parseFloat(cs.fontSize), color: cs.color, weight: cs.fontWeight,
        lvl: el.dataset.lvl || null, mcol: el.dataset.col || null});
    });
    // decorative elements
    pg.querySelectorAll('.papel, .divider, .doublerule, .foot, .feature').forEach(el => {
      const r = el.getBoundingClientRect();
      out.push({page: pi + 1, kind: el.classList.contains('feature') ? 'ornament' : (el.classList.contains('foot') ? 'footer' : 'ornament'), ref: null, col: null,
        x: r.left - P.left, y: r.top - P.top, w: r.width, h: r.height, text: el.className.baseVal !== undefined ? el.className.baseVal : el.className});
    });
  });
  return out;
}
'''

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        pg = b.new_page(viewport={'width': 816, 'height': 1344}, device_scale_factor=SCALE)
        pg.goto(URL); pg.wait_for_timeout(400); pg.evaluate('document.fonts.ready')
        fonts = pg.evaluate('[...document.fonts].filter(f=>f.status=="loaded").map(f=>f.family+" "+f.style)')
        print('fonts loaded', fonts)
        over = pg.evaluate('''[...document.querySelectorAll('.page')].map(p=>{const m=p.querySelector('main');return {scroll:p.scrollHeight, client:p.clientHeight, mainScroll:m.scrollHeight, mainClient:m.clientHeight}})''')
        print('overflow check', over)
        for i in (1, 2):
            pg.locator(f'#page-{i}').screenshot(path=f'{OUT}/preview-page-{i}.png')
        els = pg.evaluate(JS)
        ph = b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=3)
        ph.goto(URL); ph.wait_for_timeout(400)
        ph.screenshot(path=f'{OUT}/preview-phone.png', full_page=True)
        b.close()
    json.dump(els, open(os.path.join(os.path.dirname(__file__), 'els.json'), 'w'), indent=0)
    print('elements', len(els))

if __name__ == '__main__':
    main()
