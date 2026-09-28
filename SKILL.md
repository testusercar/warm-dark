---
name: Warm Dark
description: >-
  Use when any Grok Bot reports metrics, status, charts, digests, briefs, or
  alerts to the user as image cards. Warm Dark v3: JSON manifest → Python
  renderer → separate PNGs. Informational only — selectable choices go in a
  native chat widget, never on a card. Seller net for earnings. Olive means
  good only.
---

# Warm Dark

How the **fleet talks to the user**. Prefer a card over a wall of text whenever a report has a number that matters, a trend, a comparison, a list of 3+ items, a status change, or a digest of those. Quiet one-line answers stay plain text. See `docs/WHEN_TO_USE.md`.

**Locked brand (v3):** canvas `#1a1814` full-bleed · ink `#f4f2ea` · muted `#9a9688` · olive `#c4d44a` = *good only* · **Inter Display** titles + numerals, **Inter** everything else · sentence-case labels, no tracked caps · soft raised **surfaces** (`#25231f`, radius 24) group facts, lists, and callouts — tone separates, never a border · thin chart strokes (2.6 px current), one soft fade under a current line is the only gradient · no border, frame, wash, title rule, glow, drop shadow · money on earnings cards = **seller net** only · A-series portrait 810×1146 (landscape 1146×810 only for wide charts) · separate PNGs, never mosaics · ≤3–4 punches per card.

Theme swaps (Cool Dark, High contrast) change only the four brand colors. See `docs/THEMING.md`.

## Standing rule — decisions

**Never put selectable options on a Warm Dark card.** Cards are informational only. When the user must choose, send context as a card (`brief`, `alert`, `kpi`, …) and put the actual choice in a **native chat widget** (`SendToUser` type `widget`) in the same turn. Do not ask them to reply A/B/C to a card.

The `decision` card type is **retired for selection**. Do not invent new lettered option cards. If you still render a legacy `decision` PNG for context, it must not be the picker — the widget is mandatory and is the only place options are selectable.

Read order on every card: **hero number → context → facts.** Title is a calm 46 px label for *what*; the hero numeral (Inter Display Light, auto-fit 88–172 px) carries the weight; context and delta sit right under it; supporting chart or list in the middle; facts in one soft panel at the bottom.

Design rationale: `refs/DESIGN.md` · specimen: `refs/specimen.png` · tokens: `refs/tokens.json` (runtime values live in `render/warmdark/tokens.py`) · schema: `refs/manifest.schema.json` · every type in one manifest: `examples/showcase.example.json`.

## Low-token path (always)

1. Pick the type from the chooser below. Copy the matching example from `examples/*.example.json` and replace the data. Don't invent layout. Demo numbers are fictional — substitute the user's figures.
2. Write the manifest (one file, many cards). Titles 1–3 words; detail goes in `dek`, `context`, or facts.
3. Render from the installed skill folder (whatever path this fleet was given):
   ```bash
   python3 ~/.grok/skills/warm-dark/render/warm_dark.py cards.json
   # or, on a shared box:
   python3 /home/box/agent-data/workflows/warm-dark/render/warm_dark.py cards.json
   ```
   Prints one PNG path per line. Warnings go to stderr: **fix every warning** (overflow, truncation, dead space — an empty surface counts as empty — gross money on an earnings card). `--strict` exits 2 on any warning. `--validate` checks the schema only. `--types` lists types. `render/signal_dark.py` is a compatibility entry point for the same renderer.
4. **QA every PNG** (below). Re-render until clean.
5. Send all PNGs in **one** SendToUser `images` array, in manifest order. Chat text: one short line or none.

Formats: numbers are pre-formatted strings you control (`"C$12,400"`, `"7h 30m"`, `"−6.3%"`). Chart data are raw numbers plus `fmt` (Python format string: `"C${:,.0f}"`, `"{:.1f}%"`, `"{:k}"` = compact 4.2k). Use real minus `−` or plain `-`; the renderer fixes it.

Inline markup in any text field: `**strong**` (ink semibold) · `{{+12%}}` (olive if +, ink if −).

## Chooser — pick the lightest type that tells the story

