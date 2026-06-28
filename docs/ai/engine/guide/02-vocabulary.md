# Chapter 2 — The Vocabulary of the Game

> ## At a glance
> - **Where you are:** Your project runs and one green test passes (Chapter 1). There is still no game code at all.
> - **This chapter's goal:** Define the program's basic "words" — resource types, development-card kinds, turn phases, and the notion of a *move* — as precise, typo-proof values.
> - **What this chapter is NOT:** **This is vocabulary, not the rules.** You are defining the *words* the rules will later use, not writing any rule. Nothing here decides what is legal or what a move does — that comes in Chapters 6–8. After this chapter `rules.py` is still empty, and that is correct.
> - **By the end you will have:** `src/engine/types.py` (the `Resource`, `DevCard`, `Phase` enums and the `Port` record) and move records in `src/engine/moves.py` — data with no behavior.
> - **Maps to:** Task 2 in `.kiro/specs/catan-engine/tasks.md`.
> - **Prerequisites:** Chapters 0–1 (you need a runnable project and the facts-vs-rules idea).

**Goal in plain language.** Give the program an exact way to *say* things —
"wood", "the roll phase", "build a settlement at vertex 7" — before anyone writes
a rule *about* those things.

**Why.** You cannot write rules about wood until the program has an exact,
typo-proof way to say "wood." Two language tools give us this.

---

## Tool 1: enumerations for fixed sets

An **enum** is a fixed set of named values. Catan has exactly five resources, so:

```python
from enum import Enum

class Resource(Enum):
    WOOD = "wood"
    BRICK = "brick"
    SHEEP = "sheep"
    WHEAT = "wheat"
    ORE = "ore"
```

Now `Resource.WOOD` is a first-class value the program understands. A misspelling
like `Resource.WODO` is an immediate error, not a silent bug that surfaces three
hours later. Compare the fragile alternative — passing the bare string `"wood"`
everywhere — where `"wodo"` sails through unnoticed.

We define the turn **phases** the same way, because the turn is a fixed sequence
of stages:

```python
class Phase(Enum):
    SETUP = "setup"; ROLL = "roll"; DISCARD = "discard"
    ROBBER = "robber"; MAIN = "main"; GAME_OVER = "game_over"
```

## Tool 2: records for moves

A **move** is a small record describing one action a player intends — and *only*
the intent. It performs nothing itself. (Recall Chapter 0: moves are facts, not
rules.) We use a *frozen dataclass*, meaning an immutable record:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class BuildSettlement:
    vertex: int                 # the only thing this move needs to know

@dataclass(frozen=True)
class BankTrade:
    give: Resource
    receive: Resource           # exchange 4 "give" for 1 "receive"
```

Freezing buys two concrete properties we will rely on. First, a recorded move can
never be altered after the fact. Second, frozen dataclasses are **hashable** and
support equality automatically, so two moves can be compared and a list of moves
replayed deterministically:

```python
BuildSettlement(7) == BuildSettlement(7)     # True, by value
{BuildSettlement(7), BuildSettlement(7)}      # a set with ONE element
```

## Why moves carry no behavior

It is tempting to give a move an `apply()` method. We deliberately do not. Keeping
moves as inert descriptions lets the same object serve three masters later: the
move log replays a game, a bot returns a move as its decision, and the network
ships a move as a tiny message. All three work precisely because a move is just
data.

> **Margin notes**
> - **Enum**: a fixed, named set of values; prevents invalid values.
> - **Dataclass**: a concise class that mainly holds fields (a "record"/"struct").
> - **Frozen / immutable**: cannot change after creation.
> - **Hashable**: usable as a dictionary key or set member; required for fast
>   lookups and deduplication.

## Exercises

1. **Define enums.** Write the `DevCard` enum with five kinds: knight,
   victory point, road building, year of plenty, monopoly.
2. **Design moves.** Write frozen dataclasses for `BuildRoad`, `MoveRobber`
   (which hex, and an optional victim to steal from), and `EndTurn` (which needs
   no fields). For the optional victim, use `Optional[int]` and default it to
   `None`.
3. **Prove immutability.** In a test, construct a `BuildSettlement(7)`, attempt
   `move.vertex = 9`, and assert it raises. (Look up `pytest.raises`.)
4. **Prove value-equality.** Assert that two separately constructed
   `BankTrade(Resource.WOOD, Resource.ORE)` are equal and collapse into a
   single-element set. Why does this matter for a move log?

### Hints / how to start

**Where the code goes.** Enums go in a new file `src/engine/types.py`; the move
records go in `src/engine/moves.py` (which exists as an empty stub). The tests go
in `tests/test_moves.py`.

- **Ex. 1 (DevCard enum).** Copy the shape of `Resource`. Five members:
  ```python
  # src/engine/types.py
  class DevCard(Enum):
      KNIGHT = "knight"
      VICTORY_POINT = "victory_point"
      ROAD_BUILDING = "road_building"
      YEAR_OF_PLENTY = "year_of_plenty"
      MONOPOLY = "monopoly"
  ```
- **Ex. 2 (design moves).** Each is a `@dataclass(frozen=True)` carrying only the
  fields it needs. Start from these signatures and fill the bodies:
  ```python
  # src/engine/moves.py
  from dataclasses import dataclass
  from typing import Optional
  from engine.types import Resource   # import what a move references

  @dataclass(frozen=True)
  class BuildRoad:
      edge: int

  @dataclass(frozen=True)
  class MoveRobber:
      hex: int
      steal_from: Optional[int] = None   # who to steal from, if anyone

  @dataclass(frozen=True)
  class EndTurn:
      pass                               # no fields — pure intent
  ```
  Note the field with a default (`steal_from`) must come *after* fields without
  one. `EndTurn` having no fields is fine and intentional.
- **Ex. 3 (prove immutability).** The tool is `pytest.raises`. A passing test here
  *expects an error*:
  ```python
  # tests/test_moves.py
  import pytest
  from engine.moves import BuildSettlement   # add BuildSettlement to moves.py too

  def test_move_is_frozen():
      m = BuildSettlement(7)
      with pytest.raises(Exception):   # frozen dataclasses raise on assignment
          m.vertex = 9                 # this line SHOULD fail — that's the pass
  ```
  If the assignment does *not* raise, you forgot `frozen=True` on the dataclass.
- **Ex. 4 (value-equality).** What a passing test checks: two separately built but
  field-identical moves are `==`, and a `set` of them has one element.
  ```python
  from engine.moves import BankTrade
  from engine.types import Resource

  def test_moves_compare_by_value():
      a = BankTrade(Resource.WOOD, Resource.ORE)
      b = BankTrade(Resource.WOOD, Resource.ORE)
      assert a == b               # equal by fields, not identity
      assert len({a, b}) == 1     # the set collapses the duplicate
  ```
  *Why it matters:* the **move log** (Chapter 4) records every move so a game can
  be replayed. Value-equality is what lets you compare "the move that was logged"
  against "a move regenerated during replay" and confirm they match. Without it,
  replay verification (Chapter 10) would be impossible.

> A reminder on scope: when you finish this chapter you have *words and nothing
> that does anything* — no legality checks, no effects. That is the right place to
> be. "Finishing the rules" is Chapters 5–8.

---

Previous: [01 — Workspace and Tools](01-workspace-and-tools.md) | Next: [03 — The Board as a Graph](03-board.md)
