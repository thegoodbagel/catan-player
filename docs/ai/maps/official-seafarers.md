# Official — CATAN: Seafarers

Source: official rules hub <https://www.catan.com/understand-catan/game-rules>
(Seafarers PDF) and the Seafarers FAQ <https://www.catan.com/faq/seafarers>.
Content paraphrased for licensing compliance. Mechanics below are from the
published rules; treat specific scenario numbers as **UNVERIFIED**.

Seafarers extends the base game onto water: multiple islands, ships as a
road-equivalent over sea, gold, a pirate, and a set of **scenarios** (each its
own map + special victory rules).

## Delta from base game

### Topology (knob 1) [DATA]
- Boards mix **land hexes + sea hexes** and often **multiple disconnected
  islands**. The frame is configurable; islands can be reached only by ship.
- Ships from real expansion via a large set of named scenarios (e.g. "Heading
  for New Shores", "The Four Islands", "The Fog Island", "Through the Desert",
  "The Wonders of Catan", etc.). Each scenario fixes a layout and its own VP and
  bonus rules. **Layouts are per-scenario data; specifics UNVERIFIED.**

### Tile types (knob 2) [RULE]
- Adds **sea** hexes (non-producing, navigable).
- Adds **gold field** hexes: when their number is rolled, each adjacent
  settlement/city owner receives **resource(s) of their choice** (a wildcard
  yield). This is a [RULE] knob — production must allow a player choice.

### Buildings & pieces (knob 5) [RULE][STATE]
- New piece: **ship**. Costs **1 wood + 1 wool** (**UNVERIFIED**). Ships are
  placed on **sea edges**, forming routes the same way roads form on land edges.
- **Open shipping rule:** a ship at the end of a route (not closed between two of
  your settlements) may be **moved** once per turn. Closed routes are locked.
- Ships and roads both count toward connectivity but cannot directly join into a
  single continuous "longest" path through a settlement unless rules allow
  (scenario-dependent; **UNVERIFIED**).

### The pirate (knob 6) [RULE][STATE]
- A **pirate ship** is the sea counterpart of the robber: placed on a sea hex on
  a 7 (or via knight), it **blocks ship building/movement** adjacent to it and
  lets the active player steal from an adjacent player. The land robber still
  exists; both can be in play.

### Victory conditions (knob 10) [RULE]
- VP target varies by scenario (commonly higher than 10; **UNVERIFIED** per
  scenario).
- New point sources: **points for settling new islands** (a one-time VP for the
  first settlement a player builds on each additional island), and scenario-
  specific objectives. Victory remains "sum of point sources" with new sources.

### Setup (knob 11) [DATA/RULE]
- Many scenarios use **fixed or semi-fixed** starting layouts and sometimes
  restrict where initial settlements may go (main island only, etc.).

## Engine notes

- Requires **edges over sea** (ship routes) in addition to land road edges — the
  board graph must tag each edge as land/sea-capable.
- Adds movable-piece state (ship relocation) and a second blocker token
  (pirate) — additive `pirate_hex` state field.
- **Gold field** forces production to support a deferred player choice, not just
  automatic resource grants. This is the first variant where distribution is not
  fully deterministic from the dice.
- "First to island" VP needs per-island tracking in the board model.