| The user needs to know… | Type | Hero |
|---|---|---|
| One number and whether it moved | `kpi` | numeral + delta; add `spark` or `composition` + `facts` |
| This period vs last, with a breakdown | `scoreboard` | current vs prior + dumbbell rows |
| How something moved over time | `line` | chart (dual line: current ink vs prior faint) |
| A trend with 1–2 moments that explain it | `area` | numeral + full-bleed area + callouts |
| Which category is biggest / how parts stack | `bars` | chart, one highlighted bar (`stacked: true` for parts) |
| 3–4 parallel points that really are a list | `brief` (`watch` = hollow rings + when tags) | lead-ins + bottom line |
| Something broke / is blocked / recovered | `alert` | severity pill + impact + timeline + next action |
| A before→after change or distance to a target | `gap` | the gap + number-line track |
| What share each part holds | `allocation` (`style: "donut"` or share bar) | total + ranked rows |
| What's coming up | `timeline` | date rail |
| Positions with weight and P/L | `holdings` | table-lite |
| Accounts and the net total | `roster` | balance sheet |
| Where money went this week | `spend` | total + 7-day bars + merchant rows |
| An asset vs its break-even / cost basis | `breakeven` | olive-above-BE price line + stepped BE |
| Sleep / recovery / body metrics | `vitals` | value + score ring + stages + 7-night bars |
| News that matters, with sources | `radar` | numbered headlines + sources whisper + why it matters |
| Result of a test | `experiment` | verdict word + lift + interval plot |
| Distance to a goal and pace | `progress` | % + bar with pace marker + burn-up chart |
| Data isn't there yet | `empty` (or `partial` on any card) | skeleton + reason + next check |
| A digest of 2–4 cards | `cover` + the cards | contents list; series dots on every card |
| The user must choose | **chat widget** (not a card) | informational card optional; selectable options only in native `widget` |
| Consistency across days/weeks | `heatmap` | 7×N grid, best cell olive |
| Where a flow leaks | `funnel` | step-conversion bars, weakest step flagged |
| A photo or screenshot carries it | `hero` | image + one line + facts |
| Net worth across buckets, some modeled but left out | `multi_institution_nw` | included total + stacked bar + bucket rows; `included: false` rows whispered below |
| Where a period's money came from, went, and landed | `cashflow_sankey` | income → categories → accounts flows; saved flows olive |
| Net worth vs last week, and what moved it | `nw_delta_weekly` | NW numeral + one delta; spark + ≤4 signed drivers |
| Three notes: principal, accrued, mark | `notes_strip` | best-known value + 3 strips. Legacy id `manulife_notes_strip` still resolves |
| The user's share of a property | `home_equity_card` | equity dollars + formula ledger: value × % − mortgage share + joint cash share |

**Not everything is bullets.** If you wrote three bullets of narrative, you probably want `kpi`, `gap`, `alert`, or `radar`.

## Manifest

```json
{
  "version": 2,
  "agent": "Finance", "domain": "Finance", "date": "Sep 27",
  "footer": "Demo books · read-only",
  "outdir": "/tmp/cards/finance",
  "cards": [ { "type": "kpi", "slug": "cad-cash", "title": "CAD cash", "value": "C$12,400" } ]
}
```

Any card may also set `dek`, `footer`, `agent`/`domain`/`date` overrides, `format: "landscape"`, `partial`, `facts` (≤4 × `{label, value, sub?, delta?, tone?}` — rendered as one soft stat panel), and `image`. v3 changed no fields: every v1/v2 manifest renders unchanged, just in the current look.

`delta` is `"+12%"` or `{"value":"−14%","note":"vs typical","polarity":"down_good"}`. **Colour = verdict, arrow = direction:** olive when the change is good (up or down), ink when it's bad or has no verdict, muted only when flat. `polarity: "down_good"` for spend, resting HR, drift; `polarity: "neutral"` for moves with no verdict (a price cut toward comps). Put every change in a `delta`, never in grey `sub` text.

## Type examples (minimal; full versions in `examples/`)

