# PHG Menu Designer: running skills and learning log

**Purpose:** a running record of what this designer agent is, what it can do, what it built and what it learned.
It is written so the next agent can pick up exactly where this one left off.
**Append a dated entry for every working session. Never rewrite history.**

Role: create-only menu designer for the **user side of the Harmony viewport menu builder** (not the admin side).
Boundaries: `../MENU_DESIGNER_BRIEF.md` and `.claude/agents/menu-designer.md`. Data: `../MENU_DATA_ACCESS.md`.
Scoring: `../MENU_DESIGN_SCORECARD.md`. Each of the two reviewers must average above 80.
Chain of approval: designer → Coordinator → review agents → Rob → lead developer. **The designer never changes the app.**

---

## Current skill set (keep this section up to date)

| Skill | Level | Where it lives | Evidence |
|---|---|---|---|
| Voice transcript → structured menu input | Solid | `tools/parse-voice.mjs`, `tools/lexicon.mjs` | 39 regression tests (`tools/test.mjs`) |
| Hand-off contract (tasks, proposals, checks) | Solid | `tools/handoff.mjs` | local `docCheck` agrees with `phg_design_doc_check` on price/name cases |
| Designing from the venue's real draft | Good | `tools/draft.mjs` | live project ddc4bb5b: all 15 item ids, recipe links and meta kept |
| Descriptions from known facts only | Good | `draft.mjs describeFromComponents`, `tools/standards.mjs` | respects `public_visibility` and `public_components` (e.g. hidden bitters) |
| Look selection (venue × tone × census) | Good | `tools/design.mjs rankLooks`, `styles/looks.mjs` | 10 looks, all inside Menu Studio's model |
| Page fitting in Menu Studio's own flow | Strong | `tools/layout.mjs` (port of `mdcDraw` / `mdcCursorFit`) | the real app renders the files identically (`tools/studio-check.cjs`) |
| Composition (fill, balance, measure, justify) | Good | `design.mjs fit` | margins within ±1 mm with a pinned footer |
| Rendering: 300 dpi PNG, trim and bleed PDFs, phone | Strong | `tools/render.mjs` | full resolution, never downscaled |
| Scorecard geometry (`p_layout`) | Strong | `render.mjs measureLayout` | x/width measured in the browser; y/height from the Fabric model |
| Scorecard self-check (§4 measured checks and content) | Strong | `tools/selfcheck.mjs` | runs on every option before hand-off |
| Menu engineering and design theory | Studied | `knowledge/01–03` (53 sources) | rules adopted listed below |
| Library research (comparables, census) | Working | `references.sql` via `phg_designer_query` | Denver comparables #7374 #10810 #3373 #11712 |

**Known weak spots (be honest):**
- **Design elements (criterion 7).** Menu Studio draws no ornaments. See suggestion S10.
- **Multi-column price column.** The app forces prices inline above one column. See S5.
- **Header spacing.** The app adds 6 px only after sections that end in a subsection. See S7.
- **Descriptions don't wrap.** See S6.
- **Voice gaps.** Voice notes usually lack descriptions, ABV and region. The designer asks rather than invents, so the Content Reviewer's criterion 8 depends on the venue answering.
- **Research gaps.** Census covers CO, IA and NY only. No sources yet on the visual language of Latin cantinas, dive bars or hotel bars.

---

## Log

### 2026-09-27 — Session 1: toolkit v1

- Mapped Menu Studio in `index.html`:
  - the `MDC` model;
  - `MDC_FONTS` / `MDC_PRESETS` / `MDC_SIZES` / `MDC_BADGES`;
  - the flow in `mdcDraw` / `mdcCursorFit`;
  - `.menu.json` (schema_version 2);
  - Harmony voice (`phg-speech-transcribe` → `phg-language-interpreter` → `agentAnswer`);
  - the reserved purple `#6b4fa8` for seeded prices.
- **Built:**
  - the voice parser;
  - the design engine with 10 looks;
  - the port of Menu Studio's layout;
  - the Chromium renderer with 300 dpi PNG, PDF, print PDF with bleed and crop marks, and phone preview;
  - a proposal builder;
  - `studio-check.cjs`, which loads a design into the real app headlessly.
- **Proved:** Menu Studio loads and draws the generated files. Its canvas matched the previews line for line.
- **Learned the hard way:**
  - Item names must never set page directions ("Double **Black** Diamond", "**Night**fall Stout").
  - Spoken "twelve fifty" is 12.50, not 62.
  - "that's our house special" belongs to the previous item.
  - `file://` fonts do not load in `about:blank` pages, so fonts must be inlined.
  - Per-font character widths must be measured, not guessed.
