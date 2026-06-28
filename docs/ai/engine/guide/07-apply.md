# Chapter 7 — Operation Two: Making It Happen

> ## At a glance
> - **Where you are:** `legal_moves` lists every legal option per phase (Chapter 6), but nothing yet *changes* the game when a move is chosen.
> - **This chapter's goal:** Implement `apply(state, move)` — the single place all change happens — with a validation gate and an in-place/copy switch, plus the per-move effect functions.
> - **What this chapter is NOT:** This is not scoring or winning logic in detail (that's Chapter 8) and not the public API (Chapter 9). You fill in the bundle's `effects` slots here. After Chapter 7 you can actually play a whole game from the keyboard.
> - **By the end you will have:** `apply` (validate → choose path → dispatch effect → advance phase → log) and effect functions like `eff_build_road`, `eff_build_settlement`, `eff_roll`, `distribute_production`, all in `rules.py`.
> - **Maps to:** Task 8 in `.kiro/specs/catan-engine/tasks.md` (Task 7 is a checkpoint).
> - **Prerequisites:** Chapters 4 (state.copy), 5 (bundle/effects dispatch), 6 (legal_moves — `apply` calls it to validate).

**Goal in plain language.** Write the one function that turns a chosen move into
the next game state — and make it impossible for an illegal move to corrupt
anything.

---

## The shape of apply

Because moves are inert (Chapter 2), this function is the sole place facts change.
It proceeds in a careful, fixed order:

```python
def apply(state, move, in_place: bool = False):
    if is_terminal(state):
        raise GameOver()
    if move not in legal_moves(state):           # (1) validate
        raise IllegalMove(move)

    s = state if in_place else state.copy()      # (2) choose path: fast vs. safe

    effect = active_bundle(s).effects[type(move)]  # (3) look up what it does
    next_phase = effect(s, move)                   #     ... and do it (mutates s)

    s.phase = next_phase                         # (4) advance phase, record move
    s.move_log.append(move)
    if winner(s) is not None:
        s.phase = Phase.GAME_OVER
    return s
```

Two design points deserve emphasis.

**The validation gate (step 1).** By checking membership in `legal_moves` before
touching anything, we guarantee an illegal move changes nothing. This is the
single line that makes "an illegal move can never corrupt the game" true.

**The in-place/copy switch (step 2).** This is the *only* place the two modes
differ. Normal play passes `in_place=True` (fast: mutate directly). A bot's search
passes `in_place=False` (safe: work on a copy, leaving the real game untouched).
Because every effect below operates on `s` identically regardless of which branch
was taken, the two modes are *guaranteed* to produce equal results — a property we
get by construction rather than by vigilance.

## Effects are small and dispatched

Each kind of move has one effect function, found via the bundle's dispatch table.
They are mostly short:

```python
def eff_build_settlement(s, move) -> Phase:
    p = s.current_player
    pay(s, p, active_bundle(s).build_costs[BuildSettlement])  # resources -> bank
    s.settlements[move.vertex] = p
    recompute_longest_road(s)      # an opponent's new building can shorten a road!
    return Phase.MAIN

def eff_roll(s, move) -> Phase:
    d1, d2 = roll_two_dice(s)      # uses the state's seedable RNG (Chapter 9)
    total = d1 + d2
    if total == 7:
        s.pending_discards = players_over_limit(s)
        return Phase.DISCARD if s.pending_discards else Phase.ROBBER
    distribute_production(s, total)    # bank -> players: settlement 1, city 2
    return Phase.MAIN
```

> **Margin notes**
> - **Guard clause**: an early check that rejects bad input before the main work
>   (our validation gate).
> - **Determinism**: same inputs always yield the same output. Using a *seedable*
>   random generator keeps even dice rolls deterministic for tests and replay.

## Exercises

1. **apply skeleton.** Implement `apply` with the validation gate and the
   in-place/copy switch. Test that applying an illegal move raises `IllegalMove`
   and leaves the state unchanged, and that applying to a finished game raises
   `GameOver`.
2. **An effect.** Implement `eff_build_road`: deduct the cost, set
   `roads[edge] = player`, return `MAIN`. Test that resources decreased correctly
   and the road is recorded.
3. **Equivalence property.** For a hand-built state and a legal move, assert that
   `apply(s.copy(), m, in_place=True)` equals `apply(s, m, in_place=False)`, and
   that the second form left `s` unchanged. Explain why this holds *by
   construction*.
4. **Production.** Implement `distribute_production(s, total)` using
   `hex_vertices`. Test a roll that should pay a city owner 2 and a settlement
   owner 1 on the same number.

### Hints / how to start

**Where the code goes.** `apply`, the effects, and helpers like `pay` and
`distribute_production` go in `src/engine/rules.py`. Wire each effect into the
`BASE` bundle's `effects` dict (keyed by move *type*), replacing the placeholder.
Tests go in `tests/test_apply.py`.

- **Ex. 1 (apply skeleton).** Type it exactly as the chapter shows, then define
  the exceptions: `class IllegalMove(Exception): pass` and
  `class GameOver(Exception): pass`. Two tests prove the gate works:
  ```python
  def test_illegal_move_is_rejected_and_changes_nothing():
      s = make_main_state()
      before = s.copy()
      with pytest.raises(IllegalMove):
          apply(s, an_illegal_move(), in_place=True)
      assert states_equal(s, before)     # nothing mutated before the raise

  def test_apply_on_finished_game_raises():
      s = make_finished_state()
      with pytest.raises(GameOver):
          apply(s, EndTurn(), in_place=True)
  ```
  The first test passes *because* the validation gate runs before any mutation.
- **Ex. 2 (an effect).** Mirror `eff_build_settlement`. Use a shared `pay` helper
  that moves resources from the player to the bank:
  ```python
  def pay(s, p, cost: dict):
      for res, n in cost.items():
          s.resources[p][res] -= n
          s.bank[res] += n

  def eff_build_road(s, move) -> Phase:
      p = s.current_player
      pay(s, p, active_bundle(s).build_costs[BuildRoad])
      s.roads[move.edge] = p
      return Phase.MAIN
  ```
  A passing test asserts the player's wood/brick each dropped by 1 and
  `s.roads[move.edge] == p`.
- **Ex. 3 (equivalence property — the payoff of the switch).** This is the most
  important test in the chapter. What it checks: the two paths agree, and the copy
  path doesn't touch the input.
  ```python
  def test_inplace_and_copy_agree():
      s = make_main_state()
      m = some_legal_move(s)
      a = apply(s.copy(), m, in_place=True)    # mutate a throwaway copy
      snapshot = s.copy()
      b = apply(s, m, in_place=False)          # copy path: must not touch s
      assert states_equal(a, b)                # both paths agree
      assert states_equal(s, snapshot)         # original untouched by copy path
  ```
  The one-line explanation to write: it holds *by construction* because the only
  difference between the paths is `s = state` vs `s = state.copy()` in step (2) —
  every effect runs identically on `s` afterward, so they cannot diverge.
- **Ex. 4 (production).** Walk the hexes carrying the rolled number, then their
  corners, paying owners. Skeleton:
  ```python
  def distribute_production(s, total):
      board = s.board
      for h in range(board.num_hexes()):
          if board.hex_number(h) != total:
              continue
          res = board.hex_resource(h)
          for v in board.hex_vertices(h):
              if s.settlements[v] != -1:
                  s.resources[s.settlements[v]][res] += 1   # settlement: 1
              elif s.cities[v] != -1:
                  s.resources[s.cities[v]][res] += 2        # city: 2
  ```
  A passing test: build a state where the same number feeds one settlement and one
  city, fire `distribute_production`, assert +1 and +2 respectively.

## Run your tests

```bash
python3 -m pytest
```

You just added `tests/test_apply.py`. Once the equivalence property (Ex. 3)
passes, you have the cornerstone the bot's search depends on — and you can play a
full game from the keyboard by alternating `legal_moves` and `apply`.

---

Previous: [06 — Operation One: "What Can I Do Now?"](06-legal-moves.md) | Next: [08 — Scoring, and the One Hard Algorithm](08-scoring.md)
