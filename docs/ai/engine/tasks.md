# Implementation Plan: catan-engine

## Overview

This plan builds the base-Catan rules engine bottom-up: we start with the most
foundational, most-depended-on pieces (board topology), confirm they are correct
in isolation, then layer the mutable game state, the data-driven variant bundle,
and finally the three front-door operations (`legal_moves`, `apply`,
`is_terminal`/`winner`) on top. Each task is small and leaves the engine in a
state you can import and test, so you build confidence as you go rather than
writing a huge pile of code and debugging it all at once.

A few design choices recur throughout, so it helps to hold them in mind:

- **Integer-ID topology.** Hexes, vertices, and edges are plain integers, and
  adjacency lives in lookup tables on an immutable `Board`. This is *why* copying
  a `State` is cheap (you copy small arrays of ints, never the topology) and why
  the state serializes trivially later for search and networking.
- **Pure-data moves (Design B).** A `Move` only *describes intent*. It never
  mutates anything. All mutation happens inside `rules.apply`. This keeps moves
  hashable/replayable and puts every rule in one place.
- **Board immutable, State mutable.** Many `State`s share one `Board` by
  reference; only `State` ever changes.
- **Victory = sum of sources.** Victory points are computed by summing
  independent point-source functions (buildings, VP cards, longest road, largest
  army), never a hardcoded check. This is what makes scoring extensible.
- **Variant as a data-driven bundle.** Base Catan is one `VariantBundle` of
  data + functions (phases, generators, effects, VP sources, tunable counts).
  The rules read everything from the active bundle, so future variants extend
  rather than fork.

Language: **Python 3.11+**, standard library only for the engine core;
`pytest` + `hypothesis` as dev dependencies for tests (per the design's Testing
Strategy and Dependencies).

**Out of scope for v1 (no tasks here):** player-to-player negotiated trading and
JSON/file-based board loading. The seams exist in the design but we deliberately
do not implement them now.

## Tasks

- [ ] 1. Set up the package skeleton and test tooling
  - Create the `src/engine/` package with an empty `__init__.py`, and a `tests/`
    directory with its own `__init__.py`.
  - Add a `pyproject.toml` (or `requirements-dev.txt`) declaring `pytest` and
    `hypothesis` as dev dependencies, and configure `pytest` to find the
    `src/engine` package (e.g. set `pythonpath = ["src"]`).
  - Add a single trivial smoke test (`tests/test_smoke.py`) that imports the
    package and asserts `True`, so you can confirm the test runner works before
    writing real code.
  - _Why this / why now:_ the smallest possible skeleton proves your toolchain
    (imports, test discovery, hypothesis install) works *before* you depend on
    it. Every later task ends by running `pytest`, so getting this right once
    saves pain everywhere.
  - _Requirements: 25.2_

- [ ] 2. Core types and pure-data moves
  - [ ] 2.1 Implement the core enums and the `Port` type
    - In `src/engine/types.py`, define `Resource`, `DevCard`, and `Phase` enums
      and the frozen `Port` dataclass (`ratio: int`, `resource: Optional[Resource]`)
      exactly as in design Part B.1.
    - _Why this / why now:_ these are the shared vocabulary every other module
      imports. They have no dependencies, so building them first means nothing
      downstream is blocked on naming. Enums (not bare strings) make illegal
      values impossible and keep `apply` logic readable.
    - _Requirements: 9.1_

  - [ ] 2.2 Implement the pure-data `Move` dataclasses
    - In `src/engine/moves.py`, define a `Move` base and one
      `@dataclass(frozen=True)` per move kind: `BuildRoad`, `BuildSettlement`,
      `BuildCity`, `Roll`, `MoveRobber`, `Steal`, `BuyDevCard`, `PlayKnight`,
      `PlayRoadBuilding`, `PlayYearOfPlenty`, `PlayMonopoly`, `BankTrade`,
      `PortTrade`, `Discard`, `EndTurn`, `PlaceSetupSettlement`,
      `PlaceSetupRoad`.
    - Carry intent fields only (e.g. `BuildSettlement.vertex`,
      `MoveRobber.hex`/`steal_from`, `BankTrade.give`/`receive`). No methods, no
      behavior. Do **not** define any player-to-player trade move.
    - _Why this / why now:_ frozen dataclasses give you hashing and equality for
      free, which is exactly what the move log needs to replay deterministically.
      Keeping moves behavior-free (Design B) is the rule that lets `apply` be the
      single source of truth for mutation — restating it here so the structure is
      clear: the move says *what*, the rules decide *how*.
    - _Requirements: 9.1, 9.2, 9.3, 18.3_

  - [ ]* 2.3 Write unit tests for move data semantics
    - In `tests/test_moves.py`, assert moves are frozen (mutation raises), equal
      moves hash equally, and distinct moves compare unequal.
    - _Requirements: 9.2_