- Library benchmarks (`phg_menu_doc_class`): cocktails median 10 / p80 18; beer 8 / 20; wine 8 / 18; non-alcoholic 4 / 16.
  Median prices: cocktail 14, beer 7, spirit pour 14.

### 2026-09-28 — Session 2: integration with the live hand-off, research, scorecard

- Rebased onto `claude/phg-gallery-html-render-j246dy`. Took the backend's brief and agent definition, which are
  authoritative. Left `netlify.toml` alone (the app is not ours to change) and filed suggestion S11.
- **Hand-off integration** (`tools/handoff.mjs`):
  - Voice becomes the `request_design` body: `source: 'user_prompt_flow'`, `source_detail: 'harmony_voice'`.
    `inputs.items[].prices` are **plain numbers** (the database check casts them), with `price_labels` alongside.
  - A task row becomes the designer's request.
  - A proposal becomes the `phg_design_proposal_submit` arguments, including `p_layout`. The style travels in
    `p_changes.menu_studio`.
  - `stripSecrets` removes `doc.phg`: the sync token never leaves the designer.
- **Draft-aware design** (`tools/draft.mjs`):
  - Keeps item ids and recipe links.
  - Merges voice items and edits ("put the House Daiquiri first" is an edit, not a new item).
  - Writes descriptions from recipe components, honouring visibility settings.
  - Asks for ABV, region or spirit detail instead of inventing them.
- **Scorecard:**
  - `p_layout` geometry is measured in the browser.
  - `selfcheck.mjs` implements every §4 check.
  - The composer now prefers one column (the only right-aligned price column Menu Studio can draw) and penalises
    lines wider than their column by pixels.
  - A justification solver lands the last line on the bottom margin.
  - A pinned colophon footer (city/state or supplied legal lines only) works around the phantom-page behaviour (S3).
- **Found and filed** in `SUGGESTIONS_FOR_LEAD_DEV.md` (S1–S11):
  - the raw sync token is readable through the gateway (**security**);
  - apply drops style;
  - trailing gaps make a phantom page;
  - placed blocks lose their items (wrong `mdcFlowItems` arguments);
  - prices are forced inline in columns;
  - descriptions don't wrap;
  - the +6 px header quirk;
  - no designer `EXECUTE` on the check;
  - no voice → designer wiring;
  - no ornaments;
  - `/.claude/*` is served.
