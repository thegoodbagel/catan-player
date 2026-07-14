# AI-generated
# tests/test_view.py
#
# Chapter 9: the per-player view enforces hidden information in one place.

from _helpers import complete_setup

from engine.game import Game
from engine.types import DevCard


def test_view_shows_own_cards_and_gates_move_list():
    s = complete_setup(Game.new("standard", 4, seed=0))
    cur = s.current_player
    s.dev_cards[cur] = {DevCard.KNIGHT: 2}

    v_cur = Game.view(s, cur)
    assert v_cur.my_dev_cards == {DevCard.KNIGHT: 2}     # own cards: exact
    assert v_cur.legal                                    # current player sees moves

    other = (cur + 1) % s.num_players
    v_other = Game.view(s, other)
    assert v_other.legal == ()                            # non-current: empty


def test_view_exposes_opponents_only_as_counts():
    s = complete_setup(Game.new("standard", 4, seed=0))
    s.dev_cards[1] = {DevCard.KNIGHT: 1, DevCard.MONOPOLY: 2}
    v0 = Game.view(s, 0)
    assert v0.opponent_dev_card_counts[1] == 3            # a count, not identities
    # the view carries no field revealing which dev cards opponent 1 holds
    assert not hasattr(v0, "opponent_dev_cards")


def test_view_hides_opponent_card_identity():
    # two states differing ONLY in an opponent's hidden hand look identical
    s1 = complete_setup(Game.new("standard", 4, seed=0))
    s2 = s1.copy()
    s1.dev_cards[1] = {DevCard.KNIGHT: 3}
    s2.dev_cards[1] = {DevCard.MONOPOLY: 3}
    assert Game.view(s1, 2) == Game.view(s2, 2)
