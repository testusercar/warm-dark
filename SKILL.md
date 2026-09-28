---
name: Aaron fleet comms
description: >-
  Use when any Grok Bot (Ledger, Booth, Radar, Jeeves, Vitals, Max, Scout, …)
  reports metrics, status, charts, digests, briefs, alerts, or decisions to
  Aaron as image cards. Warm Dark v3 card system (clean fintech, Wealthsimple /
  Robinhood feel): JSON manifest → Python renderer → separate PNGs. 29 card
  types, mandatory per-card QA before send.
---
# Aaron fleet comms — Warm Dark v3

How the **fleet talks to Aaron**. Prefer a card over a wall of text whenever a report has a number that matters, a trend, a comparison, a list of 3+ items, a status change, or a decision. Quiet one-line answers stay plain text.

**Locked brand (v3, 2026-09-27):** canvas `#1a1814` full-bleed · ink `#f4f2ea` · muted `#9a9688` · olive `#c4d44a` = *good only* · **Inter Display** titles + numerals, **Inter** everything else (no slab) · sentence-case labels, no tracked caps · soft raised **surfaces** (`#25231f`, radius 24) group facts, lists, options and callouts — tone separates, never a border · thin chart strokes (2.6 px current), one soft fade under a current line is the only gradient · no border, frame, wash, title rule, glow, drop shadow · no cyan Signal Dark · money = **seller net** only · A-series portrait 810×1146 (landscape 1146×810 only for wide charts) · separate PNGs, never mosaics · ≤3–4 punches per card.

## Standing rule — decisions (2026-09-28)

**Never put selectable options on a Warm Dark card.** Cards are informational only. When Aaron must choose, send context as a card (`brief`, `alert`, `kpi`, …) and put the actual choice in a **native chat widget** (`SendToUser` type `widget`) in the same turn. Do not ask him to reply A/B/C to a card.

The `decision` card type is **retired for selection**. Do not invent new lettered option cards. If you still render a legacy `decision` PNG for context, it must not be the picker — the widget is mandatory and is the only place options are selectable.

Read order on every card: **hero number → context → facts.** Title is a calm 46 px label for *what*; the hero numeral (Inter Display Light, auto-fit 88–172 px) carries the weight; context and delta sit right under it; supporting chart or list in the middle; facts in one soft panel at the bottom.

Design rationale: `refs/DESIGN.md` · specimen: `refs/specimen.png` · tokens: `refs/tokens.json` · schema: `refs/manifest.schema.json` · every type in one manifest: `examples/showcase.example.json` · gallery: `artifacts/gallery/README.md` in the source repo.

## Low-token path (always)

1. Pick the type from the chooser below. Copy the matching example from `examples/*.example.json` and replace the data. Don't invent layout.
2. Write the manifest (one file, many cards). Titles 1–3 words; detail goes in `dek`, `context`, or facts.
3. Render:
   ```bash
   python3 /home/box/agent-data/workflows/aaron-fleet-comms/render/warm_dark.py cards.json
   ```
   Prints one PNG path per line. Warnings go to stderr: **fix every warning** (overflow, truncation, dead space — an empty surface counts as empty — gross money). `--strict` exits 2 on any warning. `--validate` checks the schema only. `--types` lists types. `render/signal_dark.py` still works (same renderer).
4. **QA every PNG** (below). Re-render until clean.
5. Send all PNGs in **one** SendToUser `images` array, in manifest order. Chat text: one short line or none.

Formats: numbers are pre-formatted strings you control (`"C$140,022"`, `"7h 12m"`, `"−6.1%"`). Chart data are raw numbers plus `fmt` (Python format string: `"C${:,.0f}"`, `"{:.1f}%"`, `"{:k}"` = compact 4.2k). Use real minus `−` or plain `-`; the renderer fixes it.

Inline markup in any text field: `**strong**` (ink semibold) · `{{+12%}}` (olive if +, ink if −).

## Chooser — pick the lightest type that tells the story

| Aaron needs to know… | Type | Hero |
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
| Aaron must choose | **chat widget** (not a card) | informational card optional; selectable options only in native `widget` |
| Consistency across days/weeks | `heatmap` | 7×N grid, best cell olive |
| Where a flow leaks | `funnel` | step-conversion bars, weakest step flagged |
| A photo or screenshot carries it | `hero` | image + one line + facts |
| Net worth across institutions / buckets, some modeled but left out | `multi_institution_nw` | included total + stacked bar + bucket rows; `included: false` rows whispered below |
| Where a period's money came from, went, and landed | `cashflow_sankey` | income → categories → accounts flows; saved flows olive |
| Net worth vs last week, and what moved it | `nw_delta_weekly` | NW numeral + one delta; spark + ≤4 signed drivers |
| Manulife notes performance (exactly 3) | `manulife_notes_strip` | best-known value + 3 strips: principal · accrued · MTM vs principal |
| Aaron's share of a property | `home_equity_card` | equity dollars + formula ledger: value × % − mortgage share + joint cash share |

