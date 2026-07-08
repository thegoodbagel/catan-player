# AI-generated
# tests/test_layout.py
#
# Tests for board prep: number_multiset distribution and generate_layout's
# resource/number/port assignment and the no-adjacent-red constraint.

import random
from collections import Counter

import pytest

from engine.board_data import STANDARD_BOARD
from engine.layout import (
    generate_layout,
    number_multiset,
    PIP_WEIGHTS,
    DEFAULT_NO_ADJACENT,
    LayoutError,
    _hex_neighbors,
)
from engine.types import Resource

COORDS = [tuple(h["coord"]) for h in STANDARD_BOARD["hexes"]]
NEIGHBORS = _hex_neighbors(COORDS)


# --- number_multiset -------------------------------------------------------

@pytest.mark.parametrize("count", [0, 1, 5, 18, 30, 100])
def test_multiset_has_exactly_count_tokens(count):
    assert len(number_multiset(count)) == count


def test_multiset_only_legal_tokens():
    tokens = number_multiset(18)
    assert all(t in PIP_WEIGHTS for t in tokens)
    assert 7 not in tokens


def test_multiset_is_weighted_not_uniform():
    # high-weight numbers should appear at least as often as low-weight ones
    counts = Counter(number_multiset(100))
    assert counts[5] >= counts[2]
    assert counts[6] >= counts[12]


# --- generate_layout: resources -------------------------------------------

def test_resources_match_supply():
    layout = generate_layout(STANDARD_BOARD, random.Random(1))
    counts = Counter(layout.hex_resource)
    assert counts[Resource.WOOD] == 4
    assert counts[Resource.BRICK] == 3
    assert counts[Resource.ORE] == 3
    assert counts[None] == 1            # the desert
    assert layout.desert_hex is not None
    assert layout.hex_resource[layout.desert_hex] is None


def test_desert_has_no_number_and_others_do():
    layout = generate_layout(STANDARD_BOARD, random.Random(2))
    assert layout.hex_number[layout.desert_hex] is None
    numbered = [n for n in layout.hex_number if n is not None]
    assert len(numbered) == 18          # 19 hexes minus desert


# --- generate_layout: the red-adjacency constraint -------------------------

@pytest.mark.parametrize("seed", range(25))
def test_no_adjacent_red_numbers(seed):
    layout = generate_layout(STANDARD_BOARD, random.Random(seed))
    for h, num in enumerate(layout.hex_number):
        if num in DEFAULT_NO_ADJACENT:
            for nb in NEIGHBORS[h]:
                assert layout.hex_number[nb] not in DEFAULT_NO_ADJACENT, (
                    f"red {num} at hex {h} touches red at {nb} (seed {seed})"
                )


# --- generate_layout: ports ------------------------------------------------

def test_ports_match_supply_and_positions():
    layout = generate_layout(STANDARD_BOARD, random.Random(3))
    assert len(layout.ports) == 9
    generic = [p for p in layout.ports if p.ratio == 3 and p.resource is None]
    specific = sorted(p.resource.value for p in layout.ports if p.ratio == 2)
    assert len(generic) == 4
    assert specific == ["brick", "ore", "sheep", "wheat", "wood"]
    # every placement sits on a declared position
    declared = {(p["hex"], p["dir"]) for p in STANDARD_BOARD["port_positions"]}
    assert {(p.hex, p.direction) for p in layout.ports} == declared


# --- determinism -----------------------------------------------------------

def test_same_seed_same_layout():
    a = generate_layout(STANDARD_BOARD, random.Random(42))
    b = generate_layout(STANDARD_BOARD, random.Random(42))
    assert a == b


def test_supply_mismatch_raises():
    bad = dict(STANDARD_BOARD)
    bad["hex_resources"] = {"wood": 99}
    with pytest.raises(LayoutError):
        generate_layout(bad, random.Random(0))
