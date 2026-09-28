# Graphic design, typography, grids and colour: evidence base

Read on 2026-09-28. Access: web pages fetched through the Firecrawl scrape tool (full page markdown, or a targeted question run against the full page text or PDF text where marked "queried"). Direct WebFetch to practicaltypography.com was blocked by the egress proxy, so Firecrawl was used. Each source below says how much of it was read. Nothing here is taken from memory of a book I did not open, except where it is flagged as **[my note]**.

**Not read (attempted, failed):** Ellen Lupton, *Thinking with Type* (the companion site thinkingwithtype.com gave a tunnel error or 404, and the PDF timed out). Material Design type-scale pages (m3/m2): the scale tables are rendered by JavaScript and were not in the scraped text. Hochuli, Tschichold and Bringhurst's printed book were not read directly. Bringhurst is covered only through the quotations on webtypography.net.

---

## Sources

### 1. Butterick's Practical Typography
- **Author / year:** Matthew Butterick, online book (2nd ed., continuously updated; pages read 2026-09-28)
- **URL:** https://practicaltypography.com/ (pages: typography-in-ten-minutes, summary-of-key-rules, letterspacing, headings, all-caps, bold-or-italic, mixing-fonts, system-fonts, color, rules-and-borders, centered-text, grids, maxims-of-page-layout, space-above-and-below, page-margins)
- **Type:** free online book. **Read:** those 15 pages in full.
- **Principles**
  1. **Get the body text right first.** Four choices decide how it looks: point size, line spacing, line length and font. Print body text is **10–12 pt**, web body text is **15–25 px**, and line spacing is **120–145 %** of the point size. Line length should average **45–90 characters**, or 2–3 lowercase alphabets.
  2. **Caps:** fine for less than one line. Always add **5–12 % letterspacing** to all caps and small caps (CSS `0.05em`–`0.12em`; in Word, 0.6–1.4 pt per 12 pt). This matters most at small sizes. "If the spaces between letters are large enough to fit more letters, you've gone overboard." Don't letterspace lowercase, except that text **below about 9 pt** can take a little, and large lowercase headlines can have some spacing removed. Never use fake small caps.
  3. **Bold or italic, not both, and as little as possible.** With a serif font, italic gives gentle emphasis and bold gives heavy emphasis. With a sans serif, skip italic and use bold, because sans italics barely stand out.
  4. **Headings:** use at most 3 levels, and 2 is better. Don't set heading sentences in caps. Don't underline. Center sparingly. **Space above and below** is the best emphasis. Bold beats italic. Increase size only "just a little", for example 12 → 12.5–13 pt rather than 14–15. With a heavy bold you can even *reduce* the size by 0.5–1 pt. Put more space above a heading than below it, because a heading belongs to the text that follows. Heading spacing must be larger than the space between paragraphs.
  5. **Mixing fonts:** you never have to mix. "Most documents can tolerate a second font. Few can tolerate a third. Almost none can tolerate four or more." Any two identifiably different fonts can work, and serif + sans is not required. Lower contrast between fonts can work better. Give each font one consistent role, and change fonts only at paragraph breaks.
  6. **System-font ranking** (for our 8 fonts): *A list, "generally tolerable"*: **Avenir ★, Helvetica ★, Palatino ★** (★ = plausible for body text). *C list, "questionable"*: **Century Gothic, Courier, Georgia**, Times New Roman ★. *F list*: **Trebuchet MS**. Georgia is described as screen-optimised, and such fonts look "clunky" in print.
  7. **Colour:** black is best for printed body text. "Multiple shades of one color are usually better than multiple contrasting colors." A thin or small font can carry a more intense colour than a heavy or large one. Coloured type on a coloured background is usually regretted. The eye separates light colours more easily than dark ones, so dark colours need bigger adjustments. Red is the traditional second colour, and it looks best made slightly orange. On screen, dark grey text can be more comfortable than black.
  8. **Rules and borders sparingly.** Try extra space first. Borders should be **0.5–1 pt**. Avoid patterned borders (dots, dashes, doubles). Rules have more latitude. Put a heading rule *above* the heading, not below it. Never build rules out of typed characters.
  9. **Layout maxims:** decide the body text first. Split the page into foreground and background; your tools are position, size, font and sometimes colour. Adjust in the smallest visible increments. Be consistent: "things that are the same should look the same." Relate each new element to the ones already placed. Keep it simple. Don't fear white space, and work outward from the text.
  10. **Margins and grids:** at 12 pt, side margins of 1.5–2.0″ on letter paper. Make the bottom margin about 0.25″ larger than the top, or the block looks like it is sagging. An asymmetric layout needs a left/right margin difference of at least 1″. A coarser grid gives more consistency. The eye is the final judge.
