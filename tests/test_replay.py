# AI-generated
# tests/test_replay.py
#
# Chapter 9: a game is fully reconstructable from its seed plus move log.

import pytest

from _helpers import play_random

from engine.game import Game, ReplayError
from engine import rules
from engine.moves import BuildCity


def _states_equal(a, b):
    return (a.phase == b.phase
            and a.current_player == b.current_player
            and a.settlements == b.settlements
            and a.cities == b.cities
            and a.roads == b.roads
            and a.resources == b.resources
            and a.bank == b.bank
            and a.robber_hex == b.robber_hex
            and a.longest_road_holder == b.longest_road_holder
            and a.largest_army_holder == b.largest_army_holder)


def test_replay_reproduces_a_played_game():
    s = play_random(seed=3, max_steps=800)
    replayed = Game.replay("standard", 4, seed=3, moves=s.move_log)
    assert _states_equal(replayed, s)


def test_replay_reproduces_a_full_game_to_win():
    s = play_random(seed=7)              # plays to terminal
    assert Game.is_terminal(s)
    replayed = Game.replay("standard", 4, seed=7, moves=s.move_log)
    assert _states_equal(replayed, s)
    assert Game.winner(replayed) == Game.winner(s)


def test_replay_raises_on_an_illegal_logged_move():
    s = Game.new("standard", 4, seed=0)
    with pytest.raises(ReplayError):
        # a city can't be built during SETUP; move 0 is illegal
        Game.replay("standard", 4, seed=0, moves=[BuildCity(0)])
