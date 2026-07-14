# AI-generated
# tests/test_prop_victory.py
#
# Chapter 10, Property 6: victory_points is always the sum of the bundle's
# vp_sources, and winner returns p iff p is at target on their turn.

from hypothesis import given, settings, strategies as st

from _helpers import play_random

from engine.game import Game
from engine import rules


@settings(max_examples=60, deadline=None)
@given(seed=st.integers(min_value=0, max_value=5000))
def test_victory_is_sum_of_sources(seed):
    counter = {"n": 0}

    def stop(_s):
        counter["n"] += 1
        return counter["n"] >= 60 + (seed % 100)

    s = play_random(seed, max_steps=6000, stop_pred=stop)
    for p in range(s.num_players):
        expected = sum(src(s, p) for src in rules.active_bundle(s).vp_sources)
        assert rules.victory_points(s, p) == expected


@settings(max_examples=40, deadline=None)
@given(seed=st.integers(min_value=0, max_value=5000))
def test_winner_matches_target_on_current_player(seed):
    s = play_random(seed)              # terminal
    p = s.current_player
    target = rules.active_bundle(s).vp_target
    if rules.victory_points(s, p) >= target:
        assert rules.winner(s) == p
    else:
        assert rules.winner(s) is None
