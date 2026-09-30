# Comparison artifacts: Glass Garden · Solstice · Cantina six-panel

Received from Rob 2026-09-28, no caption. They are stored unmodified here as benchmark comparison artifacts.
They are generated rasters, so this audit treats them as **concepts, not service menus** (handoff §8, D-19).

| file | px | sha256 (16) |
|---|---|---|
| ref-glass-garden.png | 1024×1536 | 2a6751616a97a433 |
| ref-solstice.png | 1222×1287 | ae89312251988fe6 |
| ref-cantina-six-panel.png | 1102×1427 | 63f42d4b0d5069a9 |

All three are below print resolution; letter at 300 dpi is 2550×3300. None can be used as a production file (D-19).

## A. Measured (tools/visual_tests.py, output in visual_tests.json)

| artifact | squint salient regions | primary area % | primary : secondary | accent area % |
|---|---|---|---|---|
| Glass Garden | 11 | 29.7 | 10.8 | 11.8 |
| Solstice | 8 | 27.2 | 16.5 | 12.2 |
| Cantina six-panel | **25** | **3.8** | **1.3** | 12.1 |
| TEST-1 round-17 (our best) | 8 | 15.3 | 59.6 | 6.4 |

Silhouette correlation:
- All three references are structurally distinct from each other (−0.02 to 0.26).
- **Solstice ↔ round-17 = 0.64**, the closest pair. round-17 already shares Solstice's split image-field / reading-field skeleton.

**What the numbers say (observation, not a verdict):**
- Glass Garden and Solstice each have one dominant image field (about 28–30% of area) and few competing regions. That is the "one gesture" structure.
- The six-panel Cantina has no dominant element (ratio 1.3) and 25 competing regions: six coloured banners, six numerals, a tile band and a sunburst. This is the "everything loud" failure, and it confirms the handoff's §8.1 read of the numbered-module design.
- **Correction to my own doctrine:** I had set accent ≤ 6% from earlier references. Rob's two preferred pieces run about 12% accent and work, because the accent sits inside the dominant image field, not scattered through the reading layer. The rule becomes **"accent concentrated in the gesture; reading layer ≤ 2 inks"**, not a fixed %.

## B. Factual / content corrections (no visual change)

### Cantina six-panel vs the TEST-1 database (phg.menu_items, project ddc4bb5b…)

**The database content is seeded sample data** (`metadata.beta_seed = true, sample_content = true`), approved in status only.

| | items |
|---|---|
| matches DB | Amber Lager 7 · Malbec 12 · Pinot Grigio 11 · Brut Rosé 13 · Blanco Tequila 12 · Añejo Tequila 16 · Cognac VSOP 18 |
| **price conflict** | "House Margarita" **14**; DB Margarita is **15** |
| **approved in DB, missing from image** | Manhattan 15 · House Daiquiri 14 · Brown Butter Old Fashioned 16 · Czech Pilsner 7 · Dry-Hopped IPA 8 · Dry Cider 8 |
| **in image, not in DB** (12) | Paloma 12 · Ranch Water 11.50 · Mezcal Negroni 15 · Spicy Pineapple Margarita 13 · Del Maguey Vida 11 · Modelo 7 · Lagunitas IPA 8 (6.2% ABV) · Tecate 5 · Nojito 7 · Jarritos 4 · House Cabernet 11 · Prosecco 10 |
| **claims not in DB** | "tequila class under NOM-006", "aged at least one year in oak. D.O. Tequila", "aged at least four years in oak" (VSOP). These are plausible category facts, but they are not PHG data |

**Question for Rob:**
- Are the 12 additions (mezcal, Mexican lagers, Jarritos, Nojito, Ranch Water and the rest) the *intended* cantina content?
- If yes, it resolves the reviewers' repeated "a cantina with no Mexican items" complaint and much of the accuracy cap. But it must enter `phg.menu_items` through the approved workflow first.
- Until then, the benchmark uses the DB content only.

### Glass Garden

- **Forbidden filler present:** "PLANTS · PEOPLE · POURS · POSSIBILITIES" (bottom left) is on Rob's banned list.
- **Other unapproved slogans:**
  - "Stranger Things Grow Here Too" (also a Netflix title, so an IP-adjacent risk)
  - "A more beautiful drinking world", "Curiosity grows here", "Drink deeper live brighter"
  - "Good wine grows better conversation", "Crisp days cold drinks brighter tomorrows"
  - the corner lists
