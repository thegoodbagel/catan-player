# Chapter 6 — Operation One: "What Can I Do Now?"

> ## At a glance
> - **Where you are:** You have the bundle shape and registry (Chapter 5) with stubbed rule slots. The engine can *find* a rulebook but can't yet list what's legal.
> - **This chapter's goal:** Implement `legal_moves(state)` — the first of the engine's three public operations — returning every move legal in the current state, dispatched by phase.
> - **What this chapter is NOT:** This is not where moves get *applied*. `legal_moves` only *lists* options; it never mutates state. Carrying a move out is Chapter 7. You are filling in the `generators` slots of the bundle, not the `effects`.
> - **By the end you will have:** `legal_moves` plus the per-phase generators (`gen_setup_moves`, `gen_roll_moves`, `gen_discard_moves`, `gen_robber_moves`, `gen_main_moves`) and shared helpers like `can_afford`, all in `rules.py`.
> - **Maps to:** Task 6 in `.kiro/specs/catan-engine/tasks.md`.
> - **Prerequisites:** Chapters 3 (board adjacency), 4 (state), 5 (bundle/dispatch).

**Goal in plain language.** Write the function that answers "what can I do right
now?" — and have it return *only* legal moves, so nothing downstream can ever
offer or attempt an illegal action.

---

## The role of legal-move generation

This single function is what a user interface turns into a menu and what a bot
chooses from. By returning *only* legal moves, we make an entire class of bugs
impossible: nothing downstream can offer or attempt an illegal action, because it
never sees one. The rules of "what is allowed" live in exactly one place.

## Dispatch on the phase

What is legal depends entirely on the current phase, so `legal_moves` looks up the
phase's generator in the bundle (the dispatch pattern from Chapter 5):

```python
def legal_moves(state) -> list:
    generator = active_bundle(state).generators[state.phase]
    return generator(state)             # delegate to the phase's lister
```

This is the engine's **finite state machine** in action: the game is always in one
phase, and the phase decides what may happen. Each generator is a small function.
The MAIN-phase generator is the largest because that is where most choices live:

```python
def gen_main_moves(state) -> list:
    p = state.current_player
    costs = active_bundle(state).build_costs
    moves = [EndTurn()]                          # always permitted

    if can_afford(state, p, costs[BuildRoad]):
        for e in buildable_road_edges(state, p):
            moves.append(BuildRoad(e))
    if can_afford(state, p, costs[BuildSettlement]):
        for v in buildable_settlement_vertices(state, p):
            moves.append(BuildSettlement(v))
    # ... cities, buy dev card, play one dev card, bank/port trades ...
    return moves
```

The placement helpers are where the spatial rules from Chapter 3 finally pay off.
The distance rule and connectivity are pure table lookups:

```python
def buildable_settlement_vertices(state, p) -> list[int]:
    board, result = state.board, []
    for v in range(board.num_vertices()):
        if state.settlements[v] != -1 or state.cities[v] != -1:
            continue                              # occupied
        if any(occupied(state, n) for n in board.vertex_neighbors(v)):
            continue                              # violates the distance rule
        if not any(state.roads[e] == p for e in board.vertex_edges(v)):
            continue                              # not connected to your roads
        result.append(v)
    return result
```

## Build the generators in order

Implement them in the order play proceeds — SETUP first, so you can actually start
a game and exercise the dispatcher end to end, then ROLL, then DISCARD/ROBBER,
then MAIN. Each is small and independently testable.

> **A useful invariant.** As long as the game is not over, `legal_moves` must
> never return an empty list — otherwise play would deadlock. Asserting this is one
> of our correctness properties (Chapter 10).

