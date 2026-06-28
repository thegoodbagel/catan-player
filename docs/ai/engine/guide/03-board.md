# Chapter 3 — The Board as a Graph

> ## At a glance
> - **Where you are:** You have the vocabulary — enums and move records (Chapter 2). You can *name* things but the program has no board to put them on.
> - **This chapter's goal:** Represent the board so the rules can ask spatial questions — "which corners touch this hex?", "are these two corners adjacent?" — in constant time, by precomputing adjacency tables on an immutable `Board`.
> - **What this chapter is NOT:** This is not the rules and not the changing game situation. The `Board` is fixed for the whole game; whose-turn-it-is and who-owns-what live in the `State` (Chapter 4). No move legality is decided here.
> - **By the end you will have:** `src/engine/board_data.py` (the `STANDARD_BOARD` constant) and `src/engine/board.py` (an immutable `Board` with adjacency tables, `load_board`, and validation that raises `InvalidScenario`).
> - **Maps to:** Task 3 in `.kiro/specs/catan-engine/tasks.md`.
> - **Prerequisites:** Chapters 1–2. This is the foundation every later rule stands on, so do not skip ahead.

**Goal in plain language.** Turn a hexagonal map into plain lookup tables of
integers, computed once, so that every later rule is array indexing instead of
geometry.

This is the foundation; every rule stands on it. We will spend the most care here.

---

## The board is three interlocking graphs

Catan has three kinds of locations:

- **hexes** — tiles that produce resources,
- **vertices** — corners where settlements and cities sit,
- **edges** — sides where roads sit.

They relate to each other: a hex has six corner vertices and six side edges; an
edge joins exactly two vertices; a vertex touches up to three hexes and two or
three edges. If you have seen an **adjacency list** on a graph problem — "for each
node, store its neighbors" — this is that idea, with three node types that
cross-reference one another.

## Address everything by integer ID

The pivotal decision: give every location a plain integer. Hexes are
`0, 1, …, 18`; vertices `0, 1, …, 53`; edges `0, 1, …, 71`. Then the board is a
set of lookup tables:

```python
# Conceptual shape of the precomputed tables (built once at load):
hex_vertices  = [(0, 1, 8, 14, 13, 7), ...]   # the 6 corners of each hex
vertex_hexes  = [(0,), (0, 1), ...]            # the up-to-3 hexes each corner touches
edge_vertices = [(0, 1), (1, 2), ...]          # the 2 endpoints of each edge
vertex_neighbors = [(1, 7), (0, 2, 8), ...]    # adjacent corners (the distance rule)
```

With these, the rules become one-line lookups. "Who can be paid when hex 4 is
rolled?" → look at `hex_vertices[4]` and see who owns those corners. "Is vertex 7
too close to build on?" → check whether any of `vertex_neighbors[7]` is occupied.

> Because these neighbor relations never change during a game, we compute them
> **once** when the board loads and then only ever read them. The rules never do
> hexagon geometry; they do array indexing.

## Deriving the IDs (where the geometry hides)

The raw data describes hexes by coordinate; vertices and edges are *derived*. Two
ideas underlie that derivation: **axial coordinates**, the system used to address a
hex, and **deduplication**, the process by which shared corners and sides receive a
single ID. The following sections treat each in turn.

### Axial coordinates

A square grid uses `(row, column)` because squares stack into aligned rows and
columns. A hex grid does not align this way: alternate rows are offset by half a
tile, which makes "the row above" ambiguous and turns neighbor calculations into a
web of special cases. Axial coordinates avoid this by placing two axes *along* the
hex grid rather than across it. The two coordinates are written `q` and `r`.

Each hex is addressed by a single `(q, r)` pair: `q` measures displacement along
one axis of the grid and `r` along the other. This is the meaning of
`"coord": [0, -2]` in `STANDARD_BOARD` — that hex sits at `q = 0, r = -2`.

The advantage of this system is that a hex's six neighbors lie at the same six
fixed offsets everywhere on the board:

