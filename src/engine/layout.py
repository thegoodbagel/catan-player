# AI-generated
# src/engine/layout.py
#
# Board prep: turn a static scenario (board_data) into a per-game, immutable
# Layout — the concrete assignment of a resource and number to each hex and a
# trade ratio to each port. This is the random part of setup; once produced the
# Layout never changes, so it belongs with the immutable board, not State.
#
# Design notes:
#  - Numbers are NOT laid along a fixed spiral. The spiral exists in the physical
#    game only to keep the high-probability "red" numbers (6, 8) off adjacent
#    hexes; we enforce that constraint directly, which generalises to any board.
#  - This module needs only hex-to-hex adjacency, which is pure coordinate math
#    (HEX_DIRECTION_OFFSETS). It does NOT depend on the vertex/edge derivation in
#    board.py, so it is fully self-contained and testable on its own.

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from engine.types import Resource, Direction, HEX_DIRECTION_OFFSETS

# Tokens are the dice outcomes minus 7. Default weights are the number of ways to
# roll each value (its pip count), so the produced multiset mirrors the real
# probability spread for any board size.
PIP_WEIGHTS = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}

# Numbers that may not sit on adjacent hexes (the high-probability "red" tokens).
DEFAULT_NO_ADJACENT = frozenset({6, 8})


class LayoutError(Exception):
    """Raised when a constraint-satisfying layout cannot be produced."""


@dataclass(frozen=True)
class PortPlacement:
    hex: int
    direction: Direction
    ratio: int                       # e.g. 3 for 3:1, 2 for 2:1
    resource: Optional[Resource]     # None == generic (any-resource) harbour


@dataclass(frozen=True)
class Layout:
    hex_resource: tuple[Optional[Resource], ...]   # per hex id; None == desert/sea
    hex_number: tuple[Optional[int], ...]           # per hex id; None == no token
    desert_hex: Optional[int]
    ports: tuple[PortPlacement, ...]


# --------------------------------------------------------------------------
# Number tokens
# --------------------------------------------------------------------------

def number_multiset(count: int, weights: dict[int, int] = PIP_WEIGHTS) -> list[int]:
    """Return `count` number tokens spread across the weighted values.

    Uses largest-remainder rounding so the counts are proportional to `weights`
    and sum to exactly `count`. Deterministic (no shuffling here)."""
    if count < 0:
        raise ValueError("count must be non-negative")
    numbers = list(weights)
    total = sum(weights.values())
    ideal = {n: weights[n] / total * count for n in numbers}
    floors = {n: int(ideal[n]) for n in numbers}
    remainder = count - sum(floors.values())
    # hand out the leftover tokens to the largest fractional parts
    by_frac = sorted(numbers, key=lambda n: ideal[n] - floors[n], reverse=True)
    for n in by_frac[:remainder]:
        floors[n] += 1
    out: list[int] = []
    for n in numbers:
        out.extend([n] * floors[n])
    return out


def _place_numbers(
    hexes: list[int],
    neighbors: dict[int, list[int]],
    tokens: list[int],
    rng: random.Random,
    no_adjacent: frozenset[int],
    max_attempts: int = 2000,
) -> dict[int, int]:
    """Assign `tokens` to `hexes` so no two `no_adjacent` values are neighbours.

    Randomised greedy with restart: shuffle hexes and tokens, place one token per
    hex skipping any choice that would put a forbidden value next to one already
    placed. Restart on a dead end."""
    if len(tokens) != len(hexes):
        raise LayoutError(f"{len(tokens)} tokens for {len(hexes)} hexes")

    for _ in range(max_attempts):
        order = hexes[:]
        rng.shuffle(order)
        bag = tokens[:]
        rng.shuffle(bag)
        assigned: dict[int, int] = {}
        stuck = False
        for h in order:
            pick = None
            for i, tok in enumerate(bag):
                if tok in no_adjacent and any(
                    assigned.get(n) in no_adjacent for n in neighbors[h]
                ):
                    continue
                pick = i
                break
            if pick is None:
                stuck = True
                break
            assigned[h] = bag.pop(pick)
        if not stuck:
            return assigned
    raise LayoutError(
        "could not place number tokens without adjacent high-probability numbers"
    )


# --------------------------------------------------------------------------
# Hex adjacency (pure coordinate math)
# --------------------------------------------------------------------------

def _hex_neighbors(coords: list[tuple[int, int]]) -> dict[int, list[int]]:
    """Map each hex id to the ids of its on-board neighbours."""
    index = {c: i for i, c in enumerate(coords)}
    neighbors: dict[int, list[int]] = {}
    for i, (q, r) in enumerate(coords):
        adj = []
        for dq, dr in HEX_DIRECTION_OFFSETS:
            nb = index.get((q + dq, r + dr))
            if nb is not None:
                adj.append(nb)
        neighbors[i] = adj
    return neighbors


# --------------------------------------------------------------------------
# Top-level board prep
# --------------------------------------------------------------------------

def _resource(name: Optional[str]) -> Optional[Resource]:
    if name is None or name == "desert":
        return None
    return Resource(name)


def generate_layout(scenario: dict, rng: Optional[random.Random] = None) -> Layout:
    """Produce a random, immutable Layout for a scenario (board prep)."""
    rng = rng or random.Random()
    hexes = scenario["hexes"]
    coords = [tuple(h["coord"]) for h in hexes]
    is_land = [h.get("type", "land") == "land" for h in hexes]

    # 1. Resources: expand the supply bag and shuffle it onto the land hexes.
    supply: list[Optional[Resource]] = []
    for name, n in scenario["hex_resources"].items():
        supply.extend([_resource(name)] * n)   # _resource("desert") -> None
    land_ids = [i for i, land in enumerate(is_land) if land]
    if len(supply) != len(land_ids):
        raise LayoutError(
            f"resource supply ({len(supply)}) != land hex count ({len(land_ids)})"
        )
    rng.shuffle(supply)

    hex_resource: list[Optional[Resource]] = [None] * len(hexes)
    desert_hex: Optional[int] = None
    for hid, res in zip(land_ids, supply):
        hex_resource[hid] = res
        if res is None:               # the desert (a land hex with no resource)
            desert_hex = hid

    # 2. Numbers: every land hex that produces (i.e. not the desert) gets a token.
    numbered = [i for i in land_ids if hex_resource[i] is not None]
    tokens = number_multiset(len(numbered))
    neighbors = _hex_neighbors(coords)
    placement = _place_numbers(numbered, neighbors, tokens, rng, DEFAULT_NO_ADJACENT)
    hex_number: list[Optional[int]] = [None] * len(hexes)
    for hid, num in placement.items():
        hex_number[hid] = num

    # 3. Ports: deal the shuffled port supply onto the fixed positions.
    positions = scenario["port_positions"]
    pool = list(scenario["port_supply"])
    if len(pool) != len(positions):
        raise LayoutError(
            f"port supply ({len(pool)}) != port positions ({len(positions)})"
        )
    rng.shuffle(pool)
    ports = tuple(
        PortPlacement(
            hex=pos["hex"],
            direction=pos["dir"],
            ratio=tok["ratio"],
            resource=_resource(tok["resource"]),
        )
        for pos, tok in zip(positions, pool)
    )

    return Layout(
        hex_resource=tuple(hex_resource),
        hex_number=tuple(hex_number),
        desert_hex=desert_hex,
        ports=ports,
    )
