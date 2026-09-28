# Suggestions for the lead developer (from the PHG Menu Designer)

Status: **proposals only. Nothing here has been applied to the app, the database or the Edge functions.** Rob relays
them to the lead developer for approval. Line numbers refer to `index.html` at build 18.49.12 (branch
`claude/phg-gallery-html-render-j246dy`, commit a694f05).

Every item below was found while designing against the real Menu Studio code and the live draft
(`phg.menu_projects` ddc4bb5b…), and was measured by the designer's scorecard self-check (`tools/selfcheck.mjs`).

| # | Priority | Area | One line |
|---|---|---|---|
| S1 | **Security, high** | Designer data access | The raw Menu Studio `sync_token` is readable through `phg_designer_query` inside `editor_state->'doc'->'phg'` |
| S2 | High | Designer hand-off | Approved proposals apply the document only; the designer's typography, colour, columns and size are dropped |
| S3 | High | Menu Studio layout | Trailing gaps count toward page height, so content can never reach the bottom margin |
| S4 | High | Menu Studio layout | Pinned (placed) sections and subsections lose their items: wrong `mdcFlowItems` arguments |
| S5 | High | Menu Studio layout | No price column above one column (forced inline), so scorecard criterion 3 fails on every multi-column menu |
| S6 | Medium | Menu Studio layout | Descriptions never wrap; long venue descriptions run into the next column |
| S7 | Medium | Menu Studio layout | Uneven header spacing: `+6 px` only after sections that end in a subsection |
| S8 | Medium | Designer access | Let the designer role execute `phg_design_doc_check` (read-only) for pre-flight |
| S9 | Medium | Harmony voice | Send a spoken menu to the designer as a structured `request_design` |
| S10 | Low | Menu Studio design | Section dividers and ornaments (scorecard criterion 7) |
| S11 | Low | Deploy | `netlify.toml`: keep `/.claude/*` unserved like `/handoff/*` |
| S12 | Medium | Menu Studio prices | A price-format option so one menu can print "11.5" or all ".00", not a mix |
| S13 | Medium | Menu Studio prices | Glass / bottle price columns: multi-price items as aligned columns with labels in the subheading |
| S14 | Medium | Menu Studio layout | Subhead / legend spacing, price separator, badge size and baseline |
| S15 | High | Menu Studio layout | Keep a subhead with its first items: a subhead can end a column while its items start the next |

---

## S1. Raw project token readable by the designer (security)

**Found:**

```sql
select public.phg_designer_query($q$ select editor_state->'doc' from phg.menu_projects $q$, 1, null)
```

This returns `doc.phg.sync_token` as a 64-hex string. `handoff/agents/MENU_DATA_ACCESS.md` says the gateway refuses
"the Menu Studio project token hash". The *hash* is refused, but the raw token rides inside the editor snapshot.
Anyone with gateway access could call `phg-menu-design` / `phg-menu-adapter` as that project, if they also have a
signed-in user.

The designer has not stored or repeated the token. `tools/handoff.mjs stripSecrets()` removes `doc.phg` from
everything the designer writes, and the saved example draft has it removed.

**Suggested fix (one of):**
- **(a)** Stop persisting `doc.phg.sync_token` in `editor_state`. The app already keeps the credential elsewhere
  (`mdcPhgCredential`).
- **(b)** Have `phg_designer_query` run against a view that strips it:
  `editor_state #- '{doc,phg,sync_token}'`, plus the same path under any history table.
- Rotate the current token for project ddc4bb5b after either fix.

## S2. Apply the designer's style with its document

`mdcDesignApply` (around line 13590) does:

```js
mdcRestore(JSON.stringify({doc:j.doc,style:MDC.style,size:MDC.sizeKey}));
```

The proposal's look is lost: fonts, sizes, colours, columns, margins, leader dots and page size. The designer sends it in
`p_changes.menu_studio = {size, style, preset}` (brief §5: "until Menu Studio stores a layout spec").

**Suggested change:**
1. `phg_design_take_approved` also returns `p.changes->'menu_studio'`.
2. The apply path uses it, keeping the current values when it is absent:

```js
var ms=(j.menu_studio&&j.menu_studio.style)?j.menu_studio:null;
mdcRestore(JSON.stringify({doc:j.doc, style: ms?ms.style:MDC.style, size: ms&&ms.size?ms.size:MDC.sizeKey}));
```

Undo already covers it, because `mdcRestore` plus `mdcCommit` snapshot the style too.

## S3. Trailing gaps create a phantom page

`mdcDraw` sets the page count with `y = mdcCursorEnd(cur) + M` (line 21055) after `cur.y += 6` (subsections) and
`cur.y += P.secGap` (every section). Those gaps are counted after the **last** section too. So:
- the lowest line on a one-page menu can never sit on the bottom margin (the scorecard measures equal margins ±1 mm);
- if you push content to the foot, a blank page 2 appears.

