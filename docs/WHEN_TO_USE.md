# When to use a Warm Dark card

Cards are for reports the user will scan later: a number that matters, a trend, a comparison, a list of three or more items, a status change, or a digest of those. One idea per PNG. A digest is a `cover` plus separate cards, never a mosaic.

Send every PNG from one manifest in a single `SendToUser` `images` array, in manifest order. The chat line, if any, is one sentence. The card is the report.

## Use a card when

- The answer has a hero number and whether it moved (`kpi`, `nw_delta_weekly`, `scoreboard`).
- The user needs the shape of a series, a mix, a funnel, or a gap (`line`, `area`, `bars`, `allocation`, `funnel`, `gap`, `breakeven`, `heatmap`).
- Three or more parallel facts would turn into a wall of bullets (`brief`, `roster`, `holdings`, `spend`, `timeline`, `radar`).
- Something broke, recovered, or is empty (`alert`, `empty`).
- You are sending two to four related reports. Start with `cover` so series dots show position even if chat reorders images.
- A photo or screenshot is the point (`hero`). Context still fits in one line plus a facts row.

Pick the lightest type that tells the story. The chooser is in [SKILL.md](../SKILL.md).

## Do not use a card when

- The answer is one line. "Yes", "6 pm", "file is saved" stay plain text.
- The user is in a back-and-forth and the next message is a question, not a report.
- The user must choose. **Never put selectable options on a card.** Send context as `brief`, `alert`, or `kpi` if a picture helps, and put the actual choice in a native chat widget (`SendToUser` type `widget`) in the same turn. Do not ask for a reply of A/B/C to a card. The legacy `decision` type still renders old manifests; it is not a picker.
- The payload is a raw dump: logs, JSON, a long table, a thread the user asked to read as text. Summarize into one hero, or leave it as text.
- You would be shoehorning. If no type fits, do not force `brief` or `kpi`. Ask for a new layout. See [NEW_LAYOUTS.md](NEW_LAYOUTS.md).
- You need a fourth color, a new aspect ratio, or olive used for "important" rather than "good". That is a theme break, not a card.

## Money

Earnings figures are **seller net** only. Do not print a gross number on an earnings card unless the user explicitly asked for gross.

## Quiet test

If you removed the image and one sentence would still answer the user, do not render a card.