**Not everything is bullets.** If you wrote three bullets of narrative, you probably want `kpi`, `gap`, `alert`, or `radar`.

## Manifest

```json
{
  "version": 2,
  "agent": "Ledger", "domain": "Finance", "date": "Sep 27",
  "footer": "Finance-xai · Wealthsimple · read-only",
  "outdir": "/tmp/cards/ledger",
  "cards": [ { "type": "kpi", "slug": "cad-assets", "title": "CAD assets", "value": "C$140,022" } ]
}
```

Any card may also set `dek`, `footer`, `agent`/`domain`/`date` overrides, `format: "landscape"`, `partial`, `facts` (≤4 × `{label, value, sub?, delta?, tone?}` — rendered as one soft stat panel), and `image`. v3 changed no fields: every v1/v2 manifest renders unchanged, just in the new look.

`delta` is `"+12%"` or `{"value":"−14%","note":"vs typical","polarity":"down_good"}`. **Colour = verdict, arrow = direction:** olive when the change is good (up or down), ink when it's bad or has no verdict, muted only when flat. `polarity: "down_good"` for spend, resting HR, drift; `polarity: "neutral"` for moves with no verdict (a price cut toward comps). Put every change in a `delta`, never in grey `sub` text.

## Type examples (minimal; full versions in `examples/`)