**Suggested change:** count the page from the last drawn line, not the trailing gap. Track
`cur.lastInk = Math.max(cur.lastInk||0, cur.y)` right after each item or heading is drawn, and use
`y = Math.max(cur.lastInk, cur.bandBottomInk) + M` for the page count. Undo, export and pagination are otherwise unchanged.

Until then, the designer pins a colophon footer (a placed, item-less section) on the bottom margin and justifies the
flow above it.

## S4. Placed blocks lose their items

`mdcDrawBlock` calls `mdcFlowItems(c, e.node.items, left, y, wAvail, skip)` (lines 16377, 16385, 16393), but
`mdcFlowItems` is `function mdcFlowItems(c, items, cur, held)` (line 16348). It receives a number as `cur`, so the items
of a pinned section or subsection are not drawn, and the returned `y` is the `left` value.

**Suggested change:** a small block-local flow:

```js
function mdcFlowItemsAt(c, items, x, y, w){
  var P=MDC.style.page;
  for(var i=0;i<items.length;i++){ y += mdcDrawItem(c, items[i], x, y, w) + P.itemGap; }
  return y;
}
```

Call it from the three sites. `mdcDrawItem` returns the item height (it already does in the flow version).

## S5. A right-aligned price column in multi-column layouts

`mdcDrawItem` (line 16106): `if (mdcColCount() > 1) inline = true;`. Every multi-column menu therefore prints
prices at ragged x positions. The scorecard (criterion 3, §4 "prices in one column share one right edge") caps that at
40.

**Suggested change:** respect `P.priceAlign` in columns too. Only force inline when the column is narrower than a
threshold, for example `colW < 220 px`:

```js
if (mdcColCount() > 1 && P.priceAlign !== 'right_always' && mdcColWidth() < 220) inline = true;
```

Alternatively, add a new `priceAlign: 'column'` option. Leader dots already work for right-aligned prices.

## S6. Wrap descriptions

`mdcDrawItem` draws `desc` as one `fabric.Text`, and `mdcItemHeight` reserves one line. The live draft's
Margarita description ("Tequila blanco, lime, orange liqueur, agave. Bright and citrus-forward.") overruns a letter-size
2-column layout by 71–116 px.

**Suggested change:** use `fabric.Textbox` with `width: colW` for descriptions. `mdcItemHeight` then needs the wrapped
line count, cached per item, style and width, so the page arithmetic stays in step with the drawing.

## S7. Consistent space above headers

`cur.y += 6` (line 21050) runs only after each subsection. A section that ends with a subsection is followed by 6 px
(1.6 mm) more space than a section that ends with plain items. The scorecard allows ±0.5 mm, so a mixed menu fails
criterion 2.

**Suggested change:** add the 6 px after a section's last block whichever kind it is, or drop it and let `secGap` do the
work. Do the same in `mdcSectionHeight` and `mdcBlockHeight`.

## S8. Let the designer run the automatic check

`phg_design_doc_check` is `STABLE` and read-only, but `phg_designer_query` refuses it: "permission denied for function".

**Suggested grant:** `grant execute on function public.phg_design_doc_check(jsonb,jsonb,jsonb) to phg_menu_designer;`

The designer could then pre-flight against the real rules, not only its local copy.

Related: the check casts `inputs.items[].prices` elements to numeric. Objects such as `{label, value}` make it error
rather than fail cleanly. The designer's voice payload sends plain numbers plus `price_labels`. The function could also
accept `{value}` objects.

## S9. Harmony voice → designer

Today a spoken request goes to `phg-language-interpreter`, and `menu_workflow` intents open the menu guide. Nothing sends
spoken items to the designer.

**Suggested flow** (user side of the Harmony viewport menu builder):
1. Bundle the designer's parser (`handoff/agents/menu-designer/tools/parse-voice.mjs` and `lexicon.mjs`: plain ES
   modules with no dependencies) into the app, or host it in an Edge function.
2. In `agentAnswer`, when the intent is `menu_workflow`, the Designer panel is available and the utterance contains
   prices or list words, call:
   ```js
   var p = phgMenuVoice.requestDesignPayload(text);   // {request, source:'user_prompt_flow', source_detail:'harmony_voice', inputs, _parser}
   // show p._parser.questions (missing prices, unplaced items) before sending
   mdcDesignRequest(p.request, p.source, p.source_detail, p.inputs);
   ```
3. `phg-menu-design` already whitelists `items`, `lists`, `venue`, `format`, `brand` and `constraints`.

`tools/run.mjs --transcript …` writes exactly this body to `request_design.json` for testing.

## S10. Design elements (scorecard criterion 7)

Menu Studio can draw rules (masthead only), badges, colour, weight and case, but no section dividers or ornaments.
The critic scores "no elements at all" low.

**Suggested small additions:**
- Style options `page.sectionRule` (hairline under each section head, 0.5–1 pt, rule colour).
- `page.ornament` (a glyph such as `✦` or `◆` centred between sections, drawn with the subtitle style).

Both are cheap in `mdcHeadBand` and `mdcSectionHeight`.

