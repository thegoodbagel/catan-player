# AI-generated
# tests/test_legal_moves.py
#
# Chapter 6: per-phase legal-move generation. legal_moves lists only legal
# options and never mutates state.

import pytest

from _helpers import complete_setup

from engine.game import Game
from engine import rules
from engine.types import Phase, Resource, EMPTY
from engine.moves import (
    PlaceSetupSettlement, PlaceSetupRoad, Roll, EndTurn,
    BuildRoad, BuildSettlement, BankTrade,
)


# --- affordability ---------------------------------------------------------

def test_can_afford_exact_short_and_plenty():
    s = Game.new("standard", 4, seed=0)
    cost = {Resource.WOOD: 1, Resource.BRICK: 1}
    s.resources[0] = {r: 0 for r in Resource}
    s.resources[0][Resource.WOOD] = 1
    s.resources[0][Resource.BRICK] = 1
    assert rules.can_afford(s, 0, cost)          # exactly enough
    s.resources[0][Resource.BRICK] = 0
    assert not rules.can_afford(s, 0, cost)      # one short
    s.resources[0] = {r: 5 for r in Resource}
    assert rules.can_afford(s, 0, cost)          # plenty


# --- SETUP -----------------------------------------------------------------

def test_setup_offers_only_distance_legal_settlements():
    s = Game.new("standard", 4, seed=0)
    assert s.phase == Phase.SETUP
    moves = Game.legal_moves(s)
    assert moves and all(isinstance(m, PlaceSetupSettlement) for m in moves)
    # every offered vertex satisfies the distance rule
    for m in moves:
        assert rules.can_place_settlement(s, m.vertex)


def test_setup_after_settlement_offers_only_adjacent_roads():
    s = Game.new("standard", 4, seed=0)
    v = Game.legal_moves(s)[0].vertex
    s = rules.apply(s, PlaceSetupSettlement(v), in_place=True)
    moves = Game.legal_moves(s)
    assert moves and all(isinstance(m, PlaceSetupRoad) for m in moves)
    incident = set(s.board.vertex_edges(v))
    assert {m.edge for m in moves} <= incident


def test_setttlement_placement_removes_neighbors_from_options():
    s = Game.new("standard", 4, seed=0)
    v = Game.legal_moves(s)[0].vertex
    s = rules.apply(s, PlaceSetupSettlement(v), in_place=True)
    e = Game.legal_moves(s)[0].edge
    s = rules.apply(s, PlaceSetupRoad(e), in_place=True)
    # next player's settlement options must exclude v and its neighbors
    offered = {m.vertex for m in Game.legal_moves(s)}
    assert v not in offered
    assert all(n not in offered for n in s.board.vertex_neighbors(v))


# --- ROLL ------------------------------------------------------------------

def test_roll_phase_offers_roll():
    s = complete_setup(Game.new("standard", 4, seed=0))
    assert s.phase == Phase.ROLL
    assert Roll() in Game.legal_moves(s)


# --- MAIN / BUILD ----------------------------------------------------------

def test_main_always_offers_end_turn_and_never_empty():
    s = complete_setup(Game.new("standard", 4, seed=0))
    s = rules.apply(s, Roll(), in_place=True)
    # if a 7 was rolled we may be in DISCARD/ROBBER; drive to BUILD if needed
    while s.phase in (Phase.DISCARD, Phase.ROBBER):
        s = rules.apply(s, Game.legal_moves(s)[0], in_place=True)
    assert s.phase == Phase.BUILD
    moves = Game.legal_moves(s)
    assert moves                                   # never empty (Property 4)
    assert EndTurn() in moves


def test_main_gates_builds_by_affordability():
    s = complete_setup(Game.new("standard", 4, seed=0))
    s = rules.apply(s, Roll(), in_place=True)
    while s.phase in (Phase.DISCARD, Phase.ROBBER):
        s = rules.apply(s, Game.legal_moves(s)[0], in_place=True)
    p = s.current_player
    s.resources[p] = {r: 0 for r in Resource}      # broke: no builds affordable
    moves = Game.legal_moves(s)
    assert not any(isinstance(m, (BuildRoad, BuildSettlement)) for m in moves)
    assert EndTurn() in moves


def test_legal_moves_does_not_mutate_state():
    s = complete_setup(Game.new("standard", 4, seed=0))
    before = s.copy()
    _ = Game.legal_moves(s)
    assert s.settlements == before.settlements
    assert s.roads == before.roads
    assert s.resources == before.resources
