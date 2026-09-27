"""Old-style capture (load + full-page screenshot) vs capture v2 on fixtures that reproduce Rob's examples."""
import asyncio, io, os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from playwright.async_api import async_playwright
from PIL import Image
from capture import capture

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.environ.get('OUT', os.path.join(HERE, 'out')); os.makedirs(OUT, exist_ok=True)
EXE = os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium')

async def text_of(page):  # OCR-free check: what text is visibly inside the captured document after v2 prep
    return await page.evaluate("document.body.innerText")

async def main():
    fails = 0
    async with async_playwright() as p:
        exe = EXE if os.path.exists(EXE) else None
        if exe and os.path.isdir(exe):
            import glob; c = glob.glob(exe + '/**/chrome', recursive=True); exe = c[0] if c else None
        b = await p.chromium.launch(executable_path=exe, args=['--no-sandbox'])
        for name, expect in [('cookie_lock', ['Cocktail 30']), ('lazy', ['Signature Cocktail 7']), ('tabs', ['Wine 10', 'Cocktail 12', 'Whiskey 15']),
                             ('inner_scroll', ['Cocktail 40']), ('fixed_wrapper', ['Cocktail 35']), ('sticky_bar', ['Cocktail 25']), ('beer_embed', ['Draft Beer'])]:
            url = 'file://' + os.path.join(HERE, 'fixtures', name + '.html')
            # old: what the current worker appears to do
            pg = await b.new_page(viewport={'width': 1400, 'height': 1000})
            await pg.goto(url); await pg.wait_for_timeout(500)
            old = await pg.screenshot(full_page=True, type='jpeg', quality=85); await pg.close()
            oi = Image.open(io.BytesIO(old)); open(f'{OUT}/{name}-old.jpg', 'wb').write(old)
            # new
            pg = await b.new_page()
            cap = await capture(pg, url)
            open(f'{OUT}/{name}-new.jpg', 'wb').write(cap.jpeg)
            await pg.close()
            ok = cap.height > oi.height or name in ('sticky_bar', 'lazy')
            print(f'{name:13s} old {oi.width}x{oi.height}  new {cap.width}x{cap.height}  notes={cap.notes}')
            if name == 'tabs':
                tabs = [n for n in cap.notes if n.startswith('tab:')]
                ok = ok and len(tabs) == 3 and not any('ORDER' in t for t in tabs)
            if name == 'beer_embed':
                im = Image.open(io.BytesIO(cap.jpeg)).convert('RGB')
                y = im.height - 900  # inside the iframe area near the bottom
                px = im.getpixel((100, y))
                ok = abs(px[0] - 245) < 20 and abs(px[2] - 200) < 25
                print('   beer iframe pixel', px)
            if name == 'sticky_bar':
                ok = any(n.startswith('overlays_hidden') for n in cap.notes)
            if name == 'cookie_lock':
                ok = 'consent' in cap.notes and cap.height > 2000
            if name in ('inner_scroll', 'fixed_wrapper'):
                ok = ok and cap.height > 2000
            if name == 'lazy':
                im = Image.open(io.BytesIO(cap.jpeg)).convert('RGB')
                # the 8th photo block must be painted (non-white pixels near the bottom third)
                def colored(im):
                    strip = im.convert('RGB').crop((0, int(im.height*0.75), 400, im.height)).getcolors(1<<20)
                    return sum(c for c, px in strip if max(px) - min(px) > 60)
                cn, co = colored(im), colored(oi)
                ok = ok and cn > 5000 and co < 1000
                print('   lazy colored px in bottom quarter: old', co, 'new', cn)
            print('   ', 'PASS' if ok else 'FAIL'); fails += (not ok)
        await b.close()
    print('FAILURES', fails); sys.exit(1 if fails else 0)

asyncio.run(main())