```jsonc
// kpi — examples/ledger-sunday 01-cad-assets, booth net-earnings
{"type":"kpi","title":"CAD assets","dek":"Five accounts at Sunday close","value":"C$140,022",
 "delta":{"value":"+C$1,204","note":"vs last Sunday"},"context":"Net of the card: **C$137,289**",
 "composition":[{"label":"Money market","num":61501},{"label":"Savings","num":40017}],
 "facts":[{"label":"Card owed","value":"−C$2,733"},{"label":"USD cash","value":"US$10,397","tone":"muted"}]}
// spark instead of composition: "spark":{"values":[…],"prior":[…],"x":["Sep 1",…,"Sep 27"],"positive":true}

// scoreboard
{"type":"scoreboard","title":"This week","current":{"label":"This week","value":"US$342"},
 "prior":{"label":"Last week","value":"US$296"},"delta":{"value":"+15.5%","note":"net earnings"},
 "rows":[{"label":"Orders","current":58,"prior":49},{"label":"Net per order","current":5.9,"prior":6.04,"fmt":"US${:.2f}"}]}

// line (dual) — nulls end a series early; landscape for long ranges
{"type":"line","title":"Pacing August","value":"+US$280","delta":{"value":"+28%","note":"ahead on day 27"},
 "series":[{"role":"prior","name":"August","values":[…]},{"role":"current","name":"September","values":[…,null]}],
 "x":["Day 1",…],"x_ticks":[0,9,19,29],"fmt":"US${:,.0f}","axis_fmt":"{:k}","zero":true,
 "annotations":[{"at":2,"text":"Back-to-school bundle","sub":"US$85 in a day"}]}

// area
{"type":"area","title":"HRV, 30 nights","value":"58 ms","delta":"+9%","values":[…],"x":["Aug 29",…,"Sep 27"],
 "callouts":[{"at":7,"text":"Red-eye to Toronto","sub":"41 ms low"}],"refs":[{"value":53,"label":"Aug avg 53 ms"}]}

// bars — one highlight; "stacked":true + several series for parts
{"type":"bars","title":"Net by product line","categories":["Bundles","Math","ELA"],
 "series":[{"name":"Net","values":[412,336,248]}],"highlight":"Bundles","fmt":"${:,.0f}"}

// brief / watch
{"type":"brief","title":"Canada","points":[{"lead":"C-39 splits the CPC on labour","text":"Union MPs break with Kenney."}],
 "takeaway":"Labour is the thread to pull into Quebec's final week."}
{"type":"watch","title":"Watch this week","points":[{"lead":"Quebec debate","text":"Last before advance polls.","when":"Thu"}]}

// alert — severity: sev1 | sev2 | sev3 | info | blocked | resolved
{"type":"alert","severity":"sev1","status":"Blocked","since":"since 06:12 · 7h 32m","title":"Nightly sweep failing",
 "body":"10 of 10 sweeps failed at sign-in.","detail":"Token expired; needs your 2FA.",
 "impact":[{"label":"Runs failed","value":"10/10"}],
 "timeline":[{"time":"06:12","text":"First failure","state":"done"},{"time":"13:44","text":"Waiting on 2FA","state":"now"}],
 "next":{"label":"Needs you","owner":"Scout","text":"Approve the prompt on your phone."}}

// gap — before/after or to-target
{"type":"gap","title":"OD1 price cut","value":"−C$7","delta":{"value":"−4.5%","polarity":"neutral"},
 "before":{"label":"Was","value":"C$155","num":155},"after":{"label":"Now","value":"C$148","num":148},
 "target":{"label":"Comps median","value":"C$145","num":145},"polarity":"down_good"}

// allocation
{"type":"allocation","style":"donut","title":"Where CAD sits","total":"C$140k","total_label":"CAD assets",
 "items":[{"label":"Money market","num":61501,"value":"C$61,501"},{"label":"Savings","num":40017,"value":"C$40,017"}]}

// timeline — state: past | today | next | later | done
{"type":"timeline","title":"Week ahead","events":[{"date":"Sep 29","dow":"Tue","text":"Dentist — Dr. Park","meta":"2:15 pm","state":"next"}],
 "note":"Tuesday is the only hard stop."}

// holdings
{"type":"holdings","title":"Holdings","rows":[{"name":"Gold","sub":"4.942 oz","value":"C$29,951","weight":32,"pl":"−C$1,938"}],
 "total":{"label":"Total","value":"C$94,316","pl":"−C$1,533"}}

// roster
{"type":"roster","title":"Wealthsimple","groups":[{"label":"Cash","subtotal":"C$107,208",
 "items":[{"label":"Money market","value":"C$61,501","num":61501}]},{"label":"Owed","items":[{"label":"Credit card","value":"−C$2,733","num":-2733}]}],
 "total":{"label":"Net CAD","value":"C$137,289","sub":"assets − card"},"aside":{"label":"USD chequing","value":"US$10,397"}}

// spend
{"type":"spend","title":"Spend this week","value":"C$612","delta":{"value":"−14%","polarity":"down_good","note":"vs typical"},
 "days":[42,118,36,64,188,96,68],"merchants":[{"name":"Costco","sub":"groceries","value":"C$188","num":188}]}

// breakeven — steps = cost basis after each buy (stepped reference)
{"type":"breakeven","title":"Gold vs break-even","value":"−6.1%","delta":{"value":"C$392/oz","dir":"down","good":false,"note":"under break-even"},
 "price":{"values":[…],"x":[…],"x_ticks":[0,9,18,26],"label":"C$6,061"},
 "steps":[{"at":2,"value":6210,"label":"buy 2.0 oz"},{"at":14,"value":6351,"label":"+1.5 oz"}],"be_label":"C$6,453"}

// vitals
{"type":"vitals","title":"Sleep","value":"7h 12m","delta":{"value":"+24m","note":"vs 7-night avg"},"score":84,
 "stages":[{"label":"Deep","minutes":88},{"label":"REM","minutes":106}],
 "history":{"values":[6.4,6.9,7.5],"labels":["Thu","Fri","Sat"],"goal":8}}

// radar
{"type":"radar","title":"Canada","items":[{"headline":"C-39 splits the CPC on labour","why":"Whip count Tuesday.",
 "sources":["CBC","Globe and Mail"],"when":"2h","signal":"rising"}],"takeaway":"Labour is the wedge to watch."}

// experiment
{"type":"experiment","title":"Onboarding test","verdict":"Ship B","lift":{"value":"+18%","note":"relative lift"},
 "confidence":"**96%** chance B beats A","winner":"B","fmt":"{:.1f}%",
 "variants":[{"key":"A","name":"A","label":"Current","rate":11.2,"ci":[9.5,12.9],"n":1204,"control":true},
             {"key":"B","name":"B","label":"Guided","rate":13.2,"ci":[11.4,15.1],"n":1206}]}

// progress
{"type":"progress","title":"2026 net goal","value":"75%","current":{"value":"US$11,240","num":11240},
 "goal":{"value":"US$15,000","num":15000},"on_pace":true,
 "pace":{"expected_frac":0.738,"actual":[…],"required":[…],"projection":[…],"x":[…]}}

// empty — or add "partial":{"ok":2,"of":3,"note":"eBay stale 3h"} to any card
{"type":"empty","title":"Carrier scans","message":"No scans yet","skeleton":"list",
 "reason":"Label created; not picked up.","expected":"Scout checks again at 18:00."}

// cover — first card of a digest; series dots switch on automatically
{"type":"cover","kicker":"Week 39 · Sunday close","title":"Sunday ledger","dek":"Assets up, gold under water.",
 "items":[{"title":"CAD assets","note":"net of card C$137,289","value":"C$140,022","delta":"+0.9%"}]}

// decision — RETIRED for selection (2026-09-28). Do not use as a picker.
// Send an informational brief/alert/kpi card if useful, then a SendToUser widget for the choice.
// Legacy shape kept only so old manifests still render:
{"type":"decision","title":"Renew the Globe?","dek":"Auto-renews Oct 2 at C$34.99/mo.",
 "options":[{"key":"A","label":"Cancel","detail":"Use PressReader.","recommended":true},{"key":"B","label":"Downgrade"}],
 "why":"Opened 3× in September.","deadline":"Reply by Oct 1, 6 pm","default":"no reply = A"}

// heatmap — weeks = columns of 7 values (Mon→Sun); best = [week, day]; null = not yet (hollow cell)
{"type":"heatmap","title":"Sales days","value":"7.9","weeks":[[3,4,2,5,4,1,2],…],"best":[6,1],"best_label":"best day · 14 orders"}
// low is good (drift, errors)? bright must still mean better:
{"type":"heatmap","title":"Bedtime drift","weeks":[…],"invert":true,"legend":["off target","on target"]}

// funnel
{"type":"funnel","title":"Store funnel","value":"1.15%","stages":[{"label":"Product views","num":18420,"value":"18,420"},
 {"label":"Purchased","num":212,"value":"212"}]}

// hero — photo/screenshot carries it
{"type":"hero","title":"Shipped","body":"Palantir #12592 · arrives **Oct 1**","image":"/abs/path/tracking.png",
 "facts":[{"label":"Arrives","value":"Oct 1"}]}
```

