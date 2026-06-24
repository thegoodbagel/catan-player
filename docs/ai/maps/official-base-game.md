# Official — CATAN (Base Game)

Source: official rules hub <https://www.catan.com/understand-catan/game-rules>
(base game PDF, owned by CATAN GmbH). Content paraphrased for licensing
compliance. Specific counts/thresholds are **UNVERIFIED** until checked against
the PDF, but these are the long-stable published values.

This is the reference variant. Everything else is described as a *delta* from
here. Mapped to the knobs in `../variation-features.md`.

## Topology (knob 1) [DATA]

- Single island of **19 land hexes**, arranged in rows of `3-4-5-4-3`, ringed by
  sea/frame with **9 harbor (port) positions** on the outer edge.
- Standard play shuffles tile placement; a fixed beginner layout also exists.
- **5–6 player extension:** larger island (**30 land hexes**, `2 deserts`),
  more ports, plus a **special build phase** after each player's turn.

## Tile types (knob 2) [DATA]

| Hex | Produces |
|-----|----------|
| Forest | lumber (wood) |
| Pasture | wool (sheep) |
| Field | grain (wheat) |
| Hills | brick |
| Mountains | ore |
| Desert | nothing; robber starts here |

Standard 19-hex bag: 4 forest, 4 pasture, 4 field, 3 hills, 3 mountains,
1 desert. (Matches the generator's `RESOURCE_ARRAY`; see
`board-generator-bunge.md`.)

## Number tokens (knob 3) [DATA]

- 18 number tokens on the 18 producing hexes: values `2..12` excluding `7`.
- Standard multiset: one each of 2 and 12; two each of 3,4,5,6,8,9,10,11.
- High-probability numbers (6 and 8) are marked red; the classic placement rule
  forbids 6 and 8 from being adjacent.
- Probability "pips" per number drive expected yield (peak at 6/8).

## Resources & commodities (knob 4) [DATA]

- Exactly the 5 base resources above. No commodities.

## Buildings & pieces (knob 5) [DATA]

Per-player piece limits (**UNVERIFIED** counts, standard values):
- Roads: 15
- Settlements: 5
- Cities: 4

Build costs:
- Road = 1 wood + 1 brick
- Settlement = 1 wood + 1 brick + 1 wool + 1 grain
- City = 2 grain + 3 ore (upgrades an existing settlement)
- Development card = 1 wool + 1 grain + 1 ore

Placement rules: settlements obey the **distance rule** (no two settlements on
adjacent vertices); roads must connect to your own road/settlement/city; a city
upgrades a settlement in place.

## The robber (knob 6) [RULE]

- Starts on the desert.
- On a roll of **7**: every player with **>7 resource cards discards half**
  (rounded down), then the roller moves the robber to any hex and steals one
  random card from a player adjacent to it.
- The robbed hex produces nothing while the robber sits on it.
- Knight dev cards also move the robber.

## Turn structure (knob 7) [RULE] — the core FSM

1. (Optional) play **one** development card — may be done before the roll.
2. **Roll** two dice.
   - On 7: discard step + move robber + steal (no production).
   - Else: **production** — each player with a settlement/city on a vertex of a
     hex showing the rolled number gains resources (settlement = 1, city = 2).
3. **Trade**: with the bank/ports and with other players (free order).
4. **Build / buy**: roads, settlements, cities, dev cards (free order).
5. End turn.

This ordered phase set is exactly the state machine the engine should assemble
from data rather than hardcode (see `src-notes.txt` FSM idea).

## Trading (knob 8) [DATA]

- Bank: **4:1** any resource.
- Generic port: **3:1**. Specific port: **2:1** for one named resource.
- Player-to-player trading allowed on your turn; no giving cards away for free
  (no 0-for-something gifts, per standard rules — **UNVERIFIED** edge cases).
- 9 ports total in the 3–4 player layout.

## Development cards (knob 9) [DATA]

Standard 25-card deck (**UNVERIFIED** counts, standard values):
- 14 Knights
- 5 Victory Point cards (hidden, +1 each)
- 2 Road Building, 2 Year of Plenty, 2 Monopoly (progress cards)

A dev card cannot be played the turn it is bought (except hidden VP at game end).

## Victory conditions (knob 10) [DATA/RULE]

- **10 VP** to win, checked on your own turn.
- Sources: settlement = 1, city = 2, hidden VP card = 1, **Longest Road** (≥5
  segments) = +2, **Largest Army** (≥3 played knights) = +2.
- Longest Road / Largest Army are transferable bonuses (held by current leader).

## Setup / initial placement (knob 11) [RULE]

- Snake draft: each player places **settlement + road**, then in reverse order a
  **second settlement + road**.
- The **second** settlement immediately yields one resource from each adjacent
  producing hex.

## Player count (knob 12) [DATA/RULE]

- 3–4 on the base board.
- 5–6 requires the extension: bigger board, more pieces/cards, and a
  **special build phase** (extra build opportunity between turns).

## Engine notes

- This variant uses **zero** of the additive state fields (no commodities,
  knights, walls, fog, pirate, barbarians). It is the empty-fields baseline.
- Needs a real board representation the generator lacks: **vertices and edges**
  for settlements/cities/roads, plus **ports** bound to specific vertices.
