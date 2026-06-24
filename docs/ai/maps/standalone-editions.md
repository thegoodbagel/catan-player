# Official — Standalone Editions, Variants & Spin-offs

Source: the catalogue listed on the official rules hub
<https://www.catan.com/understand-catan/game-rules>. The hub groups titles into
sections; below is the **catalogue as published there** plus engine-relevant
notes from general knowledge. Per-title rules are **UNVERIFIED** (the per-game
rule PDFs were not fetched this pass). Content paraphrased for licensing
compliance.

The point of this doc is breadth: which official products exist and which knobs
they bend, so the engine's variant system can be scoped. Most standalones are
**not** loadable as "just a map" — they swap whole rule sets (knob 13 [HARD]).

## Rules-hub catalogue (as listed)

### Base game & expansions
- CATAN (base) — see `official-base-game.md`
- Seafarers — see `official-seafarers.md`
- Cities & Knights — see `official-cities-and-knights.md`
- Traders & Barbarians — see `official-traders-and-barbarians.md`
- Explorers & Pirates — see `official-explorers-and-pirates.md`

### Variants & scenarios (small add-ons)
- Soccer Fever
- Treasures, Dragons & Adventurers
- Crop Trust
- Legend of the Sea Robbers
- Legend of the Conquerors
- The Helpers
- Frenemies
- Oil Springs
- The Fishermen of Catan

### Rivals for Catan (2-player card game)
- Base Game; "Age of Darkness" expansion; "Age of Enlightenment" expansion;
  Tournament Game; Deluxe Edition

### Catan Starfarers (space 4X-ish)
- Base Game; New Encounters; Starfarers Duel

### Catan On the Go (compact)
- Catan Dice Game; Struggle for Catan; Catan Traveler

### Spin-offs / themed standalones
- New Energies; Dawn of Humankind; Rise of the Inka; A Game of Thrones Catan;
  Settlers of America – Trails to Rails; Catan Family Edition; Star Trek Catan;
  Catan Geographies: Germany; Catan – Ancient Egypt; Candamir – The First
  Settlers; Elasund – The First City; Struggle for Rome; Catan Histories –
  Merchants of Europe; Starship Catan; Catan 25th Anniversary Edition

### Catan Junior / Print & Play / Archive
- Catan Junior; The Kids of Catan; Print & Play (Easter Bunny); plus an Archive
  of pre-2023/2025 editions, combinations, the Catan Card Game, old Starfarers,
  and non-Catan games.

## Engine-relevant notes on selected titles

> All **UNVERIFIED** — based on general knowledge, not the fetched PDFs.

- **Oil Springs** (scenario add-on): introduces **oil** as a special resource and
  an **environmental/pollution track**; oil can be spent for powerful effects but
  triggers disasters and a shared-loss condition. Knobs 4 (new resource), 6/13
  (disaster mechanic), 10 (pollution can end the game). A classic "rule module +
  token + global counter" case.
- **Rise of the Inka**: cities can **decline/be removed** ("decline of cities"),
  inverting the usual monotonic growth. Knob 13 [HARD] — pieces can be lost.
- **A Game of Thrones Catan / Star Trek Catan / Ancient Egypt / Geographies**:
  mostly **re-themes of base + light special pieces** (e.g. Star Trek adds
  starship/support cards). Mostly knob 2/9/10 swaps over the base FSM.
- **New Energies**: modern eco theme with **power plants** (fossil vs.
  renewable) and a **pollution/score interaction**. Knob 4/5/10/13.
- **Settlers of America – Trails to Rails**: a **pickup-and-deliver train game**
  using the Catan brand — effectively a different game; not a Catan map variant.
- **Rivals for Catan / Starfarers / On the Go**: **different game systems**
  (card duel, space 4X, dice/compact). Out of scope for a hex-board engine
  except as inspiration.

## Engine notes

- Treat standalones in three tiers:
  1. **Re-theme over base** (Geographies, Star Trek, GoT, Ancient Egypt,
     Family) → mostly knob 2/9/10 data swaps; cheap.
  2. **Base + one rule module** (Oil Springs, New Energies, the small
     variants) → one rule module + a token/counter.
  3. **Different game entirely** (Rivals, Starfarers, Settlers of America,
     On-the-Go) → not targets for this engine.
- Only tier 1 (and some tier 2) are realistic "load as a scenario" candidates.
