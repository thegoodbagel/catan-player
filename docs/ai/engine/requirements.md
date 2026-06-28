# Requirements Document

## Introduction

`catan-engine` is a pure Python rules library for **base Catan**. It encodes the
rules of the game and nothing else: it performs no input, no output, no printing,
no networking, and contains no AI. Every other part of the larger project
(terminal UI, bots, RL training, a network server, and a future C++/pybind11
port) is a *client* of this engine and interacts with it only through a small,
stable front door of three operations: `legal_moves`, `apply`, and
`is_terminal` / `winner`.

These requirements are **derived from the approved design document**
(`design.md`) and are scoped to **v1**, which targets the in-code
`STANDARD_BOARD` constant as its board data source. They reflect the locked
design decisions:

- Topology is addressed by **integer IDs** (hexes, vertices, edges), with an
  immutable `Board` and a mutable, cheaply copyable `State`.
- Moves are **pure data** (Design B): all mutation happens inside `apply`.
- The **move log** is the source of truth for replay; a seedable RNG makes dice,
  shuffles, and steals reproducible.
- Base Catan is implemented as a single **variant bundle** of data + functions;
  the seams for future variants exist but are not implemented.
- Victory points are computed as a **sum of point sources**, never a hardcoded
  check.

The following are explicitly **out of scope for v1** and are noted as future
work where relevant: player-to-player (negotiated) trading, JSON/file-based board
loading, and any non-base variant (Seafarers, Cities & Knights, etc.).

This document is the requirements companion to the design's ten numbered
correctness properties; the requirements are structured so each property can
reference the requirement(s) it validates.

## Glossary

- **Engine**: The `catan-engine` library as a whole; the system under
  specification.
- **Front_Door**: The `Game` surface (`game.py`) that clients import; exposes
  `new`, `legal_moves`, `apply`, `is_terminal`, `winner`, `view`, and `replay`.
- **Rules_Core**: The functional core (`rules.py`) that generates legal moves,
  applies moves, runs the phase machine, and checks victory.
- **Board**: The immutable topology object: hexes, vertices, edges (integer IDs),
  adjacency tables, resources, number tokens, and ports. Never mutated during a
  game.
- **State**: The mutable, copyable game situation, including occupancy arrays,
  per-player tallies, shared decks, bonuses, dice, setup progress, move log, and
  RNG state.
- **Move**: An immutable, hashable, serializable data object describing intent
  only; carries no behavior.
- **Phase**: A state of the turn finite state machine: `SETUP`, `ROLL`,
  `DISCARD`, `ROBBER`, `MAIN`, or `GAME_OVER`.
- **Variant_Bundle**: A named, data-driven ruleset module providing ordered
  phases, per-phase legal-move generators, per-move effects, victory-point
  sources, extra state fields, and tunable counts. `"base"` is the only bundle
  implemented in v1.
- **Player_View**: The filtered observation of a `State` for a single player,
  revealing public facts and that player's own hidden information only.
- **Standard_Board**: The in-code `STANDARD_BOARD` constant: the 19-hex base
  Catan board data (rows 3-4-5-4-3), ports, and bundle name, in the same shape a
  future JSON file would take.
- **Discard_Limit**: The configured hand size above which a player must discard
  on a roll of 7 (7 in base Catan).
- **VP_Target**: The configured number of victory points required to win (10 in
  base Catan).
- **Longest_Road**: The 2-VP bonus awarded for the longest simple path of road
  segments of length at least the configured minimum.
- **Largest_Army**: The 2-VP bonus awarded for playing at least the configured
  minimum number of Knight cards.

## Requirements

### Requirement 1: Front-door legal move enumeration

**User Story:** As a client developer, I want to ask the engine for every move
that is legal in the current state, so that I can offer choices to a UI, bot, or
network client without knowing the rules.

#### Acceptance Criteria

1. WHEN a client calls `legal_moves` with a non-terminal State, THE Rules_Core SHALL return the list of all moves permitted by the current Phase of that State.
2. WHILE a State is not terminal, THE Rules_Core SHALL return a non-empty list of moves from `legal_moves`.
3. WHEN a client calls `legal_moves` with a State, THE Rules_Core SHALL leave that State unchanged.
4. WHEN a client calls `legal_moves`, THE Rules_Core SHALL dispatch move generation using the active Variant_Bundle's generator for the current Phase.

### Requirement 2: Front-door apply with copy path purity