- **Research:** 53 sources, in three evidence files. Rules adopted *in code* this session:
  - **Edge placement** (Dayan & Bar-Hillel 2011, +20% first or last in category): first promoted item leads,
    second closes (`design.mjs promote`, `draft.mjs` step 4).
  - **No golden triangle** (Yang 2012; Kincaid & Corsun 2003): no "top-right sweet spot" logic. Book-order reading
    is assumed, and salience (accent colour plus badge) is used sparingly.
  - **Prices:** numerals only, no "$" and no ".00" (Yang, Kimes & Sessarego 2009). Menu Studio already prints this way.
  - **Beer lines:** "style/description · ABV%" (Cellarmaker convention).
  - **Caps tracking:** capped at 180/1000 em for headers and 300 for the title (Butterick 5–12%).
  - **Type floors:** names and prices 10.5 pt, descriptions 8.25 pt, labels 6.75 pt (Butterick 10–12 pt body,
    Sensory Trust 12 pt clear print).
  - **Contrast:** 4.5:1 for every text level, title included (scorecard §4, WCAG).
  - **Fonts:** no Trebuchet (Butterick's avoid list). No Georgia for prices (oldstyle figures).
  - **Descriptions:** classic specs are used only when the venue has no recipe, and are labelled `standard` (MENU_DATA_ACCESS).
- **Research rules not yet applied (next):**
  - Kasavana–Smith classification from `phg.menu_engineering_snapshots` to decide which items to feature.
  - Strength markers.
  - Zero-proof symbol on convertible cocktails.
  - By-the-glass pour size.
  - The standard footer block for legal lines (currently only supplied lines are printed).
  - The TV board size rule: 1" of cap height per 15 ft.
  - QR code size: 2×2 cm minimum.
- **Review rounds 1–3** (full detail in `REVIEW_LOG.md`), reviewed by independent agents using the backend's role files:
  - **Content Reviewer:** 72.6 → 80.0 → **85.6 (passes)**.
  - **Design Critic:** 53.4 → 64.1 → 69.3. Every measured check passes. It is capped by Menu Studio's price printing
    (S12/S13) and the absence of ornaments (S10).
- **Techniques learned from the reviews:**
  - **Flat sections for small fresh menus.** Menu Studio's +6 px after subsections makes header spacing uneven, so
    the subsection facts move into each item's line.
  - Section headers at least 1.3× the item size.
  - Leader dots for wide single columns.
  - Non-alcoholic last.
  - Merge one-item lists.
  - Category-specific questions.
  - `needs_input` whenever content is missing.
  - Change notes must describe what is actually printed.
  - Don't repeat the style that is already in the name.
  - Keep gold for headers and the house item; don't use it for every price.
- **Bugs found by testing myself:**
  - v1 fitting ran every remedy at once (`steps.map`). Now one at a time.
  - The badge sits 2 px low (Menu Studio draws it at `y + 2`); the self-check now allows for it.
  - A regex swallowed the next sentence ("RiNo. For").
  - The footer was not pinned on one code path.

---

## How to continue (for the next agent)

1. Read the brief, `MENU_DATA_ACCESS.md`, the scorecard, then `PLAYBOOK.md`, `knowledge/`, this log and `SUGGESTIONS_FOR_LEAD_DEV.md`.
2. Run the regression tests: `cd tools && node test.mjs` (they must all pass). Then try an example:
   `node run.mjs --transcript-file ../examples/casa-luna.voice.txt --venue-type latin_cantina --city Denver --state CO --zip 80205 --demographics ../examples/denver-80205.census.json --comparables ../examples/denver-cantina.refs.json --standards ../examples/classic-specs.json --out ../out/casa-luna`
3. For a real task: read the task row through `phg_designer_query`, then `node run.mjs --task-row task.json …`. Check
   `SUMMARY.md`, every `page-N.png` at full size, and `selfcheck.json`. Run `studio-check.cjs` on the chosen option.
   Hand `submit.json` to the Coordinator.
4. Never apply anything to the app. App changes go into `SUGGESTIONS_FOR_LEAD_DEV.md` for Rob.
5. Append to this log.

### 2026-09-28 — Session 2b: pour sizes and full-bar menus

Rob asked for draft beer and spirits in several pour sizes, each priced, plus a full menu: 5 house and 5 classic
cocktails, wines, beers, non-alcoholic drinks and mocktails.

**Built:**
- **Pour schemes in the voice parser.** A sentence such as "spirits are poured one, one and a half and two and a half
  ounces", "whiskey pours are one and a half and three ounces" or "draft beers come in ten ounce, sixteen ounce and
  pitchers" sets that list's ladder. It applies to the list or lists named, to every spirit list for "spirits", and to
  Beer › Draft for "draft".
- **Priced items.** An item followed by a run of bare prices takes the ladder's labels in order. A count mismatch
  becomes a question ("Which price goes with which pour?").
- **New lists and subsections.** Mocktails is its own list. Cocktails › House / Classics come from "house cocktails:" and
  "classic cocktails:". A generic "spirits" list was added.
- **Pour headers.** When every item in a list shares the same labels, the labels print once as the list's description
  line ("1 oz · 1.5 oz · 2.5 oz", "Glass · Bottle") and the rows print bare values ("9 / 13 / 20"). If every subsection
  shares them, they go under the section heading. Values never change; the labels stay on each item in
  `meta.price_labels`.
- **Wine grouped by style from the grape named** (Sauvignon Blanc → White, Malbec → Red): Sparkling → White → Rosé → Red.
- **One Spirits section** with a subsection per list when there are three or more small spirit lists.
- **Mocktails right after cocktails** (zero-proof as a peer: Dandelyan, NoMad); soft drinks last.
- **Multi-page planner.** It picks, without reordering, which section starts each column and page, using Menu Studio's
  own `breakCol` / `breakBefore` flags. With the plan fixed it grows type while everything still fits.

**Parser bugs fixed:**
- **False subsection labels.** A style word that is really part of an item ("Margarita, blanco tequila…") had been
  opening a subsection. Such words now open one only when spoken as a label: a colon, "we have", standing alone, or a
  comma followed by a Capitalised name. Serve formats (draft, cans, bottles, by the glass) are always subsections.
- "Fever-Tree Ginger Beer" is not beer.
- "New Zealand" no longer trips the "new" flag.

**Example:** `examples/sample-bar.voice.txt`, the fictional *PHG Sample Bar* (sample content, not a venue): 45 items,
13 lists, two letter pages. Regression tests now number 57.

**Still open:**
- Page 1 keeps spare space at the foot. The tallest slot (Spirits + Zero Proof) caps the page-wide type size.
- Menu Studio can't print pour prices as true columns under their headings (S13).
- Multi-page menus are not justified to the bottom margin.
