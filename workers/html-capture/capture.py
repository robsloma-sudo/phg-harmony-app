"""PHG HTML menu capture v2 (PHG-034).

Fixes the capture faults Rob found on 2026-09-27 (Mymoon, Bonao, 317 Main, Watershed, Adrift):
  1. Screenshot stops at the first screen (4,137 of 14,008 railway screenshots are exactly 1000 px tall):
     cookie / age pop-ups lock scrolling (body overflow:hidden) or the page scrolls inside a container.
     -> dismiss pop-ups, unlock scrolling, expand the scrolling container before measuring.
  2. Drinks and photos that only load when scrolled into view come out blank.
     -> scroll the whole page in steps until its height stops growing, force lazy images to load,
        wait for images to finish.
  3. Tabbed drinks menus (Beer | Wine | Cocktails | Spirits) keep only the first tab.
     -> click every drinks tab that changes the page in place and stitch each state under the first.
  4. Sticky "Order online" bars / chat bubbles stamped over the menu.
     -> hide small fixed/sticky overlays after the pop-ups are handled.

Resolution is never reduced: the page is laid out at target_width (1400) and saved as JPEG.
Tall pages are captured in slices and stitched, so there is no Chromium texture limit.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

from PIL import Image

MAX_HEIGHT = 60000          # px; JPEG limit is 65,535
SLICE = 8000                # px per screenshot slice
DRINK_TAB_RE = re.compile(
    r"\b(drinks?|beers?|wines?|cocktails?|spirits?|whiske?y|bourbon|tequila|mezcal|rum|vodka|gin|sake|soju|"
    r"mocktails?|zero[- ]proof|non[- ]?alcoholic|n/?a|bar|draft|taps?|cans?|bottles?|by the glass|happy hour|"
    r"sparkling|red|white|ros[eé]|frozen|margaritas?|spritz|seltzers?|ciders?|flights?)\b", re.I)
NOT_TAB_RE = re.compile(r"\b(order|reserv|book|gift|career|jobs?|login|sign|cart|delivery|catering|contact)\b", re.I)
CONSENT_RE = r"^\s*(accept( all)?( cookies)?|allow( all)?( cookies)?|i accept|i agree|agree|got it|ok(ay)?|continue|close|dismiss|no thanks|reject all|decline)\s*[.!]?\s*$"
AGE_RE = r"^\s*(yes|i am 21\+?|i'?m 21\+?|i am of legal drinking age|enter( site)?|21\+|over 21)\s*[.!]?\s*$"


@dataclass
class Capture:
    jpeg: bytes
    width: int
    height: int
    notes: list = field(default_factory=list)


# --------------------------------------------------------------------------- page preparation

JS_UNLOCK = """() => {
  for (const el of [document.documentElement, document.body]) {
    if (!el) continue;
    el.style.setProperty('overflow', 'visible', 'important');
    el.style.setProperty('overflow-y', 'visible', 'important');
    el.style.setProperty('height', 'auto', 'important');
    el.style.setProperty('max-height', 'none', 'important');
    el.style.setProperty('position', 'static', 'important');
    el.classList.remove('modal-open', 'no-scroll', 'noscroll', 'overflow-hidden', 'lock-scroll', 'scroll-lock');
  }
  // The page scrolls inside a container (html/body stay one screen tall): let it grow.
  const vh = window.innerHeight; let best = null, bestH = 0;
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    if (!/(auto|scroll|hidden)/.test(cs.overflowY)) continue;
    const r = el.getBoundingClientRect();
    if (r.width < window.innerWidth * 0.5 || r.height < vh * 0.5) continue;
    if (el.scrollHeight > el.clientHeight + 200 && el.scrollHeight > bestH) { best = el; bestH = el.scrollHeight; }
  }
  if (best && document.documentElement.scrollHeight <= vh + 50) {
    for (let el = best; el && el !== document.documentElement; el = el.parentElement) {
      if (getComputedStyle(el).position === 'fixed') el.style.setProperty('position', 'relative', 'important');
      el.style.setProperty('overflow', 'visible', 'important');
      el.style.setProperty('height', 'auto', 'important');
      el.style.setProperty('max-height', 'none', 'important');
    }
    return 'expanded_scroll_container';
  }
  return '';
}"""

JS_HIDE_OVERLAYS = """() => {
  const vw = window.innerWidth, vh = window.innerHeight; let n = 0;
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    if (cs.position !== 'fixed' && cs.position !== 'sticky') continue;
    const r = el.getBoundingClientRect();
    const area = (r.width * r.height) / (vw * vh);
    const txt = (el.innerText || '').toLowerCase();
    // Never hide a wrapper that holds the page itself (some sites put all content in a fixed/sticky box).
    if (txt.length > 1500 || el.scrollHeight > vh * 1.5 || el.querySelector('main, article, [data-phg-tab]')) continue;
    const consent = txt.length < 900 && /cookie|consent|privacy|gdpr|we use|21 or older|legal drinking age/.test(txt);
    // consent/age walls of any size; otherwise only small bars, bubbles and side tabs
    if (consent || area < 0.35) { el.style.setProperty('display', 'none', 'important'); n++; }
  }
  return n;
}"""

JS_LAZY = """() => {
  let n = 0;
  for (const img of document.querySelectorAll('img')) {
    if (img.loading === 'lazy') { img.loading = 'eager'; n++; }
    for (const a of ['data-src', 'data-lazy-src', 'data-original', 'data-lazy']) {
      const v = img.getAttribute(a);
      if (v && (!img.getAttribute('src') || img.src.startsWith('data:'))) { img.src = v; n++; }
    }
    const ss = img.getAttribute('data-srcset') || img.getAttribute('data-lazy-srcset');
    if (ss && !img.getAttribute('srcset')) { img.srcset = ss; n++; }
  }
  for (const f of document.querySelectorAll('iframe')) {  // embedded beer/wine lists (Untappd, BeerMenus...)
    if (f.loading === 'lazy') { f.loading = 'eager'; n++; }
    const v = f.getAttribute('data-src') || f.getAttribute('data-lazy-src');
    if (v && (!f.getAttribute('src') || f.src === 'about:blank')) { f.src = v; n++; }
  }
  for (const el of document.querySelectorAll('[data-bg],[data-background-image]')) {
    const v = el.getAttribute('data-bg') || el.getAttribute('data-background-image');
    if (v && !el.style.backgroundImage) { el.style.backgroundImage = 'url(' + JSON.stringify(v) + ')'; n++; }
  }
  return n;
}"""

JS_IMAGES_DONE = """() => [...document.images].every(i => i.complete || i.getBoundingClientRect().height === 0)"""

JS_HEIGHT = """() => Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0)"""


async def _settle(page) -> None:
    for state in ("domcontentloaded", "load"):
        try:
            await page.wait_for_load_state(state, timeout=8000)
        except Exception:
            pass


async def _ev(page, js: str, arg=None):
    """page.evaluate that survives a navigation (consent buttons often reload the page)."""
    for i in range(3):
        try:
            return await (page.evaluate(js, arg) if arg is not None else page.evaluate(js))
        except Exception as e:
            if "Execution context was destroyed" not in str(e) and "navigat" not in str(e) or i == 2:
                raise
            await _settle(page)


CHALLENGE_RE = re.compile(r"checking the site connection|checking your browser|just a moment|verify(ing)? you are (a )?human|"
                          r"security check|attention required|enable (javascript|cookies)|ddos protection|please wait", re.I)


async def _wait_out_challenge(page, max_s: int = 30) -> bool:
    """Bot-check interstitials (SiteGround, Cloudflare, Sucuri) solve themselves and reload; wait for the real page."""
    waited = False
    for _ in range(max_s):
        try:
            txt = await page.evaluate("(document.title || '') + ' ' + (document.body ? document.body.innerText.slice(0, 600) : '')")
        except Exception:
            txt = "please wait"  # navigating
        if len(txt) > 700 or not CHALLENGE_RE.search(txt):
            break
        waited = True
        await page.wait_for_timeout(1000)
    if waited:
        await _settle(page)
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
    return waited


async def _click_matching(page, pattern: str) -> int:
    """Click visible buttons/links whose whole label matches pattern (consent / age gates)."""
    clicked = 0
    for frame in page.frames:  # consent tools often live in an iframe
        try:
            loc = frame.locator("button, a, [role=button], input[type=button], input[type=submit]")
            count = min(await loc.count(), 200)
            for i in range(count):
                el = loc.nth(i)
                try:
                    if not await el.is_visible():
                        continue
                    label = (await el.inner_text(timeout=500)) or (await el.get_attribute("value")) or ""
                    if re.match(pattern, label.strip(), re.I) and len(label) < 40:
                        await el.click(timeout=1500)
                        clicked += 1
                        await page.wait_for_timeout(500)
                        await _settle(page)
                        break
                except Exception:
                    continue
        except Exception:
            continue
    return clicked


async def _scroll_through(page, notes: list, max_steps: int = 80) -> None:
    """Scroll to the bottom in steps so lazy content loads; stop when height is stable."""
    await _ev(page, JS_LAZY)
    last, stable, y = 0, 0, 0
    vh = page.viewport_size["height"]
    for _ in range(max_steps):
        h = await _ev(page, JS_HEIGHT)
        if y >= h - vh:
            if h == last:
                stable += 1
                if stable >= 2:
                    break
            else:
                stable = 0
            last = h
            await page.wait_for_timeout(400)
        y = min(y + int(vh * 0.8), max(0, h - vh))
        await _ev(page, f"window.scrollTo(0, {y})")
        await page.wait_for_timeout(180)
        if h > MAX_HEIGHT:
            notes.append("height_capped")
            break
    await _ev(page, JS_LAZY)
    for _ in range(40):  # up to ~8 s for images to finish
        if await _ev(page, JS_IMAGES_DONE):
            break
        await page.wait_for_timeout(200)
    for fr in page.frames[1:]:  # embedded menus: wait for each frame to finish loading
        try:
            await fr.wait_for_load_state("load", timeout=5000)
        except Exception:
            pass
    await _ev(page, "window.scrollTo(0, 0)")
    await page.wait_for_timeout(250)


async def _paint_iframes(page, out: Image.Image, top: int) -> int:
    """Cross-origin iframes (Untappd beer lists, wine widgets) below the first screen come out blank in a
    full-page shot; screenshot each one in view and paste it at its place on the page."""
    n = 0
    frames = page.locator("iframe")
    if not await frames.count():
        return 0
    hide_js = """(on) => {
      if (!on) { for (const el of document.querySelectorAll('[data-phg-hid]')) { el.style.visibility = el.dataset.phgHid; el.removeAttribute('data-phg-hid'); } return; }
      for (const el of document.querySelectorAll('body *')) {
        const p = getComputedStyle(el).position;
        if ((p === 'fixed' || p === 'sticky') && !el.querySelector('iframe')) { el.dataset.phgHid = el.style.visibility || ''; el.style.visibility = 'hidden'; }
      }
    }"""
    for i in range(min(await frames.count(), 12)):
        el = frames.nth(i)
        try:
            box = await el.bounding_box()
            if not box or box["height"] < 150 or box["width"] < 200:
                continue
            src = (await el.get_attribute("src") or "")
            if "google.com/maps" in src or "youtube" in src or "facebook" in src:
                continue
            await el.scroll_into_view_if_needed(timeout=2000)
            await page.wait_for_timeout(600)
            await _ev(page, hide_js, True)  # sticky headers re-appear on scroll
            y_doc = await el.evaluate("e => e.getBoundingClientRect().top + window.scrollY")
            x_doc = await el.evaluate("e => e.getBoundingClientRect().left + window.scrollX")
            png = await el.screenshot(type="png", timeout=10000)
            im = Image.open(io.BytesIO(png)).convert("RGB")
            y = int(round(y_doc)) - top
            if y + im.height <= 0 or y >= out.height:
                continue
            out.paste(im, (int(round(x_doc)), y))
            n += 1
        except Exception:
            continue
    await _ev(page, hide_js, False)
    if n:
        await _ev(page, "window.scrollTo(0, 0)")
    return n


async def _shot(page, top: int = 0) -> Image.Image:
    """Full-page screenshot from `top` down, in slices (no texture-size limit)."""
    width = page.viewport_size["width"]
    height = min(await _ev(page, JS_HEIGHT), MAX_HEIGHT)
    top = max(0, min(top, height - 1))
    out = Image.new("RGB", (width, height - top), "white")
    y = top
    while y < height:
        h = min(SLICE, height - y)
        png = await page.screenshot(full_page=True, clip={"x": 0, "y": y, "width": width, "height": h}, type="png")
        out.paste(Image.open(io.BytesIO(png)).convert("RGB"), (0, y - top))
        y += h
    await _paint_iframes(page, out, top)
    return out


async def _drink_tabs(page) -> list:
    """In-page tabs whose labels are drinks (Beer / Wine / Cocktails ...). Links to other pages are not tabs."""
    js = """(reS) => {
      const re = new RegExp(reS[0], 'i'), no = new RegExp(reS[1], 'i'), out = [];
      const cands = [...document.querySelectorAll('[role=tab], button, a, li, label, [data-tab], [data-toggle=tab], [data-bs-toggle=tab], [aria-controls], [onclick]')]
        .concat([...document.querySelectorAll('div, span, h2, h3, h4, p')].filter(e => e.childElementCount <= 1 && getComputedStyle(e).cursor === 'pointer'));
      for (const el of cands) {
        const t = (el.innerText || '').trim();
        if (!t || t.length > 30 || !re.test(t) || no.test(t)) continue;
        const r = el.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
        if (el.tagName === 'A') {
          const h = el.getAttribute('href') || '';
          const inPage = !h || h.startsWith('#') || h.startsWith('javascript') || el.hasAttribute('aria-controls') || el.getAttribute('role') === 'tab' || el.hasAttribute('data-toggle') || el.hasAttribute('data-bs-toggle');
          if (!inPage) continue;
        }
        if (el.closest('nav, header, footer') && el.getAttribute('role') !== 'tab') continue;
        // keep the innermost clickable (skip an li whose child button is also a candidate)
        if (el.querySelector('[role=tab], button, a, [onclick]')) continue;
        if (el.hasAttribute('data-phg-tab')) continue;
        el.setAttribute('data-phg-tab', out.length);
        out.push({i: out.length, text: t, y: Math.round(r.top + window.scrollY)});
      }
      return out;
    }"""
    try:
        return await _ev(page, js, [DRINK_TAB_RE.pattern, NOT_TAB_RE.pattern])
    except Exception:
        return []


def _thumb(img: Image.Image) -> Image.Image:
    return img.convert("L").resize((64, max(1, img.height // 40)))


def _same(a: Image.Image, b: Image.Image) -> bool:
    """Same tab state? Tolerates focus rings / hover styling on the clicked tab."""
    if abs(a.height - b.height) > max(8, 0.02 * a.height):
        return False
    ta, tb = _thumb(a), _thumb(b.resize(a.size) if b.size != a.size else b)
    diff = sum(abs(x - y) for x, y in zip(ta.getdata(), tb.getdata())) / (ta.width * ta.height)
    return diff < 2.0


JS_DIAG = """() => {
  const vh = innerHeight, de = document.documentElement, b = document.body;
  const fixed = [], scrollers = [];
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    if ((cs.position === 'fixed' || cs.position === 'sticky') && r.width * r.height > 0)
      fixed.push([el.tagName, (el.id || el.className || '').toString().slice(0, 40), Math.round(r.width), Math.round(r.height), (el.innerText || '').length]);
    if (/(auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + 100)
      scrollers.push([el.tagName, (el.id || el.className || '').toString().slice(0, 40), el.clientHeight, el.scrollHeight]);
  }
  return {doc: de.scrollHeight, body: b ? b.scrollHeight : 0, vh, htmlOverflow: getComputedStyle(de).overflowY,
          bodyOverflow: b ? getComputedStyle(b).overflowY : '', bodyPos: b ? getComputedStyle(b).position : '',
          fixed: fixed.slice(0, 12), scrollers: scrollers.slice(0, 8),
          iframes: [...document.querySelectorAll('iframe')].map(f => [(f.src || f.getAttribute('data-src') || '').slice(0, 90), f.loading, Math.round(f.getBoundingClientRect().height)]).slice(0, 8),
 text: (b ? b.innerText : '').length, url: location.href};
}"""


async def capture(page, url: str, target_width: int = 1400, jpeg_quality: int = 85, diag: dict | None = None) -> Capture:
    notes: list = []

    async def d(step: str):
        if diag is not None:
            try:
                diag[step] = await _ev(page, JS_DIAG)
            except Exception as e:
                diag[step] = {"error": str(e)[:200]}
    await page.set_viewport_size({"width": target_width, "height": 1000})
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        notes.append("no_networkidle")

    if await _wait_out_challenge(page):
        notes.append("waited_bot_check")
    await d("loaded")
    if await _click_matching(page, AGE_RE):
        notes.append("age_gate")
    if await _click_matching(page, CONSENT_RE):
        notes.append("consent")
    unlocked = await _ev(page, JS_UNLOCK)
    if unlocked:
        notes.append(unlocked)
    await d("unlocked")
    await _scroll_through(page, notes)
    await d("scrolled")
    hidden = await _ev(page, JS_HIDE_OVERLAYS)
    if hidden:
        notes.append(f"overlays_hidden:{hidden}")
    await _ev(page, JS_UNLOCK)

    parts = [await _shot(page)]
    seen: list = []

    await d("prepared")
    tabs = await _drink_tabs(page)
    if diag is not None:
        diag["tabs"] = tabs
    if len(tabs) >= 2:
        top = max(0, min(t["y"] for t in tabs) - 20)
        seen.append(parts[0].crop((0, top, parts[0].width, parts[0].height)))  # the tab already showing
        for t in tabs[:12]:
            try:
                await page.locator(f'[data-phg-tab="{t["i"]}"]').first.click(timeout=2000)
                await page.wait_for_timeout(600)
                await _ev(page, JS_UNLOCK)
                await _scroll_through(page, notes, max_steps=40)
                await _ev(page, JS_HIDE_OVERLAYS)
                img = await _shot(page, top)
                if any(_same(img, x) for x in seen):
                    continue
                seen.append(img)
                parts.append(img)
                notes.append("tab:" + t["text"][:20])
            except Exception:
                continue

    width = target_width
    total = min(sum(p.height for p in parts) + 12 * (len(parts) - 1), MAX_HEIGHT)
    sheet = Image.new("RGB", (width, total), "white")
    y = 0
    for i, p in enumerate(parts):
        if y >= total:
            notes.append("tabs_truncated")
            break
        if i:  # thin divider between tab states
            sheet.paste(Image.new("RGB", (width, 4), (200, 200, 200)), (0, y + 4))
            y += 12
        sheet.paste(p.crop((0, 0, width, min(p.height, total - y))), (0, y))
        y += p.height
    buf = io.BytesIO()
    sheet.save(buf, "JPEG", quality=jpeg_quality, optimize=True)
    return Capture(buf.getvalue(), width, sheet.height, notes)
