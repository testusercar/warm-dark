# Theming Warm Dark

The renderer reads four brand colors from `render/warmdark/tokens.py`. Everything else — surfaces, dividers, chart grid, the monochrome ramp — is a straight mix of those four. Change the four. Do not invent new hues in chart code.

`refs/tokens.json` is the published copy of the same tokens. The renderer does not load it. After you change `tokens.py`, update the `brand` block in `tokens.json` so bots and humans read the same values. Leave the `derived` block as a snapshot, or regenerate it from the mixes in `tokens.py`. Editing only `derived` does nothing at render time.

Olive is **good only**. A rise that is good and a fall that is good are both olive; the arrow carries direction. Bad news and neutral moves stay ink. Never paint olive on something merely because it is important, selected, or loud.

Surfaces (`surface`, `surface_hi`) are tone lifts of canvas toward ink. They group facts. They are not a place to introduce a fifth color.

## What to edit

In `render/warmdark/tokens.py`:

```python
CANVAS = "#1a1814"  # full-bleed background
INK = "#f4f2ea"     # text, current series, bad or neutral deltas
MUTED = "#9a9688"   # secondary text, flat deltas
OLIVE = "#c4d44a"   # good only
```

Then mirror `CANVAS`, `INK`, `MUTED`, and `OLIVE` into `refs/tokens.json` → `brand`. Re-render one example and read the PNG before you socialize the change.

Safe to change: those four hex values.

Leave alone unless you are deliberately retuning the system: type sizes, margins, corner radius, stroke widths, and the mix ratios. A theme swap that also changes layout is a new visual language. Warm Dark v3 does not want one.

## Recipes

Paste the four lines into `tokens.py` and the same hexes into `tokens.json` `brand`. Olive stays the good-only color in every recipe below.

### Warm Dark (default)

| Token | Hex |
|---|---|
| canvas | `#1a1814` |
| ink | `#f4f2ea` |
| muted | `#9a9688` |
| olive | `#c4d44a` |

Warm base. Surfaces sit a few steps toward ink (`#25231f`, `#2e2c27` at the default mix ratios). This is the system the examples and `refs/specimen.png` show.

### Cool Dark

| Token | Hex |
|---|---|
| canvas | `#14181c` |
| ink | `#eef3f6` |
| muted | `#8d98a3` |
| olive | `#c4d44a` |

Same roles, cooler neutrals. Olive is unchanged on purpose: if "good" becomes a new hue, every existing card silently changes meaning. Surfaces recompute from the new canvas and ink.

### High contrast

| Token | Hex |
|---|---|
| canvas | `#0e0d0b` |
| ink | `#ffffff` |
| muted | `#c8c4b8` |
| olive | `#d6ee55` |

Darker canvas, paper-white ink, a lighter muted so secondary text still clears the background. Olive is a brighter yellow-green and still means good only. Check a `kpi` with a bad delta and a `spend` card with `polarity: "down_good"` before you keep it. Bad must stay ink; good must stay olive.

## Checks after a swap

1. Render `examples/showcase.example.json` (or at least a `kpi`, an `alert`, and a `notes_strip`).
2. Olive appears only where the news is good.
3. Muted text is still readable on canvas and on a surface.
4. You did not add a border, a glow, a drop shadow, or a second bright series color to "make it pop".

If the user wants a choice of theme, offer Warm Dark, Cool Dark, and High contrast in a **chat widget**, not on a card. Apply the recipe they pick, re-render a sample, and show the PNG.
