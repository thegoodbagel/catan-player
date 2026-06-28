# tests/test_moves.py
import pytest
from engine.moves import BuildSettlement, BankTrade
from engine.types import Resource

def test_move_is_frozen():
    m = BuildSettlement(7)
    with pytest.raises(Exception):   # frozen dataclasses raise on assignment
        m.vertex = 9

def test_moves_compare_by_value():
    a = BankTrade(Resource.WOOD, Resource.ORE)
    b = BankTrade(Resource.WOOD, Resource.ORE)
    assert a == b               # equal by fields, not identity
    assert len({a, b}) == 1     # the set collapses the duplicate