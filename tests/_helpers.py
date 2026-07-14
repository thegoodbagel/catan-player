# AI-generated
# tests/_helpers.py
#
# Shared helpers for the engine tests: driving a game through setup, playing a
# random game to a reachable/terminal state, and a small hand-built graph for
# the longest-road unit tests.

import random
from types import SimpleNamespace

from engine.game import Game
from engine import rules
from engine.types import EMPTY


def complete_setup(state, seed=0):
    """Play the SETUP phase by picking a legal move each step until ROLL."""
    rng = random.Random(seed)
    while state.phase.name == "SETUP":
        moves = Game.legal_moves(state)
        state = rules.apply(state, rng.choice(moves), in_place=True)
    return state


def play_random(seed, max_steps=6000, stop_pred=None):
    """Play a game with uniformly-random legal moves. Returns the final state
    (terminal, or the first state satisfying stop_pred)."""
    s = Game.new("standard", 4, seed=seed)
    rng = random.Random(seed + 1)
    steps = 0
    while not Game.is_terminal(s) and steps < max_steps:
        if stop_pred is not None and stop_pred(s):
            return s
        moves = Game.legal_moves(s)
        s = rules.apply(s, rng.choice(moves), in_place=True)
        steps += 1
    return s


# --- a minimal fake board for the longest-road unit tests -----------------
# longest_road_length only reads: board.num_edges(), board.edge_vertices(e),
# board.vertex_edges(v), plus state.roads / settlements / cities. So a tiny
# purpose-built graph lets us describe each topology exactly.

class FakeBoard:
    def __init__(self, edge_list):
        self._edges = edge_list
        self._nv = max(max(e) for e in edge_list) + 1
        self._ve = {v: [] for v in range(self._nv)}
        for i, (a, b) in enumerate(edge_list):
            self._ve[a].append(i)
            self._ve[b].append(i)

    def num_edges(self):
        return len(self._edges)

    def num_vertices(self):
        return self._nv

    def edge_vertices(self, e):
        return self._edges[e]

    def vertex_edges(self, v):
        return self._ve[v]


def fake_state(edge_list, owner=0):
    """A SimpleNamespace state whose roads are all owned by `owner`."""
    board = FakeBoard(edge_list)
    return SimpleNamespace(
        board=board,
        roads=[owner] * board.num_edges(),
        settlements=[EMPTY] * board.num_vertices(),
        cities=[EMPTY] * board.num_vertices(),
    )