- [ ] 3. Board topology — the foundation everything stands on
  - [ ] 3.1 Add the in-code `STANDARD_BOARD` constant
    - In `src/engine/board_data.py`, define `STANDARD_BOARD` in the future-file
      *shape* from the design Data Models section: a `meta` block, 19 `hexes`
      (each with `coord`, `resource`, `number`; desert has no token), 9 `ports`
      (vertex bindings + ratios), and `"rules": "base"`.
    - _Why this / why now:_ we hardcode the board as data (not JSON yet) so v1
      has zero file-parsing complexity, but we write it in the exact shape a JSON
      file will take later — so swapping the source touches only `load_board`,
      not this data or anything downstream. Map = data is the whole reason a
      bigger board later is "just a different dataset."
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ] 3.2 Implement `Board` construction and adjacency derivation
    - In `src/engine/board.py`, implement the immutable `Board` and
      `load_board(scenario_dir="standard")`. Derive vertex and edge integer IDs
      deterministically from the hex coordinates, then build and **freeze**
      (store as tuples) all adjacency tables: `hex_vertices`, `hex_edges`,
      `vertex_hexes`, `vertex_neighbors`, `vertex_edges`, `edge_vertices`, plus
      `hex_resource`, `hex_number`, and `ports`.
    - Expose only read-only query methods (the interface in design Components).
    - _Why this / why now:_ this is the single most depended-on object in the
      engine — every spatial rule (distance, connectivity, production, robber,
      longest road) is just a lookup into these tables. Deriving IDs from coords
      once and freezing the tables is what makes the `Board` immutable and
      shareable by reference (cheap state copies). Getting adjacency right here
      means the rules layer never has to think about geometry again.
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ] 3.3 Implement board validation
    - In `board.py`, validate the data during `load_board` and raise
      `InvalidScenario` (naming the failing rule) when: a producing hex lacks
      exactly one token / the desert has one, adjacency references a missing hex,
      port count or ratios are illegal, or the named bundle (`"base"`) is not
      registered.
    - _Why this / why now:_ catching a malformed board *before* play begins turns
      a confusing mid-game crash into a clear, early error. These are the same
      checks the future JSON loader will run, so writing them now means file
      loading later inherits them for free.
    - _Requirements: 7.5_

  - [ ]* 3.4 Write a property test for adjacency consistency
    - In `tests/test_board_adjacency.py`, assert the tables are mutually
      symmetric/consistent: e.g. `v in hex_vertices[h]` ⇔ `h in vertex_hexes[v]`,
      `edge_vertices[e]` endpoints each list `e` in their `vertex_edges`,
      neighbor relation is symmetric, and all IDs are in range.
    - _Why this / why now:_ test the foundation first — a symmetric, consistent
      adjacency table is the assumption every later rule silently relies on.
    - _Requirements: 6.4_

  - [ ]* 3.5 Write unit tests for standard board composition and validation
    - In `tests/test_board_validation.py`, assert the standard board has 19 hexes
      in rows 3-4-5-4-3, correct token range (2-12 except 7, desert none), the
      five resources plus desert, and 9 ports; and that corrupted copies of the
      data raise `InvalidScenario` identifying the failing rule.
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 4. Mutable, copyable state
  - [ ] 4.1 Implement the `State` dataclass and `State.copy()`
    - In `src/engine/state.py`, implement `State` with the fields from design A.4
      (occupancy arrays `settlements`/`cities`/`roads` indexed by ID with `-1` =
      empty, per-player tallies, shared decks, bonus holders, `dice`,
      `setup_index`, `pending_discards`, `move_log`, `rng_state`).
    - Implement `copy()` exactly as design B.4: shallow-copy the object, **share**
      the `board` reference, and deep-copy only the mutable containers
      (lists/dicts of primitives).
    - `State` holds no rules logic and must not import `rules`.
    - _Why this / why now:_ now that `Board` exists we can hold a game situation
      against it. Building `copy()` immediately — and testing it next — locks in
      the cheap-copy property that MCTS depends on. Storing buildings as int
      arrays (not objects) is what makes copy and equality fast and what keeps
      `State` a plain data container.
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 25.3_

  - [ ]* 4.2 Write a property test for copy purity
    - In `tests/test_state.py`, build a `State`, copy it, mutate the copy's
      arrays/dicts, and assert the original is byte-for-byte unchanged and that
      `copy.board is original.board` (shared, not duplicated).
    - _Why this / why now:_ proving copy isolation early prevents a whole class of
      "spooky action at a distance" bugs once `apply` starts mutating.
    - _Requirements: 8.2_