## Digests (2–4 cards)

Start with a `cover` whose items mirror the cards that follow (title, one-line note, headline value). The renderer turns on series dots so Aaron can see card 3 of 5 even if chat reorders images. Keep every card self-contained: each one must make sense alone.

## Mandatory per-card QA (before SendToUser)

Open **each** PNG with Read (vision), one by one:

1. **No clip or overlap.** Title, hero, labels and footer fully visible; no label sits on a line or another label.
2. **Right type.** Narrative bullets → rewrite as `kpi` / `gap` / `alert` / `radar`. A number with history → add `spark` or use `line`.
3. **One hero.** One big thing. If two numbers fight, move one into facts.
4. **Olive = good.** Nothing olive that isn't good; no grey for bad news. Same entity, same shade across cards (first series brightest).
   Surfaces are for grouping only: a panel with nothing meaningful in it is dead space, not decoration.
5. **Numbers agree.** The same figure (a month total, a balance) is identical on every card in the send, and deltas match the values they compare. Net worth on `multi_institution_nw` = `nw_delta_weekly` hero; notes total = the notes bucket; home equity = the excluded row.
6. **Dead space.** No empty band taller than about a quarter of the card (the renderer warns). Fix with facts, spark, timeline, image, or a denser type. Never pad with filler copy.
7. **Density.** ≤3–4 punches; cut copy or split the card, never shrink type. Don't repeat the same fact in dek, context, facts and footer.
8. **Money.** Seller net only on earnings cards. One time format per card (7 pm, not 19:00 next to 9 pm).
9. **One idea per card**; digests use a cover.

Any fail → edit JSON → re-render → Read again.

## Anti-patterns (seen in the hated cards)

- A small number floating on a tall empty card. Use the full hero, a spark or composition, and a bottom facts row.
- `A · B · C` runs of numbers in one muted line. Use facts, a roster, or a table.
- Grey used for negative values (reads as disabled). Use ink with ▼.
- Leading with the unit when the question is the gap ("4.942 oz" when Aaron wants "under break-even by 6.1%").
- Two accounts per bullet. One row each, with aligned figures.
- Legends when a direct end label fits; boxed charts; axis lines; two bright series; thick HUD strokes.
- Signal Dark cyan, borders or outlined boxes, washes, glow, drop shadows, gradients other than the one area fade, emoji decoration.
- Editorial slab headlines or ALL-CAPS tracked eyebrows (v2 look); panels nested inside panels.
- Stitching several cards into one image.

// ---- Ledger net worth (examples/ledger-networth.example.json) ----

