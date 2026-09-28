# Warm Dark v3 — design rationale

v3 (2026-09-27) is a visual-language refresh toward clean consumer fintech: generous whitespace, soft surfaces, clear hierarchy, simple charts, one modern sans. The card inventory, the JSON manifest → Python renderer path, the verdict-colour rules and every QA check are unchanged. Tokens live in `tokens.json` (kept in step with `render/warmdark/tokens.py`); the one-page visual reference is `specimen.png`.

## What changed from v2, and why

| v2 (editorial, Granola-leaning) | v3 (fintech) | Why |
|---|---|---|
| Roboto Slab 62 titles, slab 200 numerals | Inter Display SemiBold 46 titles, Inter Display Light numerals auto-fit 88–172 | One sans family reads as a product UI, not a magazine. The Display cut is drawn for large sizes, so it stays tight without faked tracking. A smaller title lets the number lead. |
| UPPERCASE tracked 14.5 px eyebrows | Sentence-case Inter Medium 17 labels | Tracked caps are chrome. Sentence case is quieter and matches fintech section labels ("Where it sits", "Top merchants"). |
| Everything flat on the canvas, separation by space alone | Soft raised surfaces (`surface #25231f`, radius 24) for facts, ranked lists, options, callouts, empty states | Grouping becomes visible without a single border. A card within the card is how fintech apps chunk information. |
| 3.2 px current line, 12 px bars, thick dumbbells | 2.6 px current, 1.7 px prior, 1.4 px dashed references, 6–10 px bars, fully rounded caps | Calmer charts, less "dashboard HUD". |
| Flat area fill | One vertical fade under a current line (16% → 0) | The single permitted gradient: it grounds a line without adding a colour. |
| Square legend swatches | Dot markers | Softer, and they match the end dots on lines. |
| Series dots | Pill for the current card + dots | Carousel convention; reads at a glance in chat. |

What did not change: the four brand colours, olive = good only, A-series sizes, ≤3–4 punches, separate PNGs, seller net, and every QA warning.

## Canvas decision (locked)

Canvas stays **`#1a1814`**. A deeper neutral fintech black (`#121212`-ish) was considered; it would make surfaces pop more, but it throws away the warm family that ties olive, ink and muted together, and it needs higher-contrast surfaces to separate, which reads louder. The warm base plus a 5% ink lift (`surface`) and a 9% lift for the one emphasised surface (`surface_hi`: recommended option, blocked next action) gives enough separation at low contrast. No new hues: every derived tone is a straight mix of the four brand colours.

## Hierarchy (read order)

1. **Hero** — a number, a verdict word ("Ship B"), or a chart. Inter Display Light, auto-fit; currency prefix raised and muted at 0.40×. Never two competing heroes.
2. **Context** — delta (arrow + sign + verdict colour + muted note) and one line of context directly under the hero.
3. **Support** — chart, ranked list, timeline or composition. Charts sit on the canvas; lists sit in a surface.
4. **Facts** — up to 4 stats in one soft panel anchored to the bottom, with quiet 1 px dividers between columns.
5. **Chrome** — masthead (agent · domain, date) and footer whisper (source · partial ring · series pill). Both quiet, 15.5–17 px.

The **title** (1–3 words) says *what*; the **dek** says *which slice*. Neither competes with the hero.

## Typography (card px at 810 wide)

| Role | Face | Size / line |
|---|---|---|
| Display numeral | Inter Display Light | 88–172 auto-fit; units 0.40× (0.34× for 3+ chars), prefix raised to cap height |
| Title | Inter Display SemiBold | 46/51 → steps to 42, 38, 34 before wrapping to 2 lines (landscape 42) |
| Stat (totals) | Inter Display Regular | 64 · 44 |
| Fact value | Inter Display Medium | 30 (shrinks to fit its column) |
| Callout / bottom line | Inter Display Regular | 30/40 |
| Lead (punch lead-in) | Inter SemiBold | 27–30 |
| Body | Inter Regular | 26–29 |
| Row / table | Inter Regular + Inter Medium **tabular figures** | 24/32 |
| Dek / context | Inter Regular, muted | 22/31 |
| Label | Inter Medium, sentence case, untracked | 17 |
| Axis / whisper | Inter Regular (tabular for axes), quiet | 15–15.5 |

Tabular figures are frozen into the `*-tnum.ttf` files (built by `tools/build_fonts.py` from the Inter 4.1 release), so money columns align even without libraqm. v2 slab font kinds still resolve to Inter Display for old forks.

## Surfaces

- `surface` for grouping: facts, ranked rows (spend merchants, roster groups, allocation, holdings), scoreboard breakdown, cover contents, decision options, empty-state skeleton, callouts (bottom line, why it matters, next action, cadence).
- `surface_hi` marks the **one** emphasised surface on a card: the recommended option, or a blocking next action. Never more than one.
- Inside a surface: 24–28 px padding, 1 px `divider` between rows or columns, `track_s` for bar tracks.
- Surfaces never nest, never carry borders or shadows, and never exist for decoration. The dead-space scan treats an empty surface exactly like empty canvas.

