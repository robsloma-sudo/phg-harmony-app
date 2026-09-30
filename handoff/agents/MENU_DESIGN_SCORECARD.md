# Menu design scorecard

Set by Rob, 2026-09-28: "Scores need to be determined by upper-echelon design skill sets."

Every design proposal is scored by three reviewers: the **Design Critic** (visual craft), the **Menu Content
Reviewer** (content and prices) and the **Ingredient & Venue Accuracy Reviewer** (added by Rob 2026-09-28: ingredient
descriptions and accuracy, venue type, and how descriptions and prices are laid out; it may correct description text in
the design files from verified data). Each scores the criteria below from 0 to 100. A proposal can only be approved when
**each reviewer's average is above 80**. The database enforces this: `phg_design_proposal_review` refuses to approve
without it. **The averages are necessary, not sufficient:** a proposal must also pass every hard gate in section 1a
(no average can offset a failed gate) and must not regress on any criterion against the best-so-far version
(section 1b). A failed proposal comes back to the designer with the scores and notes, and the designer submits a new
version.

The designer must hand over the **layout geometry** (section 3), so alignment, margins and price columns are measured,
not guessed.

## 1. Criteria

| # | Criterion | Scored by | What 100 looks like | Automatic fail (score ≤ 40) |
|---|---|---|---|---|
| 1 | **Alignment and grid.** Lines line up | Critic | Every text line sits on one baseline grid; item names share one left edge per column; nothing is off by more than 1 px at print size | Visible ragged edges; items in one column start at different x positions |
| 2 | **Headers and subheaders** | Critic | One consistent style per level; headers and subheaders line up with the grid and with each other across columns and pages; clear hierarchy | Two styles for the same level; a header out of line with its column |
| 3 | **Price alignment and format** | Critic + Content | Prices in one aligned column (or one consistent inline style); same format everywhere ($ or no $, decimals or none); glass/bottle prices in their own aligned columns. A far-right price column is **not** automatically good (`fix_remote_prices`): it scores well only when eye travel is short (short measure, reduced column span) or the row grid is strong (leaders, row rules, tabular figures); otherwise move prices nearer the name | Prices at different x positions within a section; mixed formats; remote prices with long eye travel and no leader or row rule |
| 4 | **Colour palette and numbers** | Critic | A deliberate, eye-catching palette (2–4 colours plus neutrals) that fits the venue; contrast at least 4.5:1 for text; prices and numbers styled to stand out without shouting | Clashing or muddy colours; low-contrast text; default black-on-white with no intent |
| 5 | **Focal order and reading path** (was "Layout and flow") | Critic + Content | **Deliberate focal order and reading path:** one clear entry point, then a path the eye follows through sections; emphasis comes from hierarchy and grouping (scale, weight, enclosure, position within a group), never from a claimed "sweet spot" or prime-spot placement (`reject_sweet_spot_claim`: there is no universal gaze hot spot and attention is not sales; never score a placement as a revenue gain without POS evidence). Logical section order (for example cocktails → beer → wine → spirits → non-alcoholic); balanced columns and pages | Several competing focal points or none; sections in random order; the reader has to hunt; layout justified only by "golden triangle" / top-right folklore |
| 6 | **Margins and spacing** | Critic | Equal outer margins on all sides (within 1 mm at print); consistent gutters between columns; consistent space between sections and between items. Every empty area has a job (groups, separates, frames, emphasises or paces): **empty canvas is not good whitespace** (`whitespace_relational`, `fix_dead_space`) | Uneven margins; crowded edges; inconsistent gaps; large unused fields (content ending far above the bottom, columns ending at very different heights) |
| 7 | **Design elements that elevate it** | Critic | Purposeful dividers, ornaments, icons, textures or imagery that fit the venue and lift the menu above a plain list, without clutter. Every device survives the restraint check (section 1c) | No elements at all, or decoration that fights the content; device accumulation with no quiet zones |
| 8 | **Items, descriptions and ingredients** | Content | Every item has its proper name, a description, and its ingredient names (cocktails list spirit, modifiers, garnish; wine lists grape and region; beer lists style and ABV; spirits list type or age). Descriptions may be *written* by the designer, but only from known facts (the draft's ingredients and recipes, or the inputs); unknown ingredients are flagged `missing_ingredients` and asked for, never made up | Items missing descriptions or ingredients with no flag; any invented item or ingredient |
| 9 | **Prices match** | Content | Every price exactly matches the draft or the inputs (the automatic check also enforces this) | Any changed, missing or invented price |
| 10 | **Coherence** | Critic + Content | Everything reads as one design: typography, colour, spacing, tone and content all agree, on paper and on a phone | Parts look like different menus |

| 11 | **Ingredient accuracy** | Accuracy | Every printed ingredient, garnish, glass, serve, grape, region, style, ABV, age or brand traces to a real Supabase row or the inputs, spelled exactly as the source | Any printed fact with no source |
| 12 | **Description quality** | Accuracy | Guest language, appetising, one voice, right length; never just repeats the item name; no taxonomy wording | Descriptions that read like database classes or repeat the name |
| 13 | **Venue-type fit** | Accuracy | Reads as this venue (type, city, demographics): order and emphasis, correct Spanish/other-language use, expected categories, price tier | Menu could belong to any venue; wrong or misused language |
| 14 | **Descriptions and prices laid out together** | Accuracy | Description measure and breaks, price-to-name relationship, glass/bottle/pour labels, nothing orphaned or crowded, readable in print and on a phone | Prices detached from items; unlabelled glass/bottle prices; crowded or orphaned lines |

| 15 | **Design concept** (added by Rob 2026-09-28) | Critic | A bold, ownable big idea - a visual narrative or system rooted in the venue and its culture - executed so the menu is unforgettable | A tidy list with generic festive trim; no idea |
| 16 | **Art direction and image system** (added 2026-09-28 from the design KB) | Critic | A written creative thesis (one sentence, 4-7 concept words, an avoid-list) that every device traces to (`creative_thesis_required`); one illustration/collage grammar of line, perspective, detail range, grain and colour mapping (`illustration_family_grammar`); one image treatment rule set for contrast, saturation, crop, grain and edges (`image_treatment_system`); type and image reinforce, contrast or extend each other and the image could not be swapped for a generic one (`word_image_integration_pass`, image-substitution test); full-bleed art cropped on purpose, gaze and leading lines toward the menu content (`crop_with_intent`); art bleeds ≥ 3 mm past trim with text inside the safe inset (`bleed`); texture holds up at actual size and its contrast drops near text (`texture_reproduction_test`); paper, grain, ink and metallic effects justified by the concept, not generic fake texture (`materiality_supports_voice`) | No thesis; mixed illustration styles; stock-looking or swappable art; text fighting texture; edge slivers; generic grain or gold for its own sake |

Reviewers score Roger-Ebert tough: see handoff/designs/REVIEW_PROTOCOL.md for calibration anchors (60 = clean but
forgettable; 85+ = portfolio concept executed flawlessly; **90+ = stands beside Rob's reference boards** in
handoff/designs/references/rob-2026-09-28/; 95+ = among the best bar menus in the country).

- **Critic average** = mean of criteria 1, 2, 3, 4, 5, 6, 7, 10, 15 and 16.
- **Content average** = mean of criteria 3, 5, 8, 9 and 10.
- **Accuracy average** = mean of criteria 10, 11, 12, 13 and 14.

(Criteria 3, 5 and 10 are scored by both reviewers independently. Criteria 1-15 keep their numbers so earlier score
history still compares; criterion 16 is new from 2026-09-28 and has no earlier history.)

## 1a. Hard gates (pass/fail; no average can offset a failure)

From the design KB (`hard_gates`, `regressions_block_pass`). Every reviewer reports each gate in its lens as `pass` or
`fail`; one `fail` blocks approval whatever the averages are.

| Gate (KB key) | Checked by | Fails when |
|---|---|---|
| `content_integrity` | Content + Accuracy | any wrong, changed, missing or invented price, item or printed fact (criteria 9 and 11); any tagline, prop caption or side-rail text that states an item fact |
| `legibility` | Critic | any essential text (names, descriptions, prices, section heads) is unreadable at print size or on a phone |
| `accessibility` | Critic | any text fails 4.5:1 contrast **at its worst pixel over the art or texture behind it** (not against an average background colour); or meaning carried only by colour |
| `menu_item_association` | Critic + Content + Accuracy | any price or description reads as belonging to the wrong item, or a price is detached from its item (long eye travel with no leader or row rule) |
| `environmental_legibility` | Critic | essential content would be unreadable in the venue (dim bar light, glare, reversed small type, metallic ink on small text) |

## 1b. Per-dimension tracking and reversion

Do not optimise one number (`no_single_average`, `revert_allowed`). The Coordinator keeps the **best-so-far version**
and its per-criterion scores. Each new version states its revision hypothesis and is compared to the best-so-far
criterion by criterion; **any criterion that regresses is reverted** to the best-so-far treatment (or the regression is
justified and fixed in the next version). Newer is not better by default.

## 1c. Restraint check (`controlled_maximalism_pass`)

Before submitting, the designer lists every decorative device (ornaments, rules, textures, badges, taglines, props,
illustrations, effects) and removes 25% of them; only devices whose removal visibly hurts the concept, hierarchy or
function come back. Critics name at least one device to remove in every review. Rich is fine; uniform ornament, many
equal focal points and no quiet zones are not.

## 2. Scoring bands

| Score | Meaning |
|---|---|
| 95–100 | Among the best bar menus in the country |
| 90–94 | Stands beside Rob's reference boards (handoff/designs/references/rob-2026-09-28/) |
| 85–89 | Strong professional work; a top agency would sign it; minor polish only |
| 81–84 | Good; publishable |
| 60–80 | Competent but visibly amateur somewhere; fix before publishing |
| 0–59 | Not a professional menu |

## 3. Layout geometry the designer must include (`proposal.layout`)

```json
{"page": {"width_mm": 215.9, "height_mm": 279.4, "margins_mm": {"top": 15, "right": 15, "bottom": 15, "left": 15}},
 "grid": {"columns": 2, "gutter_mm": 8, "baseline_pt": 12},
 "palette": {"background": "#0F1A2B", "text": "#F4EDE1", "accent": "#E0A64B", "muted": "#9AA7B8"},
 "type": {"header": {"font": "Playfair Display", "size_pt": 22}, "subheader": {"font": "...", "size_pt": 14},
          "item": {"font": "...", "size_pt": 11}, "description": {"font": "...", "size_pt": 9}, "price": {"font": "...", "size_pt": 11}},
 "elements": [{"kind": "header|subheader|item_name|description|price|divider|ornament|image",
               "page": 1, "x_mm": 15, "y_mm": 32, "w_mm": 80, "h_mm": 6, "text": "...", "ref": "item id"}]}
```

## 4. Measured checks (reviewers run these on `layout.elements`)

- **Margins:** the smallest distance from any element to each page edge equals the declared margin (±1 mm), and all four are equal unless the brief says otherwise.
- **Left edges:** item names in one column share one `x_mm` (±0.3 mm).
- **Price column:** prices in one column share one right edge (`x_mm + w_mm`, ±0.3 mm).
- **Headers:** headers of one level share one size and one `x_mm` per column; their spacing above and below is consistent (±0.5 mm).
- **Spacing:** the gap between consecutive items in a section is constant (±0.5 mm).
- **Contrast:** text colour against background is at least 4.5:1 (WCAG), measured at the **worst pixel** of the art or
  texture behind each text element, not the average ground colour (hard gate `accessibility`).
- **Price-pair scan:** eye travel (price left edge − name right edge) as a fraction of column width; flag rows over ~40%
  with no leader or row rule (`fix_remote_prices`, hard gate `menu_item_association`).
- **Dead space:** flag large empty regions with no job, and columns ending at very different heights (`fix_dead_space`).
- **Bleed and safe area:** full-bleed art extends ≥ 3 mm past trim; all text sits inside the safe inset.
- **Content:** every item element has a description element; cocktail descriptions name their spirit and at least two further ingredients.