// multi_institution_nw — total = sum of included rows (auto if omitted, checked if num given);
// "included": false (or "exclude": true) keeps a row modeled at its share but out of the total
{"type":"multi_institution_nw","title":"Net worth","total":{"label":"Current net worth","value":"C$366,236","num":366236},
 "rows":[{"label":"Liquid CAD","sub":"Wealthsimple cash + crypto","value":"C$110,072","num":110072},
         {"label":"Maxxit","sub":"phantom · 8× CY profit","share":"3% stake","value":"C$144,000","num":144000},
         {"label":"Credit card","value":"−C$2,733","num":-2733},
         {"label":"Home equity","sub":"nets CIBC joint + mortgage","share":"45% share","value":"C$197,280","num":197280,"included":false}],
 "excluded_label":"Not in current net worth","all_in":{"label":"All-in with home equity","value":"C$563,516"}}

// cashflow_sankey — columns inferred from links (or node "column"); "tone":"good" = olive (saved/invested);
// in ≠ out on a middle node warns; >7 nodes in a column or >14 total → "format":"landscape"
{"type":"cashflow_sankey","title":"September cashflow","value":"C$4,722","delta":{"value":"+C$610","note":"saved vs August"},
 "stages":["Income","Where it went","Landed in"],
 "nodes":[{"id":"pay","label":"Net pay","value":"C$9,850"},{"id":"rent","label":"Rent","value":"C$2,650"},
          {"id":"saved","label":"Saved","value":"C$7,200","tone":"good"},{"id":"chq","label":"Chequing","value":"C$2,650"},
          {"id":"mm","label":"Money market","value":"C$7,200"}],
 "links":[{"source":"pay","target":"rent","num":2650},{"source":"pay","target":"saved","num":7200},
          {"source":"rent","target":"chq","num":2650},{"source":"saved","target":"mm","num":7200}]}

// nw_delta_weekly — one delta; "polarity":"down_good" for debt; drivers must sum to num − prior.num
{"type":"nw_delta_weekly","title":"Net worth","value":"C$366,236","num":366236,
 "delta":{"value":"+C$3,412","note":"+0.9% vs last Sunday"},"prior":{"label":"Sep 20","value":"C$362,824","num":362824},
 "spark":{"values":[…],"x":["Jul 12",…,"Sep 27"]},
 "drivers":[{"label":"Cash saved","value":"+C$3,500","num":3500},{"label":"Gold","value":"−C$412","num":-412}]}
// no spark/drivers? "composition":[{label,num}] fills the lower half instead

// manulife_notes_strip — exactly 3; "mtm": null = not known yet (strip shows MTM pending, hero uses principal + accrued)
{"type":"manulife_notes_strip","title":"Manulife notes","value":"C$70,806","delta":{"value":"+C$806","note":"vs C$70,000 principal"},
 "notes":[{"name":"TSX 60 MPN","principal":{"value":"C$25,000","num":25000},"accrued":{"value":"C$612","num":612},
           "mtm":{"value":"C$25,840","num":25840},"maturity":"Mar 2028"}, …],
 "note":"Manual from Manulife statements · no Plaid feed"}

// home_equity_card — hero = property × equity_pct − mortgage × share + joint cash × share (shares default to equity_pct)
{"type":"home_equity_card","title":"Home equity","status":"Pre-closing","equity_pct":45,"equity_source":"Westway · Coda",
 "property":{"value":"C$1,200,000","num":1200000},"mortgage":{"label":"Mortgage share","value":"C$780,000","num":780000},
 "joint_cash":{"label":"Joint cash share","value":"C$18,400","num":18400},"num":197280}

## Contributing

**Never shoehorn.** If no type fits, do not force `brief` / `kpi` / etc. Message **Jeeves** with the content shape and why existing types fail. Jeeves is empowered (Aaron 2026-09-27) to launch an **Opus-only** Cloud Agent and land a new template in this skill **without asking Aaron**. Domain bots request; Jeeves ships; requesting bot gets an FYI when the type is live.

New type = a function in `render/warmdark/templates/*.py` with `@template("name", "alias")`, a schema branch in `refs/manifest.schema.json`, an example in `examples/`, a row in the chooser, then `python3 tools/build_gallery.py` and `pytest` in the source repo. Feed failures (clip, void, wrong type) back into this file the same turn. No fourth palette, no new aspect ratio without Aaron.

Landed this way (2026-09-27, Ledger request): `multi_institution_nw`, `cashflow_sankey`, `nw_delta_weekly`, `manulife_notes_strip`, `home_equity_card` in `templates/networth.py`. They exist because roster/allocation/kpi/spend could not show excluded-but-modeled rows, flows, driver sums, note MTM, or an ownership formula. Don't fold net-worth reporting back into those.

Owner for socialization + template pipeline: **Jeeves**. Domain bots own their data and render here when reporting to Aaron.

