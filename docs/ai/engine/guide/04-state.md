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

---

## Appendix: The Python behind `State`

One idea sits under most of what follows, so it comes first. An **annotation** is
the `: type` you can attach to a variable or field, as in `x: int`. Python records
annotations but never checks or acts on them while the program runs — they exist
for human readers and for tools such as type checkers and editors. So "the type is
wrong" is never itself a runtime error here, and a few of the oddities below (a
type written in quotes, a bare `list`) are simply notes to those readers rather
than instructions to Python.

### Dataclasses

Writing a small class that just holds a few values normally means writing a
repetitive constructor that copies each argument onto `self`, and then writing
`__repr__` and `__eq__` by hand. A **dataclass** generates all of that from the
fields you declare, and you declare a field simply by giving it a name and an
annotation.

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
```

The annotation is doing real work: the decorator scans the class for annotated
attributes and treats each as a field. From those fields it builds a constructor,
so that `Point(1, 2)` and `Point(x=1, y=2)` both work, a readable string form, and
an equality check that compares two points field by field.

A field may carry a default value, and the rule mirrors ordinary function
arguments: once one field has a default, every field after it must have one too.
Required fields therefore come first and defaulted ones last, or Python refuses to
build the class. This is the exact ordering that broke `State` earlier, when the
defaulted fields had drifted above the required ones.

Defaults that are themselves mutable — a list, a dict, a set — need special care.
If you wrote `move_log: list = []`, that one list would be shared by every `State`
ever created, so appending to one game's log would silently change every other.
Dataclasses catch this and make you request a fresh object per instance through a
factory instead:

```python
from dataclasses import dataclass, field

@dataclass
class State:
    move_log: list = field(default_factory=list)   # a new empty list for each State
```

`field(...)` is the general way to configure a single field; asking for a
`default_factory` is its most common use, though it can also drop a field out of
the generated equality check (`compare=False`) or hide it from the string form
(`repr=False`).

A dataclass can also be **frozen**, meaning its fields cannot be reassigned after
construction; a frozen instance is additionally hashable, so it can live in a set
or serve as a dict key. That is why the move records are written
`@dataclass(frozen=True)`: a recorded move should never change afterward, and
hashability is what lets the move log be compared and replayed. `State` is left
unfrozen, because the turn loop updates it in place.

### Types that don't exist yet, and types left vague

Because annotations are never executed, you can name a type Python cannot resolve
at that moment by writing it as a string — a **forward reference**. A method that
returns its own class needs one, as in `def copy(self) -> "State":`, written while
`State` is still being defined, and so does the `board: "Board"` field. `Board` is
imported in a block that runs only for type checkers:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:          # a constant that is False at runtime, True for tools
    from engine.board import Board
```

Importing it this way avoids an import cycle and does not require `board.py` to
exist yet, but it also means the name `Board` genuinely is not available while the
program runs, so it may appear only inside a string. (Adding
`from __future__ import annotations` at the top of the file turns every annotation
into a string automatically, which is why the quotes are strictly optional.)

The opposite case is a type left deliberately vague. `move_log: list` says "a
list" without saying of what, because a move can be any of several record types and
there is no single name covering them yet. That is a valid annotation; it simply
promises less.

### Copying without leaks

The chapter's core problem is a copy that is both cheap and safe, and the two
ready-made copies each fail one of those goals. A **shallow copy** (`copy.copy`)
makes a new outer object but leaves its fields pointing at the very same inner
objects, so editing the copy's resource dict would also edit the original's. A
**deep copy** (`copy.deepcopy`) duplicates everything recursively, which is safe
but wasteful, since it would clone the large, unchanging board on every call.

What `State.copy()` needs lies between the two: keep sharing the parts that never
change, and duplicate the parts that do. Sharing is safe exactly for values that
cannot be mutated — an integer, a string, a tuple, a frozen record, or the
immutable `Board` — because nothing can alter them through the shared reference.
Everything mutable is rebuilt fresh:

```python
import copy as _copy

def copy(self) -> "State":
    new = _copy.copy(self)                             # start from a shallow copy
    new.board = self.board                             # deliberately keep sharing it
    new.settlements = list(self.settlements)           # a new list of the same ints
    new.resources = [dict(r) for r in self.resources]  # a new list AND a new dict each
    return new
```

The difference between those last two lines is the point of the whole chapter.
`list(xs)` makes a new list, which is enough when its elements are themselves
immutable, as the owner ints are. But when a list holds mutable items — each
player's resource dict — a new outer list still shares those dicts, so each one
must be copied too, which is what `[dict(r) for r in xs]` does. Overlooking this is
precisely the aliasing bug Exercise 2 asks you to reproduce.

One convenience for later: `dataclasses.replace(record, field=value)` returns a
copy of a record with a single field changed, which is the normal way to "modify" a
frozen instance you are not allowed to assign to.

### Iterating an enum during setup

Initialising the per-player tallies relies on two small facts: an `Enum` can be
looped over, yielding its members in order, and a member can be used as a dict key.
Together they let one comprehension give every player a fully zeroed resource
count:

```python
resources = [{r: 0 for r in Resource} for _ in range(num_players)]
```

The inner `for r in Resource` walks `Resource.WOOD`, `Resource.BRICK`, and the
rest, building one `{resource: 0}` dict, and the outer comprehension repeats that
for each player.