**User Story:** As a search/MCTS developer, I want to apply a move to a state and
receive the next state without mutating my original, so that I can explore many
candidate moves safely.

#### Acceptance Criteria

1. WHEN a client calls `apply` with `in_place=False`, THE Rules_Core SHALL return a new State advanced by exactly the given Move.
2. WHEN a client calls `apply` with `in_place=False`, THE Rules_Core SHALL leave the input State unchanged in its entirety.
3. WHEN `apply` produces the next State, THE Rules_Core SHALL append the applied Move to that State's move log.
4. WHEN `apply` advances a State, THE Rules_Core SHALL set the next Phase to the value returned by the applied Move's effect in the active Variant_Bundle.

### Requirement 3: Front-door apply with in-place fast path

**User Story:** As a real-play client developer, I want a fast in-place apply
path, so that ordinary game progression avoids the cost of copying state.

#### Acceptance Criteria

1. WHEN a client calls `apply` with `in_place=True`, THE Rules_Core SHALL mutate the given State directly and return it as the next State.
2. THE Rules_Core SHALL produce, for any State and Move, a result from `apply(state.copy(), move, in_place=True)` that is equivalent to the result from `apply(state, move, in_place=False)`.

### Requirement 4: Legality closure and illegal move rejection

**User Story:** As a client developer, I want the engine to accept a move if and
only if it is legal, so that no invalid move can ever corrupt game state.

#### Acceptance Criteria

1. WHEN a client calls `apply` with a Move that is a member of `legal_moves` for the State, THE Rules_Core SHALL apply the Move successfully.
2. IF a client calls `apply` with a Move that is not a member of `legal_moves` for the State, THEN THE Rules_Core SHALL raise an `IllegalMove` error and leave the State unchanged.
3. IF a client calls `apply` on a terminal State, THEN THE Rules_Core SHALL raise a `GameOver` error and leave the State unchanged.

### Requirement 5: Terminal detection and winner reporting

**User Story:** As a client developer, I want to know whether the game is over
and who won, so that I can stop play and report the result.

#### Acceptance Criteria

1. WHEN a client calls `is_terminal` with a State whose Phase is `GAME_OVER`, THE Rules_Core SHALL return true.
2. WHEN a client calls `is_terminal` with a State in which a player has reached the VP_Target on that player's own turn, THE Rules_Core SHALL return true.
3. WHEN a client calls `winner` with a State in which the current player's victory points are at least the VP_Target, THE Rules_Core SHALL return that player's identifier.
4. IF no player has reached the VP_Target on their own turn, THEN THE Rules_Core SHALL return no winner from `winner`.

### Requirement 6: Board topology model from the in-code standard board

**User Story:** As an engine developer, I want an immutable board built from the
in-code standard board data, so that spatial rule queries are answered in
constant time and the same state can share one board cheaply.

#### Acceptance Criteria

1. WHEN `load_board` is called for the standard scenario, THE Engine SHALL construct the Board from the in-code `STANDARD_BOARD` constant.
2. THE Board SHALL address every hex, vertex, and edge by a contiguous integer identifier.
3. THE Board SHALL derive vertex and edge identifiers deterministically from hex coordinates at load time.
4. THE Board SHALL expose read-only adjacency queries between hexes, vertices, and edges, and per-hex resource, number token, and port lookups.
5. THE Board SHALL remain immutable for the entire duration of a game after `load_board` completes.
6. WHERE multiple States exist for one game, THE Engine SHALL allow those States to share a single Board by reference without copying topology.

### Requirement 7: Standard board composition and validation

**User Story:** As an engine developer, I want the standard board data validated
against base Catan's structure, so that an inconsistent board is rejected before
play begins.

#### Acceptance Criteria

1. THE Standard_Board SHALL define 19 hexes arranged in rows of 3, 4, 5, 4, and 3 tiles.
2. THE Standard_Board SHALL assign each producing hex exactly one number token in the range 2 to 12 excluding 7, and SHALL assign the desert hex no number token.
3. THE Standard_Board SHALL define the five resource types (wood, brick, sheep, wheat, ore) plus the desert.
4. THE Standard_Board SHALL define 9 ports, comprising generic 3:1 ports and resource-specific 2:1 ports.
5. IF the board data fails a validation rule (number-token assignment, adjacency consistency, port legality, or existence of the named Variant_Bundle), THEN THE Engine SHALL raise an `InvalidScenario` error identifying the failing rule.

### Requirement 8: Mutable, copyable, serializable state model

