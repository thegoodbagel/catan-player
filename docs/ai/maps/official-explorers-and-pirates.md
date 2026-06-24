# Official — CATAN: Explorers & Pirates

Source: official rules hub <https://www.catan.com/understand-catan/game-rules>
(Explorers & Pirates PDF) and the E&P FAQ
<https://www.catan.com/faq/explorer-pirates>. Content paraphrased for licensing
compliance. Specifics are **UNVERIFIED** until checked against the PDF.

E&P is built around **exploration of a hidden map**, **ships that carry units**,
and a sequence of **scenarios** that culminate in a combined campaign. It is the
clearest example of the [HARD] "fog reveal / moving board" knob.

## The scenarios (build up to the full game)

> Names from the published overview; rules **UNVERIFIED**.
- **Land Ho!** — intro to ships, exploration, and settlers.
- **Pirate Lairs** — clear pirate lairs from the sea.
- **Fish for Catan** — fishing grounds / fish hauls.
- **Spices for Catan** — deliver spices to harbor villages.
- **Explorers & Pirates** — the large combined scenario using all systems.

## Delta from base game

### Topology + fog (knob 1 / knob 2 / knob 13) [RULE][STATE]
- The map starts **mostly face-down**: unknown hexes are placed as **fog/face-
  down tiles** and **revealed when a ship reaches an adjacent sea space**.
- Revealing a tile can grant a one-time bonus (gold, resources, or place a
  resource on a new land hex). The board literally **grows in knowledge** during
  play — production depends on what has been discovered.
- This is the **fog/unknown-tile** knob: requires hidden state + a reveal phase.

### Buildings & pieces (knob 5) [RULE][STATE]
- **Ship** is not just a road over water — it is a **vehicle with movement
  points** that **carries cargo**: a **settler** (to found new settlements far
  away), **spices/fish**, or a **crew**. Ships move each turn (movement points),
  unlike Seafarers' place-and-lock ships.
- New unit: **settler** — transported by ship, then converted into a settlement
  on a discovered island.
- **Harbor settlements / villages** as delivery targets in some scenarios.

### The pirate (knob 6) [RULE][STATE]
- **Pirates** are NPC ships on the sea; bumping into them triggers a **strength
  check / combat** (roll vs. pirate strength). Different from both the base
  robber and the Seafarers pirate-blocker.

### Turn structure (knob 7) [RULE]
- Adds an explicit **ship movement phase** (spend movement points) and a
  **fog-reveal step** when a ship enters a sea space next to face-down land.

### Victory conditions (knob 10) [RULE]
- Scenario-specific **mission/objective VPs** (e.g. settling, clearing lairs,
  delivering goods) on top of the usual settlement/city points. Targets vary per
  scenario, often combined-campaign style. **UNVERIFIED.**

## Engine notes

- This variant breaks the base assumption that **the full board is known at
  setup**. The board model must support **hidden tiles + a reveal operation**,
  and production must only consider revealed hexes.
- Ships need **movement points and a cargo slot** — genuinely new piece state,
  not a road analogue. This is more like a unit-movement game than placement.
- Pirate combat introduces a **dice-resolved PvE encounter** phase.
- Strongest case in the official line for the engine supporting **dynamic
  topology** (tiles added/flipped mid-game), flagged [HARD] in
  `../variation-features.md`.
