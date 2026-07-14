# AI-generated
# tests/test_prop_playthrough.py
#
# Chapter 10, the centerpiece: play full games by choosing random legal moves,
# asserting the engine's invariants at every step. This single harness exercises
# the whole engine and is where most real bugs would surface.

from collections import Counter

from hypothesis import given, settings, strategies as st

from engine.game import Game
from engine import rules
from engine.types import Resource, EMPTY


def _no_two_adjacent_buildings(s):
    board = s.board
    for v in range(board.num_vertices()):
        if s.settlements[v] == EMPTY and s.cities[v] == EMPTY:
            continue
        for n in board.vertex_neighbors(v):
            assert s.settlements[n] == EMPTY and s.cities[n] == EMPTY, (
                f"adjacent buildings at {v} and {n}"
            )


def _resources_conserved(s):
    # bank + all players = 19 of each resource, always
    tally = Counter(s.bank)
    for p in range(s.num_players):
        tally.update(s.resources[p])
    for r in Resource:
        assert tally[r] == 19, f"{r} not conserved: {tally[r]}"


def _all_resource_counts_non_negative(s):
    assert all(c >= 0 for c in s.bank.values())
    for p in range(s.num_players):
        assert all(c >= 0 for c in s.resources[p].values())


def _assert_invariants(s):
    _all_resource_counts_non_negative(s)
    _resources_conserved(s)
    _no_two_adjacent_buildings(s)


@settings(max_examples=60, deadline=None)
@given(seed=st.integers(min_value=0, max_value=10_000))
def test_random_playthrough_preserves_invariants(seed):
    import random
    s = Game.new("standard", num_players=4, seed=seed)
    rng = random.Random(seed + 1)
    steps = 0
    while not Game.is_terminal(s) and steps < 6000:
        moves = Game.legal_moves(s)
        assert moves, "no legal moves but game not over (deadlock!)"   # Property 4
        s = Game.apply(s, rng.choice(moves), in_place=True)
        _assert_invariants(s)                                          # 5, 7, (8 via setup)
        steps += 1
    assert Game.is_terminal(s), "game failed to terminate within the step cap"