**User Story:** As a search and networking developer, I want game state that is
cheap to copy and trivial to serialize, so that MCTS rollouts and network
payloads are efficient.

#### Acceptance Criteria

1. THE State SHALL store buildings as occupancy arrays indexed by integer identifier, using -1 to denote an empty location.
2. WHEN `State.copy` is called, THE State SHALL deep-copy its mutable fields and share its Board by reference without copying topology.
3. THE State SHALL hold no rules logic and SHALL act only as a plain data container.
4. THE State SHALL retain a move log as the single source of truth for replay, and SHALL NOT store a history of past States.

### Requirement 9: Pure-data move model

**User Story:** As an engine developer, I want moves to be pure data describing
intent only, so that the same move can be logged, compared, hashed, and replayed
deterministically.

#### Acceptance Criteria

1. THE Move SHALL describe intent as immutable data and SHALL carry no behavior.
2. THE Move SHALL be hashable and comparable so that a move log replays deterministically.
3. WHEN any state change occurs, THE Rules_Core SHALL perform all mutation, and THE Move SHALL mutate nothing.

### Requirement 10: Turn phase state machine

**User Story:** As an engine developer, I want the turn modeled as a data-driven
phase machine, so that play progresses through well-defined phases and variants
can reshape the sequence without rewriting the core.

#### Acceptance Criteria

1. THE Rules_Core SHALL assemble the ordered Phase sequence from the active Variant_Bundle rather than from hardcoded logic.
2. WHEN `legal_moves` is called, THE Rules_Core SHALL select the move generator by the State's current Phase.
3. WHEN `apply` completes a Move's effect, THE Rules_Core SHALL set the State's next Phase to the value returned by that effect.
4. WHEN a player reaches the VP_Target during the end-of-turn check, THE Rules_Core SHALL set the Phase to `GAME_OVER`.

### Requirement 11: Setup snake draft

**User Story:** As a player, I want the initial placement to follow the snake
draft with second-settlement production, so that the game begins per base Catan
rules.

#### Acceptance Criteria

1. WHILE in the SETUP Phase, THE Rules_Core SHALL require each player, in snake-draft order (forward then reverse), to place one settlement followed by one road.
2. WHEN a player places a settlement during setup, THE Rules_Core SHALL offer only vertices that satisfy the distance rule.
3. WHEN a player places a setup road, THE Rules_Core SHALL require that road to attach to the settlement just placed.
4. WHEN a player places the second settlement of the snake draft, THE Rules_Core SHALL grant that player one resource from each adjacent producing hex.
5. WHEN the snake draft completes, THE Rules_Core SHALL transition the State to the ROLL Phase.

### Requirement 12: Dice roll and resource production

**User Story:** As a player, I want rolling the dice to pay out production from
the bank, so that buildings on matching hexes earn resources.

#### Acceptance Criteria

1. WHEN the active player rolls in the ROLL Phase, THE Rules_Core SHALL produce a two-dice result using the State's seedable RNG.
2. WHEN a roll other than 7 occurs, THE Rules_Core SHALL distribute resources from the bank to players for each settlement (one) and city (two) on hexes carrying the rolled number, then transition to the MAIN Phase.
3. WHEN resources are distributed, THE Rules_Core SHALL keep every player's resource counts non-negative and SHALL NOT allow the bank to go negative.
4. WHERE the active player holds a playable dev card, THE Rules_Core SHALL allow at most one dev card to be played before the roll.

### Requirement 13: Robber and discard on a roll of seven

**User Story:** As a player, I want a roll of 7 to trigger discards, robber
movement, and stealing, so that the game enforces base Catan's robber rules.

#### Acceptance Criteria

1. WHEN a 7 is rolled and at least one player holds more cards than the Discard_Limit, THE Rules_Core SHALL transition to the DISCARD Phase.
2. WHILE in the DISCARD Phase, THE Rules_Core SHALL require each over-limit player to discard half of their hand rounded down, and SHALL remain in the DISCARD Phase until every owing player has discarded.
3. WHEN all required discards are complete, or WHEN a 7 is rolled and no player is over the Discard_Limit, THE Rules_Core SHALL transition to the ROBBER Phase.
4. WHEN the active player moves the robber in the ROBBER Phase, THE Rules_Core SHALL place the robber on the chosen hex and then transition to the MAIN Phase.
5. WHEN the robber moves and a steal target is chosen, THE Rules_Core SHALL transfer one random card from the chosen opponent to the active player.
6. IF the chosen steal target holds no cards, THEN THE Rules_Core SHALL resolve the move as no card stolen.