```jsonc
// kpi — examples/finance-sunday.example.json, ops-store net-earnings
{"type":"kpi","title":"CAD cash","dek":"Five accounts at Sunday close","value":"C$12,400",
 "delta":{"value":"+C$200","note":"vs last Sunday"},"context":"Net of the card: **C$12,000**",
 "composition":[{"label":"Money market","num":6400},{"label":"Savings","num":3200}],
 "facts":[{"label":"Card owed","value":"−C$400"},{"label":"USD cash","value":"US$800","tone":"muted"}]}
// spark instead of composition: "spark":{"values":[…],"prior":[…],"x":["Sep 1",…,"Sep 27"],"positive":true}

// scoreboard — examples/ops-store.example.json
{"type":"scoreboard","title":"This week","current":{"label":"This week","value":"US$340"},
 "prior":{"label":"Last week","value":"US$300"},"delta":{"value":"+15%","note":"net earnings"},
 "rows":[{"label":"Orders","current":58,"prior":49},{"label":"Net per order","current":5.9,"prior":6.04,"fmt":"US${:.2f}"}]}

// line (dual) — nulls end a series early; landscape for long ranges
{"type":"line","title":"Pacing August","value":"+US$280","delta":{"value":"+28%","note":"ahead on day 27"},
 "series":[{"role":"prior","name":"August","values":[…]},{"role":"current","name":"September","values":[…,null]}],
 "x":["Day 1",…],"x_ticks":[0,9,19,29],"fmt":"US${:,.0f}","axis_fmt":"{:k}","zero":true,
 "annotations":[{"at":2,"text":"Bundle launch","sub":"US$80 in a day"}]}

// area — examples/health.example.json
{"type":"area","title":"HRV, 30 nights","value":"60 ms","delta":"+9%","values":[…],"x":["Aug 29",…,"Sep 27"],
 "callouts":[{"at":7,"text":"Overnight flight","sub":"41 ms low"}],"refs":[{"value":53,"label":"Aug avg 53 ms"}]}

// bars — one highlight; "stacked":true + several series for parts
{"type":"bars","title":"Net by product line","categories":["Bundles","Kits","Guides"],
 "series":[{"name":"Net","values":[400,300,200]}],"highlight":"Bundles","fmt":"US${:,.0f}"}

// brief / watch — examples/radar.example.json
{"type":"brief","title":"Desk","points":[{"lead":"Spec split","text":"The working group is two votes short of a delay."}],
 "takeaway":"The missing appendix is the thread to pull."}
{"type":"watch","title":"Watch this week","points":[{"lead":"Public comment","text":"Last session before the packet locks.","when":"Thu"}]}

// alert — severity: sev1 | sev2 | sev3 | info | blocked | resolved
{"type":"alert","severity":"sev1","status":"Blocked","since":"since 06:12 · 7h 32m","title":"Nightly sweep failing",
 "body":"10 of 10 sweeps failed at sign-in.","detail":"Token expired; needs your 2FA.",
 "impact":[{"label":"Runs failed","value":"10/10"}],
 "timeline":[{"time":"06:12","text":"First failure","state":"done"},{"time":"13:44","text":"Waiting on 2FA","state":"now"}],
 "next":{"label":"Needs you","owner":"Ops","text":"Approve the prompt on your phone."}}

// gap — before/after or to-target. examples/ops-store.example.json
{"type":"gap","title":"Bundle A price cut","value":"−C$4","delta":{"value":"−10%","polarity":"neutral"},
 "before":{"label":"Was","value":"C$40","num":40},"after":{"label":"Now","value":"C$36","num":36},
 "target":{"label":"Comps median","value":"C$35","num":35},"polarity":"down_good"}

// allocation
{"type":"allocation","style":"donut","title":"Where CAD sits","total":"C$12,400","total_label":"CAD cash",
 "items":[{"label":"Money market","num":6400,"value":"C$6,400"},{"label":"Savings","num":3200,"value":"C$3,200"}]}

// timeline — state: past | today | next | later | done
{"type":"timeline","title":"Week ahead","events":[{"date":"Sep 29","dow":"Tue","text":"Clinic visit","meta":"2:15 pm","state":"next"}],
 "note":"Tuesday is the only hard stop."}

// holdings — examples/finance-more.example.json
{"type":"holdings","title":"Holdings","rows":[{"name":"Metal","sub":"2.0 oz","value":"C$12,000","weight":60,"pl":"−C$800"}],
 "total":{"label":"Total","value":"C$20,000","pl":"−C$640"}}

// roster — examples/finance-sunday.example.json
{"type":"roster","title":"Demo bank","groups":[{"label":"Cash","subtotal":"C$12,000",
 "items":[{"label":"Money market","value":"C$6,400","num":6400}]},{"label":"Owed","items":[{"label":"Credit card","value":"−C$400","num":-400}]}],
 "total":{"label":"Net CAD","value":"C$12,000","sub":"assets − card"},"aside":{"label":"USD cash","value":"US$800"}}

// spend
{"type":"spend","title":"Spend this week","value":"C$240","delta":{"value":"−14%","polarity":"down_good","note":"vs typical"},
 "days":[20,40,20,30,60,40,30],"merchants":[{"name":"North Market","sub":"groceries","value":"C$60","num":60}]}

// breakeven — steps = cost basis after each buy (stepped reference)
{"type":"breakeven","title":"Metal vs break-even","value":"−6.3%","delta":{"value":"C$400/oz","dir":"down","good":false,"note":"under break-even"},
 "price":{"values":[…],"x":[…],"x_ticks":[0,9,18,26],"label":"C$6,000"},
 "steps":[{"at":2,"value":6200,"label":"buy 1.0 oz"},{"at":14,"value":6600,"label":"+1.0 oz"}],"be_label":"C$6,400"}

// vitals — examples/health.example.json
{"type":"vitals","title":"Sleep","value":"7h 30m","delta":{"value":"+20m","note":"vs 7-night avg"},"score":80,
 "stages":[{"label":"Deep","minutes":88},{"label":"REM","minutes":106}],
 "history":{"values":[6.4,6.9,7.5],"labels":["Thu","Fri","Sat"],"goal":8}}

// radar
{"type":"radar","title":"Desk","items":[{"headline":"Draft spec splits the working group","why":"Vote wants the appendix first.",
 "sources":["Wire","Daily"],"when":"2h","signal":"rising"}],"takeaway":"The spec vote is the item to watch."}

// experiment — examples/ops.example.json
{"type":"experiment","title":"Onboarding test","verdict":"Ship B","lift":{"value":"+18%","note":"relative lift"},
 "confidence":"**96%** chance B beats A","winner":"B","fmt":"{:.1f}%",
 "variants":[{"key":"A","name":"A","label":"Current","rate":11.2,"ci":[9.5,12.9],"n":1204,"control":true},
             {"key":"B","name":"B","label":"Guided","rate":13.2,"ci":[11.4,15.1],"n":1206}]}

// progress — examples/ops-store.example.json
{"type":"progress","title":"Year net goal","value":"75%","current":{"value":"US$9,000","num":9000},
 "goal":{"value":"US$12,000","num":12000},"on_pace":true,
 "pace":{"expected_frac":0.74,"actual":[…],"required":[…],"projection":[…],"x":[…]}}

// empty — or add "partial":{"ok":2,"of":3,"note":"Marketplace stale 3h"} to any card
{"type":"empty","title":"Carrier scans","message":"No scans yet","skeleton":"list",
 "reason":"Label created; not picked up.","expected":"Ops checks again at 18:00."}

// cover — first card of a digest; series dots switch on automatically
{"type":"cover","kicker":"Week 39 · Sunday close","title":"Sunday books","dek":"Cash up, metal under water.",
 "items":[{"title":"CAD cash","note":"net of card C$12,000","value":"C$12,400","delta":"+1.6%"}]}

// decision — RETIRED for selection. Do not use as a picker.
// Send an informational brief/alert/kpi if useful, then a SendToUser widget for the choice.
// Legacy shape kept only so old manifests still render. See examples/ops.example.json.
{"type":"decision","title":"Renew the paper?","dek":"Auto-renews Oct 2 at C$20/mo. Choose in the chat widget.",
 "options":[{"key":"A","label":"Cancel","detail":"Use the library copy.","recommended":true},{"key":"B","label":"Downgrade"}],
 "why":"Opened 3× in September.","deadline":"Reply by Oct 1, 6 pm","default":"no reply = A"}

// heatmap — weeks = columns of 7 values (Mon→Sun); best = [week, day]; null = not yet (hollow cell)
{"type":"heatmap","title":"Sales days","value":"7.9","weeks":[[3,4,2,5,4,1,2],…],"best":[6,1],"best_label":"best day · 14 orders"}
// low is good (drift, errors)? bright must still mean better:
{"type":"heatmap","title":"Bedtime drift","weeks":[…],"invert":true,"legend":["off target","on target"]}

// funnel
{"type":"funnel","title":"Store funnel","value":"1.15%","stages":[{"label":"Product views","num":18420,"value":"18,420"},
 {"label":"Purchased","num":212,"value":"212"}]}

// hero — photo/screenshot carries it. examples/ops.example.json uses refs/sample-tracking.png
{"type":"hero","title":"Shipped","body":"Order 1042 · arrives **Oct 1**","image":"/abs/path/label.png",
 "facts":[{"label":"Arrives","value":"Oct 1"}]}
```

