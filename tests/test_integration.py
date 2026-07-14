# AI-generated
# tests/test_integration.py
#
# Chapter 10, Ex. 4: drive a game from setup all the way to a 10-VP win and
# assert the end-to-end "play -> win -> terminal" path. Rather than hard-code
# fragile edge/vertex ids, we drive with a fixed build-greedy policy, which is
# deterministic for a given seed and reliably reaches a winner.

from engine.game import Game
from engine import rules
from engine.moves import (
    BuildCity, BuildSettlement, BuildRoad, BuyDevCard, EndTurn,
    PlaceSetupSettlement, PlaceSetupRoad,
)


def _greedy_choice(moves):
    # prefer moves that advance toward victory, in decreasing value order
    priority = (BuildCity, BuildSettlement, BuildRoad, BuyDevCard)
    for kind in priority:
        for m in moves:
            if isinstance(m, kind):
                return m
    # during setup take the first offered placement
    for m in moves:
        if isinstance(m, (PlaceSetupSettlement, PlaceSetupRoad)):
            return m
    # otherwise take a non-EndTurn action if one exists, else end the turn
    for m in moves:
        if not isinstance(m, EndTurn):
            return m
    return EndTurn()


def test_scripted_game_reaches_a_winner():
    s = Game.new("standard", 4, seed=11)
    steps = 0
    while not Game.is_terminal(s) and steps < 8000:
        s = Game.apply(s, _greedy_choice(Game.legal_moves(s)), in_place=True)
        steps += 1

    assert Game.is_terminal(s)
    w = Game.winner(s)
    assert w is not None
    assert Game.victory_points(s, w) >= rules.active_bundle(s).vp_target