- **Menu application:** item names and descriptions are the "body text", so set them first (print 9–11 pt; phone 15–17 px). Section labels in spaced caps are the textbook case of "less than one line of caps". Use one or two fonts in fixed roles. Favour Avenir, Helvetica and Palatino. Use Georgia, Century Gothic and Courier only deliberately, and avoid Trebuchet. Separate sections with space before reaching for rules.

### 2. The Elements of Typographic Style Applied to the Web (Bringhurst, adapted by Rutter)
- **Author / year:** Richard Rutter, quoting Robert Bringhurst's *The Elements of Typographic Style*; site c. 2005–2020
- **URL:** http://webtypography.net/ (sections 2.1.2, 2.1.6, 2.2.1, 2.2.2, 3.1.1, 3.2.2)
- **Type:** free website (Bringhurst quotations plus commentary). **Read:** those 6 sections in full. The Bringhurst text is a quotation, not the whole book.
- **Principles**
  1. **Measure:** "Anything from 45 to 75 characters is widely regarded as a satisfactory length of line… The 66-character line… is widely regarded as ideal. **For multiple column work, a better average is 40 to 50 characters.**" On average one character is about 0.5 em wide, so 33 em ≈ 66 characters.
  2. **Letterspace all strings of capitals and small caps**, and long strings of digits, by **5–10 % of the type size**. Don't letterspace lowercase without a reason.
  3. **Leading** is the page's basic rhythmic unit. Text usually benefits from 1.3 or more on screen; the site itself uses 1.5. Negative leading (<1) is acceptable on short display lines if ascenders and descenders don't collide.
  4. **Add and delete vertical space in measured intervals.** Headings, notes and gaps should take up whole multiples of the base line height. Example: with a 12/18 base, a 14 px heading gets line-height 18/14 = 1.286. Asymmetric heading margins are fine if they add up to a multiple (for example 1.5 lines above and 0.5 below).
  5. **Don't compose without a scale.** Use a "modest set of distinct and related intervals". Example scale in px: 12 / 14 / 18 / 24 / 36.
  6. **No fake small caps.** Real small caps differ in weight and fit, so shrunken full caps are "a parody".
- **Menu application:** in 2–3 column menus, keep description lines at about 40–50 characters. Size gaps between sections as whole multiples of the item line height, so every column shares one vertical rhythm. Use a fixed size ladder such as 9 / 11 / 14 / 18 / 24 pt. Track caps section heads 50–100/1000 em.

### 3. Web Typography, sample chapter "Numerals and tables"
- **Author / year:** Richard Rutter, *Web Typography* (Ampersand Type, 2017)
- **URL:** https://book.webtypography.net/Web-Typography_Numerals-and-tables.pdf
- **Type:** free sample chapter (26 pp PDF). **Read:** queried the full text.
- **Principles**
  1. Use oldstyle numerals in running text. Use **lining numerals where numbers are the focus**, as in lists and tables, because their evenness helps scanning and comparison.
  2. **Tabular (equal-width) figures** align vertically. Use tabular lining figures in tables.
  3. **Right-align numeric columns** so magnitudes compare when scanning down. Align on the decimal point when precision varies.
  4. Avoid frames or borders around tables. Shape them with alignment, spacing and grouping. Use rules "judiciously, preferably not at all". Add vertical rules only when the columns are so close that misreading would happen.
  5. Avoid zebra striping, tints and fills. Left-align text columns and don't justify narrow columns.
  6. Match header alignment to the data below it: right for numbers, left for text.