## Spacing

- 64 px side margins; masthead baseline 62; title top 112; footer baseline 46 from the bottom; body ends 90 from the bottom.
- Vertical rhythm comes from a flex stack: fixed blocks keep their size, springs and charts absorb the rest, lists spread up to a cap and then stop. Surfaces are flex-aware (`B.in_panel`), so a panel can grow with the card and hand the height to its contents.
- Hairlines only for chart gridlines (`grid`), dividers inside surfaces, and axis baselines.

## Colour

Four brand colours: canvas `#1a1814`, ink `#f4f2ea`, muted `#9a9688`, olive `#c4d44a`. Every other tone (`surface`, `surface_hi`, `divider`, `track_s`, `grid`, `hair`, `track`, `ash`, `faint`, `quiet`, `soft`, `area`) is a straight mix of those four.

- **Olive means good, in either direction.** A rise that is good (net earnings ▲) and a fall that is good (spend ▼, resting HR ▼, bedtime drift ▼) are both olive; the arrow carries direction, the colour carries the verdict. Also: bullets, the price segment above break-even, a winning variant, an on-pace bar, the best heatmap cell, "Recommended", a resolved pill. Nothing else.
- **Bad and neutral are ink, never grey.** A move that is bad, or that has no verdict (`polarity: "neutral"`, e.g. a price cut toward comps), keeps full contrast with its arrow. Grey only means *secondary* or *flat*.
- Changes always render as deltas (arrow + sign + colour), never as grey sub-text.
- Composition uses a monochrome ramp (ink → soft → muted → faint → ash → track), first series brightest, same order on every card. In stacked columns the highlighted column (default: the latest) takes that ramp and every other column is dimmed.
- Heatmaps: brighter always means better. Set `invert: true` when low values are good, and label the legend.

## Chart rules

- No box, no axis lines, no tick marks, no legend when a direct label fits. Gridlines are 3–4 `grid` hairlines with quiet tabular labels in a left gutter; sparks drop them entirely.
- Current series: ink, 2.6 px, monotone-smoothed (no overshoot), end dot with a canvas halo, value + name labelled at the end. Optional soft fade underneath.
- Prior: `faint`, 1.7 px. Targets and break-even: dashed, 1.4 px. Projections: dotted.
- Olive appears on a line only when it is above a reference (break-even, goal) or the series is flagged positive.
- Callouts: ≤2, placed as close above their point as the lines allow, with a short dotted leader.
- Bars: ≤42% of the slot, rounded tops, grey family with **one** highlighted bar in ink.
- Funnels: bar length is volume against the top stage (true scale); step conversion is text; only the weakest step is highlighted.

- Sankey (`cashflow_sankey`): node bars step ink → soft → muted by column, olive for `tone: "good"` (saved, invested). Flows are straight canvas mixes, not new hues: muted at 20%, olive at 30% for good flows, ink at 24% for an emphasised flow. Labels sit directly over the flows, never boxed. Portrait up to 7 nodes per column; beyond that, landscape.
- Net-worth rows: included assets take the monochrome ramp in both the stacked bar and the row swatches; a liability is an ink dash, a zero or excluded row a hollow faint ring. Excluded rows are muted because they are genuinely out of the total, which is the one place grey means "not counted".

## Aspect ratios

- **Default: A-series portrait 810×1146** for everything.
- **Approved alternate: A-series landscape 1146×810** (`"format": "landscape"`), only for time series longer than ~20 points or bar charts with 6+ categories. No other ratios.

## Density

≤3–4 punches per card. A card over budget drops optional blocks (spark, then facts) with a stderr warning rather than shrinking type. The renderer scans every PNG for empty bands (canvas or empty surface) and warns when one exceeds 26% of the card height.

## What not to do

- No cyan, no `#141416`, no HUD corners — Signal Dark is retired.
- No borders or outlined boxes, inset frames, washes, title rules, glow, glass, drop shadows. No gradient except the area fade.
- No slab headlines, no ALL-CAPS tracked eyebrows, no nested panels.
- No dual-bright series (two ink lines, or olive vs ink as peers). Current is bright, prior recedes.
- No grey for negatives. No olive for "important".
- No gross money on earnings cards — seller net only.
- No mosaics. One idea per PNG; digests use a `cover` + separate cards.
- No stock illustration, emoji, or icons as decoration.

## History: why v2 existed

The Sep 26 cards failed on scale contrast (a 72 px number on an 1146 px card), grey used for negatives, three numbers crushed into one `·` line, and no visual other than text. v2 fixed that with a hero numeral, verdict colour, composition strips, balance-sheet rows and a bottom facts row. v3 keeps all of those fixes and changes only the visual language around them.
