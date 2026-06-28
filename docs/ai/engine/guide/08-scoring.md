# Chapter 8 — Scoring, and the One Hard Algorithm

> ## At a glance
> - **Where you are:** Moves now change the game via `apply` (Chapter 7). You can play a full game, but nothing computes who is winning.
> - **This chapter's goal:** Compute victory points as a sum of independent sources, decide the winner, and implement the two bonuses — including longest road, the only genuinely hard algorithm in the project.
> - **What this chapter is NOT:** This is not the public interface (Chapter 9). You're filling in the bundle's `vp_sources` and the bonus logic in `rules.py`. There is no hardcoded `if score >= 10` anywhere — the winner check just sums the sources.
> - **By the end you will have:** `victory_points`, `winner`, `is_terminal`, the source functions (`vp_from_buildings`, `vp_from_vp_cards`, `vp_from_longest_road`, `vp_from_largest_army`), and `longest_road_length` / `recompute_longest_road`, all in `rules.py`.
> - **Maps to:** Task 9 in `.kiro/specs/catan-engine/tasks.md`.
> - **Prerequisites:** Chapters 3 (edge↔vertex tables — the DFS walks them), 5 (vp_sources slot), 7 (effects that trigger recompute).

**Goal in plain language.** Add up each player's points from independent sources,
declare a winner at the target, and correctly measure the *longest simple path* of
each player's roads — the one place a naive implementation goes wrong.

---

## Victory as a sum of independent sources

A player's score is a sum of small contributions, each its own function:

```python
def victory_points(state, p) -> int:
    return sum(source(state, p) for source in active_bundle(state).vp_sources)

def vp_from_buildings(state, p) -> int:
    s = sum(1 for owner in state.settlements if owner == p)
    c = sum(2 for owner in state.cities if owner == p)
    return s + c

def vp_from_longest_road(state, p) -> int:
    return 2 if state.longest_road_holder == p else 0
```

There is no hidden `if score >= 10` anywhere; the winner check simply calls
`victory_points`. Adding a new scoring rule later means appending one function to
`vp_sources`. This is the data-oriented payoff again: new operations are cheap.

## Longest road: state the problem precisely

This is where careless implementations go wrong, so we are exact:

- A player's roads form a network that can **branch** and contain **cycles**. It
  is *not* a chain or a tree.
- "Longest road" is the **longest simple path**: the longest route through your
  roads that repeats no edge and no vertex.
- **An opponent's settlement or city on a vertex breaks the path through that
  vertex.** You may end a path there but not pass through. Your own building never
  breaks your path.

Finding the longest simple path in a general graph is, in the worst case, a hard
problem (it is NP-hard — no known fast general solution). The reprieve is **scale**:
a player has at most 15 roads, so exhaustively exploring every path is instant.
The risk here is never speed — it is *modeling it wrong* as a simple traversal.

## The algorithm: exhaustive depth-first search

We try every path by depth-first search — follow a path as far as it goes, then
back up and try another branch — the same shape as classic maze/graph problems:

```python
def longest_road_length(state, p) -> int:
    board = state.board
    own = [e for e in range(board.num_edges()) if state.roads[e] == p]

    def dfs(edge, visited_edges, came_from_vertex) -> int:
        best = len(visited_edges)
        for v in board.edge_vertices(edge):
            if v == came_from_vertex:
                continue                           # don't walk back the way we came
            if occupied_by_opponent(state, v, p):
                continue                           # an enemy building cuts the path
            for nxt in board.vertex_edges(v):
                if state.roads[nxt] == p and nxt not in visited_edges:
                    best = max(best, dfs(nxt, visited_edges | {nxt}, v))
        return best

    return max((dfs(e, {e}, None) for e in own), default=0)
```

We recompute it whenever roads change *or* a settlement/city is placed (because an
opponent's building can shorten someone's road), then award the 2-point bonus to
the leader at length ≥ 5, with standard tie handling.

## Largest army

By contrast, largest army is easy: track played knights, award +2 to the player
with the most once they reach three, transfer it when someone overtakes them.

> **Margin notes**
> - **Longest simple path**: longest route repeating no vertex or edge.
> - **NP-hard**: a class of problems with no known efficient general solution;
>   acceptable here only because our graphs are tiny.
> - **Depth-first search (DFS)**: explore as deep as possible, then backtrack.
> - **Backtracking**: undoing the last step to try an alternative (here, the
>   `visited_edges | {nxt}` set passed down each branch).

## Exercises

1. **Scoring.** Implement `victory_points`, `vp_from_buildings`,
   `vp_from_vp_cards`, `winner`, and `is_terminal`. Test a constructed state with a
   known score.
2. **Longest road — the four cases.** This is the most important test in the
   chapter. On hand-built road networks, verify the length is correct for: (a) a
   straight chain, (b) a branch (the longest arm wins), (c) a loop, and (d) a chain
   **cut** by an opponent's settlement in the middle. Case (d) is the one that
   catches naive implementations.
3. **Recompute triggers.** Explain why placing a *settlement* (not just a road)
   must trigger `recompute_longest_road`. Construct the state that proves it.
4. **Largest army.** Implement the holder logic and test that it transfers when a
   second player overtakes the first.

### Hints / how to start

**Where the code goes.** All of it lands in `src/engine/rules.py`. Append the new
source functions to the `BASE` bundle's `vp_sources` tuple. Tests go in
`tests/test_victory.py`.

