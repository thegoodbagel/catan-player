# Dimensions of Variation in Catan

The goal of this document is NOT to list every scenario. It is to enumerate the
*knobs* that scenarios turn. If the engine can represent each knob as data or as
a swappable rule module, then most scenarios become configuration rather than new
code. Each section notes how hard the knob is to support and which engine piece
owns it.

Legend for effort:
- [DATA]  = should be expressible as map/config data, no new code
- [RULE]  = needs a swappable rule module / extra phase
- [STATE] = needs extra fields in game state
- [HARD]  = touches multiple systems; treat as a real feature, not config

---

## 1. Board topology (the physical layout)

- Number of hexes and overall shape (small island, large island, archipelago).      [DATA]
- Row structure: each row offset +/- relative to the previous, variable length.     [DATA]
- Edge of board: is the outer ring sea, or do land hexes touch the boundary?         [DATA]
- Multiple disconnected landmasses / islands.                                        [DATA]
- Fixed vs randomized layout (tournament maps are often fixed; base game shuffles).  [DATA]

Engine implication: topology is a graph of hexes/vertices/edges loaded from a
file. Bigger or weirder boards = bigger graph. No code change if adjacency is
data-driven and addressed by integer IDs.

## 2. Hex / tile types

- Standard resource tiles: forest(wood), pasture(sheep), field(grain),
  hills(brick), mountains(ore).                                                      [DATA]
- Desert (produces nothing, default robber start).                                   [DATA]
- Sea/ocean tiles.                                                                   [DATA]
- Gold field (produces a resource of the player's choice).                           [RULE]
- Fog/unknown tiles (revealed on exploration — Explorers & Pirates, fan "mist" maps).[RULE][STATE]
- Special hazard hexes (fan-made): volcano, iceberg, jungle, earthquake, etc.        [RULE]
  See special-hexes section in scenario-index.md.

Engine implication: a tile has a *type*; a type maps to "what it produces" and
optionally "what special rule fires." Adding a new tile type = new entry in a
type table + (maybe) a rule module.

## 3. Number tokens (dice-roll production)

- Which numbers sit on which hexes.                                                  [DATA]
- The dice probability curve (two d6 = 2..12, peak at 7).                            [DATA]
- Alternate dice schemes: event die (Cities & Knights adds a 3rd colored die).       [RULE]
- "No 6/8 adjacent" placement constraints (a generation rule, only for auto-maps).   [RULE]

## 4. Resources & commodities

- Base 5 resources.                                                                  [DATA]
- Commodities (Cities & Knights: coin, cloth, paper) layered on top.                 [STATE][RULE]
- Gold as a wildcard resource.                                                       [RULE]
- Variant maps that change which resources exist or rename them (themed editions).   [DATA]

## 5. Buildings & pieces

- Settlement, city, road (base).                                                     [DATA]
- City walls, knights (Cities & Knights).                                            [STATE][RULE]
- Ships / boats as a road-equivalent over water (Seafarers).                         [RULE][STATE]
- Bridges, special pieces in fan/standalone editions.                                [RULE]
- Piece supply limits per player (how many of each you may build).                   [DATA]

## 6. The robber (and friends)

- Standard robber: moved on a 7, blocks a hex, steals a card.                        [RULE]
- Pirate ship (Seafarers): robber-equivalent on the sea.                             [RULE][STATE]
- Barbarians (Cities & Knights): a shared threat advancing on a track.               [RULE][STATE]
- Variant "no robber" or "friendly robber" (house rules).                            [RULE]

## 7. Turn structure (the phase machine)

- Standard: (optional dev card) -> roll -> distribute/rob -> trade/build phase.       [RULE]
- Extra phases for variants: barbarian roll & resolution, exploration reveal,
  event-die effects.                                                                 [RULE]
- This is the FSM. A variant = a different ordered set of phases. THIS is the most
  important extensibility surface; design it as assembled-from-data, not hardcoded.

## 8. Trading rules

- Bank trade 4:1.                                                                    [DATA]
- Harbor/port trades 3:1 generic and 2:1 specific.                                   [DATA]
- Port locations and types.                                                          [DATA]
- Player-to-player trading: allowed? restricted? (some variants limit it).           [RULE]

## 9. Development cards / progress cards

- Base dev deck: knight, victory point, road building, year of plenty, monopoly.     [DATA]
- Deck composition (counts of each card) varies by map size.                         [DATA]
- Cities & Knights progress cards (3 categories tied to commodities).                [STATE][RULE]
- Themed editions swap the card list entirely.                                       [DATA][RULE]

## 10. Victory conditions & points

- VP target (base = 10; many fan maps use 12; C&K commonly 13; Gold-for-Catan
  noted 12, or 15 with Cities & Knights).                                            [DATA]
- Longest Road bonus (+2) and minimum length.                                        [DATA][RULE]
- Largest Army bonus (+2) and threshold.                                             [DATA][RULE]
- Metropolis (C&K): points from upgraded city improvements.                          [RULE]
- Special/scenario VPs: first to settle an island, control a region, harbor points
  (Seafarers), trade-route or chapel/library style bonuses.                          [RULE]
- Hidden VP (victory-point dev cards).                                               [DATA]

Engine implication: victory is "sum of point sources." Make point-sources a list
the variant contributes to, rather than a hardcoded `if vp >= 10`.

## 11. Setup / initial placement

- Standard snake-draft of 2 settlements + 2 roads, second settlement grants resources.[RULE]
- Fixed starting positions (some scenarios/tournaments).                             [DATA]
- Variant starting inventories (some maps grant starting resources or pieces).       [DATA]
- Number of pieces placed at setup can differ.                                       [DATA]

## 12. Player count

- 3-4 standard; 5-6 with extension (changes board size, piece counts, special
  build phase).                                                                      [DATA][RULE]
- 1-2 player variants exist (and our Part 1 "one human controls everyone" mode).     [RULE]

## 13. Special / one-off scenario mechanics [HARD]

These resist generalization and are where "just add a rule module" earns its keep:
- Exploration & fog reveal (Explorers & Pirates).
- Moving/expanding board, eru街ions, earthquakes that remove tokens (fan hazard hexes).
- Story/objective-driven goals (themed editions like A Game of Thrones, Inkas
  "decline of cities", New Energies' eco mechanics).
- Cooperative or semi-cooperative threats (barbarians).

---

## Design takeaways for the engine

1. Most knobs are [DATA]: topology, tile types, numbers, ports, deck composition,
   VP target, piece limits, setup positions. A robust **map/scenario file format**
   covers the majority of variants with zero code.
2. The high-value [RULE] surfaces are: the **turn phase machine**, **legal-move
   generation**, **production/distribution**, and **victory point sources**. Make
   each of these assembled per-variant (Option D in the structural notes).
3. A few mechanics are genuinely [HARD] (fog, barbarians, story objectives). Accept
   that these are real features. The win is that the *base* and the easy variants
   cost nothing, so your effort concentrates where it's actually needed.
4. Extra state for variants (commodities, knights, walls, fog, barbarian position)
   should be *additive* — base game simply leaves those fields empty.