```python
# The six directions around any hex, as (dq, dr) offsets:
HEX_DIRECTIONS = [
    (+1,  0), (+1, -1), ( 0, -1),
    (-1,  0), (-1, +1), ( 0, +1),
]
# Neighbor of hex (q, r) in direction i:  (q + dq, r + dr)
```

No row-parity branching is required: the hex at `(0, -2)` has neighbors at
`(1, -2)`, `(1, -3)`, and so on. This regularity is what makes the next step —
determining which corners two hexes share — a mechanical operation.

> The coordinate system need not be derived from scratch; treat `HEX_DIRECTIONS` as
> given. A complete treatment is available in Red Blob Games' "Hexagonal Grids"
> article. For the engine, the offset table above is all `load_board` requires.

### Deduplication

A hexagon has 6 corners and 6 sides, so a naive assignment would give 19 hexes
`19 × 6 = 114` corners. Adjacent hexes, however, **share** corners and edges: where
two hexes meet, the corner between them is a single point belonging to both. The
standard board therefore has **54 vertices and 72 edges**.

Deduplication enforces a simple invariant: **one ID per physical location.** When a
corner has already been created by an earlier hex, the existing ID is reused rather
than a new one assigned. Without this invariant — if a single corner received
`vertex 3` from one hex and `vertex 9` from another — a settlement recorded at
`vertex 3` would fail to block construction at `vertex 9`, despite the two
referring to the same location, and the engine would be silently incorrect.

The mechanism assigns each corner a **canonical key** derived from its geometry, so
that the same physical point always produces the same key, then maps keys to IDs,
reusing the stored ID whenever a key recurs:

```python
vertex_of_key: dict = {}          # canonical corner key -> vertex id
def vertex_id(key) -> int:
    if key not in vertex_of_key:
        vertex_of_key[key] = len(vertex_of_key)   # first occurrence: assign next id
    return vertex_of_key[key]                     # later occurrences: reuse the id
```

Edges are handled identically, keyed by their two endpoints. This computation runs
**once** in `load_board`; the resulting tables are stored, and the remainder of the
engine operates on integer IDs alone, free of coordinates.

## The board as data, hardcoded for now

A Catan layout is generated fresh for each game: terrain tiles are shuffled onto
the positions, and number tokens are placed in a fixed order (described in the next
section). A scenario therefore does not record `"resource"` and `"number"` per hex.
It records the **positions** (fixed geometry) together with the **ingredients and
ordering** from which a setup step constructs a concrete layout.

We describe the standard board as a constant in the future-file *shape*, so
swapping to a file later changes only the loader:

```python
STANDARD_BOARD = {
    "meta":  {"name": "standard", "player_counts": [3, 4], "vp_target": 10},

    # Geometry only — where the hexes sit. No resource or number here; those are
    # assigned per game during setup.
    "hexes": [
        {"coord": [0, -2]},
        {"coord": [1, -2]},
        {"coord": [2, -2]},
        {"coord": [-1, -1]},
        # ... 19 hex positions total ...
    ],

    # The bag of terrain tiles to shuffle across those positions (base game):
    # 4 wood, 4 sheep, 4 wheat, 3 brick, 3 ore, 1 desert = 19.
    "terrain_supply": {
        "wood": 4, "sheep": 4, "wheat": 4, "brick": 3, "ore": 3, "desert": 1,
    },

    # The number tokens in their fixed placement order (the A..R sequence,
    # 18 of them — one per non-desert hex). See the next section.
    "number_order": [5, 2, 6, 3, 8, 10, 9, 12, 11, 4, 8, 10, 9, 4, 5, 6, 3, 11],

    # The order to walk hex positions when laying tokens: a spiral from an outer
    # corner inward, as hex indices into "hexes". The loader skips whichever
    # position turns out to be the desert this game.
    "token_spiral": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],

    "ports": [
        {"vertices": [0, 1], "ratio": 3, "resource": None},      # generic 3:1
        {"vertices": [3, 4], "ratio": 2, "resource": "wheat"},   # specific 2:1
        # ...
    ],
    "rules": "base",
}
```