## S11. Deploy

`netlify.toml` blocks `/handoff/*`, `/supabase/*`, `/workers/*` and `/netlify.toml`, but not `/.claude/*`. That
folder holds the agent definitions.

**Suggested addition:**

```toml
[[redirects]]
  from = "/.claude/*"
  to = "/__not_found__"
  status = 404
  force = true
```

## S12. One price format per menu

`mdcPriceText` prints whole numbers bare and anything else with two decimals, so "14" and "11.50" appear on the same
menu. The critic scores mixed formats down (criterion 3).

**Suggested change:** add a style option `page.priceFormat`:
- `auto`: today's behaviour;
- `trim`: prints "11.5";
- `fixed2`: prints "14.00" everywhere;
- `half`: prints "11½".

Do not change the stored values.

## S13. Glass / bottle price columns

Items with several labelled prices print as "Glass 11 / Bottle 40" in the price position. Wine directors and the
scorecard expect a column for each label, with the labels printed once in the subheading row.

**Suggested change:** when a subsection's items share price labels, draw each label's value right-aligned in its own
column, and draw the labels once, beside the subheading. Use an en dash for a missing price.

The same applies to pour sizes (draft 10 oz / 16 oz / Pitcher; spirits 1 / 1.5 / 2.5 oz or 1.5 / 3 oz), which Rob wants
on every bar menu. Until then, the designer prints the labels once as the list's description line, prints the rows as
bare values ("9 / 13 / 20"), and keeps the labels in `meta.price_labels`. A `phg.menu_item_prices` pour-size column
would let costing, POS and the menu share the same pours.

## S14. Header and legend spacing, price separator, badge size (review panel round 1)

All 15 panel reviewers marked down three Menu Studio drawing rules that the designer cannot change from the file:

- **Space around subheads and heading descriptions.** `mdcDraw` advances a fixed 9 px after a subhead and 4 px after a
  heading description, and adds only 6 px after a subsection's last item. A pour legend ("Glass · Bottle",
  "1 oz · 1.5 oz · 2.5 oz") therefore touches the first item under it, and a section legend sits 0.55 mm above the next
  subhead. **Suggested change:** add `page.subGap` (space above a subhead, default 6) and `page.legendGap` (space after a
  heading description, default 4), both counted in `mdcSectionHeight` so the flow stays exact.
- **Price separator.** `mdcPriceText` joins prices with `'  /  '` (two spaces each side), which reviewers read as loose.
  **Suggested change:** a `page.priceSep` style option (`' / '`, `' · '`, thin-space slash), default unchanged.
- **Badge size.** HOUSE / SEASONAL / NEW badges are drawn at about 7 pt as raised small caps, which low-light reviewers
  could not read and typographers flagged as off the baseline. **Suggested change:** draw badges at
  `max(8.5pt, desc size × 0.8)` on the name's baseline.
- **Section order within the page plan.** The designer can only choose where columns and pages break; sections stay in
  list order. Letting a short final section (Zero Proof) fill the shorter column on its page would balance two-page menus.
- **Round 3 (high-altitude) repeat.** All 15 reviewers again read the raised 7 pt grey badges (HOUSE, SEASONAL, NEW)
  as superscripts off the baseline, too faint for bar light. The `mdcDrawItem` badge (index.html ~16091:
  `top: y + 2`, `fontSize: max(7, desc × 0.7)`, fill `style.sub.c`) is the whole cause. **Suggested change (same as
  above, now with a colour):** `top` on the name's baseline (`y + (name.s − badgeSize) × 0.8`), size
  `max(9pt, desc.s × 0.85)`, fill `style.desc.c` or darker, a fixed word-space before the price.

## S15. Keep a subhead with its first items (review panel round 3)

**Found:** `mdcDraw` (index.html ~21042) fits a subsection heading with `mdcCursorFit(cur, sh)`, the heading's own
height only. When the column target falls just after the heading, the heading prints at the foot of one column and
its items start the next column with no label. On High Altitude Brewing the CANS subhead sat alone at the bottom of
column 1 and "Summit Pils 4 Pack 16" opened column 2; every one of the 15 panel reviewers named it the worst defect on
the page (Design Theory 66, Beverage 66, Brand 68 mean).

**Designer workaround (in the toolkit now):** after fitting, the designer finds any subhead whose first two items land
in another column or page and promotes that subsection to its own section ("Beer · Cans"), which Menu Studio keeps
whole. It costs a level of hierarchy (the subsection becomes a section head).

**Suggested change:** reserve the heading plus its first two items (or all of them when fewer) before placing it:

```js
var keep = sh + sub.items.slice(0, 2).reduce(function (a, it) { return a + mdcItemHeight(it) + MDC.style.page.itemGap; }, 0);
mdcCursorFit(cur, keep);
```

Do the same for a section heading whose section is taller than a column (the `sh + name.s` branch at ~21018), and
count nothing extra in `mdcSectionHeight`, so page counts do not change.