- [ ] 5. The data-driven variant bundle (the extensibility core)
  - [ ] 5.1 Implement `VariantBundle` and the registry
    - In `src/engine/rules.py`, define the frozen `VariantBundle` dataclass (per
      design B.2: `phases`, `generators`, `effects`, `vp_sources`, `extra_state`,
      and the tunable counts `vp_target`, `dev_deck_composition`, `piece_limits`,
      `discard_limit`, `longest_road_min`, `largest_army_min`, `build_costs`).
    - Add the `VARIANTS` registry dict, `register_variant`, and a helper
      `activeBundle(state)` that looks up `state.variant`.
    - _Why this / why now:_ this is the data-driven core. By defining the bundle
      shape *before* writing any rule, we force every later rule to read its
      numbers from configuration (`activeBundle(s).build_costs[...]`) instead of
      sprinkling magic constants through the code. That single discipline is what
      lets a future variant change a value without editing logic.
    - _Requirements: 24.1, 24.2, 24.3_

  - [ ] 5.2 Register the `base` bundle with tunable config
    - In `rules.py`, construct and `register_variant` the `BASE` bundle with the
      standard values from design B.2 (VP target 10; dev deck 14/5/2/2/2; piece
      limits 15/5/4; discard limit 7; longest-road min 5; largest-army min 3;
      build costs). Wire the `generators`, `effects`, and `vp_sources` maps to the
      functions you will fill in over tasks 6-8 (stub them for now so the module
      imports).
    - _Why this / why now:_ registering the bundle now gives every later task a
      concrete place to plug its function into, and makes `legal_moves`/`apply`
      dispatch real from the first generator you write. Verify the exact counts
      against the rulebook as you go (the design flags this).
    - _Requirements: 17.6, 24.2, 24.3_

