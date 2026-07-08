# AI-generated
# tests/test_board_data.py
#
# Format checks for the static STANDARD_BOARD scenario. These validate the data
# itself (shape, counts, internal agreement) and do NOT depend on load_board, so
# they pass before the board derivation exists.

from collections import Counter

import pytest

from engine.board_data import STANDARD_BOARD
from engine.types import Direction, HEX_DIRECTION_OFFSETS

BOARD = STANDARD_BOARD
HEXES = BOARD["hexes"]
COORDS = [tuple(h["coord"]) for h in HEXES]
COORDSET = set(COORDS)


def neighbor(coord, direction):
    q, r = coord
    dq, dr = HEX_DIRECTION_OFFSETS[direction]
    return (q + dq, r + dr)


# --- hexes -----------------------------------------------------------------

def test_nineteen_unique_hexes():
    assert len(HEXES) == 19
    assert len(COORDSET) == 19, "duplicate hex coordinates"


def test_rows_are_3_4_5_4_3():
    rows = Counter(r for _, r in COORDS)
    sizes = [rows[r] for r in sorted(rows)]
    assert sizes == [3, 4, 5, 4, 3]


def test_top_left_hex_is_origin():
    assert COORDS[0] == (0, 0)


def test_offsets_indexable_by_direction():
    assert len(HEX_DIRECTION_OFFSETS) == len(Direction) == 6


# --- terrain supply --------------------------------------------------------

def test_resource_supply_fills_every_hex():
    supply = BOARD["hex_resources"]
    assert sum(supply.values()) == len(HEXES)
    assert supply["desert"] == 1


# --- number tokens ---------------------------------------------------------

def test_number_count_matches_non_desert_hexes():
    desert = BOARD["hex_resources"]["desert"]
    assert len(BOARD["hex_numbers"]) == len(HEXES) - desert


def test_numbers_are_legal_tokens():
    assert all(2 <= n <= 12 and n != 7 for n in BOARD["hex_numbers"])


def test_number_multiset_matches_standard_distribution():
    expected = Counter(
        {2: 1, 3: 2, 4: 2, 5: 2, 6: 2, 8: 2, 9: 2, 10: 2, 11: 2, 12: 1}
    )
    assert Counter(BOARD["hex_numbers"]) == expected


# --- token spiral ----------------------------------------------------------
# The token order is no longer stored in the scenario: numbers are placed at
# setup by layout.generate_layout under a no-adjacent-red constraint. Those
# properties are covered in tests/test_layout.py, so there is nothing static to
# check here.


# --- ports -----------------------------------------------------------------

def test_port_positions_are_distinct_coastal_edges():
    seen = set()
    for port in BOARD["port_positions"]:
        h, d = port["hex"], port["dir"]
        assert 0 <= h < len(HEXES)
        assert isinstance(d, Direction)
        nb = neighbor(COORDS[h], d)
        assert nb not in COORDSET, f"port on hex {h} {d.name} faces land {nb}"
        edge = frozenset({COORDS[h], nb})
        assert edge not in seen, f"duplicate port edge at hex {h}"
        seen.add(edge)


def test_one_supply_token_per_port_position():
    assert len(BOARD["port_supply"]) == len(BOARD["port_positions"]) == 9


def test_port_supply_is_standard_mix():
    supply = BOARD["port_supply"]
    generic = [p for p in supply if p["ratio"] == 3 and p["resource"] is None]
    specific = sorted(p["resource"] for p in supply if p["ratio"] == 2)
    assert len(generic) == 4
    assert specific == ["brick", "ore", "sheep", "wheat", "wood"]