- **Menu application:** the price column is a table. Right-align prices to a shared edge, keep price formats consistent (all "12" or all "12.00"), and prefer fonts with lining figures for prices. **[my note]** Georgia's default figures are oldstyle, so prices set in Georgia bounce. Palatino, Helvetica and Avenir default to lining figures. Use leader dots *or* whitespace to link name to price, and don't add boxes around them.

### 4. Grid Systems in Graphic Design
- **Author / year:** Josef Müller-Brockmann, 1981 (Niggli). English/German edition PDF on Monoskop.
- **URL:** https://monoskop.org/images/a/a4/Mueller-Brockmann_Josef_Grid_Systems_in_Graphic_Design_Raster_Systeme_fuer_die_Visuele_Gestaltung_English_German_no_OCR.pdf
- **Type:** book (PDF). **Read:** only the first 50 of 162 pages were parsed, and I queried them (sections: typographic grid, width of column, leading, margin proportions, page numbers, body and display faces). These are **excerpts, not the whole book**.
- **Principles**
  1. **Column width:** "7 words per line… If we want to have 7–10 words per line…" A column reads easily at "an average of 10 words per line". Columns that are too long weary the eye. Columns that are too short break the reading flow.
  2. **Leading:** lines set too close make the eye "double" (read adjacent lines at once), and the type looks too dark. Lines set too far apart make it hard to find the next line. Good leading carries the eye from line to line.
  3. **Grid fields:** a field's depth is a whole number of text lines. "The vertical distance between the fields is 1, 2 or more lines of text."
  4. **Body sizes:** "Sizes of 8 to 12 points are usually right for the texts of books, brochures and catalogues." Size steps must be unequivocal: "The 9-point face is immediately distinguishable from the 6-point face."
  5. **Weights** create grey values: medium gives a light grey area, semi-bold a medium grey, bold a deep grey. Use these distinct steps for hierarchy.
  6. **Don't mix similar faces:** "no Helvetica with a Univers or a Garamond with a Bodoni." For unity, set headings in the same face as the text.
  7. Classic works set margins by calculated proportions, such as the golden section.
- **Menu application:** base the grid on the item line. Gaps between sections should be 1–2 item lines, and columns should hold about 7–10 words. Make size steps obvious, not 10 vs 10.5. Never pair near-twins, such as Helvetica with Avenir at similar weights, or Times with Georgia.

### 5. WCAG 2.2, Understanding SC 1.4.3 Contrast (Minimum)
- **Author / year:** W3C WAI, WCAG 2.2 (2023; page current 2026)
- **URL:** https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
- **Type:** standard / guidance. **Read:** queried the full page.
- **Principles**
  1. Text contrast should be **at least 4.5:1**. **Large text** (**18 pt, or 14 pt bold**, about 24 px or 18.5 px) can be **3:1**. Logos and pure decoration are exempt.
  2. 4.5:1 compensates for vision of about 20/40. **AAA 7:1** compensates for about 20/80.
  3. Thin or unusual fonts render fainter than their nominal colour because of anti-aliasing. In those cases choose a heavier font or exceed the minimum contrast.
- **Menu application:** keep every price and description at 4.5:1 or better against the page background. Bars and restaurants are dim, so aim for 7:1 on body text. Thin light-weight fonts, such as Avenir Light or Century Gothic at small sizes, need extra contrast margin.

### 6. WCAG 2.2, Understanding SC 1.4.12 Text Spacing
- **Author / year:** W3C WAI, 2023
- **URL:** https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html
- **Type:** standard. **Read:** queried the full page.
- **Principles:** content must survive user overrides of line height **≥ 1.5×** font size, paragraph spacing **≥ 2×**, letter spacing **≥ 0.12×** and word spacing **≥ 0.16×** without losing content. These are override targets, not required author settings.
- **Menu application:** a phone menu should not clip or overlap when the user enlarges spacing, so avoid fixed-height boxes. Also, 0.12 em is the upper end of Butterick's caps tracking range, so staying at or below 120/1000 em matches both sources.

