# Chapter 0 — The Central Idea: Separate Facts from Rules

> ## At a glance
> - **Where you are:** The very start. Nothing is built yet; this chapter is the one idea the whole project is organized around.
> - **This chapter's goal:** Understand the single design rule — keep *facts* in plain data and *rules* in separate functions — and why it beats the object-oriented default for a game engine.
> - **What this chapter is NOT:** This is not setup and not code you ship. You will not install anything or create engine files here — that starts in Chapter 1. This is the mental model everything else hangs on.
> - **By the end you will have:** A clear answer to "where does logic live?", the ability to label any game concept as a fact or a rule, and a one-paragraph argument for why this choice makes a bot's search cheap.
> - **Maps to:** Foundational — informs every task in `.kiro/specs/catan-engine/tasks.md` (no single task number).
> - **Prerequisites:** None beyond basic Python/Java and the [README](README.md) intro.

**Goal in plain language.** Learn to tell *what is true right now* (facts) apart
from *what may happen and what follows* (rules), and commit to storing the first
as plain data and the second as functions. That's it. Get this, and the rest of
the book is detail.

---

## Why this matters as a running example

We use the Catan board game for the same reason algorithms texts use sorting: it
is small enough to hold in your head, yet rich enough to demand real design. By
the end of the book you will have built a complete, tested game engine, and —
more importantly — you will understand *why* it is built the way it is.

Every interactive program manages two fundamentally different things, and the
quality of your design depends on telling them apart.

- **Facts** describe what is true at a moment: piece positions, whose turn it is,
  each player's cards. Facts are inert — pure information.
- **Rules** describe what may happen and what follows: which moves are legal, what
  a move does to the facts. Rules are active — they read facts and produce new facts.

The thesis of this entire project is one sentence:

> **Keep the facts in plain data structures, and keep the rules in separate
> functions that transform that data.**

This is sometimes called a *data-oriented* design with a *functional core*: the
core of the program is functions that take data and return data, with no hidden
state and no side effects.

## Contrast with what you may have learned

In introductory object-oriented programming you are taught to bundle data with
the methods that act on it. A `Settlement` would store its location *and* contain
`build()` logic. That is a fine default for many programs. For a game engine it is
the wrong default, and it is worth seeing why with a concrete miniature.

Here is the object-oriented instinct:

```python
class Settlement:
    def __init__(self, vertex, owner):
        self.vertex = vertex
        self.owner = owner
    def victory_points(self):           # behavior lives inside the data
        return 1
```

And here is the data-oriented alternative we will use:

```python
@dataclass(frozen=True)
class Settlement:                        # data only -- no methods
    vertex: int
    owner: int

def victory_points(piece) -> int:        # behavior lives outside, in a function
    return 1
```

They compute the same number. The difference is *where the logic lives*, and that
difference compounds. Because our `Settlement` is pure data, we can copy it,
compare it, store it in a list, and serialize it to send across a network — without
any logic getting entangled. We will exploit this relentlessly: a bot copies the
entire game state thousands of times to explore hypothetical futures, and that is
only cheap because the state is plain data.

## The expression problem (a preview)

There is a classic trade-off named the **expression problem**. Object-oriented
code makes it easy to add new *types* but awkward to add new *operations* across
all existing types; the functional/data style makes it easy to add new
*operations* but awkward to add new *types*. A game engine accumulates operations
constantly (list moves, apply moves, score, render, evaluate) over a few stable
data shapes, so we choose the side that makes new operations cheap. In Chapter 5
we will buy back the weak direction with a small registry, so adding a new game
*variant* stays easy too.

> **Margin notes**
> - **State**: the complete set of changeable facts at one instant.
> - **Pure function**: a function whose output depends only on its inputs and
>   which changes nothing outside itself. Easy to test, easy to reason about.
> - **Side effect**: any change a function makes to the world beyond its return
>   value (printing, writing a file, mutating a global). Our core avoids these.

## Exercises

1. **Classify.** For each, label it *fact* or *rule*: (a) "player 2 owns vertex
   7"; (b) "a settlement costs one wood and one brick"; (c) "the robber is on hex
   9"; (d) "on a 7, players over the hand limit discard half." Explain each in one
   line.
2. **Refactor.** Take the object-oriented `Settlement` above and rewrite a
   `Road(edge, owner)` plus a free function `road_points(road)` returning 0.
   Notice what you did and did *not* put inside the class.
3. **Predict the payoff.** In one paragraph, explain why a bot that explores
   10,000 hypothetical move sequences benefits from the data-oriented choice.
   (We will verify your prediction in Chapter 4.)

### Hints / how to start

These are pencil-and-paper / scratch-file exercises — there is no engine code to
write yet, so do them in a throwaway `.py` file or even a notebook.

- **Ex. 1 (classify).** Ask one question per item: *does it describe something
  that is simply true right now, or does it describe what's allowed / what
  happens next?* The first is a fact, the second is a rule. Watch (b) and (d):
  they sound like "the state of the game" but they are really *rules* — a cost and
  a procedure. Write your one-liner as "fact, because …" or "rule, because …".
- **Ex. 2 (refactor).** Mirror the data-oriented `Settlement` exactly. Start from:
  ```python
  from dataclasses import dataclass

  @dataclass(frozen=True)
  class Road:
      edge: int
      owner: int

  def road_points(road) -> int:
      return 0   # roads are worth no victory points on their own
  ```
  The thing to *notice and write down*: the class has no methods at all, and
  `road_points` is a free function that takes a `Road`. That separation is the
  whole point.
- **Ex. 3 (predict).** Anchor your paragraph on one word: **copying**. A search
  that tries 10,000 futures must duplicate the game 10,000 times. If state is
  plain data (ints, lists, dicts) a copy is a fast, shallow data duplication with
  no tangled object graph and no behavior to re-wire. Note that you'll *measure*
  this in Chapter 4 — so make a concrete prediction now (e.g. "copies will be
  cheap because there are no methods or back-references to follow").

There is nothing to run for this chapter. Carry the one-sentence thesis forward —
you will see it justified in every chapter that follows.

---

Previous: [README — index & tools](README.md) | Next: [01 — Workspace and Tools](01-workspace-and-tools.md)