### Requirement 14: Build road

**User Story:** As a player, I want to build roads that connect to my existing
network, so that I can expand toward new settlement locations.

#### Acceptance Criteria

1. WHEN the active player builds a road in the MAIN Phase, THE Rules_Core SHALL require the active player to afford the configured road cost and SHALL deduct that cost to the bank.
2. WHEN listing buildable road edges, THE Rules_Core SHALL offer only unoccupied edges connected to the active player's road network.
3. THE Rules_Core SHALL ensure every road belongs to a path connected to one of its owner's settlements or cities.

### Requirement 15: Build settlement with distance rule

**User Story:** As a player, I want to build settlements only on legal vertices,
so that placement respects the distance rule and connectivity.

#### Acceptance Criteria

1. WHEN the active player builds a settlement in the MAIN Phase, THE Rules_Core SHALL require the active player to afford the configured settlement cost and SHALL deduct that cost to the bank.
2. WHEN listing buildable settlement vertices, THE Rules_Core SHALL offer only unoccupied vertices whose neighboring vertices are all unoccupied.
3. WHEN listing buildable settlement vertices in the MAIN Phase, THE Rules_Core SHALL require the vertex to be incident to one of the active player's roads.
4. THE Rules_Core SHALL ensure no two settlements or cities ever occupy adjacent vertices.

### Requirement 16: Build city

**User Story:** As a player, I want to upgrade a settlement to a city, so that it
produces double resources and counts for more victory points.

#### Acceptance Criteria

1. WHEN the active player builds a city in the MAIN Phase, THE Rules_Core SHALL require the active player to afford the configured city cost and SHALL deduct that cost to the bank.
2. WHEN listing city upgrades, THE Rules_Core SHALL offer only vertices occupied by one of the active player's existing settlements.
3. WHEN a city is built, THE Rules_Core SHALL replace the active player's settlement at that vertex with a city.

### Requirement 17: Development cards

**User Story:** As a player, I want to buy and play development cards, so that I
can gain knights, victory points, and special actions per base Catan.

#### Acceptance Criteria

1. WHEN the active player buys a development card in the MAIN Phase, THE Rules_Core SHALL require the active player to afford the configured cost and SHALL require the development deck to be non-empty.
2. WHEN a development card is bought, THE Rules_Core SHALL make that card unplayable until the player's following turn.
3. WHILE in a single turn, THE Rules_Core SHALL allow the active player to play at most one development card.
4. WHEN the active player plays a Knight, THE Rules_Core SHALL transition to the ROBBER Phase and count the play toward Largest_Army.
5. WHEN the active player plays Road Building, Year of Plenty, or Monopoly, THE Rules_Core SHALL apply that card's effect (two roads, two chosen resources, or claiming all of one resource from all opponents) respectively.
6. THE development deck SHALL be composed according to the active Variant_Bundle's configured dev-deck composition.

### Requirement 18: Bank and port trading

**User Story:** As a player, I want to trade resources with the bank and through
my ports, so that I can convert surplus resources at standard ratios.

#### Acceptance Criteria

1. WHEN the active player performs a bank trade in the MAIN Phase, THE Rules_Core SHALL exchange four identical resources for one resource of the player's choice.
2. WHERE the active player owns a port, THE Rules_Core SHALL offer trades at that port's ratio (3:1 generic or 2:1 specific).
3. THE Rules_Core SHALL NOT define any move that represents a player-to-player negotiated trade in v1.

> **Future work:** Player-to-player (negotiated) trading is out of scope for v1
> and is expected to be added later via a negotiation sub-phase and dedicated
> offer/response move kinds.

### Requirement 19: Longest road bonus

**User Story:** As a player, I want the longest road bonus computed precisely, so
that the 2-VP award reflects the true longest simple path with opponent buildings
breaking continuity.

#### Acceptance Criteria

1. WHEN a player's roads change or a settlement or city is placed, THE Rules_Core SHALL recompute the longest road for all players.
2. WHEN computing longest road, THE Rules_Core SHALL measure the longest simple path over a player's road subgraph, allowing branches and cycles, with no repeated edge or vertex.
3. WHEN computing a player's longest road, THE Rules_Core SHALL treat an opponent's settlement or city on a vertex as breaking path continuity through that vertex.
4. WHEN a player attains the longest simple path of length at least the configured Longest_Road minimum, THE Rules_Core SHALL award that player the 2-VP Longest_Road bonus using standard tie and steal handling.

