# Chapter 10 — Proving It Works

> ## At a glance
> - **Where you are:** The engine is complete and wrapped behind `Game` with view and replay (Chapter 9). You have example-based tests scattered across earlier chapters.
> - **This chapter's goal:** Build the tests that earn real confidence — above all, one that plays thousands of random games hunting for any rule violation.
> - **What this chapter is NOT:** This is not new engine features. You add no game logic; you encode the design's correctness properties as tests and let Hypothesis attack them.
> - **By the end you will have:** A property-based test suite in `tests/` — the random-playthrough harness plus one test per correctness property — and a scripted game played to a win.
> - **Maps to:** Task 12 in `.kiro/specs/catan-engine/tasks.md`.
> - **Prerequisites:** All prior chapters — the suite exercises the whole engine. Hypothesis installed (Chapter 1).

**Goal in plain language.** Stop trusting the engine because *you* checked a few
cases, and start trusting it because thousands of generated games couldn't break
its rules.

---

## Two kinds of tests

You have written **example-based tests**: "in this exact situation, expect this."
They are essential but limited — you only catch what you thought to check.

**Property-based testing** is stronger. You state a rule that must *always* hold
and let Hypothesis generate many inputs trying to violate it. When it finds a
counterexample, it even shrinks it to the smallest failing case.

## The centerpiece: a random playthrough

The single most valuable test plays full games by choosing random legal moves,
asserting the engine's invariants at every step:

```python
from hypothesis import given, strategies as st

@given(seed=st.integers(min_value=0, max_value=10_000))
def test_random_playthrough_preserves_invariants(seed):
    s = Game.new("standard", num_players=4, seed=seed)
    steps = 0
    while not Game.is_terminal(s) and steps < 2000:
        moves = Game.legal_moves(s)
        assert moves, "no legal moves but game not over (deadlock!)"   # Property 4
        s = Game.apply(s, moves[seed % len(moves)], in_place=True)     # pick one
        assert_invariants(s)
        steps += 1
    assert Game.is_terminal(s), "game failed to terminate"

def assert_invariants(s):
    for p in range(s.num_players):
        assert all(c >= 0 for c in s.resources[p].values())   # Property 5
    assert no_two_adjacent_settlements(s)                      # Property 7
    assert all_roads_connected(s)                              # Property 8
```

Run this over thousands of seeds and it will surface bugs you would never have
hand-written a case for — an illegal production payout, a distance-rule leak, a
non-terminating game.

## Encode each correctness property

The design lists ten properties; turn each into a test. Several you have already
met as chapter exercises:

```python
def test_copy_is_pure():                 # Property 1
    s = some_state()
    snapshot = serialize(s)
    _ = Game.apply(s, a_legal_move(s), in_place=False)
    assert serialize(s) == snapshot      # copy path left original untouched

def test_replay_round_trip(seed):        # Property 9
    s = play_random_game(seed)
    assert Game.replay("standard", 4, seed, s.move_log) == s
```

Finish with one fully scripted game played to a win, asserting the right player is
declared the winner.

## Why this is non-negotiable

This engine is the foundation for bots and multiplayer; a subtle error here
corrupts everything built above. Property-based tests are how you gain justified
confidence across situations you did not personally imagine. This is where the
project's correctness actually comes from.

> **Margin notes**
> - **Example-based test**: checks one concrete case.
> - **Property-based test**: checks a universal rule against many generated inputs.
> - **Shrinking**: Hypothesis reducing a failing input to its simplest form.
> - **Coverage**: how much of your code the tests exercise; the playthrough test
>   covers a great deal at once.

## Exercises

1. **Write the playthrough.** Implement the random-playthrough test and the
   `assert_invariants` helper. Run it over many seeds; fix whatever it finds.
2. **One property each.** Implement tests for copy purity, in-place/copy
   equivalence, victory-as-sum-of-sources, replay round-trip, and view privacy.
3. **Deliberate bug.** Temporarily make `eff_build_road` forget to deduct the
   cost. Which test(s) catch it, and what does Hypothesis report? Restore the code.
4. **Scripted win.** Script a minimal game to a 10-point victory and assert
   `winner` returns the expected player.

### Hints / how to start

**Where the code goes.** These go in `tests/`, one file per concern:
`tests/test_prop_playthrough.py`, `tests/test_prop_apply_paths.py`,
`tests/test_prop_victory.py`, `tests/test_prop_replay.py`,
`tests/test_prop_view.py`, and `tests/test_integration.py`. The property tests use
Hypothesis's `@given`; the scripted win is a plain example test.

- **Ex. 1 (the playthrough — highest value, write it first).** Copy the chapter's
  harness, then implement the three invariant helpers it calls:
  - `no_two_adjacent_settlements(s)` — for every occupied vertex, assert no
    neighbor (via `board.vertex_neighbors`) is also occupied. This is the
    distance rule from Chapter 3, checked as a global invariant.
  - `all_roads_connected(s)` — for each player, every road touches a vertex that
    connects to another of their roads or one of their buildings.
  - the per-player non-negative resource check is inline already.
  The `steps < 2000` cap is a safety net against an accidental infinite game — if
  it trips, that itself is a bug (a non-terminating game). Run with many seeds; fix
  whatever the harness surfaces before moving on.
- **Ex. 2 (one property each).** You've already built most of these as earlier
  exercises — now formalize them. Copy purity (Chapter 4 Ex. 2), in-place/copy
  equivalence (Chapter 7 Ex. 3), victory-as-sum (assert `victory_points(s, p)`
  equals `sum(src(s, p) for src in active_bundle(s).vp_sources)` for random
  reachable states), replay round-trip (Chapter 9 Ex. 3), and view privacy
  (Chapter 9 Ex. 2). Wrap the ones over many states in `@given` with a seed
  strategy and a helper that plays a random game to a reachable state.
- **Ex. 3 (deliberate bug — see the suite earn its keep).** Comment out the `pay`
  call in `eff_build_road` so roads become free, then run the suite. Expect the
  **resource-conservation** invariant (Property 5) in the playthrough — and likely
  a bank/conservation property test — to fail. Note what Hypothesis prints: a
  concrete failing seed plus a *shrunk* minimal sequence of moves that reaches the
  bad state. That shrinking is the feature that makes property tests debuggable.
  Restore the `pay` call and confirm green again.
- **Ex. 4 (scripted win).** This is a plain (non-Hypothesis) integration test.
  Drive a fixed list of legal moves from setup all the way to a player reaching 10
  VP. Skeleton:
  ```python
  def test_scripted_game_declares_winner():
      s = Game.new("standard", 4, seed=1)
      for m in SCRIPTED_MOVES_TO_A_WIN:    # a hand-authored sequence
          s = Game.apply(s, m, in_place=True)
      assert Game.is_terminal(s)
      assert Game.winner(s) == EXPECTED_WINNER
  ```
  Authoring `SCRIPTED_MOVES_TO_A_WIN` is the work: step through with
  `legal_moves` to pick valid moves at each phase. Keep it minimal — the goal is to
  prove the end-to-end "play → win → terminal" path, not to play realistically.

## Run your tests

```bash
python3 -m pytest
```

You just added the `tests/test_prop_*.py` suite and `tests/test_integration.py`.
The random playthrough (Ex. 1) is the centerpiece — let it run across many seeds.
When the whole suite is green, the engine is trustworthy enough to build bots and
multiplayer on top of.

---

Previous: [09 — The Front Door, Privacy, and Replay](09-front-door.md) | Next: [11 — Afterword & Appendices](11-afterword.md)
