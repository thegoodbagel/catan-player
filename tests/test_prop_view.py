# AI-generated
# tests/test_prop_view.py
#
# Chapter 10, Property 10: view soundness. Two states differing only in another
# player's hidden cards produce identical views for a third player.

from hypothesis import given, settings, strategies as st

from _helpers import play_random

from engine.game import Game
from engine.types import DevCard


@settings(max_examples=50, deadline=None)
@given(seed=st.integers(min_value=0, max_value=5000))
def test_view_is_blind_to_opponent_hidden_hand(seed):
    counter = {"n": 0}

    def stop(_s):
        counter["n"] += 1
        return counter["n"] >= 50 + (seed % 80)

    s1 = play_random(seed, max_steps=6000, stop_pred=stop)
    viewer = 0
    opponent = 1 if viewer != 1 else 2

    s2 = s1.copy()
    # swap the opponent's hidden hand for a different one of the SAME size
    n = sum(s1.dev_cards[opponent].values())
    s2.dev_cards[opponent] = {DevCard.KNIGHT: n} if n else {}

    assert Game.view(s1, viewer) == Game.view(s2, viewer)
