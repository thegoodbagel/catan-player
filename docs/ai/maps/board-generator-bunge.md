# Board Generator — catan.bunge.io (data model & code)

Sources:
- Live generator: <https://catan.bunge.io/> ("BetterCatan BoardGenerator" by
  Jamison Bunge) and its `/expansion` mode <https://catan.bunge.io/expansion>.
- **Source code** (the live site is a thin SPA; readable source found via a
  public MIT-licensed fork): <https://github.com/DarrenSem/catan>, file
  `catan-gen.js`. The fork is "speed/feature improvements based on the original
  by Jamison Bunge." Code reviewed directly.

Content paraphrased / structurally summarized for licensing compliance; no large
verbatim code blocks copied. This doc records **how the generator represents a
board**, which is the most directly reusable artifact for our engine.

## TL;DR for the engine

The generator confirms the **row-based / flat-array** representation sketched in
`src-notes.txt`. A board is a **flat array of tile objects**; adjacency is a
**hardcoded index → neighbor-index lookup table**; placement validity is
**rejection sampling** of shuffled fixed bags against a handful of constraints.

**Important limitation:** it models **hexes + number tokens only**. There are
**no ports, no vertices/edges, no settlements/roads, and no axial/cube
coordinates.** Useful as a reference for tile bags + number constraints + an
adjacency table; **not** a complete board model for actual play.

## The tile model

A tile is a tiny object:

```
{ chit: <2..12 or 0>, resource: <"sheep"|"wheat"|"wood"|"brick"|"ore"|"desert"> }
```

- `chit` is the number token; **`0` means no token** (the desert).
- `resource` is one of six strings (5 resources + `"desert"`).
- A board is `tiles[]`, indexed `0..18` (normal) or `0..29` (expansion).
- Rendering position is computed separately as CSS `left/top` %, not stored on
  the tile — i.e. **geometry is derived, identity is the array index.**

## The bags (fixed multisets, then shuffled)

Normal (3–4 player) board — 19 tiles total:
- **Numbers** (`NUM_ARRAY`, 18 entries; the 19th tile is the desert with no
  number): `2, 3,3, 4,4, 5,5, 6,6, 8,8, 9,9, 10,10, 11,11, 12`.
- **Resources** (`RESOURCE_ARRAY`, 18 entries + 1 desert added in code):
  `3× ore, 3× brick, 4× sheep, 4× wood, 4× wheat` (+ 1 desert) → matches the
  official 4/4/4/3/3 + desert bag.

Expansion (5–6 player) board — 30 tiles total:
- **Numbers**: each of `2..12` (no 7) appears **two or three** times
  (specifically: 2×{2,12}, 3×{3,4,5,6,8,9,10,11}) → 28 number tiles.
- **Resources**: `5× ore, 5× brick, 6× sheep, 6× wood, 6× wheat` (28) **+ 2
  deserts** → 30 tiles.

Generation: copy the bag, **Fisher–Yates shuffle** numbers and resources
independently, zip them into tiles, append desert(s), shuffle the whole tile
array, then validate. Retry until valid.

## The geometry / row structure

Rows per board (drives the visual layout and matches `src-notes.txt`'s
"row-based, ± offset per row" idea):
- **Normal:** `tiles_per_row = [3, 4, 5, 4, 3]`.
- **Expansion ("" / expanded):** `tiles_per_row = [1, 2, 3, 4, 3, 4, 3, 4, 3, 2, 1]`.

X/Y for each hex is computed from row index, a per-row step, and an even-row
half-cell shift — classic offset-hex rendering. The engine does **not** need to
copy this (it's just CSS placement), but it confirms a row-offset layout is
sufficient to describe the standard boards.

## The adjacency model (the reusable bit)

Adjacency is a **hardcoded array-of-arrays**: for each tile index, the list of
neighboring tile indices (authored "starting to the right, then clockwise").
- Normal: 19 entries (indices 0–18).
- Expansion: 30 entries (indices 0–29).

Two derived views are built once per mode:
- `globalAdjacencyAll` — each tile's full neighbor list (sorted). Used for the
  "no two adjacent hexes share a resource" check.
- `globalAdjacencyHigherIndexOnly` — only neighbors with a **higher index**.
  Used for symmetric number-adjacency checks so each pair is tested once.

**Engine takeaway:** a precomputed integer adjacency table is enough for
**hex-level** rules (production neighbors, robber, "same number/resource
adjacency"). For settlements/roads we still need vertices/edges, which this
generator does not provide — but vertices/edges can be **derived** from such a
hex adjacency table (each shared edge = 2 hexes; each vertex = up to 3 hexes),
which is consistent with our `map-ingestion-flow.md` "derive vertex/edge IDs
from hex coords" plan.

## The placement constraints (knob 3, generation rules)

Validity is checked per tile against neighbors. Each constraint is a toggle
(default **off** in this fork, i.e. fewest restrictions):

| Flag | Meaning |
|------|---------|
| `adjacent_6_8` | allow two 6/8 tiles to touch (off = forbid, the classic rule) |
| `adjacent_2_12` | allow two 2/12 tiles to touch |
| `adjacent_same_numbers` | allow equal "regular" numbers (3,4,5,9,10,11) to touch |
| `adjacent_same_resource` | allow same resource hexes to touch (normal map only) |
| `desert_in_center` | allow desert on the center tile(s) |
| `resource_multiple_6_8` | allow one resource type to carry 2+ (normal) / 3+ (exp) of the 6/8 tokens |

- "Regular numbers" = `[3,4,5,9,10,11]`; 6/8 are high-prob (red), 2/12 are rare.
- Center tile is index `9` (normal) or `{11,14,15,18}` (expansion).
- The validator **early-exits** on the first failed constraint (performance).

**Engine takeaway:** these are exactly the **board-generation constraints** our
auto-map mode (knob 3) would want, expressed as independent boolean rules over
the adjacency table. Good candidate to port directly.

## Performance / RNG detail (minor, but informative)

- Uses a **seedable LCG** (`seed = (9301*seed + 49297) % 233280`) so boards are
  reproducible from a seed — handy for our tests/replays (`src-notes.txt` notes
  wanting reproducible single games).
- For the fully-default normal map it ships a **precomputed list of ~749 "fast"
  seeds** known to validate quickly, to dodge slow rejection-sampling loops.
  Not needed for us, but shows rejection sampling can be slow under strict
  constraints — relevant if we add many generation rules.

## What it deliberately does NOT model (gaps to fill ourselves)

- **Ports / harbors** — absent entirely. We must add port positions + ratios.
- **Vertices & edges** — absent; no settlement/road/city representation.
- **Coordinates** — uses array index + CSS offsets, **not axial/cube**. Our
  `map-ingestion-flow.md` still recommends axial/cube; the generator's table can
  seed/validate but we own the coordinate system.
- **Sea/gold/fog tiles, scenarios, expansions beyond 5–6** — only "normal" and
  the 5–6 "expansion" bags exist; Seafarers etc. are stubbed out in the mode
  switch but unimplemented.

## Verdict

Reusable for: tile bags (number/resource multisets), the **generation constraint
set**, a **seedable RNG** for reproducibility, and a worked **hex adjacency
table** for the two standard boards. Not reusable as a full board/state model —
it has no ports, vertices, edges, or coordinates, which our engine needs for
actual settlement/road play.