## How Catan assigns numbers (and why the format stores an order, not numbers)

Number tokens are not chosen freely. They are placed by a fixed procedure designed
to distribute the high-probability numbers across the board:

- The 18 tokens (one per land hex) are lettered **A through R**, each printed with
  a fixed number: A=5, B=2, C=6, D=3, E=8, F=10, G=9, H=12, I=11, J=4, K=8, L=10,
  M=9, N=4, O=5, P=6, Q=3, R=11. Recorded as a plain sequence of numbers, this is
  the `number_order` above.
- Beginning at a corner hex, the tokens are placed in alphabetical order along a
  **counterclockwise spiral from the outer ring inward**, skipping the desert,
  which holds the robber and receives no number.
- The letter-to-number assignment is constructed so that the two
  highest-probability numbers, **6 and 8** (the red numbers), are never placed on
  adjacent hexes. Because 6 and 8 are the most frequent rolls, two of them on
  touching hexes would concentrate excessive production at a single corner.

Terrain tiles, by contrast, are shuffled randomly onto the positions. A game's
layout is therefore the combination of **random terrain placement and fixed-order
number placement.** Since terrain is random, the desert's position varies between
games, which is why the spiral skips whichever hex is the desert in a given game
rather than a fixed index.

This has a direct consequence for the data format: the scenario stores the *order*
(`number_order` and `token_spiral`) and the *supply* (`terrain_supply`), not the
per-hex result. A setup step produces one concrete assignment of resource and
number to each hex. The fixed geometry — positions and adjacency tables — belongs
on the immutable `Board`, while the per-game resource and number assignment is
determined at setup and held in the `State` (Chapter 4) rather than the static
board.

## Validate before you trust

Before play, check the data is coherent and fail loudly otherwise:

```python
def load_board(scenario="standard") -> "Board":
    data = STANDARD_BOARD
    # ... derive ids, build tables ...
    _validate(board)   # raises InvalidScenario("terrain supply sums to 20, expected 19") etc.
    return board

class InvalidScenario(Exception):
    pass
```

The loader should verify that the terrain supply sums to the number of hex
positions, that `number_order` contains exactly one entry per non-desert hex (the
hex count minus the desert count), that every entry in `number_order` is a legal
token (2–12, excluding 7), and that `token_spiral` lists every hex position exactly
once. A malformed board caught at load produces a clear message; the same mistake
caught mid-game produces a baffling crash. These are exactly the checks a future
file loader will reuse.

## Immutability

The `Board` never changes after `load_board`. Store its tables as tuples (which
cannot be mutated) rather than lists. An immutable board can be shared by every
copy of the game state without fear — central to the cheap-copy story in Chapter 4.

> **Margin notes**
> - **Graph / node / edge**: a set of things and the connections between them.
> - **Adjacency list**: for each node, the list of its neighbors.
> - **Axial coordinates**: a tidy coordinate system for hex grids (two axes).
> - **Derived data**: values computed from other data (vertex IDs from hex coords)
>   rather than stored directly.
> - **Layout vs. geometry**: the *geometry* (positions, adjacency) is fixed for all
>   games; the *layout* (which resource and number land on each hex) is rolled fresh
>   each game during setup.

## Exercises

1. **Hand-trace adjacency.** On paper, draw three hexes in a row. Number their
   vertices and edges, deduplicating shared ones. Write out `vertex_hexes` for two
   shared corners. This is the deduplication `load_board` must perform.
2. **Consistency property.** Write a test asserting the tables agree with each
   other: for every hex `h` and corner `v` in `hex_vertices[h]`, confirm `h` is in
   `vertex_hexes[v]`. Why is this the *first* test to write?
3. **Validation.** Make a corrupted copy of `STANDARD_BOARD` whose `terrain_supply`
   does not sum to the number of hex positions (or whose `number_order` has the
   wrong length), and assert `load_board` raises `InvalidScenario` naming the
   problem.