### 7. The Layer-Cake Pattern of Scanning Content on the Web, and Text Scanning Patterns: Eyetracking Evidence
- **Author / year:** Kara Pernice, NN/g, 2019 (Aug 4 and Aug 25)
- **URLs:** https://www.nngroup.com/articles/layer-cake-pattern-scanning/ ; https://www.nngroup.com/articles/text-scanning-patterns-eyetracking/
- **Type:** UX research articles. **Read:** both in full.
- **Principles**
  1. There are 4 scanning patterns, from worst to best: F-pattern, spotted, **layer-cake**, commitment. Layer-cake means fixations fall on headings, and the reader drops into the body only where it is relevant. It is "by far the most effective way" to scan.
  2. Subheadings must stand out consistently and predictably. Use size, weight, colour, a different face or a combination. But don't make them so loud that they look like ads.
  3. Make clear which text belongs to which heading, using proximity: less space between a heading and its own content than before the next group.
  4. The **spotted** pattern picks up words that are styled differently, and things that look like the target, such as **digits** when hunting for numbers. That is why prices get spotted.
  5. Chunk content, group like with like, and separate chunks with space, borders or backgrounds. Use irregular spacing and you lose the pattern.
- **Menu application:** a menu is scanned, not read, so section headers are the layer-cake "frosting". Headers must be clearly different from item names. Keep item descriptions quieter than names. Keep every section's spacing identical.

### 8. F-Shaped Pattern of Reading on the Web: Misunderstood, But Still Relevant (Even on Mobile)
- **Author / year:** Kara Pernice, NN/g, 2017-11-12
- **URL:** https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/
- **Type:** research article. **Read:** queried the full page.
- **Principles:** put the most important items first. Make headings more visible than text. Front-load headings, because the first 2 words must carry the gist. Group small related chunks with a border or background. Bold key words. Cut unnecessary content. On liquid or mobile layouts the text reflows, so fixations differ between devices.
- **Menu application:** item names should lead with the distinctive word ("Negroni, barrel-aged", not "Our house barrel-aged…"). The first items in each section, and the top-left of the page, get the most attention, so place signature or high-margin items there. The phone layout must be re-checked on its own, not assumed from print.

### 9. Proximity Principle in Visual Design
- **Author / year:** Aurora Harley, NN/g, 2020-08-02
- **URL:** https://www.nngroup.com/articles/gestalt-proximity/
- **Type:** article. **Read:** queried the full page.
- **Principles:** items close together are seen as a group. Vary the whitespace to unite or separate. The whitespace around a heading should put it closer to its own section than to the previous one. A label should sit tight to its field and further from the next pair.
- **Menu application:** keep the gap between an item's name and its description smaller than the gap between items, and keep the gap between items smaller than the gap before a section header. This spacing ladder is the menu's main grouping device.

### 10. Similarity Principle in Visual Design
- **Author / year:** Aurora Harley, NN/g, 2020-09-06
- **URL:** https://www.nngroup.com/articles/gestalt-similarity/
- **Type:** article. **Read:** queried the full page.
- **Principles:** shared colour, shape, size or font treatment (bold, italic) signals the same kind of thing. Use size consistently to build hierarchy. Reserve a distinct colour for the one thing that must stand out.
- **Menu application:** every item name gets the identical style, and so does every price. If one accent colour is used, give it one role only, for example section heads. Otherwise it reads as "special".

### 11. Low-Contrast Text Is Not the Answer
- **Author / year:** Katie Sherwin, NN/g, 2015-06-07
- **URL:** https://www.nngroup.com/articles/low-contrast/
- **Type:** article. **Read:** queried the full page.
- **Principles:** low-contrast text hurts legibility and findability, and it is nearly unreadable on a phone in sunlight. Light grey text looks like a disabled item. It's fine to vary sizes, but **use at least an 8-pt font**. Larger text gets read first.
- **Menu application:** set a floor of 8 pt for the smallest print text (allergen notes, footers), and prefer 9 pt or more. Don't render descriptions in pale grey on phone menus.

### 12. 7 Practical Tips for Cheating at Design (Refactoring UI)
- **Author / year:** Adam Wathan & Steve Schoger, 2019-01-16
- **URL:** https://medium.com/refactoring-ui/7-practical-tips-for-cheating-at-design-40c736799886
- **Type:** article (free excerpt of the *Refactoring UI* approach). **Read:** queried the full article.
- **Principles**
  1. **Build hierarchy with colour and weight, not just size.** Use 2–3 text colours: dark for primary, grey for secondary, lighter grey for ancillary. Use 2 weights: normal plus one heavier for emphasis. Avoid weights under 400 for UI text.
  2. **Don't put grey text on coloured backgrounds.** To de-emphasise, pick a colour with the background's hue and adjust its saturation and lightness, or use reduced-opacity white.
  3. **Use fewer borders.** Use spacing or a background change instead.
  4. **Accent borders:** a single coloured stripe (top of the layout, or the side of a block) adds colour to a bland design.
