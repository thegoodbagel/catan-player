# AI-generated
# tests/test_prop_apply_paths.py
#
# Chapter 10, Properties 1 & 2: the copy path leaves the input unchanged, and
# apply(in_place=True) on a copy agrees with apply(in_place=False).

import random

from hypothesis import given, settings, strategies as st

from _helpers import play_random

from engine.game import Game
from engine import rules


def _snapshot(s):
    return (list(s.settlements), list(s.cities), list(s.roads),
            [dict(r) for r in s.resources], dict(s.bank),
            s.phase, s.current_player, s.robber_hex)


def _reachable_state_and_move(seed):
    """Play partway into a game, stopping at a non-terminal state, and pick a
    legal move there."""
    target = 40 + (seed % 120)
    counter = {"n": 0}

    def stop(_s):
        counter["n"] += 1
        return counter["n"] >= target

    s = play_random(seed, max_steps=6000, stop_pred=stop)
    if Game.is_terminal(s):
        return None, None
    moves = Game.legal_moves(s)
    m = random.Random(seed).choice(moves)
    return s, m


@settings(max_examples=60, deadline=None)
@given(seed=st.integers(min_value=0, max_value=5000))
def test_copy_path_is_pure_and_matches_in_place(seed):
    s, m = _reachable_state_and_move(seed)
    if s is None:
        return
    before = _snapshot(s)

    a = rules.apply(s.copy(), m, in_place=True)     # throwaway copy
    b = rules.apply(s, m, in_place=False)           # copy path: must not touch s

    # Property 2: both paths agree
    assert a.settlements == b.settlements
    assert a.cities == b.cities
    assert a.roads == b.roads
    assert a.resources == b.resources
    assert a.bank == b.bank
    assert a.phase == b.phase

    # Property 1: the copy path left the original byte-for-byte unchanged
    assert _snapshot(s) == before