4. **Count check.** Assert the standard board has 19 hexes in rows 3-4-5-4-3, that
   `terrain_supply` sums to 19 with exactly one desert, that `number_order` has 18
   entries each in 2–12 excluding 7, and that there are 9 ports.
5. **(Stretch) Distance rule, in advance.** Using only `vertex_neighbors`, write a
   function `can_place_settlement(occupied_vertices, v)` returning whether `v` and
   all its neighbors are unoccupied. You will reuse this in Chapter 6.

### Hints / how to start

**Where the code goes.** `STANDARD_BOARD` lives in a new file
`src/engine/board_data.py`. The `Board` class, `load_board`, `_validate`, and
`InvalidScenario` go in `src/engine/board.py`. Tests go in
`tests/test_board_adjacency.py` and `tests/test_board_validation.py`.

- **Ex. 1 (hand-trace).** Pencil and paper. Draw three hexes side by side. Label
  hex corners 0–N, reusing a number wherever two hexes share a corner. The two
  shared corners between hex 0 and hex 1 should each list *both* hexes — that pair
  is your `vertex_hexes` entry. The whole point: shared corners get *one* ID, not
  two. This is exactly the deduplication `load_board` performs in code.
- **Ex. 2 (consistency property — write this FIRST).** Before any rule, prove the
  tables agree. Signature and shape:
  ```python
  # tests/test_board_adjacency.py
  from engine.board import load_board

  def test_hex_vertex_tables_agree():
      board = load_board("standard")
      for h in range(board.num_hexes()):
          for v in board.hex_vertices(h):
              assert h in board.vertex_hexes(v)   # if hex says it touches v, v must agree
  ```
  *Why first:* every later rule silently assumes these tables are mutually
  consistent. If they aren't, you'll chase "impossible" bugs in the rules that are
  really board bugs. Test the foundation before building on it.
- **Ex. 3 (validation).** Build a deliberately broken copy and assert the loader
  rejects it. Sketch:
  ```python
  import copy, pytest
  from engine.board import load_board, InvalidScenario
  from engine.board_data import STANDARD_BOARD

  def test_terrain_supply_must_match_hex_count():
      bad = copy.deepcopy(STANDARD_BOARD)
      bad["terrain_supply"]["wood"] += 1   # now sums to 20, but there are 19 hexes
      with pytest.raises(InvalidScenario):
          load_board(bad)   # have load_board accept either a name or a data dict
  ```
  Make `_validate` raise `InvalidScenario("terrain supply sums to 20, expected 19")`
  so the message names the failing rule.
- **Ex. 4 (count check).** Pure assertions on the loaded board:
  `assert board.num_hexes() == 19`; `assert sum(supply.values()) == 19` and
  `assert supply["desert"] == 1`; `assert len(number_order) == 18` and every entry
  is in `set(range(2, 13)) - {7}`; `assert len(board.ports) == 9`. For the
  3-4-5-4-3 row shape, group hex positions by the second axial coordinate and
  assert the row sizes.
- **Ex. 5 (stretch — distance rule).** This one you *will* reuse, so write it
  cleanly. Signature and first line:
  ```python
  def can_place_settlement(board, occupied_vertices, v) -> bool:
      if v in occupied_vertices:
          return False
      return all(n not in occupied_vertices for n in board.vertex_neighbors(v))
  ```
  A passing test: on a tiny occupied set, a vertex adjacent to an occupied one
  returns `False`, and an isolated vertex returns `True`.

## Run your tests

```bash
python3 -m pytest
```

You just added `tests/test_board_adjacency.py` and
`tests/test_board_validation.py`. Make the consistency test (Ex. 2) pass *first* —
if the foundation is wrong, everything above it will be mysteriously wrong too.

---

Previous: [02 — The Vocabulary of the Game](02-vocabulary.md) | Next: [04 — The Game State and Cheap Copying](04-state.md)
