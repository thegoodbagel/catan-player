# AI-generated
# tests/test_state.py
#
# Tests for State.copy(): it must share the immutable board (by identity) while
# duplicating every mutable container so edits to a copy never reach the original.

from engine.state import State
from engine.types import Phase, Resource, EMPTY


def make_state(num_players: int = 2) -> State:
    # `board` is only ever shared by reference, so a plain object stands in for it.
    board = object()
    return State(
        board=board,
        phase=Phase.SETUP,
        current_player=0,
        settlements=[EMPTY, EMPTY, EMPTY],
        roads=[EMPTY, EMPTY],
        resources=[{r: 0 for r in Resource} for _ in range(num_players)],
        robber_hex=0,
        move_log=[],
        bank={r: 19 for r in Resource},
        dev_deck=[],
        last_roll=None,
        setup_progress=0,
        rng_state=None,
    )


def test_copy_shares_board_by_identity():
    s = make_state()
    c = s.copy()
    assert c.board is s.board          # the SAME object, not a duplicate


def test_copy_isolates_occupancy_arrays():
    s = make_state()
    c = s.copy()
    c.settlements[0] = 3
    c.roads[0] = 1
    assert s.settlements[0] == EMPTY   # original untouched
    assert s.roads[0] == EMPTY


def test_copy_does_not_leak_resource_dicts():
    # the aliasing bug from Chapter 4, Ex. 2: inner dicts must be copied too
    s = make_state()
    c = s.copy()
    c.resources[0][Resource.WOOD] += 1
    assert s.resources[0][Resource.WOOD] == 0


def test_copy_isolates_bank_deck_and_log():
    s = make_state()
    c = s.copy()
    c.bank[Resource.ORE] -= 5
    c.dev_deck.append("KNIGHT")
    c.move_log.append("some move")
    assert s.bank[Resource.ORE] == 19
    assert s.dev_deck == []
    assert s.move_log == []


def test_copy_is_a_distinct_object():
    s = make_state()
    c = s.copy()
    assert c is not s
    assert c.settlements is not s.settlements
    assert c.resources is not s.resources