- [ ] 6. Legal-move generation, phase by phase
  - [ ] 6.1 Implement `legal_moves` dispatch and shared helpers
    - In `rules.py`, implement `legal_moves(state)` to assert the phase is in the
      bundle and dispatch to `activeBundle(state).generators[state.phase]`, never
      mutating state. Add shared helpers used by generators: `can_afford`,
      `occupied(state, v)`, `own_settlements`, etc.
    - _Why this / why now:_ the dispatcher is tiny but it nails down the FSM
      contract (phase selects generator) before any phase logic exists. Helpers
      written once here keep each generator short and readable.
    - _Requirements: 1.1, 1.3, 1.4, 10.2_

  - [ ] 6.2 Implement the SETUP generator
    - In `rules.py`, implement `gen_setup_moves`: in snake-draft order, offer
      `PlaceSetupSettlement(v)` for vertices satisfying the distance rule, then
      `PlaceSetupRoad(e)` for edges incident to the settlement just placed.
    - _Why this / why now:_ SETUP is the entry phase, so building it first lets
      you actually start a game and exercise the dispatcher end to end. The
      distance-rule check here is the same predicate MAIN will reuse.
    - _Requirements: 11.1, 11.2, 11.3_

  - [ ] 6.3 Implement the ROLL generator
    - In `rules.py`, implement `gen_roll_moves`: offer `Roll()`, plus at most one
      pre-roll dev-card play when the active player holds a playable dev card.
    - _Requirements: 12.1, 12.4_

  - [ ] 6.4 Implement the DISCARD and ROBBER generators
    - In `rules.py`, implement `gen_discard_moves` (a `Discard` of half-rounded-
      down for each owing player in `pending_discards`) and `gen_robber_moves`
      (`MoveRobber(hex, steal_from?)` for each legal target hex and stealable
      opponent).
    - _Why this / why now:_ these two phases only exist as a consequence of a 7,
      so building them together keeps the robber flow coherent. DISCARD is the one
      multi-player phase — generating per owing player is what lets the FSM stay
      in DISCARD until everyone has paid.
    - _Requirements: 13.1, 13.2, 13.4, 13.5, 13.6_

  - [ ] 6.5 Implement the MAIN generator
    - In `rules.py`, implement `gen_main_moves` per design B.3: always `EndTurn`;
      builds gated by both cost (`can_afford`) and placement legality
      (`buildable_road_edges`, `buildable_settlement_vertices` enforcing the
      distance rule + road connectivity, city upgrades on own settlements);
      `BuyDevCard` when affordable and deck non-empty; at most one dev-card play
      if none played this turn; and bank (4:1) + port (3:1/2:1) trades.
    - _Why this / why now:_ MAIN is the largest generator and the heart of a turn.
      Doing it after the simpler phases means the helpers and patterns are already
      proven. Gating builds by *both* affordability and placement keeps illegal
      options out of the menu entirely.
    - _Requirements: 1.1, 14.2, 15.2, 15.3, 16.2, 17.1, 17.3, 18.1, 18.2_

  - [ ]* 6.6 Write unit tests for each generator
    - In `tests/test_legal_moves.py`, test each phase's generator on hand-built
      states: setup distance filtering, road-must-attach, MAIN affordability and
      connectivity gating, discard targets, robber targets.
    - _Requirements: 1.1, 11.2, 14.2, 15.2, 15.3_

