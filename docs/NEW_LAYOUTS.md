# Adding a card layout

Warm Dark already has a type for most reports. Use one. A new layout exists only when the content shape cannot be told by any current type without lying about it.

The user asks a Grok Bot to launch a **Cursor Cloud Agent** to add the type. Opus is the preferred model. The bot does not invent the layout in chat, and it does not squeeze the data into `brief` or `kpi` while it waits.

## What the user says

Paste this, filling the brackets:

```text
Launch a Cursor Cloud Agent on https://github.com/testusercar/warm-dark
(model: Opus if I can choose). Add one Warm Dark v3 card type for [shape].

Stay inside the existing visual system. Do not invent a new palette, font,
aspect ratio, or olive-means-important rule. Canvas #1a1814, ink #f4f2ea,
muted #9a9688, olive #c4d44a for good only, Inter Display + Inter, soft
surfaces, A-series 810×1146 (landscape 1146×810 only for wide charts).

Acceptance criteria:
- A template function with @template("name", "alias") in render/warmdark/templates/
- A schema branch in refs/manifest.schema.json
- An example in examples/ using fictional round demo numbers and no personal data
- A row in the chooser in SKILL.md
- python3 render/warm_dark.py on that example is clean under --strict
- QA: no clip, one hero, olive = good only, numbers agree, no dead band

Do not shoehorn this into an existing type. If an existing type already
fits, say so and do not add a template.
```

The bot's job is to launch that agent, then tell the user when the type is on the branch. Domain bots supply the content shape and why the current types fail. They do not design a fourth palette on the side.

## Acceptance criteria

A new type is done when all of these are true:

1. **Template.** A function in `render/warmdark/templates/*.py` registered with `@template("name", "alias")`. `name` is the id bots write in JSON.
2. **Schema.** A branch in `refs/manifest.schema.json` so `--validate` accepts the new fields and rejects a card that is missing the ones the layout needs.
3. **Example.** A card in `examples/` (its own file, or a card in `examples/showcase.example.json`) with fictional round numbers. No real people, accounts, or institutions.
4. **Chooser.** One row in the chooser table in `SKILL.md`: when to pick it, the type id, what the hero is.
5. **QA.** `python3 render/warm_dark.py <example> --strict` exits 0. Read each PNG: nothing clipped, one hero, olive only for good, the same figure matches across cards, no empty band taller than about a quarter of the card.

No new aspect ratio and no new brand color without the user explicitly asking for a theme change. Theme changes go through [THEMING.md](THEMING.md), not through a one-off template.

## Never shoehorn

If the report is "a number and a delta", it is a `kpi`. If it is "three notes with principal, accrued, and a mark", it is `notes_strip`, not three bullets. Add a type only for a shape the inventory cannot show: excluded-but-modeled rows, a flow that must balance, a formula the user has to see, and similar.

Shipped because roster, allocation, kpi, and spend could not carry them: `multi_institution_nw`, `cashflow_sankey`, `nw_delta_weekly`, `notes_strip`, `home_equity_card`. A legacy type id `notes_strip` still resolves to `notes_strip` so old manifests render. New manifests should say `notes_strip`.

When a render fails QA (clip, void, wrong type), fix the template or the example in the same change. Do not socialize a type that warns under `--strict`.
