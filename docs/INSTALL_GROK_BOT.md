# Install Warm Dark on a Grok Bot fleet

Warm Dark is a folder of Python, fonts, examples, and `SKILL.md`. Installing it means putting that folder where your bots can read it, then telling every bot the path and the rules.

## 1. Put the skill on disk

Pick one path and use it everywhere:

- A single user: `~/.grok/skills/warm-dark`
- A shared box fleet: `/home/box/agent-data/workflows/warm-dark`

```bash
git clone https://github.com/testusercar/warm-dark.git ~/.grok/skills/warm-dark
python3 -m pip install -r ~/.grok/skills/warm-dark/requirements.txt
```

On a fleet box, clone to `/home/box/agent-data/workflows/warm-dark` instead. Do not rename the folder per person. The skill is Warm Dark for any user.

## 2. Render one example

```bash
python3 ~/.grok/skills/warm-dark/render/warm_dark.py \
  ~/.grok/skills/warm-dark/examples/finance-sunday.example.json \
  --outdir /tmp/warm-dark-cards --strict
```

You should get five PNG paths and no stderr warnings. Open one. It should be a warm dark card with a hero number, not a screenshot of someone else's accounts. The figures are fictional.

## 3. Send the images

In the same turn, call `SendToUser` with those PNG paths in an `images` array, in the order printed. One short line of chat is enough ("Sunday sample — five cards."). Do not paste the JSON into the chat.

## 4. Socialize the fleet

Tell every other bot, in whatever channel you use to update them (a fleet note, a skill pointer, or a short message to each):

- The skill name is **Warm Dark**.
- The folder is the path you cloned (the absolute path, not a guess).
- Read `SKILL.md` in that folder before rendering.
- Render with `python3 <skill>/render/warm_dark.py <manifest.json>`.
- Cards are informational. Selectable options go in a native chat widget, never on the card.
- Earnings are seller net.
- Olive means good, only.
- Examples use fake round numbers. Replace them with the user's data at render time. Do not invent a layout.
- If no type fits, follow `docs/NEW_LAYOUTS.md`. Do not shoehorn.

## Sample prompt — ask a bot to install it

Give this to any Grok Bot that can write files and run Python:

```text
Install the Warm Dark skill for this fleet.

1. Clone https://github.com/testusercar/warm-dark into ~/.grok/skills/warm-dark
   (if this machine uses /home/box/agent-data/workflows for skills, use
   /home/box/agent-data/workflows/warm-dark instead).
2. pip install -r <that folder>/requirements.txt
3. Render examples/finance-sunday.example.json with render/warm_dark.py --strict
   into /tmp/warm-dark-cards.
4. SendToUser the PNGs in one images array, in print order.
5. Remember the absolute skill path. When you report a number, a trend, a
   comparison, a list of 3+ items, or a status change, render a Warm Dark card
   from SKILL.md. One-line answers stay text. Never put selectable options on
   a card; use a chat widget. Earnings are seller net. Olive is good only.
6. Reply with the install path and confirm the sample rendered clean.
```

A disposable bot that does this and then trains the others is written out in [ONBOARDING_BOT.md](ONBOARDING_BOT.md). Delete that bot when it finishes. Keep the skill folder.
