"""Capture real menu URLs old-style and with capture v2, save half-size previews + diagnostics (run on Actions)."""
import asyncio, io, json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from playwright.async_api import async_playwright
from PIL import Image
from capture import capture

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('OUT', os.path.join(HERE, 'out'))
os.makedirs(OUT, exist_ok=True)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"


def small(jpeg: bytes, path: str):
    im = Image.open(io.BytesIO(jpeg)).convert('RGB')
    if im.width > 700:
        im = im.resize((700, max(1, round(im.height * 700 / im.width))))
    if im.height > 12000:
        im = im.crop((0, 0, im.width, 12000))
    im.save(path, 'JPEG', quality=70)


async def main():
    urls = [l.strip() for l in open(os.path.join(HERE, '..', 'diagnose_urls.txt')) if l.strip() and not l.startswith('#')]
    summary = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--no-sandbox'])
        for u in urls:
            slug = re.sub(r'[^a-z0-9]+', '-', u.lower().split('//')[-1])[:60].strip('-')
            row = {'url': u, 'slug': slug}
            try:
                ctx = await b.new_context(user_agent=UA, viewport={'width': 1400, 'height': 1000})
                pg = await ctx.new_page()
                await pg.goto(u, wait_until='domcontentloaded', timeout=45000)
                await pg.wait_for_timeout(2500)
                old = await pg.screenshot(full_page=True, type='jpeg', quality=85)
                row['old_h'] = Image.open(io.BytesIO(old)).height
                small(old, f'{OUT}/{slug}-old.jpg')
                await ctx.close()
            except Exception as e:
                row['old_error'] = str(e)[:200]
            try:
                ctx = await b.new_context(user_agent=UA)
                pg = await ctx.new_page()
                diag = {}
                cap = await asyncio.wait_for(capture(pg, u, diag=diag), timeout=180)
                row.update(new_h=cap.height, notes=cap.notes, diag=diag)
                small(cap.jpeg, f'{OUT}/{slug}-v2.jpg')
                await ctx.close()
            except Exception as e:
                row['new_error'] = str(e)[:300]
            print(json.dumps({k: v for k, v in row.items() if k != 'diag'}), flush=True)
            summary.append(row)
        await b.close()
    json.dump(summary, open(f'{OUT}/summary.json', 'w'), indent=1)

asyncio.run(main())
