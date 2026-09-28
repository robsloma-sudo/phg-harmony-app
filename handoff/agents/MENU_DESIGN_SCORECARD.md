# Menu design scorecard

Set by Rob, 2026-09-28: "Scores need to be determined by upper-echelon design skill sets."

Every design proposal is scored by three reviewers: the **Design Critic** (visual craft), the **Menu Content
Reviewer** (content and prices) and the **Ingredient & Venue Accuracy Reviewer** (added by Rob 2026-09-28: ingredient
descriptions and accuracy, venue type, and how descriptions and prices are laid out; it may correct description text in
the design files from verified data). Each scores the criteria below from 0 to 100. A proposal can only be approved when
**each reviewer's average is above 80**. The database enforces this: `phg_design_proposal_review` refuses to approve
without it. A failed proposal comes back to the designer with the scores and notes, and the designer submits a new
version.

The designer must hand over the **layout geometry** (section 3), so alignment, margins and price columns are measured,
not guessed.

## 1. Criteria

| # | Criterion | Scored by | What 100 looks like | Automatic fail (score ≤ 40) |
|---|---|---|---|---|
| 1 | **Alignment and grid.** Lines line up | Critic | Every text line sits on one baseline grid; item names share one left edge per column; nothing is off by more than 1 px at print size | Visible ragged edges; items in one column start at different x positions |
| 2 | **Headers and subheaders** | Critic | One consistent style per level; headers and subheaders line up with the grid and with each other across columns and pages; clear hierarchy | Two styles for the same level; a header out of line with its column |
| 3 | **Price alignment and format** | Critic + Content | Prices in one right-aligned column (or one consistent inline style); same format everywhere ($ or no $, decimals or none); glass/bottle prices in their own aligned columns | Prices at different x positions within a section; mixed formats |
| 4 | **Colour palette and numbers** | Critic | A deliberate, eye-catching palette (2–4 colours plus neutrals) that fits the venue; contrast at least 4.5:1 for text; prices and numbers styled to stand out without shouting | Clashing or muddy colours; low-contrast text; default black-on-white with no intent |
| 5 | **Layout and flow** | Critic + Content | The eye moves naturally: best sellers and high-margin items in the prime spots; logical section order (for example cocktails → beer → wine → spirits → non-alcoholic); balanced columns and pages | Cramped or empty areas; sections in random order; the reader has to hunt |
| 6 | **Margins and spacing** | Critic | Equal outer margins on all sides (within 1 mm at print); consistent gutters between columns; consistent space between sections and between items | Uneven margins; crowded edges; inconsistent gaps |
| 7 | **Design elements that elevate it** | Critic | Purposeful dividers, ornaments, icons, textures or imagery that fit the venue and lift the menu above a plain list, without clutter | No elements at all, or decoration that fights the content |
| 8 | **Items, descriptions and ingredients** | Content | Every item has its proper name, a description, and its ingredient names (cocktails list spirit, modifiers, garnish; wine lists grape and region; beer lists style and ABV; spirits list type or age). Descriptions may be *written* by the designer, but only from known facts (the draft's ingredients and recipes, or the inputs); unknown ingredients are flagged `missing_ingredients` and asked for, never made up | Items missing descriptions or ingredients with no flag; any invented item or ingredient |
| 9 | **Prices match** | Content | Every price exactly matches the draft or the inputs (the automatic check also enforces this) | Any changed, missing or invented price |
| 10 | **Coherence** | Critic + Content | Everything reads as one design: typography, colour, spacing, tone and content all agree, on paper and on a phone | Parts look like different menus |

| 11 | **Ingredient accuracy** | Accuracy | Every printed ingredient, garnish, glass, serve, grape, region, style, ABV, age or brand traces to a real Supabase row or the inputs, spelled exactly as the source | Any printed fact with no source |
| 12 | **Description quality** | Accuracy | Guest language, appetising, one voice, right length; never just repeats the item name; no taxonomy wording | Descriptions that read like database classes or repeat the name |
| 13 | **Venue-type fit** | Accuracy | Reads as this venue (type, city, demographics): order and emphasis, correct Spanish/other-language use, expected categories, price tier | Menu could belong to any venue; wrong or misused language |
| 14 | **Descriptions and prices laid out together** | Accuracy | Description measure and breaks, price-to-name relationship, glass/bottle/pour labels, nothing orphaned or crowded, readable in print and on a phone | Prices detached from items; unlabelled glass/bottle prices; crowded or orphaned lines |

- **Critic average** = mean of criteria 1, 2, 3, 4, 5, 6, 7 and 10.
- **Content average** = mean of criteria 3, 5, 8, 9 and 10.
- **Accuracy average** = mean of criteria 10, 11, 12, 13 and 14.

(Criteria 3, 5 and 10 are scored by both reviewers independently.)

## 2. Scoring bands

| Score | Meaning |
|---|---|
| 95–100 | Portfolio-grade; a top agency would sign it |
| 85–94 | Strong professional work; minor polish only |
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
- **Contrast:** text colour against background is at least 4.5:1 (WCAG).
- **Content:** every item element has a description element; cocktail descriptions name their spirit and at least two further ingredients.