## Net worth (examples/finance-networth.example.json)

```jsonc
// multi_institution_nw — total = sum of included rows (auto if omitted, checked if num given);
// "included": false (or "exclude": true) keeps a row modeled at its share but out of the total
{"type":"multi_institution_nw","title":"Net worth","total":{"label":"Current net worth","value":"C$48,000","num":48000},
 "rows":[{"label":"Cash","sub":"Demo bank","value":"C$12,400","num":12400},
         {"label":"Northwind","sub":"modeled · round multiple","share":"20% stake","value":"C$8,000","num":8000},
         {"label":"Credit card","value":"−C$800","num":-800},
         {"label":"Home equity","sub":"nets the joint mortgage","share":"50% share","value":"C$20,000","num":20000,"included":false}],
 "excluded_label":"Not in current net worth","all_in":{"label":"All-in with home equity","value":"C$68,000"}}

// cashflow_sankey — columns inferred from links (or node "column"); "tone":"good" = olive (saved/invested);
// in ≠ out on a middle node warns; >7 nodes in a column or >14 total → "format":"landscape"
{"type":"cashflow_sankey","title":"September cashflow","value":"C$3,000","delta":{"value":"+C$400","note":"saved vs August"},
 "stages":["Income","Where it went","Landed in"],
 "nodes":[{"id":"pay","label":"Net pay","value":"C$8,000"},{"id":"rent","label":"Rent","value":"C$2,400"},
          {"id":"saved","label":"Saved","value":"C$3,000","tone":"good"},{"id":"chq","label":"Chequing","value":"C$2,400"},
          {"id":"mm","label":"Money market","value":"C$1,800"}],
 "links":[{"source":"pay","target":"rent","num":2400},{"source":"pay","target":"saved","num":2800},
          {"source":"rent","target":"chq","num":2400},{"source":"saved","target":"mm","num":1800}]}

// nw_delta_weekly — one delta; "polarity":"down_good" for debt; drivers must sum to num − prior.num
{"type":"nw_delta_weekly","title":"Net worth","value":"C$48,000","num":48000,
 "delta":{"value":"+C$2,000","note":"+4.3% vs last Sunday"},"prior":{"label":"Sep 20","value":"C$46,000","num":46000},
 "spark":{"values":[…],"x":["Jul 12",…,"Sep 27"]},
 "drivers":[{"label":"Cash saved","value":"+C$1,600","num":1600},{"label":"Metal","value":"−C$200","num":-200}]}
// no spark/drivers? "composition":[{label,num}] fills the lower half instead

// notes_strip — exactly 3; "mtm": null = not known yet (strip shows MTM pending, hero uses principal + accrued)
// Legacy type id manulife_notes_strip still renders. Prefer notes_strip in new manifests.
{"type":"notes_strip","title":"Notes","value":"C$12,400","delta":{"value":"+C$400","note":"vs C$12,000 principal"},
 "notes":[{"name":"Harbor Index","principal":{"value":"C$4,000","num":4000},"accrued":{"value":"C$200","num":200},
           "mtm":{"value":"C$4,400","num":4400},"maturity":"Mar 2028"}, …],
 "note":"Manual from sample statements · no live feed"}

// home_equity_card — hero = property × equity_pct − mortgage × share + joint cash × share (shares default to equity_pct)
{"type":"home_equity_card","title":"Home equity","status":"Pre-closing","equity_pct":50,"equity_source":"ownership note",
 "property":{"value":"C$200,000","num":200000},"mortgage":{"label":"Mortgage","value":"C$180,000","num":180000},
 "joint_cash":{"label":"Joint cash","value":"C$20,000","num":20000},"num":20000}
```

