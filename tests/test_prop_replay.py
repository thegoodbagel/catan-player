# AI-generated
# tests/test_prop_replay.py
#
# Chapter 10, Property 9: seed + move log reproduces the final state exactly.

from hypothesis import given, settings, strategies as st

from _helpers import play_random

from engine.game import Game


def _states_equal(a, b):
    return (a.phase == b.phase
            and a.current_player == b.current_player
            and a.settlements == b.settlements
            and a.cities == b.cities
            and a.roads == b.roads
            and a.resources == b.resources
            and a.bank == b.bank
            and a.robber_hex == b.robber_hex
            and a.dev_cards == b.dev_cards
            and a.new_dev_cards == b.new_dev_cards)


@settings(max_examples=40, deadline=None)
@given(seed=st.integers(min_value=0, max_value=5000))
def test_replay_round_trip(seed):
    s = play_random(seed, max_steps=1000)
    replayed = Game.replay("standard", 4, seed=seed, moves=s.move_log)
    assert _states_equal(replayed, s)