> **Margin notes**
> - **Finite state machine (FSM)**: a system always in one of a fixed set of
>   states, moving between them by defined transitions.
> - **Generator** (here): a function that lists the legal moves for one phase. (Not
>   to be confused with Python's `yield`-based generators.)
> - **Invariant**: a condition that must always hold.

## Exercises

1. **SETUP generator.** Implement `gen_setup_moves`: during setup, offer
   `PlaceSetupSettlement(v)` for every distance-legal vertex; after a settlement is
   placed, offer `PlaceSetupRoad(e)` only for edges touching it. Reuse your
   Chapter 3 distance helper.
2. **Affordability.** Implement `can_afford(state, p, cost)` where `cost` is a
   dict of `Resource -> int`. Test it on a player who has exactly enough, one short,
   and far more than enough.
3. **MAIN generator.** Implement `gen_main_moves` for builds and bank trades
   (defer dev cards and ports if you like). Write a test on a hand-built state with
   known resources and roads, asserting the exact set of legal moves.
4. **Deadlock check.** Construct a mid-game state and assert `legal_moves` is
   non-empty. Then reason: in which phase could a naive implementation wrongly
   return nothing, and how do you prevent it?

### Hints / how to start

**Where the code goes.** All generators and helpers go in `src/engine/rules.py`
(continuing the file you began in Chapter 5). Wire each finished generator into
the `BASE` bundle's `generators` dict, replacing its placeholder. Tests go in
`tests/test_legal_moves.py`.

- **Ex. 2 (affordability — do this first, everything uses it).** It's a small,
  pure helper. Signature and body:
  ```python
  def can_afford(state, p, cost: dict) -> bool:
      have = state.resources[p]
      return all(have.get(res, 0) >= need for res, need in cost.items())
  ```
  Three tests: a hand with *exactly* the cost → `True`; one resource short →
  `False`; a hand with plenty → `True`.
- **Ex. 1 (SETUP generator).** Setup has two sub-steps that alternate: place a
  settlement, then place a road touching it. Use a flag/field on the state (e.g.
  whether the last setup placement was a settlement awaiting its road). Reuse your
  Chapter 3 `can_place_settlement`. Skeleton:
  ```python
  def gen_setup_moves(state) -> list:
      board = state.board
      if state.awaiting_setup_road is None:   # need a settlement next
          occupied = {v for v, o in enumerate(state.settlements) if o != -1}
          return [PlaceSetupSettlement(v) for v in range(board.num_vertices())
                  if can_place_settlement(board, occupied, v)]
      v = state.awaiting_setup_road           # need a road touching vertex v
      return [PlaceSetupRoad(e) for e in board.vertex_edges(v)
              if state.roads[e] == -1]
  ```
  A passing test: on a fresh game, every offered settlement vertex passes the
  distance rule; after one is placed, only edges touching it are offered.
- **Ex. 3 (MAIN generator).** Build on the chapter's `gen_main_moves` sketch.
  Start with just `EndTurn`, then add roads and settlements gated by *both*
  `can_afford` and the placement helpers, then bank trades (4 of one resource for
  1 of another). Defer dev cards/ports if you like. A passing test builds a state
  by hand with a known hand and known roads, calls `gen_main_moves`, and asserts
  the returned set *exactly* equals the moves you worked out on paper — use
  `set(...)` so order doesn't matter (this is why moves are hashable, Chapter 2).
- **Ex. 4 (deadlock check).** Assert `legal_moves(state)` is non-empty on a
  mid-game state. The reasoning to write down: the danger phase is MAIN — a naive
  generator that only lists *builds/trades* returns `[]` for a player who can
  afford nothing. The fix is the line `moves = [EndTurn()]` — `EndTurn` is always
  legal, so the list is never empty. That guarantee is Property 4 in Chapter 10.

## Run your tests

```bash
python3 -m pytest
```

You just added `tests/test_legal_moves.py`. Build the generators SETUP → ROLL →
DISCARD/ROBBER → MAIN so you can drive the dispatcher end to end as you go. Keep
the "never empty until terminal" invariant in mind — it's the one Chapter 10 will
hammer with thousands of random games.

---

Previous: [05 — The Rulebook as Data: The Variant Bundle](05-variant-bundle.md) | Next: [07 — Operation Two: Making It Happen](07-apply.md)