- **Menu application:** use a 3-tone text palette: item name in near-black, description in mid-tone, notes in a lighter tone that still passes 4.5:1. On a coloured page background, tint the secondary text toward the background hue instead of using neutral grey. One thin accent rule at the top can be the entire decoration.

### 13. More Meaningful Typography (modular scales)
- **Author / year:** Tim Brown, *A List Apart*, 2011-05-03
- **URL:** https://alistapart.com/article/more-meaningful-typography/
- **Type:** article. **Read:** queried the full article.
- **Principles:** a modular scale is a sequence of numbers related by a ratio. Start from the body size and multiply or divide by the ratio (for example the golden ratio 1.618: 10 → 16.18 → 26.18; 10 → 6.18). A second "important number" can form a double-stranded scale. Use scale values for type sizes, line height, measure, margins and column widths. Rounding or breaking from the scale is fine if you document it. (Butterick, source 1, dissents: "When your headings look right, they are right.")
- **Menu application:** pick one ratio. Around 1.2–1.333 suits compact menus, because 1.618 jumps too far for a 4-level menu. Derive all sizes from the item size, for example 10 × 1.25 → 12.5 / 15.6 / 19.5. Treat the result as a starting point and adjust by eye.

### 14. Google Fonts Knowledge: "Choosing a suitable line height" and "Pairing typefaces"
- **Author / year:** Google Fonts Knowledge (c. 2021–2023)
- **URLs:** https://fonts.google.com/knowledge/using_type/choosing_a_suitable_line_height ; https://fonts.google.com/knowledge/choosing_type/pairing_typefaces
- **Type:** educational articles. **Read:** queried both pages. A third page, "choosing a type scale", redirected to an index and was not read.
- **Principles**
  1. Body line height is typically **115–150 %** (1.15–1.5) for Latin text. Smaller type needs more. **Display type can go to 90–100 %.**
  2. A wider measure needs more line height. A narrow mobile column can be tighter (about 130 % instead of 150 %).
  3. A face with a large x-height, which looks bigger, needs more open leading.
  4. Pairing: faces should be "different enough but not too different", aiming for distinction and harmony without competing. Serif + sans is the reliable method. Matching x-heights helps. Always ask whether an extra face is really needed.
- **Menu application:** item lines ≈ 1.2–1.35. Multi-line section titles and large display names ≈ 1.0–1.1. Phone single columns ≈ 1.3–1.45. Pair Palatino (text) with Avenir or Helvetica (labels); both have comparable x-heights and clear stylistic contrast.

### 15. Robin Williams, *The Non-Designer's Design Book*: CRAP principles
- **Author / year:** summary by Wiredcraft (2019) of Robin Williams's book (4th ed. 2014)
- **URL:** https://wiredcraft.com/blog/robin-williams-four-basic-design-principles-for-non-designers/
- **Type:** **secondary summary with the book's illustrations. I did not read the book.**
- **Principles**
  1. **Proximity:** group related items into one visual unit. "Elements that are logically connected should also be visually connected."
  2. **Alignment:** "Nothing should be placed on the page arbitrarily." A strong flush left or right edge makes an invisible connecting line. Centred edges are "soft", and beginners over-centre.
  3. **Repetition:** repeat colour, shape, rule weight, font and size throughout to unify the piece.
  4. **Contrast:** "If items do not belong to the same unit, then make them *very* different." Weak contrast looks like a mistake. Contrast both attracts the eye and organises.
- **Menu application:** if a header differs from an item name, it should differ strongly: caps plus tracking plus a size step, not +0.5 pt. Pick one alignment system per page. Centred menus are legitimate but need strong proximity to hold together. Repeat the same rule weight and header treatment in every section.

