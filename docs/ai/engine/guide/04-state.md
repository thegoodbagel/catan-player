# Chapter 4 — The Game State and Cheap Copying

> ## At a glance
> - **Where you are:** You have an immutable `Board` with adjacency tables (Chapter 3). It describes the map but holds nothing that changes during play.
> - **This chapter's goal:** Build the `State` object holding everything that *changes*, and a `copy()` operation cheap and leak-free enough to call thousands of times.
> - **What this chapter is NOT:** This is not the rules. `State` holds facts only and must not import `rules` or decide anything about legality. It is a plain data container — the changing companion to the fixed `Board`.
> - **By the end you will have:** `src/engine/state.py` with the `State` dataclass and a `copy()` that shares the immutable board but duplicates every mutable container — proven leak-free by a test.
> - **Maps to:** Task 4 in `.kiro/specs/catan-engine/tasks.md`.
> - **Prerequisites:** Chapters 2–3 (you need the enums/moves and a `Board` to hold state against).

**Goal in plain language.** Make one object that captures the whole changing
situation of a game, and make copying it both fast and safe — because the bot in a
later phase will copy it constantly to imagine futures.

---

## What changes versus what does not

The board (Chapter 3) is fixed. The **state** holds the rest: the current phase,
whose turn it is, who owns each vertex and edge, each player's resources and
cards, the robber's location, the deck, the dice, and — crucially — the **move log**.

Ownership is stored as arrays of integers, mirroring the board's ID scheme:

```python
from dataclasses import dataclass, field

@dataclass
class State:
    board: "Board"                       # SHARED, never copied (it's immutable)
    phase: Phase
    current_player: int
    settlements: list[int]               # settlements[v] = owner, or -1 if empty
    roads: list[int]                     # roads[e] = owner, or -1
    resources: list[dict[Resource, int]] # resources[p][Resource.WOOD] = count
    robber_hex: int
    move_log: list                       # every move applied so far
    # ... bank, dev deck, dice, setup progress, rng state ...
```

Using `-1` for "empty" keeps ownership as flat integer arrays — fast to copy and to
compare, exactly the property we want.

## Shallow versus deep copy

This distinction is the heart of the chapter. A **shallow copy** duplicates the
outer container but shares the inner objects; a **deep copy** duplicates
everything. We want something in between: duplicate the *changeable* parts, but
*share* the immutable board.

```python
def copy(self) -> "State":
    new = replace_shallow(self)             # a shallow copy first
    new.board = self.board                  # SHARE the immutable board (safe!)
    new.settlements = list(self.settlements)   # duplicate the mutable lists
    new.roads = list(self.roads)
    new.resources = [dict(r) for r in self.resources]   # duplicate each player's dict
    new.move_log = list(self.move_log)
    return new
```

Sharing the board is safe precisely because nothing can mutate it. Duplicating the
mutable lists means a change to the copy cannot leak back to the original. This is
the concrete reason the board had to be immutable.

## Why this matters

In Chapter 7 the `apply` function will optionally work on a copy, and in the bot
phase a search will copy the state at every node it explores. If copying were
expensive or leaky, search would be impossible. We therefore prove the copy is
clean *now*, with a test, and depend on it forever after.

> **Margin notes**
> - **Shallow copy**: new outer container, shared inner contents.
> - **Deep copy**: everything duplicated, top to bottom.
> - **Aliasing bug**: two variables unexpectedly referring to the same object, so
>   changing one changes the other. Correct copying prevents this.

## Exercises

1. **Implement `copy`.** Then write a test: copy a state, set
   `copy.settlements[0] = 3`, and assert the original's `settlements[0]` is
   unchanged and `copy.board is original.board` (the same object).
2. **Find the aliasing bug.** Replace `[dict(r) for r in self.resources]` with the
   buggy `list(self.resources)`. Write a test that exposes the bug by mutating one
   player's resource dict in the copy and observing the original change. Then fix
   it. Explain in a sentence why the shallow version leaked.
3. **Equality.** Decide how you will compare two states for equality (you will
   need it for replay tests in Chapter 10). Sketch what fields must match.

### Hints / how to start

**Where the code goes.** All of this lives in `src/engine/state.py`. Tests go in
`tests/test_state.py`. Remember: `state.py` must not import `rules`.

- **Ex. 1 (implement `copy`).** Use the body shown above. The cleanest way to get
  the "shallow copy first" is `dataclasses.replace` or `copy.copy(self)`, then
  overwrite the mutable fields with fresh duplicates. A passing test:
  ```python
  # tests/test_state.py
  def test_copy_is_isolated_and_shares_board():
      s = make_state()         # a small helper that builds a State
      c = s.copy()
      c.settlements[0] = 3
      assert s.settlements[0] != 3        # original untouched
      assert c.board is s.board           # board SHARED, not duplicated
  ```
  The `is` (not `==`) in the last line is deliberate: you want the *same object*,
  proving you didn't waste time copying the immutable board.
- **Ex. 2 (find the aliasing bug).** This teaches the single most important idea
  in the chapter. Temporarily swap in the buggy line, then write a test that
  *fails* because of it:
  ```python
  def test_shallow_copy_leaks():
      s = make_state_with_resources()
      c = s.copy()                         # using the BUGGY list(self.resources)
      c.resources[0][Resource.WOOD] += 1   # change only the copy...
      # ...but the dict was shared, so the original changed too:
      assert s.resources[0][Resource.WOOD] != c.resources[0][Resource.WOOD]  # FAILS with bug
  ```
  With `list(self.resources)` the outer list is new but the inner dicts are
  shared, so this test fails. Switch back to `[dict(r) for r in self.resources]`
  (a fresh dict per player) and it passes. One-sentence explanation to write down:
  *copying the outer container isn't enough — you must copy the mutable things
  inside it too.*
- **Ex. 3 (equality).** You don't need to write a perfect `__eq__` yet — just
  decide and sketch. List the fields that must match for two states to be "the
  same game situation": `phase`, `current_player`, `settlements`, `cities`,
  `roads`, `resources`, `robber_hex`, bank, decks, bonus holders, and — for
  replay — `move_log` and the RNG state. A `@dataclass` gives you field-by-field
  `==` for free if you don't set `eq=False`; note which fields (like the shared
  `board`) compare by identity and whether that's what you want.

> **Predicted payoff, now verifiable.** Back in Chapter 0 you predicted why a bot
> exploring 10,000 futures benefits from data-oriented state. Here it is concrete:
> a copy is just duplicating small int arrays and dicts plus one shared board
> reference — no object graph to untangle. That's the cheap copy the search relies
> on.

## Run your tests

```bash
python3 -m pytest
```

You just added `tests/test_state.py`. The aliasing test (Ex. 2) is the one that
matters — watch it fail with the buggy copy, then pass once you copy the inner
dicts. A copy you have proven leak-free is the foundation `apply` depends on.

---

Previous: [03 — The Board as a Graph](03-board.md) | Next: [05 — The Rulebook as Data: The Variant Bundle](05-variant-bundle.md)