## Digests (2–4 cards)

Start with a `cover` whose items mirror the cards that follow (title, one-line note, headline value). The renderer turns on series dots so the user can see card 3 of 5 even if chat reorders images. Keep every card self-contained: each one must make sense alone.

## Mandatory per-card QA (before SendToUser)

Open **each** PNG, one by one:

1. **No clip or overlap.** Title, hero, labels and footer fully visible; no label sits on a line or another label.
2. **Right type.** Narrative bullets → rewrite as `kpi` / `gap` / `alert` / `radar`. A number with history → add `spark` or use `line`.
3. **One hero.** One big thing. If two numbers fight, move one into facts.
4. **Olive = good.** Nothing olive that isn't good; no grey for bad news. Same entity, same shade across cards (first series brightest). Surfaces are for grouping only: a panel with nothing meaningful in it is dead space, not decoration.
5. **Numbers agree.** The same figure (a month total, a balance) is identical on every card in the send, and deltas match the values they compare. Net worth on `multi_institution_nw` = `nw_delta_weekly` hero; notes total = the notes bucket; home equity = the excluded row.
6. **Dead space.** No empty band taller than about a quarter of the card (the renderer warns). Fix with facts, spark, timeline, image, or a denser type. Never pad with filler copy.
7. **Density.** ≤3–4 punches; cut copy or split the card, never shrink type. Don't repeat the same fact in dek, context, facts and footer.
8. **Money.** Seller net only on earnings cards. One time format per card (7 pm, not 19:00 next to 9 pm).
9. **One idea per card**; digests use a cover.