- **Ex. 1 (scoring).** These are short sums. Write `vp_from_vp_cards` as the count
  of victory-point dev cards the player holds. `winner` returns the current player
  iff their summed `victory_points` ≥ `active_bundle(s).vp_target`; `is_terminal`
  is `s.phase == Phase.GAME_OVER or winner(s) is not None`. A passing test builds a
  state with, say, 2 settlements + 1 city = 4 VP and asserts `victory_points` == 4.

#### Ex. 2 — longest road, the careful scaffold (budget extra time here)

This is the hardest exercise in the whole guide. Work it in this order.

**How to structure the DFS.** A "longest simple path" search tries every path and
keeps the best. The recursion carries three things:
1. the **current edge** you're standing on,
2. the **set of edges already visited** on this path (so you never reuse one),
3. the **vertex you arrived from**, so you don't immediately walk back.

From the current edge, look at its *two* endpoint vertices. For each endpoint
(except the one you came from), look at every edge touching that vertex; if it's
*your* road and not yet visited, recurse into it with that edge added to the
visited set. The best length is the largest visited-set size you reach. Start the
search from *every* one of your edges, because the longest path may not begin at
the one you happen to pick first.

**How to represent "visited."** Use a Python `set` of edge IDs, and pass a *new*
set down each branch with `visited | {next_edge}` — never mutate one shared set.
Passing a fresh set is what makes backtracking automatic: when a branch returns,
the caller's set is unchanged, so a sibling branch explores cleanly. (You can also
track visited *vertices* if you prefer; tracking edges is enough to forbid reusing
a road, and the "came_from_vertex" guard prevents the immediate U-turn.)

**How to encode "an opponent's building cuts the path."** Before you continue
*through* a vertex `v`, check whether an opponent owns a settlement or city there:
```python
def occupied_by_opponent(state, v, p) -> bool:
    owner_s = state.settlements[v]
    owner_c = state.cities[v]
    return (owner_s != -1 and owner_s != p) or (owner_c != -1 and owner_c != p)
```
If it returns `True`, you `continue` — you do **not** expand neighbors through `v`.
The subtle point: a path may *end* at such a vertex (the edge leading into it still
counts), but it may not *pass through* it to the edges on the far side. Your own
building never blocks you, which is why the check compares against `p`.

**The four test cases — describe and build each one explicitly.** Build each road
network by hand by setting `state.roads[edge] = p` for the right edges on the
standard board (read edge IDs from your Chapter 3 tables). What each must assert:

- **(a) Chain.** Lay N roads end-to-end in a single line, no forks. Expected
  length = N. This is the sanity case; if a straight chain is wrong, stop and fix
  the basic recursion before anything else.
- **(b) Branch.** A trunk that forks into two arms of *different* lengths (e.g. a
  shared start, then a 3-edge arm and a 2-edge arm). Expected length = the longest
  *single* simple path through the network (trunk + the longer arm), **not** the
  total number of edges. This case catches implementations that wrongly *sum* all
  roads instead of finding one path.
- **(c) Loop.** Roads forming a cycle (e.g. a hexagon of 6 edges). Expected length
  = the number of edges in the loop (you can traverse all of them without
  repeating an edge). This catches implementations that loop forever or that
  miscount because they assumed a tree.
- **(d) Opponent-cut.** Take your straight chain from (a) and place an *opponent's*
  settlement on a vertex in the **middle** of it. Expected length = the longer of
  the two segments on either side of the cut, **not** the full chain. This is the
  case naive code gets wrong — it's the entire reason `occupied_by_opponent` exists.
  Build it by setting `state.settlements[middle_vertex] = other_player`.

Skeleton for one test so you have a starting shape:
```python
def test_longest_road_straight_chain():
    s = make_empty_state()
    chain_edges = [e0, e1, e2, e3]          # adjacent edges in a line (from board tables)
    for e in chain_edges:
        s.roads[e] = 0
    assert longest_road_length(s, 0) == len(chain_edges)
```

- **Ex. 3 (recompute triggers).** The explanation to write: longest road depends
  not just on *your* roads but on *opponents' buildings*, because an opponent's new
  settlement can cut your path (case d). So placing a settlement must call
  `recompute_longest_road`, not only placing a road. Prove it: build a state where
  player 0 holds a length-5 chain and the bonus; place an opponent settlement in
  the middle; assert player 0's recomputed length drops below 5 and the bonus moves
  or vanishes. (This is why `eff_build_settlement` in Chapter 7 calls
  `recompute_longest_road`.)
- **Ex. 4 (largest army).** Track each player's played-knight count. Award +2 to
  the player with the most once they reach the configured minimum (3); transfer it
  the moment another player *strictly* exceeds the current holder. A passing test:
  player 0 reaches 3 knights → holds the bonus; player 1 reaches 4 → bonus
  transfers to player 1.

## Run your tests

```bash
python3 -m pytest
```

You just added `tests/test_victory.py`. The four longest-road cases (Ex. 2) are
the ones to get green — especially **(d) opponent-cut**. If only (d) fails, your
DFS is otherwise fine and the bug is in `occupied_by_opponent` / the
"don't pass through" guard.

---

Previous: [07 — Operation Two: Making It Happen](07-apply.md) | Next: [09 — The Front Door, Privacy, and Replay](09-front-door.md)
