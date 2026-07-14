# AI-generated
# tests/test_apply.py
#
# Chapter 7: apply() validates before mutating, chooses the in-place/copy path,
# dispatches the effect, and advances the phase. The effects do the real work.

import pytest

from _helpers import complete_setup

from engine.game import Game
from engine import rules
from engine.types import Phase, Resource, EMPTY
from engine.moves import Roll, BuildRoad, BuildSettlement, EndTurn


def _drive_to_build(s):
    s = rules.apply(s, Roll(), in_place=True)
    while s.phase in (Phase.DISCARD, Phase.ROBBER):
        s = rules.apply(s, Game.legal_moves(s)[0], in_place=True)
    return s


# --- the validation gate ---------------------------------------------------

def test_illegal_move_is_rejected_and_changes_nothing():
    s = complete_setup(Game.new("standard", 4, seed=0))
    before = s.copy()
    with pytest.raises(rules.IllegalMove):
        rules.apply(s, BuildRoad(9999), in_place=True)   # not a legal move now
    assert s.settlements == before.settlements
    assert s.roads == before.roads
    assert s.resources == before.resources
    assert s.phase == before.phase


def test_apply_on_finished_game_raises():
    s = Game.new("standard", 4, seed=0)
    s.phase = Phase.GAME_OVER
    with pytest.raises(rules.GameOver):
        rules.apply(s, EndTurn(), in_place=True)


# --- an effect: build road -------------------------------------------------

def test_build_road_deducts_cost_and_records_road():
    s = _drive_to_build(complete_setup(Game.new("standard", 4, seed=0)))
    p = s.current_player
    s.resources[p] = {r: 5 for r in Resource}
    edge = rules.buildable_road_edges(s, p)[0]
    wood0, brick0 = s.resources[p][Resource.WOOD], s.resources[p][Resource.BRICK]
    bank_wood0 = s.bank[Resource.WOOD]
    s2 = rules.apply(s, BuildRoad(edge), in_place=True)
    assert s2.roads[edge] == p
    assert s2.resources[p][Resource.WOOD] == wood0 - 1
    assert s2.resources[p][Resource.BRICK] == brick0 - 1
    assert s2.bank[Resource.WOOD] == bank_wood0 + 1     # paid to the bank


# --- in-place / copy equivalence (the cornerstone) -------------------------

def test_inplace_and_copy_paths_agree_and_copy_is_pure():
    s = _drive_to_build(complete_setup(Game.new("standard", 4, seed=0)))
    p = s.current_player
    s.resources[p] = {r: 5 for r in Resource}
    edge = rules.buildable_road_edges(s, p)[0]
    m = BuildRoad(edge)

    a = rules.apply(s.copy(), m, in_place=True)
    snapshot = s.copy()
    b = rules.apply(s, m, in_place=False)

    assert a.roads == b.roads and a.resources == b.resources and a.bank == b.bank
    # the copy path must not have touched the input
    assert s.roads == snapshot.roads and s.resources == snapshot.resources


# --- production ------------------------------------------------------------

def test_distribute_production_pays_settlement_one_city_two():
    s = Game.new("standard", 4, seed=0)
    layout = s.layout
    # pick a producing hex and its number
    h = next(i for i in range(s.board.num_hexes())
             if layout.hex_number[i] is not None and i != s.robber_hex)
    res = layout.hex_resource[h]
    total = layout.hex_number[h]
    corners = s.board.hex_vertices(h)
    s.settlements[corners[0]] = 0
    s.cities[corners[1]] = 1
    before0 = s.resources[0][res]
    before1 = s.resources[1][res]
    rules._distribute_production(s, total)
    assert s.resources[0][res] == before0 + 1        # settlement -> 1
    assert s.resources[1][res] == before1 + 2        # city -> 2


def test_end_turn_advances_player_and_returns_to_roll():
    s = _drive_to_build(complete_setup(Game.new("standard", 4, seed=0)))
    p = s.current_player
    s2 = rules.apply(s, EndTurn(), in_place=True)
    assert s2.current_player == (p + 1) % s.num_players
    assert s2.phase == Phase.ROLL
