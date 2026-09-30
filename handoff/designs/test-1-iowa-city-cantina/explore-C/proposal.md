# Explore-C: Late-Night Risograph Zine

**Thesis:** A two-ink risograph flyer pulled off a college-town corkboard at midnight, where pink and teal overprint into a third ink that carries every word you need to read.

**Concept words:** overprint, halftone, misregistered, stamped, tilted, DIY.
**Avoid-list:** lotería, papel picado, cut-paper sun, torn rail, vertical CANTINA, gold leaf, ink wash, script accents, AI lettering, brand/film IP.

## Why this is the opposite of rounds 1-18
| Rounds 1-18 | Explore-C |
|---|---|
| Warm cut-paper / collage, apricot and terracotta | Two flat fluorescent drums (pink #ff48b0, teal #00a3ad) on cool newsprint, multiply overprint |
| Vertical CANTINA wordmark on a torn rail | Horizontal stacked BAR MENU, pink and teal plates misregistered 5/4 px |
| Illustrated sun, hills, lotería cards | Halftone dot screens (SVG, generated in build.py): agave rosette at 15°, coupe and rocks glass at 75° |
| Calm editorial columns | Tilted flyer blocks (-1.5° to +3°) with hard offset shadows, hand-stamped 01-05 section numbers (turbulence-roughened) |
| `ingredient · ingredient` serif line | One ingredient per boxed tag with draft quantity (e.g. TEQUILA BLANCO 2 OZ); garnish as a dashed tag; method / glass as an italic line |

## Layout geometry (CSS px at 96 dpi; letter 816x1056; render x3.125 = 2550x3300)
- Safe margin 48 px (36 pt) all sides; all text blocks measured inside it (checks.json).
- Masthead 48,48 420x199 · Cider 551,98 220x123 (+3°) · Cocktails 45,256 725x330 (-1°, 2 columns: Classics / House Originals)
- Beer 46,635 · Wine 291,627 · Spirits 538,640 (3 columns x 228 px, ±1.5°) · Tagline 77,913 · Footer 48,991 720x17.
- Art: SVG halftone layer with 12 px (3.2 mm) bleed past trim, text-free; pink and teal groups use mix-blend multiply, teal shifted (3,-2) px for misregistration.
- Type: DM Sans 700 (wordmark 96 px, heads 23 px tracked 5, names 16 px, tags 11 px), Liberation Mono (quantities), Fraunces 600 italic (descriptions 13.5 px, method/glass 13 px), Courier 10 Pitch (stamps).
- Palette: paper #f3efe4, pink #ff48b0, teal #00a3ad, overlap #00207c (computed multiply), text ink #1b1446.

## Contrast (worst pixel)
Every text block sits on an opaque paper card, the ink kicker, or the opaque pink tagline chip; no dots sit behind text.
Ink on paper 14.8:1 · stamp numerals (overlap ink) on paper 11.0:1 · ink on opaque pink tagline 5.51:1 · paper on ink kicker 14.8:1.
The pink/teal wordmark is display only (the navy overlap reads as the letterform). Legible at 1 m: names 16 px = 12 pt, smallest text 11 px = 8.3 pt caps in bold.

## Data (all 14 items, exact names and prices from ../build/draft_doc.json)
Cocktail tags come from draft components (quantity + unit). Manhattan hides Aromatic Bitters (meta.public_components). Old Fashioned shows no quantities because public_visibility.house_recipe = false. "Fresh Lime Juice" is shortened to FRESH LIME per brief; the Daiquiri syrup is "HOUSE DEMERARA SYRUP" as the draft desc says. Garnish, glass and method from phg.recipe_versions f06abb74 / 9fb77eaa / 7095fd3d / 14d45e57 (cited in ../round-17/proposal.md). Beer, wine, spirits, cider print the draft description in full.
"IOWA CITY · LATE" and "GOOD DRINKS / GOOD COMPANY" are generic brand voice; "Nº 1 · PRINTED IN TWO INKS" describes the design, not a product.

## Restraint pass
Devices listed: 1 two-ink overprint wordmark · 2 misregistration · 3 halftone agave · 4 halftone coupe · 5 halftone rocks glass · 6 tilted blocks · 7 offset shadows · 8 rough stamps · 9 ingredient tags · 10 dashed garnish tag · 11 dotted leaders · 12 pink tagline chip · 13 ink kicker · 14 newsprint dot grain · 15 second agave at bottom · 16 zine issue line.
Removed (25%): a stamped "LATE" sticker, a zig-zag border, rotated vertical tags on the rail and per-item pink highlight bars (they were in the plan, all dropped before rendering). Kept 16 only because each carries the riso/flyer thesis; the bottom agave stays to balance the heavy top-right art.

## Revision log
R1 overflowed the page (blocks stacked in two columns); hypothesis: three columns under a full-width cocktails card fits. R2 fixed it but hid the kicker and cropped the coupe; R3 moved the cider card and coupe apart and kept long names on one line. The phone build is a single column (1170 x 6231).

## References
Library: 572 (Coa Cantina, Iowa City: local price band), 7923 (compact cocktail-led list), per round 17. Quality bar: rob-2026-09-28 ref-03 (the vinyl/poster variant for loud display type over quiet lists) and ref-07 (text on stable backing cards over busy art). Structure only; no art copied.

## Files
build.py, menu.html, preview-letter.png (2550x3300), preview-phone.png (1170x6231), checks.json, variations.md.