### 16. Josef Albers, *Interaction of Color*
- **Author / year:** Albers, 1963 (Yale). Pages read: Josef & Anni Albers Foundation page, plus Jeff Zych's chapter-by-chapter exercise notes (2020).
- **URLs:** https://www.albersfoundation.org/alberses/teaching/interaction-of-color ; https://jlzych.com/2020/04/29/exercises-from-interactions-of-color-by-josef-albers/
- **Type:** **foundation overview plus a secondary summary. I did not read the book itself.**
- **Principles**
  1. "In visual perception a color is almost never seen as it really is… color is the most relative medium in art." Always judge colours in context, never from swatches alone.
  2. One colour can look like two on different grounds, and two different colours can look alike (simultaneous contrast).
  3. **Vibrating boundaries:** contrasting hues of similar saturation and brightness side by side vibrate. **Equal light intensity:** similar hues of equal lightness make borders "disappear".
  4. **Quantity:** the same colours feel different depending on their proportions.
  5. Colour intervals: a palette can be "transposed" by keeping the lightness and saturation relationships.
- **Menu application:** never put red text on green, or blue on orange, at similar lightness, because it vibrates. Text and background must differ in *lightness*, not just hue, or the letters dissolve. Use accent colour in small quantities (rules, section heads). The page tint changes how the accent reads, so evaluate the accent on the actual background.

### 17. Print production guides
- **Sources:** AlphaGraphics Helena, "Complete Guide to Print-Ready File Setup: Bleed, Resolution, Color Mode, and Trim Explained" (2026-05), https://www.alphagraphics.com/us-montana-helena-us846/blog/blog/2026/05/the-complete-guide-to-print-ready-file-setup-bleed-resolution-color-mode-and-trim-explained ; Greenerprinter (Michael Assadi), "What Is Rich Black in CMYK?" (2023, updated 2026-09), https://www.greenerprinter.com/blog/blog-what-is-cmyk-rich-black/
- **Type:** printer guides. **Read:** queried both pages. Search snippets (not read in full) from 4over4 and an Adobe forum answer mention a total ink limit of about 240 % for C60 M40 Y40 K100 on most stocks.
- **Principles**
  1. **Bleed 0.125″ (≈3 mm)** on every edge when a background colour runs to the edge.
  2. **Safe zone:** keep important content **≥ 0.25″** inside trim.
  3. **300 DPI** at print size for flyers and brochures, CMYK colour mode, fonts embedded, PDF/X-1a, document size = trim + bleed.
  4. **Rich black C60 M40 Y40 K100** only for large solid black areas. Use **100 K only for small text and fine lines**, because rich black misregisters and blurs at small sizes.
- **Menu application:** a coloured full-page background needs bleed, and margins of ≥ 0.25″ (in practice 0.4–0.6″ for menus) keep prices off the trim. Body text in dark colours should be 100 K or a single-ink-heavy mix. Avoid reversed hairline rules and tiny light text on dark rich-black grounds.

---

## Rules for a menu designer (design fundamentals)

