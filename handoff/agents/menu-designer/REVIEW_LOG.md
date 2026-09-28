# Design review log: PHG Menu Designer proposals

The gate (`../MENU_DESIGN_SCORECARD.md`): **each** reviewer's average must be **above 80**.
Nothing goes live until it passes. The reviewers here are independent agents running the backend's role files
(`.claude/agents/design-critic.md`, `.claude/agents/menu-content-reviewer.md`) against the real proposal files.

## Casa Luna (voice note, Latin cantina, Denver 80205), option A "Speakeasy Noir"

| Round | Design Critic | Content Reviewer | Gate |
|---|---|---|---|
| 1 | 53.4 | 72.6 | ✗ |
| 2 | 64.1 | 80.0 | ✗ (80.0 is not above 80) |
| 3 | 69.3 | **85.6 ✓** | ✗ (critic) |

### Round 1 → 2: what the reviewers found and what changed

- **Critic.**
  - Headers were the same size as item names. **Fix:** section headers at least 1.3× the name size.
  - Eye travel of 188 mm with no leaders. **Fix:** leader dots on wide single columns.
  - Zero Proof sat mid-menu. **Fix:** non-alcoholic goes last.
  - "Denver, CO" appeared twice. **Fix:** the subtitle lists the offerings; the footer shows the neighbourhood and city.
  - Dead band above the footer. **Fix:** tighter footer break.
  - The declared baseline grid wasn't followed. **Fix:** honestly declare none.
  - The palette read as generic noir. **Fix:** a second accent (copper) for subheads and badges.
- **Content.**
  - Generic questions. **Fix:** category-specific ones.
  - Submitted with 11 items undescribed. **Fix:** `needs_input` when content is missing.
  - One-item Mezcal section. **Fix:** Tequila & Mezcal share a section.
  - "By the glass" with a bottle price. **Fix:** renamed.
  - The standard spec wasn't confirmed. **Fix:** confirmation question added.

### Round 2 → 3

- **Critic** measured the header-spacing spread as 1.46 mm: only Cocktails ended on items, while every other section
  ended on a subsection, and Menu Studio adds 6 px after subsections.
  **Fix:** flat sections for small fresh menus. The subsection name moves into each item's line as a fact ("Draft ·",
  "Blanco tequila"). **All measured geometry checks now pass on all three options.**
- **Critic** also said two columns with inline prices is one consistent style. **Fix:** the self-check tests inline
  consistency, and the composer no longer over-favours one column.
- **Critic:** the sub level was too small. **Fix:** at least 8.25 pt.
- **Critic:** the phone and print footers differed. **Fix:** they now match, and the phone title fits one line.
- **Content:**
  - Asked for facts already given. **Fix:** "Blanco tequila", "IPA · 6.2% ABV" and the grape come from the inputs.
  - Mixed description styles. **Fix:** one house style (serial list, hyphenation), with the words unchanged.
  - The new Mezcal Negroni sat mid-list. **Fix:** it takes the closing edge.
  - "RINO" in forced capitals. **Fix:** keep the venue's casing.

### Round 3 result

**Content Reviewer 85.6: passes.**
- Remaining notes:
  - Descriptions still missing until the venue answers.
  - The change list described subsections that were later folded away. **Fixed:** the notes now match what's printed.
  - "IPA" was repeated from the name. **Fixed.**

**Design Critic 69.3.** All §4 measurements pass: margins, left edges, price right edge, header sizes and spacing,
item gaps, and contrast (6.2:1 or better). The scores are held down by:
- **Criterion 3 (capped at 40): mixed price formats.** "11.50" among whole numbers, and "Glass 11 / Bottle 40" inline.
  Both come from Menu Studio's price printing (S12, S13) or would need the venue to restate prices. The designer may
  not change values.
- **Criterion 7 (50):** no ornaments or dividers in Menu Studio (S10).
- **Taste notes:** wide single-column leaders; gold overused; subtitle repeating the section list; footer band.

**Applied after round 3:**
- two columns preferred when one column would be wider than about 6.7 in;
- the footer break equals one section gap;
- cream prices, with gold kept for headers and the house item;
- a "Cantina · RiNo" subtitle, from the venue type and neighbourhood the speaker gave.

**Arithmetic:** with criterion 3 at 40 and criterion 7 at 50, the other six criteria would need an average of about
95 for the critic to exceed 80. **The Design Critic gate for this menu is blocked by Menu Studio (S10, S12, S13) plus
the venue's missing answers, not by the layout.** The next round should run after the venue answers the questions,
or after the lead developer ships S12/S13.

### Known ceilings (not fixable by the designer; filed as suggestions)

- **Criterion 7, design elements:** no ornaments or section rules in Menu Studio (S10).
- **Criterion 3, price format:** 11.50 among whole numbers (S12); glass/bottle columns (S13).
- **Criterion 8, descriptions:** until the venue answers the questions, 7 items print without a description. This
  is correct behaviour; the gate should pass once the answers arrive.
