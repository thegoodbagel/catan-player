# AI-generated
# tests/test_board_adjacency.py
#
# Tests that load_board derives a consistent set of geometry tables from the
# standard scenario: correct counts, tables that agree with each other, and
# port positions that resolve to real vertices.

import copy

import pytest

from engine.board import load_board, InvalidScenario
from engine.board_data import STANDARD_BOARD


BOARD = load_board("standard")


# --- counts ---------------------------------------------------------------

def test_standard_board_counts():
    assert BOARD.num_hexes() == 19
    assert BOARD.num_vertices() == 54
    assert BOARD.num_edges() == 72


# --- tables agree with each other -----------------------------------------

def test_hex_and_vertex_tables_agree():
    # if a hex lists a vertex as one of its corners, that vertex must list the hex
    for h in range(BOARD.num_hexes()):
        for v in BOARD.hex_vertices(h):
            assert h in BOARD.vertex_hexes(v)


def test_hex_edges_endpoints_are_hex_corners():
    for h in range(BOARD.num_hexes()):
        corners = set(BOARD.hex_vertices(h))
        for e in BOARD.hex_edges(h):
            a, b = BOARD.edge_vertices(e)
            assert a in corners and b in corners


def test_vertex_adjacency_is_symmetric():
    for v in range(BOARD.num_vertices()):
        for u in BOARD.vertex_neighbors(v):
            assert v in BOARD.vertex_neighbors(u)


# --- shape sanity ----------------------------------------------------------

def test_every_vertex_touches_one_to_three_hexes():
    for v in range(BOARD.num_vertices()):
        assert 1 <= len(BOARD.vertex_hexes(v)) <= 3


def test_every_vertex_has_two_or_three_neighbors():
    for v in range(BOARD.num_vertices()):
        assert 2 <= len(BOARD.vertex_neighbors(v)) <= 3


def test_center_hex_has_six_neighbors():
    # the hex at (0, 2) is the board centre; it should be fully surrounded
    center = BOARD.coords.index((0, 2))
    assert len(BOARD.hex_neighbors(center)) == 6


# --- ports -----------------------------------------------------------------

def test_ports_resolve_to_two_distinct_vertices_of_their_hex():
    for p in STANDARD_BOARD["port_positions"]:
        v1, v2 = BOARD.port_vertices(p["hex"], p["dir"])
        assert v1 != v2
        corners = set(BOARD.hex_vertices(p["hex"]))
        assert v1 in corners and v2 in corners


# --- validation ------------------------------------------------------------

def test_bad_resource_supply_is_rejected():
    bad = copy.deepcopy(STANDARD_BOARD)
    bad["hex_resources"]["wood"] += 1      # supply no longer matches hex count
    with pytest.raises(InvalidScenario):
        load_board(bad)