Any fail → edit JSON → re-render → read again.

## Anti-patterns

- A small number floating on a tall empty card. Use the full hero, a spark or composition, and a bottom facts row.
- `A · B · C` runs of numbers in one muted line. Use facts, a roster, or a table.
- Grey used for negative values (reads as disabled). Use ink with ▼.
- Leading with the unit when the question is the gap ("2.0 oz" when the user wants "under break-even by 6.3%").
- Two accounts per bullet. One row each, with aligned figures.
- Legends when a direct end label fits; boxed charts; axis lines; two bright series; thick strokes.
- Borders or outlined boxes, washes, glow, drop shadows, gradients other than the one area fade, emoji decoration.
- Editorial slab headlines or ALL-CAPS tracked eyebrows; panels nested inside panels.
- Stitching several cards into one image.
- Selectable options drawn on the card. Use a chat widget.

## Contributing

**Never shoehorn.** If no type fits, do not force `brief` / `kpi` / etc. The user asks a Grok Bot to launch a **Cursor Cloud Agent** (Opus preferred) to add one template that matches this theme. The prompt and the acceptance bar are in `docs/NEW_LAYOUTS.md`.

New type = a function in `render/warmdark/templates/*.py` with `@template("name", "alias")`, a schema branch in `refs/manifest.schema.json`, an example in `examples/` with fictional round numbers, a row in the chooser, then `python3 render/warm_dark.py` on that example under `--strict`. Feed failures (clip, void, wrong type) back into this file in the same change. No new palette and no new aspect ratio unless the user asked for a theme change (`docs/THEMING.md`).

`multi_institution_nw`, `cashflow_sankey`, `nw_delta_weekly`, `notes_strip`, and `home_equity_card` live in `templates/networth.py` because roster, allocation, kpi, and spend could not show excluded-but-modeled rows, flows, driver sums, note marks, or an ownership formula. Don't fold net-worth reporting back into those. A legacy alias on the notes template still accepts old manifests; new JSON says `notes_strip`.

Domain bots own their data and render with this skill when they report to the user. Install and fleet training: `docs/INSTALL_GROK_BOT.md`.
