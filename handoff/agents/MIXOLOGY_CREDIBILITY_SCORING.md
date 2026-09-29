# PHG Mixology credibility scoring

Rob 2026-09-29: catalog every recipe and grade it by the quality of who stands behind it: credentials, how people are
scored, influencer vs legitimate writer, known or unknown.

Every **source** and every **creator** (person) gets a **credibility score 0-100** made of six parts, plus the tier
(what kind of source it is). Every **recipe, prep and technique** then gets a **quality score 0-100** computed from the
sources that back it. Scores are stored with their parts and the evidence for each part, so they can be explained
("Difford's: 88 because ...") and re-scored when evidence changes.

## 1. Person / source credibility (0-100)

| part | max | what earns it (evidence required, a URL or citation) |
|---|---|---|
| **Credentials** | 30 | Industry awards: Tales of the Cocktail Spirited Awards (win 10, nomination 5), James Beard (win 10, nom 5), World's 50 Best / North America's 50 Best Bars (listed bar 8, #1 bar 10), Bar Convent / Drinks International Bar Legend or Bartender's Bartender (8); author of a published cocktail book from an established publisher (8 each, max 16); recognized formal credential (WSET 3+, Master Sommelier / Cicerone, BarSmarts Advanced, food-science degree) (4). Capped at 30. |
| **Professional standing** | 20 | Years behind a professional bar or running a program (1 per year, max 10); owner/partner/beverage director of a recognized bar (6); trains other professionals (seminars at Tales, BCB, brand academies as educator) (4). |
| **Recognition** | 15 | Cited by name by tier-1/2 sources as an authority or originator of a drink or technique (3 per independent citation, max 12); has a Wikipedia article or equivalent reference entry (3). "Known" = at least 6 here. |
| **Method rigor** | 15 | Publishes exact specs (measured amounts, units, method) (5); explains why (dilution, balance, ratios) (4); tests/iterates visibly (side-by-sides, measurements) (3); corrects errors / credits originators (3). |
| **Editorial & independence** | 10 | Editorial process (editor, fact-checking, test kitchen) (5); discloses sponsorships, not primarily paid brand content (3); no history of copied or uncredited recipes (2). Brand marketing pages score 0-3 here. |
| **Track record** | 10 | Their recipes are reproduced by other tier-1/2 sources or on respected menus (up to 6); longevity of output (3+ years active) (4). |

Audience size (followers, subscribers) is **recorded but never scored**: popularity is not quality. It is kept as
`reach` so Harmony can say "popular" separately from "credible".

### Grades
- **A (85-100) authority**: canon authors, top award-winning bartenders, pro reference sites with editorial process.
- **B (70-84) established**: respected bartenders and publications, the best technical creators.
- **C (50-69) credible**: working professionals, solid creators with exact specs.
- **D (30-49) unproven**: little verifiable track record; usable with care.
- **E (0-29) unverified / marketing**: anonymous, brand marketing, or copied content. Never used as the only source.

### Kind (separate from score)
`canon_author`, `pro_bartender`, `bar` , `publication`, `reference_site`, `technical_creator` (science/technique
channels), `lifestyle_influencer`, `brand`, `academic`, `historian`. A social creator can score high (Kevin Kos:
technical creator with exact, tested specs) and a famous name can score lower on method rigor; the kind says what
they are, the score says how much to trust them.

## 2. Recipe / prep / technique quality (0-100)

Computed from its attributions, not typed in:

- **Best backer** (50%): the highest credibility score among its sources.
- **Agreement** (25%): number of independent sources that agree on the core spec: 1 = 8, 2 = 16, 3 = 21, 4+ = 25.
  Sources that disagree become variants and do not add agreement.
- **Completeness** (15%): amounts for every line (6), method (3), glass (2), garnish (2), origin/creator stated (2).
- **Verification** (10%): every number checked on the actual page or book (10); from search excerpts only (3);
  unverified (0).

Quality grade uses the same A-E bands. Harmony uses the grade when answering: A/B specs are given as "the standard
spec"; C as "a well-regarded version"; D/E only when asked, and always named ("a version from <source>").

## 3. Who scores

Research agents propose the parts with evidence URLs; the lead developer loads them; anything scoring A must have
evidence for every part it claims. Scores are re-computed on each reload (never hand-edited in the DB).