- [ ] 7. Checkpoint - legal-move layer
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Applying moves: the mutation core
  - [ ] 8.1 Implement the `apply` skeleton (validation + path choice)
    - In `rules.py`, implement `apply(state, move, in_place=False)` per design
      B.4: raise `GameOver` if terminal; raise `IllegalMove` if
      `move not in legal_moves(state)`; then choose `s = state` (in-place) or
      `s = state.copy()` (copy path); dispatch to
      `activeBundle(s).effects[type(move)]`; set `s.phase`, append to
      `move_log`, and fold in the victory check.
    - _Why this / why now:_ isolating the in-place-vs-copy decision to one branch
      is the entire trick behind copy-purity and in-place/copy equivalence — every
      effect below then operates on `s` identically, so those properties hold *by
      construction* rather than by careful effort in each effect. Validating
      before mutating guarantees a rejected move never corrupts state.
    - _Requirements: 2.1, 2.3, 2.4, 3.1, 4.1, 4.2, 4.3_

  - [ ] 8.2 Implement the SETUP effects
    - In `rules.py`, implement effects for `PlaceSetupSettlement` and
      `PlaceSetupRoad`: place the piece, advance `setup_index` through the snake
      draft, grant one resource per adjacent producing hex when the **second**
      settlement is placed, and transition to ROLL when the draft completes.
    - _Why this / why now:_ effects mirror the generators you just built, so doing
      SETUP first means you can drive a real game from `Game.new` through initial
      placement and watch `setup_index` snake correctly.
    - _Requirements: 11.1, 11.4, 11.5_

  - [ ] 8.3 Implement the ROLL effect and production payout
    - In `rules.py`, implement `eff_roll`: roll 2d6 from the seedable RNG; on 7,
      set `pending_discards` and go to DISCARD (or ROBBER if none over limit); on
      any other roll, distribute production from the bank (settlement 1, city 2)
      for hexes carrying the number, keeping all counts non-negative and the bank
      never negative, then go to MAIN.
    - _Requirements: 12.1, 12.2, 12.3, 13.1_

  - [ ] 8.4 Implement the DISCARD and ROBBER effects
    - In `rules.py`, implement `eff_discard` (remove the discarded cards, drop the
      player from `pending_discards`, stay in DISCARD until empty then go to
      ROBBER) and `eff_move_robber` (place robber, steal one random card via the
      RNG when a target is given, resolve as no-steal if the target is empty, then
      go to MAIN).
    - _Why this / why now:_ pairing these effects keeps the 7-roll flow in one
      place. Using the seedable RNG for the steal is what keeps a game reproducible
      from its seed + move log.
    - _Requirements: 13.2, 13.3, 13.4, 13.5, 13.6_

  - [ ] 8.5 Implement the MAIN build effects
    - In `rules.py`, implement `eff_build_road`, `eff_build_settlement`, and
      `eff_build_city`: pay the configured cost to the bank, update the occupancy
      array, and (for settlement/city) call `recompute_longest_road` since an
      opponent's new building can shorten someone's road. All stay in MAIN.
    - _Why this / why now:_ builds are the actions that change the board graph, so
      their effects are where longest road must be recomputed. Reading costs from
      the bundle (not constants) keeps the config discipline intact.
    - _Requirements: 14.1, 15.1, 16.1, 16.3_

  - [ ] 8.6 Implement the dev-card effects
    - In `rules.py`, implement `eff_buy_dev` (pay cost, draw from deck, mark
      unplayable until next turn) and the play effects: `PlayKnight` (go to
      ROBBER, count toward largest army), `PlayRoadBuilding`,
      `PlayYearOfPlenty`, `PlayMonopoly` (their respective effects), all enforcing
      at most one dev card played per turn.
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

  - [ ] 8.7 Implement the trade effects
    - In `rules.py`, implement `eff_bank_trade` (4 identical → 1 chosen) and
      `eff_port_trade` (at the owned port's 3:1 or 2:1 ratio), exchanging through
      the bank and staying in MAIN.
    - _Requirements: 18.1, 18.2_

  - [ ] 8.8 Implement the end-turn effect and victory wiring
    - In `rules.py`, implement `eff_end_turn`: if the current player's
      `victory_points` ≥ VP target, return `GAME_OVER`; otherwise promote
      bought-this-turn dev cards to playable, reset the per-turn dev-play flag,
      advance `current_player`, and return ROLL.
    - _Why this / why now:_ end-turn is where the victory check lives, and it must
      ask `victory_points` (the summed sources) rather than counting anything
      itself — keeping the "victory = sum of sources" rule honest at the one place
      the game can end.
    - _Requirements: 10.3, 10.4, 21.3_

  - [ ]* 8.9 Write unit tests for apply effects
    - In `tests/test_apply.py`, test each effect on hand-built states: production
      payout, discard/robber/steal, build deductions, dev-card play, trades, and
      end-turn advancement; assert `IllegalMove` and `GameOver` are raised
      appropriately.
    - _Requirements: 4.2, 4.3, 12.2, 13.5, 14.1, 17.4, 18.1_

- [ ] 9. Victory points and the two bonuses
  - [ ] 9.1 Implement `victory_points`, `winner`, and `is_terminal`
    - In `rules.py`, implement `victory_points(s, p)` as the sum over
      `activeBundle(s).vp_sources`; implement the source functions
      `vp_from_buildings` and `vp_from_vp_cards`; implement `winner` (current
      player iff their summed VP ≥ target) and `is_terminal` (`phase == GAME_OVER`
      or `winner` is not None).
    - _Why this / why now:_ writing scoring as a sum of independent source
      functions — instead of one big check — is what makes it transparent and
      extensible: longest road and largest army (next tasks) are just two more
      source functions appended to the bundle. No hardcoded victory check anywhere.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 21.1, 21.2, 21.3_

  - [ ] 9.2 Implement longest road (the hard one — longest simple path via DFS)
    - In `rules.py`, implement `recompute_longest_road` and `dfs_longest` per
      design A.3.1 and B.5, plus the `vp_from_longest_road` source. For each
      player, take the subgraph of edges they own (which may **branch and contain
      cycles** — it is a general graph, not a tree) and find the **longest simple
      path** (no repeated edge or vertex) by exhaustive DFS from each owned edge.
      An **opponent's settlement or city on a vertex breaks continuity through
      that vertex** (a path may end there but not pass through); your own building
      never breaks your path. Award the 2-VP bonus at length ≥ the configured
      minimum with standard tie/steal handling. Recompute on any road change and
      on any settlement/city placement.
    - _Why this / why now:_ **this is the genuinely tricky algorithm in the whole
      engine — do not underestimate it.** The common mistake is treating roads as
      a tree and doing a simple traversal; that is wrong because roads branch and
      loop, and because opponent buildings cut paths. The good news is scale makes
      it easy: a player has ≤ 15 roads, so a brute-force DFS over the road subgraph
      is plenty fast and easy to reason about. The board's edge↔vertex↔edge tables
      from task 3.2 are exactly what the DFS walks. Budget extra time and write
      targeted tests (branch, cycle, opponent-cut) for this one.
    - _Requirements: 19.1, 19.2, 19.3, 19.4_

  - [ ] 9.3 Implement largest army
    - In `rules.py`, implement `vp_from_largest_army` and the holder update: award
      the 2-VP bonus to the player with the most played knights once they reach the
      configured minimum, and transfer it when another player surpasses the holder.
    - _Requirements: 20.1, 20.2_

  - [ ]* 9.4 Write unit and property tests for scoring and bonuses
    - In `tests/test_victory.py`, unit-test `vp_from_buildings`/`vp_cards`, the
      largest-army transfer, and especially longest road on a branching graph, a
      cyclic graph, and a graph cut by an opponent building.
    - _Requirements: 19.2, 19.3, 20.1, 20.2, 21.1_

- [ ] 10. Checkpoint - full rules core
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. The front door, view, and replay
  - [ ] 11.1 Implement the player-view (observation) function
    - In `src/engine/game.py`, implement `Game.view(state, player)` returning a
      `PlayerView` (design B.7): all public facts (board, buildings, robber, bank,
      bonus holders, played knights), the requesting player's own exact resources
      and dev cards, only aggregate counts for opponents (never identity or hidden
      VP cards), and `legal_moves` only when the player is the current player.
    - _Why this / why now:_ centralizing hidden-information policy in one function
      means UI and networking later can never accidentally leak an opponent's hand
      — there is exactly one place that decides what a player may see.
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5_

  - [ ] 11.2 Implement `Game.new`, the front-door delegators, and `replay`
    - In `game.py`, implement `Game.new(scenario_dir, num_players, seed)` (load
      board, build the initial `State` with a seeded RNG, register/select the
      `base` bundle, start in SETUP), the thin delegators `legal_moves`/`apply`/
      `is_terminal`/`winner`, and `replay(scenario_dir, num_players, seed, moves)`
      that re-creates the game and applies each logged move, raising `ReplayError`
      with the move index if a logged move is illegal at its point.
    - _Why this / why now:_ this wires every piece you built into the single small
      surface clients use, and `replay` closes the loop on reproducibility: a seed
      plus the move log is enough to reconstruct any game exactly. This is the
      "wire it all together" step — after it, the engine is usable end to end.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 23.1, 23.2, 23.3_

  - [ ]* 11.3 Write unit tests for view and replay
    - In `tests/test_view.py` and `tests/test_replay.py`, test view field
      filtering and the non-current-player empty move list, and a short
      play-then-replay equality check.
    - _Requirements: 22.3, 22.5, 23.1, 23.3_

- [ ] 12. Property-based test suite and end-to-end game
  - [ ]* 12.1 Property test: random legal playthrough harness (the centerpiece)
    - In `tests/test_prop_playthrough.py`, use Hypothesis to seed a new game and
      repeatedly pick a random move from `legal_moves` and `apply` it, asserting at
      every step that the move list is non-empty until terminal, every applied move
      was legal, resource/bank counts stay non-negative, the distance rule holds,
      and roads stay connected — and that the game terminates.
    - **Property 3: Legality closure** / **Property 4: Legal moves never empty** /
      **Property 5: Resource conservation** / **Property 7: Distance rule** /
      **Property 8: Road connectivity**
    - **Validates: Requirements 1.2, 4.1, 12.3, 14.3, 15.4, 26.2, 26.3**
    - _Why this / why now:_ this single harness exercises the entire engine on
      thousands of random games and is by far the highest-value test — it is where
      most real bugs will surface. Build it as soon as the core is wired.

  - [ ]* 12.2 Property test: copy purity and in-place/copy equivalence
    - In `tests/test_prop_apply_paths.py`, for random reachable states/moves assert
      the copy-path leaves the input byte-for-byte unchanged and that
      `apply(s.copy(), m, in_place=True)` equals `apply(s, m, in_place=False)`.
    - **Property 1: Apply purity (copy path)** / **Property 2: In-place/copy
      equivalence**
    - **Validates: Requirements 2.2, 3.2**

  - [ ]* 12.3 Property test: victory is a sum of sources
    - In `tests/test_prop_victory.py`, assert `victory_points` always equals the
      sum of the bundle's `vp_sources` and that `winner` returns `p` iff
      `victory_points(s, p) ≥ target` on `p`'s turn.
    - **Property 6: Victory is a sum of sources**
    - **Validates: Requirements 21.1, 21.2**

  - [ ]* 12.4 Property test: serialize/replay round-trip
    - In `tests/test_prop_replay.py`, play a random game, then assert
      `replay(seed, move_log)` reproduces the final state exactly.
    - **Property 9: Serialize/replay round-trip**
    - **Validates: Requirements 23.1, 26.1**

  - [ ]* 12.5 Property test: view soundness
    - In `tests/test_prop_view.py`, assert that two states differing only in
      another player's hidden cards produce identical views for the requesting
      player, and that no opponent card identity is exposed.
    - **Property 10: View soundness**
    - **Validates: Requirements 22.4**

  - [ ]* 12.6 Integration test: scripted game to a 10-VP win
    - In `tests/test_integration.py`, drive a fixed, scripted sequence of moves
      from setup to a player reaching 10 VP, asserting `is_terminal` becomes true
      and `winner` returns the expected player.
    - **Validates: Requirements 5.2, 5.3, 21.3**

- [ ] 13. Final checkpoint - ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks. They are not implemented by
  the agent automatically and can be skipped for a faster first cut — but the
  property suite (task 12) is where this engine earns its correctness, so skipping
  it is strongly discouraged.
- Each task references specific requirement sub-clauses for traceability, and each
  property test names the design property number it encodes.
- Checkpoints (tasks 7, 10, 13) are natural places to stop, run everything, and
  ask questions before moving on.
- **Out of scope (no tasks):** player-to-player negotiated trading (only bank 4:1
  and port 3:1/2:1 trades exist in v1) and JSON/file-based board loading (v1 uses
  the in-code `STANDARD_BOARD` constant). Both seams are designed for but
  deliberately deferred.
- The hardest task is **9.2 (longest road)** — treat it as longest *simple path*
  over a possibly branching/cyclic road subgraph with opponent buildings breaking
  continuity, solved by brute-force DFS at Catan's tiny scale.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "2.2", "3.1"] },
    { "id": 2, "tasks": ["2.3", "3.2"] },
    { "id": 3, "tasks": ["3.3", "3.4"] },
    { "id": 4, "tasks": ["3.5", "4.1"] },
    { "id": 5, "tasks": ["4.2", "5.1"] },
    { "id": 6, "tasks": ["5.2"] },
    { "id": 7, "tasks": ["6.1"] },
    { "id": 8, "tasks": ["6.2"] },
    { "id": 9, "tasks": ["6.3"] },
    { "id": 10, "tasks": ["6.4"] },
    { "id": 11, "tasks": ["6.5"] },
    { "id": 12, "tasks": ["6.6", "8.1"] },
    { "id": 13, "tasks": ["8.2"] },
    { "id": 14, "tasks": ["8.3"] },
    { "id": 15, "tasks": ["8.4"] },
    { "id": 16, "tasks": ["8.5"] },
    { "id": 17, "tasks": ["8.6"] },
    { "id": 18, "tasks": ["8.7"] },
    { "id": 19, "tasks": ["8.8"] },
    { "id": 20, "tasks": ["8.9", "9.1"] },
    { "id": 21, "tasks": ["9.2"] },
    { "id": 22, "tasks": ["9.3"] },
    { "id": 23, "tasks": ["9.4", "11.1"] },
    { "id": 24, "tasks": ["11.2"] },
    { "id": 25, "tasks": ["11.3", "12.1", "12.2", "12.3", "12.4", "12.5", "12.6"] }
  ]
}
```
