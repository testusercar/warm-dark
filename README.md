# Warm Dark

Warm Dark is a card system for Grok Bot fleets. A bot writes a JSON manifest, a Python renderer draws one PNG per card, and the bot sends those images in a single `SendToUser` turn.

The look is Warm Dark v3: canvas `#1a1814`, ink `#f4f2ea`, muted `#9a9688`, olive `#c4d44a` for good news only, Inter Display for titles and numerals, Inter for everything else, soft raised surfaces, no borders. Cards are informational. Selectable choices stay in a native chat widget.

Every figure in `examples/` is a round fictional demo.

## Quickstart

```bash
git clone https://github.com/testusercar/warm-dark.git
cd warm-dark
python3 -m pip install -r requirements.txt
python3 render/warm_dark.py examples/finance-sunday.example.json --outdir /tmp/warm-dark-cards
```

The command prints one PNG path per line. Warnings go to stderr. Fix every warning before sending. `--strict` exits 2 when any card warns.

Send the PNGs in one `SendToUser` `images` array, in manifest order. Chat text is one short line, or none.

## Install the skill

Copy this repo to a skill folder the fleet can read. Two conventional paths:

- `~/.grok/skills/warm-dark`
- `/home/box/agent-data/workflows/warm-dark`

The renderer entry point is `render/warm_dark.py` inside that folder. See [docs/INSTALL_GROK_BOT.md](docs/INSTALL_GROK_BOT.md) for the Grok Bot steps, including how to tell the rest of the fleet.

## Requirements

- Python 3
- [Pillow](https://pypi.org/project/Pillow/) (`requirements.txt`)
- Inter and Inter Display, already bundled in `render/fonts/` (SIL Open Font License, see `render/fonts/Inter-LICENSE.txt`)

`jsonschema` is optional. When it is installed, `--validate` checks the manifest against `refs/manifest.schema.json`.

## Read next

| Doc | What it answers |
|---|---|
| [SKILL.md](SKILL.md) | How a bot picks a type, writes JSON, renders, and QA's |
| [docs/WHEN_TO_USE.md](docs/WHEN_TO_USE.md) | When a card beats text, and when it does not |
| [docs/THEMING.md](docs/THEMING.md) | How to swap canvas, ink, muted, and olive |
| [docs/NEW_LAYOUTS.md](docs/NEW_LAYOUTS.md) | How to ask for a new card type from a Cloud Agent |
| [docs/ONBOARDING_BOT.md](docs/ONBOARDING_BOT.md) | A disposable bot that installs Warm Dark, then gets deleted |
| [refs/DESIGN.md](refs/DESIGN.md) | Why the visual system looks like this |

Design tokens: `refs/tokens.json` and `render/warmdark/tokens.py`. Schema: `refs/manifest.schema.json`. One sample of every type: `examples/showcase.example.json`. Visual reference: `refs/specimen.png`.
