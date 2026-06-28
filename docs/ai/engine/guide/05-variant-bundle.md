# Chapter 5 — The Rulebook as Data: The Variant Bundle

> ## At a glance
> - **Where you are:** You have an immutable `Board` (Chapter 3) and a cheap-copy `State` (Chapter 4). You can represent a game situation but the engine knows no rules yet.
> - **This chapter's goal:** Gather everything that defines "base Catan" — its phases, tunable numbers, and the function slots for rules — into one named data **bundle** the engine reads, so the engine itself contains no game-specific rules.
> - **What this chapter is NOT:** This is not where you write the actual rules. You build the bundle's *shape* and registry and register a `BASE` bundle whose rule functions are **placeholders**. The real logic arrives in Chapters 6–8. After this chapter the module imports but the rule slots are stubs — that is correct.
> - **By the end you will have:** `src/engine/rules.py` begun: the `VariantBundle` dataclass, the `VARIANTS` registry, `register_variant`, `active_bundle`, and a registered `BASE` bundle with standard config and stubbed function slots.
> - **Maps to:** Task 5 in `.kiro/specs/catan-engine/tasks.md`.
> - **Prerequisites:** Chapters 0 (expression problem), 2 (moves/enums), 4 (state).

**Goal in plain language.** Make the engine a referee that holds no rulebook of
its own — and put "the rules of base Catan" into a separate data package the
referee reads.

---

## The referee analogy

Picture a referee who knows how to *run a turn-based game in general* but holds no
specific rulebook. Hand them the Catan rulebook and they can run Catan; hand them
a different one and they run that. We make the engine that referee, and we make
each game a **rulebook** — which we name a *variant bundle*. (Our coinage; the
standard term is a "ruleset module." Either way it is *the bundle of rules for one
version of the game*.)

## What a bundle contains

```python
from typing import Callable

@dataclass(frozen=True)
class VariantBundle:
    name: str
    phases: tuple                        # which turn phases exist
    generators: dict                     # phase -> function listing legal moves
    effects: dict                        # move type -> function carrying it out
    vp_sources: tuple                    # functions that each contribute points
    # --- tunable configuration, not magic numbers buried in code ---
    vp_target: int                       # points to win (10)
    build_costs: dict                    # move type -> required resources
    piece_limits: dict                   # {"road": 15, "settlement": 5, "city": 4}
```

## Dispatch by dictionary

The engine never says "if base Catan, do X." It looks up the answer in the
bundle. This **dispatch table** pattern — using a dictionary to choose behavior —
is the workhorse of the whole engine:

```python
VARIANTS: dict[str, VariantBundle] = {}

def register_variant(b: VariantBundle):
    VARIANTS[b.name] = b

def active_bundle(state) -> VariantBundle:
    return VARIANTS[state.variant]       # find the rulebook by name
```

Registering base Catan fills the slots with standard values and points at the
functions you implement in the next chapters:

```python
BASE = VariantBundle(
    name="base",
    phases=(Phase.SETUP, Phase.ROLL, Phase.DISCARD, Phase.ROBBER, Phase.MAIN),
    generators={Phase.MAIN: gen_main_moves, ...},   # filled in Chapter 6
    effects={BuildRoad: eff_build_road, ...},        # filled in Chapter 7
    vp_sources=(vp_from_buildings, vp_from_longest_road, ...),  # Chapter 8
    vp_target=10,
    build_costs={
        BuildRoad: {Resource.WOOD: 1, Resource.BRICK: 1},
        BuildSettlement: {Resource.WOOD: 1, Resource.BRICK: 1,
                          Resource.SHEEP: 1, Resource.WHEAT: 1},
    },
    piece_limits={"road": 15, "settlement": 5, "city": 4},
)
register_variant(BASE)
```

## Why this is the extensibility core