1. **Design the item line first.** Fix item-name size, description size, line height and column width before headers or decoration. [1, 2]
2. **Print sizes:** item names and descriptions 9–11 pt (body range 8–12 pt). The smallest note should be at least 8 pt, preferably 9. **Phone:** body 15–17 px, never below about 13 px. [1, 4, 11]
3. **Line height:** item text 120–135 %. Description blocks 125–145 %. Display titles 90–110 %. On phone single columns, 130–145 %. [1, 2, 14]
4. **Measure:** description lines of 40–50 characters in multi-column menus and at most about 66 in single-column. Roughly 7–10 words per line. [2, 4]
5. **Use a limited size ladder of 4–5 sizes** from one ratio (≈1.2–1.333), for example 9 / 11 / 14 / 18 / 24 pt. Steps must be clearly visible, and adjacent levels need at least about 20 % difference or a change of weight or case. [2, 4, 13]
6. **Keep hierarchy to 3 levels,** 2 if possible. Menu title → section header → item (with description and price as attributes). Add a fourth level only for sub-sections of very long menus. [1]
7. **Build contrast between levels decisively.** If two things are different levels, change two or more of: size, weight, case and tracking, colour. If they are the same level, change nothing. [1, 15, 10]
8. **Prefer weight, colour and case over size for hierarchy.** Use one regular weight plus one bold. Use 2–3 text tones (primary, secondary, tertiary). [12, 4]
9. **All caps only for short labels** (section heads, menu title, footers). Never for descriptions or anything longer than one line. [1]
10. **Always track caps +50 to +120/1000 em.** Smaller caps get more (about 100–120 at 8–10 pt), larger caps less (about 50–80 at 18 pt or more). Never track lowercase body text. At 24 pt or more, lowercase can take −10 to −20. [1, 2, 6]
11. **Bold or italic, not both.** Italic for gentle emphasis in serif faces (descriptions, origin notes). No italic with sans faces; use weight or colour instead. [1]
12. **Use at most 2 typefaces with fixed roles,** for example one for headers and prices and one for items, or one family throughout. Never pair near-identical faces. [1, 4, 14]
13. **Proximity ladder:** name → description gap < item → item gap < gap before a section header. The header sits closer to its own items than to the previous section, so give it more space above than below. [1, 7, 9, 15]
14. **Space before rules.** Separate sections with whitespace first. If you add rules, use 0.5–1 pt solid lines, one weight throughout, placed above headers rather than under them, and no double or dashed patterns. [1, 3, 12]
15. **Vertical rhythm:** make section gaps whole multiples of the item line height, for example 1 line or 2 lines, so parallel columns line up. [2, 4]
16. **Treat prices as a table column.** Align them flush right to one edge, use one consistent format, and use lining figures. Link names to prices either with leader dots or with whitespace, and use the same method everywhere. [3, 7]
17. **No boxes or zebra fills around items.** Group with alignment and space. A single accent rule or stripe is enough decoration. [3, 12, 1]
18. **Pick one alignment system per page.** Flush-left structure is the most robust. A centred layout is fine for short, symmetrical menus but needs tight proximity. Never centre long description blocks. [1, 15]
19. **Consistency:** every item, price, description and header of the same level gets an identical style across all sections and pages. [1, 10, 15]
20. **Front-load names.** The distinctive word comes first. Place signature or high-priority items first in a section and top-left on the page, where scanning attention is highest. [7, 8]
21. **Headers must be unmistakable,** but not so loud that they compete with the items or look like ads. [7]
22. **Contrast:** text needs at least 4.5:1 against the background, and body text should aim for 7:1 because menus are read in dim light. Large or bold display text (18 pt, or 14 pt bold, or larger) may go to 3:1. Thin fonts need more. [5, 11]
23. **Colour restraint:** use one accent colour with one role, plus shades of the text colour. Text must differ from the background in lightness, not just hue. No saturated complementary pairs at equal lightness (they vibrate). [1, 10, 16]
24. **On coloured backgrounds, tint the secondary text toward the background hue** rather than using neutral grey. Keep body text dark and near-neutral on light stocks. [12, 1]
25. **Judge colours on the actual background** at actual quantity. A small accent carries more intensity than a large field. Thin or small type can carry a stronger colour than heavy type. [16, 1]
26. **Margins:** generous, with at least 0.25″ safe area from trim. For a tabletop menu, about 0.5″ or more. Make the bottom margin slightly larger than the top. Let white space come from good text settings; don't fill it. [1, 17]
27. **Print production:** full-bleed backgrounds get 0.125″ (3 mm) bleed. Small text and hairlines use 100 K or a single ink. Reserve rich black (C60 M40 Y40 K100) for large solid areas. Output at 300 dpi, CMYK, with fonts embedded. [17]
28. **Phone layout is its own design.** Use a single column, re-check scanning order and headers, and don't clip when users enlarge spacing (line height 1.5×, letter spacing 0.12 em). [6, 8, 14]
29. **Smallest visible increments, then check by eye.** When unsure, render two variants and compare. A grid or scale is a starting point, not proof. [1, 13]
30. **Keep it simple:** if the menu seems to need three colours, three fonts, boxes and ornaments, remove things until the hierarchy works with type and space alone. [1, 12]

---

## How to express these with the limited toolset

**Hierarchy with only size, weight, italic, case, tracking and colour.** A proven 4-level recipe (print sizes; phone ≈ ×1.6 in px):

