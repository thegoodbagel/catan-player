# AI-generated
# tests/test_victory.py
#
# Chapter 8: victory as a sum of independent sources, the winner check, longest
# road (the four careful cases), and largest army.

from _helpers import fake_state, play_random

from engine.game import Game
from engine import rules
from engine.types import EMPTY, DevCard


# --- victory points as a sum of sources -----------------------------------

def test_victory_points_sum_buildings_and_cards():
    s = Game.new("standard", 4, seed=0)
    # hand-place 2 settlements and 1 city for player 0, plus a VP dev card
    s.settlements[0] = 0
    s.settlements[1] = 0
    s.cities[2] = 0
    s.dev_cards[0] = {DevCard.VICTORY_POINT: 1}
    # 2 settlements (2) + 1 city (2) + 1 VP card (1) = 5
    assert rules.vp_from_buildings(s, 0) == 4
    assert rules.vp_from_vp_cards(s, 0) == 1
    assert rules.victory_points(s, 0) == 5


def test_victory_points_equals_sum_of_bundle_sources():
    s = Game.new("standard", 4, seed=1)
    s.settlements[5] = 2
    s.cities[7] = 2
    total = sum(src(s, 2) for src in rules.active_bundle(s).vp_sources)
    assert rules.victory_points(s, 2) == total


def test_winner_and_terminal_at_target():
    s = Game.new("standard", 4, seed=0)
    s.current_player = 1
    # give player 1 five cities => 10 VP
    for v in range(5):
        s.cities[v] = 1
    assert rules.victory_points(s, 1) == 10
    assert rules.winner(s) == 1
    assert rules.is_terminal(s)


def test_no_winner_below_target():
    s = Game.new("standard", 4, seed=0)
    s.current_player = 0
    s.settlements[0] = 0
    assert rules.winner(s) is None
    assert not rules.is_terminal(s)


# --- longest road: the four cases -----------------------------------------

def test_longest_road_straight_chain():
    s = fake_state([(0, 1), (1, 2), (2, 3), (3, 4)])
    assert rules.longest_road_length(s, 0) == 4


def test_longest_road_branch_takes_two_longest_arms():
    # a Y from vertex 0: arms of length 3, 2, 1. Longest simple path = 3 + 2 = 5.
    s = fake_state([
        (0, 1), (1, 2), (2, 3),   # arm of 3
        (0, 4), (4, 5),           # arm of 2
        (0, 6),                   # arm of 1
    ])
    assert rules.longest_road_length(s, 0) == 5     # not 6 (would be summing)


def test_longest_road_loop():
    # a hexagon of 6 edges: all traversable without repeating an edge.
    s = fake_state([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)])
    assert rules.longest_road_length(s, 0) == 6


def test_longest_road_cut_by_opponent_building():
    # straight chain of 4, opponent settlement on the middle vertex (2) splits it
    s = fake_state([(0, 1), (1, 2), (2, 3), (3, 4)])
    s.settlements[2] = 1                # an opponent, not player 0
    # path may not pass through vertex 2: best segment is 2 edges on either side
    assert rules.longest_road_length(s, 0) == 2


def test_own_building_never_cuts_your_road():
    s = fake_state([(0, 1), (1, 2), (2, 3), (3, 4)])
    s.settlements[2] = 0                # your own building
    assert rules.longest_road_length(s, 0) == 4


# --- recompute + holder logic ---------------------------------------------

def test_longest_road_holder_awarded_and_transferred():
    s = Game.new("standard", 4, seed=0)
    board = s.board
    chain = _walk_chain(board, 5)
    for e in chain[:5]:
        s.roads[e] = 0
    rules.recompute_longest_road(s)
    assert s.longest_road_holder == 0        # first to reach the minimum (5)

    # player 1 builds a strictly longer road and overtakes
    other = _walk_chain(board, 6, avoid=set(chain))
    for e in other[:6]:
        s.roads[e] = 1
    rules.recompute_longest_road(s)
    assert s.longest_road_holder == 1


def test_settlement_placement_can_break_longest_road():
    # placing an opponent settlement in the middle must trigger a recompute
    s = Game.new("standard", 4, seed=0)
    board = s.board
    chain = _walk_chain(board, 5)
    for e in chain[:5]:
        s.roads[e] = 0
    rules.recompute_longest_road(s)
    assert s.longest_road_holder == 0

    # find a middle vertex of the chain and drop an opponent settlement on it
    mid_edge = chain[2]
    mid_v = board.edge_vertices(mid_edge)[0]
    s.settlements[mid_v] = 1
    rules.recompute_longest_road(s)
    assert s.longest_road_holder != 0        # road no longer long enough to hold


# --- largest army ----------------------------------------------------------

def test_largest_army_awarded_and_transferred():
    s = Game.new("standard", 4, seed=0)
    s.played_knights[0] = 3
    rules._recompute_largest_army(s)
    assert s.largest_army_holder == 0

    s.played_knights[1] = 4
    rules._recompute_largest_army(s)
    assert s.largest_army_holder == 1


def test_largest_army_tie_does_not_transfer():
    s = Game.new("standard", 4, seed=0)
    s.played_knights[0] = 3
    rules._recompute_largest_army(s)
    s.played_knights[1] = 3                  # ties, does not overtake
    rules._recompute_largest_army(s)
    assert s.largest_army_holder == 0


# --- helper: walk a simple chain of edges on the real board ---------------

def _walk_chain(board, length, avoid=frozenset()):
    start = next(e for e in range(board.num_edges()) if e not in avoid)
    edges = [start]
    a, b = board.edge_vertices(start)
    visited_v = {a}
    cur = b
    while len(edges) < length:
        nxt = None
        for e in board.vertex_edges(cur):
            if e in edges or e in avoid:
                continue
            x, y = board.edge_vertices(e)
            other = y if x == cur else x
            if other in visited_v:
                continue
            nxt, cur = e, other
            visited_v.add(cur)
            break
        if nxt is None:
            break
        edges.append(nxt)
    return edges