### Requirement 20: Largest army bonus

**User Story:** As a player, I want the largest army bonus awarded for playing
knights, so that aggressive knight play is rewarded per base Catan.

#### Acceptance Criteria

1. WHEN a player has played at least the configured Largest_Army minimum number of Knights and more than any other player, THE Rules_Core SHALL award that player the 2-VP Largest_Army bonus.
2. WHEN another player surpasses the current holder's played-knight count, THE Rules_Core SHALL transfer the Largest_Army bonus to that player.

### Requirement 21: Victory points as a sum of sources

**User Story:** As an engine developer, I want victory points computed as a sum
of independent point sources, so that scoring is transparent, correct, and
extensible.

#### Acceptance Criteria

1. WHEN `victory_points` is called for a player, THE Rules_Core SHALL return the sum of the active Variant_Bundle's victory-point source contributions (buildings, victory-point cards, Longest_Road, Largest_Army).
2. THE Rules_Core SHALL NOT use a hardcoded victory check in place of summing the configured point sources.
3. WHEN the active player's summed victory points reach the VP_Target on that player's turn, THE Rules_Core SHALL report that player as the winner.

### Requirement 22: Player-view hidden-information filter

**User Story:** As a UI and networking developer, I want a single function that
filters state into one player's legal view, so that hidden information is never
leaked to the wrong player.

#### Acceptance Criteria

1. WHEN `view` is called for a player, THE Front_Door SHALL expose all public facts (board, buildings, robber position, bank counts, bonus holders, and played knights).
2. WHEN `view` is called for a player, THE Front_Door SHALL reveal that player's own exact resources and development cards.
3. WHEN `view` is called for a player, THE Front_Door SHALL reveal only aggregate counts of opponents' resources and development cards, and SHALL NOT reveal opponents' hidden victory-point cards or card identities.
4. WHERE two States differ only in another player's hidden cards, THE Front_Door SHALL produce identical views for the requesting player.
5. WHEN `view` is called for a player who is not the current player, THE Front_Door SHALL provide an empty legal-move list.

### Requirement 23: Move-log replay and reproducibility

**User Story:** As a developer, I want to replay a game from its seed and move
log, so that I can save, load, and synchronize games exactly.

#### Acceptance Criteria

1. WHEN `replay` is called with a scenario, player count, seed, and move log, THE Front_Door SHALL reproduce the exact State that the original sequence of moves produced.
2. THE State SHALL carry an explicit seedable RNG state so that dice rolls, deck shuffles, and steals are reproducible.
3. IF a logged move is not legal at its point during replay, THEN THE Front_Door SHALL raise a `ReplayError` identifying the move index.

### Requirement 24: Variant bundle extensibility and tunable configuration

**User Story:** As an engine developer, I want base Catan implemented as a
data-driven variant bundle with tunable counts, so that future variants extend
the engine without forking the core.

#### Acceptance Criteria

1. THE Rules_Core SHALL obtain its phases, per-phase move generators, per-move effects, victory-point sources, and extra state fields from the active Variant_Bundle.
2. THE Rules_Core SHALL read tunable counts (VP_Target, dev-deck composition, piece limits, Discard_Limit, Longest_Road minimum, Largest_Army minimum, and build costs) from the active Variant_Bundle rather than from module-level constants.
3. THE Engine SHALL implement only the `"base"` Variant_Bundle in v1 while preserving the seams for registering additional bundles.

### Requirement 25: Purity and absence of I/O

**User Story:** As a client developer, I want the engine to perform no I/O, so
that it can back any UI, server, or port without side effects.

#### Acceptance Criteria

1. THE Engine SHALL perform no printing, input, file I/O, or networking within its rules logic.
2. THE Engine SHALL depend only on the Python standard library for its core.
3. THE Rules_Core nouns (Board, State, Move) SHALL NOT import the rules verbs.

### Requirement 26: Determinism and property-based testability

**User Story:** As a test author, I want deterministic, reproducible behavior and
testable invariants, so that I can verify correctness with property-based tests.

#### Acceptance Criteria

1. WHERE a State is constructed with a given seed, THE Engine SHALL produce identical play outcomes across runs for identical move sequences.
2. THE Engine SHALL expose the three front-door operations in a form that supports random legal playthroughs for property-based testing.
3. WHILE a random legal playthrough proceeds, THE Engine SHALL preserve all stated invariants (resource non-negativity, distance rule, road connectivity) at every step and SHALL terminate every game.