- **Missing item-stack element:** no sensory descriptions. The stack is name + ingredients only.
- **Ice and garnish in ingredient lists:** "crushed ice" appears as an ingredient; ice and garnish must be modelled separately.
- **Ingredient order:** e.g. Greenhouse Spritz "gin · cucumber · elderflower · lemon · mint · sparkling wine". The modifier comes after cucumber, and soda/sparkling should come after citrus.
- **Duplicate names:** "Strawberry Fields" is both a $15 cocktail and a $7 NA drink, the same defect as The Last Round's "Second Chance".
- **Pricing gaps and overlap:** Sparkling Water has no price. "Zero Proof" and "Mocktails" are two sections doing one job.
- **Real producers named by an image model:** Raventós i Blanc, Domaine Vacheron, Meinklang, Terlano, Château de Plaisance, Broc Cellars, Matassa. These are **invented supplier listings until Rob confirms them.** "Gulp/Habitat" looks garbled.
- **Beer:** styles only, with no brewery, ABV or pour.

### Solstice

- **Serious name issue: "Strange Fruit"** is the title of Billie Holiday's anti-lynching song. It must not be used as a cocktail name.
- **Missing item-stack element:** no sensory descriptions. "Crushed ice" is listed as an ingredient.
- **Unapproved slogans:** "Fresh Ideas Higher Vibes", "A higher state of drinking", "Good drinks good company brighter tomorrows", "Natural wines. Real people.", "Bold flavors brighter days", plus the corner lists.
- **Conflicts with Glass Garden (same wine list):**

  | item | Solstice | Glass Garden |
  |---|---|---|
  | Rosé | 13 \| 52 | 14 \| 56 |
  | Mexican Lager | 7 | 8 |
  | Sparkling Water | 3 | no price |

  Neither is canonical without a manifest.
- **Same producer-invention risk** as Glass Garden.

## C. Visual redesign notes (content held fixed)

These are my observations. Rob's preference is recorded separately in D.

**Glass Garden:**
- **What works:**
  - The concept governs the geometry: greenhouse panes *are* the section panels.
  - The central vista (arch → fountain → door) gives depth and a resting point.
  - The coupe on the table is the one hero object.
  - This is the handoff's "reading pockets inside the artwork" executed well.
- **What doesn't:**
  - The panes are still rounded rectangles holding conventional rows.
  - Four corner micro-slogans and the card on the table compete with the vista.
  - Ingredient type is about 9 px at native size and would fail actual-size legibility.

**Solstice:**
- **What works:**
  - The strongest figure/ground on the page: an organic cream shape carves the reading field out of a collage of marble, sea and citrus.
  - The sun disc crosses the wordmark: one gesture, one display word.
  - Two short columns.
- **What doesn't:**
  - Slogan clutter in five places.
  - The right-hand micro-column (sun / leaf / "bold flavors") is decoration inside the reading field.

**Cantina six-panel:**
- **What works:** clear sections; descriptions present.
- **What doesn't:**
  - Six equal enclosures, six coloured banners, and numerals 1–6 that encode nothing.
  - The tile band and sunburst compete.
  - Long dotted leaders.
  - This is the numbered-module direction the handoff flags as risky (§8.1). Its lineage label ("round three") is unverified (D-16).

**Transferable to TEST-1 round 21+ (from Rob's two preferred pieces):**
1. One large photographic or collage field that *contains* the reading pockets, rather than a background behind rows.
2. A single hero object that is an actual drink.
3. The display word interacting with the gesture (Solstice sun/wordmark).
4. Zero slogans.

Code-drawn art cannot reach this craft level (that is logged). This direction needs raster art, which is blocked by the Canva download hosts (network policy) until they are allowed or assets are supplied.

## D. Rob's preference (recorded as preference, not validation)

Rob has repeatedly selected the Glass Garden / Solstice / expressive-scene family over the gridded Cantina modules and over our code-built TEST-1 rounds. That is binding direction for work built for Rob. It is **one stakeholder's judgement**, not evidence of guest performance, and the benchmark keeps it in `rob_preference.json`, outside the win count.

**Proposal for benchmark Arm D:** Solstice's structure, rebuilt on the locked TEST-1 manifest with exact HTML text. It is the closest silhouette to our best round (0.64), which makes it the cleanest test of "Rob-preferred structure vs KB-assisted". I'll confirm this with Rob before running.