Two payoffs. First, every tunable number lives in one place, so a rules tweak
changes data, not logic. Second — recall the expression problem from Chapter 0 — a
new game variant becomes a *new bundle you register*, not a fork of the engine.
The dispatch dictionary is exactly the "buy back" that makes adding new types
cheap again. The engine never learns the word "Catan."

> **Margin notes**
> - **Dispatch table**: a dictionary mapping a key (a phase, a move type) to the
>   function that handles it. An alternative to long `if/elif` chains.
> - **Registry**: a dictionary you register things into and look them up by name.
> - **Configuration**: tunable values kept separate from logic.

## Exercises

1. **Build the registry.** Implement `VariantBundle`, `VARIANTS`,
   `register_variant`, and `active_bundle`. Register a stub `BASE` whose function
   slots point at empty placeholders so the module imports.
2. **Dispatch vs. if/elif.** Rewrite this chain as a dispatch dictionary and
   explain which is easier to extend:
   ```python
   def cost(move):
       if isinstance(move, BuildRoad): return {...}
       elif isinstance(move, BuildSettlement): return {...}
   ```
3. **Override config.** Construct a second bundle `"speed"` identical to base but
   with `vp_target=5`. Without writing any rules, argue why a game using it would
   end sooner. Which lines of engine logic did you change? (Answer: none.)

### Hints / how to start

**Where the code goes.** Everything lands in `src/engine/rules.py` (this is the
first chapter that touches it). Tests, if you write them, go in
`tests/test_rules_registry.py`.

- **Ex. 1 (build the registry).** The trick that lets the module *import* before
  any real rule exists: define no-op placeholder functions and point the slots at
  them. Sketch:
  ```python
  # src/engine/rules.py
  from dataclasses import dataclass
  from engine.types import Phase, Resource
  from engine.moves import BuildRoad, BuildSettlement

  def _todo(*args, **kwargs):
      raise NotImplementedError("filled in a later chapter")

  VARIANTS = {}
  def register_variant(b): VARIANTS[b.name] = b
  def active_bundle(state): return VARIANTS[state.variant]

  BASE = VariantBundle(
      name="base",
      phases=(Phase.SETUP, Phase.ROLL, Phase.DISCARD, Phase.ROBBER, Phase.MAIN),
      generators={Phase.MAIN: _todo},     # real generators arrive in Chapter 6
      effects={BuildRoad: _todo},          # real effects arrive in Chapter 7
      vp_sources=(_todo,),                 # real sources arrive in Chapter 8
      vp_target=10,
      build_costs={BuildRoad: {Resource.WOOD: 1, Resource.BRICK: 1}},
      piece_limits={"road": 15, "settlement": 5, "city": 4},
  )
  register_variant(BASE)
  ```
  A passing test just imports `rules` and asserts `active_bundle` finds `BASE` by
  name — proving the registry wiring works without any rule logic.
- **Ex. 2 (dispatch vs if/elif).** Replace the chain with a dict keyed by the move
  *type*:
  ```python
  COSTS = {
      BuildRoad: {Resource.WOOD: 1, Resource.BRICK: 1},
      BuildSettlement: {Resource.WOOD: 1, Resource.BRICK: 1,
                        Resource.SHEEP: 1, Resource.WHEAT: 1},
  }
  def cost(move):
      return COSTS[type(move)]
  ```
  Write one sentence: the dict version is easier to extend because adding a move
  kind is adding one entry, with no growing `if/elif` to edit — and it's the same
  shape as `build_costs` inside the bundle.
- **Ex. 3 (override config).** Build a second bundle by copying `BASE` and
  changing only one field (`dataclasses.replace(BASE, name="speed", vp_target=5)`,
  then `register_variant` it). The argument to write: a game ends when a player
  reaches `vp_target`, so lowering it to 5 ends sooner — and you changed *zero*
  lines of engine logic, only data. That is the whole thesis of the chapter in one
  exercise.

---

Previous: [04 — The Game State and Cheap Copying](04-state.md) | Next: [06 — Operation One: "What Can I Do Now?"](06-legal-moves.md)
