# Building a Game Engine: The Catan Project

*A hands-on course in designing correct, extensible software.*

---

## How to use this guide

This is the teaching companion to the implementation plan in
`.kiro/specs/catan-engine/tasks.md`. That tasks file is a terse checklist for
someone who already builds software; this guide is the course behind it. Read one
chapter, then implement the task with the same number, then run your tests before
moving on. The chapters build strictly on one another, so go in order and resist
skipping. Every chapter opens with an **"At a glance"** box telling you where you
are, what this chapter is and is *not*, and what you will have built by the end.
Reading is not the same as knowing, so do the exercises in code — each chapter's
exercises now include **"Hints / how to start"** scaffolding so you are never
staring at a blank file.

## Chapter index

Each guide file pairs with a task group in `.kiro/specs/catan-engine/tasks.md`.
The task numbers do not line up one-for-one with chapter numbers because the
plan has *checkpoint* tasks (7, 10, 13) between work tasks — the mapping below is
the source of truth.

| File | Chapter | One-line summary | Maps to task |
|---|---|---|---|
| [00-central-idea.md](00-central-idea.md) | Central idea | Separate facts from rules; data-oriented design and the expression problem | Foundational (informs all tasks) |
| [01-workspace-and-tools.md](01-workspace-and-tools.md) | Workspace & tools | Create the project skeleton and get one green test before any game code | Task 1 |
| [02-vocabulary.md](02-vocabulary.md) | Vocabulary | Define the program's "words": resources, dev cards, phases, and moves | Task 2 |
| [03-board.md](03-board.md) | The board | Represent the board as integer-ID adjacency tables on an immutable `Board` | Task 3 |
| [04-state.md](04-state.md) | The state | Build the mutable `State` and a cheap, leak-free `copy()` | Task 4 |
| [05-variant-bundle.md](05-variant-bundle.md) | Variant bundle | Gather "base Catan" into one data bundle the engine reads | Task 5 |
| [06-legal-moves.md](06-legal-moves.md) | Legal moves | Implement `legal_moves(state)` dispatched per phase | Task 6 |
| [07-apply.md](07-apply.md) | Apply | Implement `apply(state, move)` — the single place facts change | Task 8 |
| [08-scoring.md](08-scoring.md) | Scoring | Victory points, the winner check, and longest road (the one hard algorithm) | Task 9 |
| [09-front-door.md](09-front-door.md) | Front door | Wrap it in `Game`, add per-player `view`, and add `replay` | Task 11 |
| [10-testing.md](10-testing.md) | Testing | Property-based tests, led by a random-playthrough harness | Task 12 |
| [11-afterword.md](11-afterword.md) | Afterword | How to proceed, what you learned, and the reference appendices | Wrap-up (checkpoints 7/10/13) |

## Prerequisites and reading order

**Prerequisites.** You can read and write basic Python or Java: variables, loops,
functions, classes, lists, dictionaries. You have seen a graph and a recursion
problem (the leetcode level is plenty). You need nothing else; every larger idea
is developed here.

**Reading order.** Straight through, 00 → 11. Each layer leans only on the ones
beneath it:

```
00  central idea       ─ the one design rule everything follows
01  tooling             ─ can you run tests?
02  vocabulary          ─ words: resources, phases, moves        (types.py, moves.py)
03  board               ─ the map + neighbor lookups             (board.py, board_data.py)
04  state               ─ what changes, copyable                 (state.py)
05  rulebook shape      ─ the empty bundle + registry            (rules.py)
06  list moves          ─ legal_moves                            (rules.py)
07  do moves            ─ apply                                  (rules.py)
08  score               ─ victory, longest road                  (rules.py)
09  front door          ─ the public interface                   (game.py)
10  prove it            ─ tests                                  (tests/)
```

After Chapter 7 you can already play a full game from the keyboard. After
Chapter 10 you have a trustworthy engine.

---

## The tools, concretely

Three tools recur throughout. Meet them now so they are not mysterious later.
(Chapter 1 walks you through installing them step by step.)

**1. Python 3.11+** is our language. We lean on three modern features:

```python
from dataclasses import dataclass      # concise "data record" classes
from enum import Enum                   # fixed sets of named values
from typing import Optional             # type hints that document intent

@dataclass(frozen=True)                 # a record whose fields can't change
class Point:
    x: int                              # ": int" is a type hint
    y: int

p = Point(2, 3)
print(p)            # Point(x=2, y=3)  -- dataclasses print themselves nicely
# p.x = 5          # would raise: frozen records are immutable
```

**2. pytest** runs our tests. A test is any function whose name starts with
`test_`; you assert what should be true, and pytest reports failures.

```python
# tests/test_point.py
from engine.geometry import Point

def test_point_holds_coordinates():
    p = Point(2, 3)
    assert p.x == 2 and p.y == 3
```

Run it from the project root with `python3 -m pytest`. Green means all assertions
held.

**3. Hypothesis** is a *property-based testing* library (Chapter 10). Rather than
checking one example, it invents hundreds of inputs trying to break a rule you
state:

```python
from hypothesis import given, strategies as st

@given(st.integers(), st.integers())
def test_addition_commutes(a, b):
    assert a + b == b + a     # Hypothesis tries many (a, b) pairs
```

You will install these once in Chapter 1.

---

Next: [00 — The Central Idea](00-central-idea.md)
