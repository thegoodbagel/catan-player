# Official — CATAN: Traders & Barbarians

Source: official rules hub <https://www.catan.com/understand-catan/game-rules>
(Traders & Barbarians PDF). Content paraphrased for licensing compliance.
Scenario specifics are **UNVERIFIED** until checked against the PDF.

Unlike the other expansions, Traders & Barbarians is a **bundle of independent
mini-scenarios and rule variants** rather than one cohesive system. For an
engine, treat each as its own small rule module + map. It also packages
official **rules for 2-player and 3-player** play and some quality-of-life
variants.

## The scenarios (each is a separate map + rule module)

> Names from the published collection; exact rules **UNVERIFIED**.

- **The Fishermen of Catan** — adds **fish/lake** hexes and **fish tokens**.
  Players catch fish (collected from a "fish shoal"); fish are spent for special
  one-off effects (move the robber, buy a resource, swap a card, gain VP).
  [RULE][STATE] — adds a fish-token economy parallel to resources.
- **The Rivers of Catan** — adds **river** features along edges plus **gold**
  riverbanks; building along the river yields gold but a "poorest player" rule
  redistributes coins. [RULE][STATE].
- **The Caravans** — adds **camel/caravan** movement toward desert oasis goals.
  [RULE][STATE].
- **Barbarian Attack** — a **PvE** scenario: barbarians land and must be
  repelled with knights; settlements can be pillaged. [RULE][STATE].
- **Traders & Barbarians (main)** — a **delivery/commodity transport** scenario:
  move **trade goods** (e.g. coal, wine, marble) along routes to a castle for
  points. [RULE][STATE].
- **The Castle / catapults** and other smaller add-ons. **UNVERIFIED.**

## Packaged rule variants (not maps)

- **Catan for 2 players** — uses a **trade/event card** mechanism to balance
  two-player play. [RULE]
- **Catan for 3 players** (harbormaster, etc.) and **Friendly Robber** /
  **Event Cards instead of dice** variants. The **Event Cards** variant replaces
  the two dice with a deck that guarantees a fixed long-run distribution of
  numbers — relevant to knob 3 (dice scheme). [RULE]
- **Harbormaster** — adds a transferable **+2 VP "Harbor Master"** bonus for
  harbor-adjacent buildings (harbor points). [RULE]

## Knob mapping (across the bundle)

| Knob | What this set touches |
|------|------------------------|
| 2 tile types | fish/lake, river edges, oasis/desert, castle |
| 3 numbers/dice | Event-Cards-instead-of-dice variant |
| 4 resources | trade goods (coal/wine/marble), fish tokens, gold/coins |
| 5 pieces | camels/caravans, catapults, transported goods |
| 6 robber | Friendly Robber variant; barbarian pillaging |
| 7 phases | delivery/transport steps; barbarian resolution |
| 10 victory | Harbor Master +2, delivery points, scenario VPs |
| 12 player count | official 2- and 3-player rule modules |

## Engine notes

- This is the strongest argument for a **plug-in rule-module + per-scenario map**
  architecture: a dozen loosely related mechanics share the base engine but each
  needs its own small module.
- The **Event Cards** dice replacement is a clean, fully-data-driven alternate
  for knob 3 (swap the RNG source).
- The **Harbor Master** and delivery scenarios reinforce "victory = list of
  point sources the scenario contributes."
- Several scenarios add **token economies** (fish, gold/coins, trade goods)
  separate from the 5 base resources — model as additive named inventories.