| Level | Font role | Size | Weight | Case | Tracking (1/1000 em) | Colour |
|---|---|---|---|---|---|---|
| Menu title | display | 20–28 pt | regular or bold | caps | +60 to +100 | primary or accent |
| Section header | display or label | 11–14 pt | bold (or regular if caps + accent) | caps | +80 to +120 | accent or primary |
| Item name | text | 10–12 pt | bold (sans) or regular (serif) | as written | 0 | primary |
| Description | text | 8.5–10 pt | regular, *italic allowed in serif* | as written | 0 (+10 to +20 only if < 9 pt) | secondary tone (≥ 4.5:1) |
| Price | same face as item, or label face | same size as item | same as item or regular | n/a | 0 to +20 | primary |
| Notes / allergens | label | 7.5–8.5 pt (never < 8 if avoidable) | regular | caps or sentence | +50 to +100 if caps | tertiary tone (≥ 4.5:1) |

- Each level differs from its neighbour by at least two attributes. Section header vs item name, for example, differ in caps + tracking + colour, not in size alone.
- Italic: use it only with Georgia, Times or Palatino. With Helvetica, Avenir, Trebuchet or Century Gothic, use weight or colour instead.

**Spacing values (relative to the item line height L):**
- Name → description: 0 to 0.25 L.
- Item → item: 0.5 to 0.75 L.
- Before a section header: 1.5 to 2 L. After it: 0.5 L.
- Column gap: at least 1.5–2 em of body size, so it reads clearly larger than the word space.

**Rules:** 0.5–0.75 pt in the accent or a secondary tone, full column width or short centred, above section headers or under the title only. Leader dots use the secondary tone, never the primary, so they recede.

**Font pairing among the 8 (grounded in Butterick's ranking [1] plus role logic [12, 14]):**
- **Palatino + Avenir:** the safest serif/sans pair (both A-list). Palatino for items and descriptions (with italic descriptions), Avenir caps for headers, prices and notes. Suits cocktail bars, wine lists and bistros.
- **Palatino alone:** caps + tracking for headers, roman for items, italic for descriptions. Classic and quiet.
- **Helvetica alone** or **Avenir alone:** bold/regular plus a 3-tone colour palette. Modern, strong on phones. Avenir is warmer, Helvetica more neutral.
- **Georgia + Helvetica or Avenir:** good for phone menus, since Georgia is screen-optimised. In print Georgia is C-list, and its oldstyle figures make uneven price columns **[my note on figures]**. If Georgia is used, set prices in the sans.
- **Times:** acceptable as a single serif, but Butterick treats it as a "default" signal. Prefer Palatino.
- **Century Gothic:** display only (title or section headers in tracked caps). It is geometric and light, and not for body text.
- **Courier:** only as a deliberate typewriter or "prep list" conceit, in one role (for example prices or notes), never paired with another "effect" face.
- **Trebuchet:** F-list for Butterick. Avoid unless a brand requires it.
- **Never pair:** Helvetica + Avenir (too similar), Georgia + Times or Palatino (near-twins), or any combination of three or more faces.

**Tracking cheat-sheet (1/1000 em):** caps ≥ 18 pt: +50 to +80. Caps 11–14 pt: +80 to +100. Caps 7–10 pt: +100 to +120. Lowercase 9–14 pt: 0. Lowercase below 9 pt: +10 to +30. Lowercase display at 24 pt or more: −10 to −20. Never exceed about +150; over +120 is already outside the sources' recommended ranges.

**Colour palette recipe:**
- Background plus up to 3 text tones and 1 accent.
- On light paper: primary near-black (100 K in print); secondary a dark warm or cool grey, or a hue-tinted dark, at about 7:1 or better; accent used on headers and rules only.
- On dark backgrounds: primary off-white; secondary off-white tinted toward the background hue (not neutral grey); check that all text passes 4.5:1, aiming for 7:1.
- Avoid equal-lightness hue pairs such as red on green.

**Columns and margins:**
- 1 column for phones and short lists.
- 2 columns for A4/Letter menus of about 20–40 items.
- 3 columns only for landscape or tabloid sizes, keeping about 40–50 characters per line.
- Margins at least 0.4–0.6″ (≥ 0.25″ safe zone, plus 0.125″ bleed when the background runs to the edge).
