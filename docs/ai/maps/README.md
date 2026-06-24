# Catan Variants — Research Compilation (maps/)

This folder collects research on official Catan games, expansions, standalone
editions, fan maps, and a third-party board generator. The goal is **engine
modeling**: for each variant, capture the rules that change how a game engine
must represent state and transitions, and map those onto the knobs in
[`../variation-features.md`](../variation-features.md).

This is a research scratchpad. Nothing here is authoritative. Treat every
"official" rule summary as **needs verification against the actual rulebook PDF**
before it is encoded as data or code.

## Contents

| File | Topic |
|------|-------|
| [`official-base-game.md`](./official-base-game.md) | CATAN base game (3–4 and 5–6 player extension) |
| [`official-seafarers.md`](./official-seafarers.md) | Ships, islands, gold, pirate, scenario VPs |
| [`official-cities-and-knights.md`](./official-cities-and-knights.md) | Commodities, knights, walls, barbarians, progress cards, event die |
| [`official-traders-and-barbarians.md`](./official-traders-and-barbarians.md) | A bundle of smaller scenarios (caravans, fishery, rivers, etc.) |
| [`official-explorers-and-pirates.md`](./official-explorers-and-pirates.md) | Fog/exploration, ship-as-carrier, settlers, missions |
| [`standalone-editions.md`](./standalone-editions.md) | Themed standalones and spin-offs from the rules hub |
| [`board-generator-bunge.md`](./board-generator-bunge.md) | **Data model of the catan.bunge.io generator (source code found)** |
| [`fan-maps-lost-maps.md`](./fan-maps-lost-maps.md) | The catancollector.com "Lost Maps" catalogue + special hex rules |

## Sources

- Official rules hub: <https://www.catan.com/understand-catan/game-rules> (owned
  by CATAN GmbH). The hub lists free PDF rulebooks for the base game, all major
  expansions, variants/scenarios, Rivals, Starfarers, spin-offs, and an archive.
- Board generator: <https://catan.bunge.io/> ("BetterCatan BoardGenerator" by
  Jamison Bunge). Source code located via a public fork:
  <https://github.com/DarrenSem/catan> (MIT license).
- Fan map index: <https://catancollector.com/maps-scenarios/the-lost-maps>
  (fan-curated, **not official**; "Catan" IP rests with CATAN GmbH).

## Caveats (read before trusting anything here)

- **catan.com per-game rule pages are JavaScript-heavy and could not be fetched
  reliably during this research pass.** The rules hub page itself loaded (it is
  the index of titles + PDF links). The detailed official rule summaries below
  are therefore drawn from general knowledge of the published rulebooks and are
  flagged **UNVERIFIED** where a specific number/threshold matters. Verify
  against the actual PDF before encoding.
- **catancollector.com stores layouts and special rules as IMAGES.** Page *text*
  gives only metadata (sets needed, player count, VP target, short rule notes).
  Anything that would require reading the board diagram is flagged
  **"layout in image, needs manual transcription."**
- Content paraphrased from the sources above for licensing compliance. No source
  text is copied verbatim beyond short factual labels; no images are stored.

## Most engine-relevant takeaways (summary)

1. **Board generator data model (see `board-generator-bunge.md`):** confirms the
   row-based representation in `src-notes.txt`. A board is a flat array of tiles
   `{ chit, resource }`; adjacency is a hardcoded index→neighbor lookup table;
   number/resource bags are fixed multisets shuffled then rejection-tested
   against placement constraints. **It models hexes + numbers only — no ports,
   no vertices/edges, no axial coordinates.** Good reference for tile bags and
   constraints; insufficient for settlements/roads.
2. **Phase machine is the real extensibility surface.** Expansions add phases
   (event-die + barbarian step in C&K; exploration reveal in E&P), which is
   exactly the FSM design called out in `variation-features.md`.
3. **Additive state wins.** Commodities, knights, walls, fog, pirate position,
   barbarian track are all *extra fields* the base game leaves empty.
4. **Victory = sum of point sources** holds across every variant; only the VP
   target and the set of contributing sources change.
