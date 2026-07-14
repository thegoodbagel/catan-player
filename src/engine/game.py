# AI-generated
# src/engine/game.py
#
# The front door (Chapter 9): a small, stable public interface every client uses.
# Game wraps the internal operations in rules.py, adds a per-player `view` that
# enforces hidden information in one place, and adds `replay` so any game can be
# reconstructed from its seed plus move log.

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from engine import rules
from engine.board import load_board
from engine.board_data import SCENARIOS
from engine.layout import generate_layout
from engine.state import State
from engine.types import Phase, Resource, DevCard, EMPTY


class ReplayError(Exception):
    """Raised when a logged move is illegal at its point during replay."""


@dataclass(frozen=True)
class PlayerView:
    """What one player is allowed to see: all public facts, their own exact
    cards, and only aggregate counts for opponents."""
    board: object
    layout: object
    phase: Phase
    current_player: int
    settlements: tuple
    cities: tuple
    roads: tuple
    robber_hex: int
    bank: dict
    last_roll: Optional[tuple]
    longest_road_holder: int
    largest_army_holder: int
    played_knights: tuple
    my_resources: dict
    my_dev_cards: dict
    opponent_resource_counts: dict
    opponent_dev_card_counts: dict
    legal: tuple


def _hidden_dev_count(state, q: int) -> int:
    return (sum(state.dev_cards[q].values())
            + sum(state.new_dev_cards[q].values()))


class Game:
    @staticmethod
    def new(scenario: str = "standard", num_players: int = 4, seed: Optional[int] = None) -> State:
        board = load_board(scenario)
        data = SCENARIOS[scenario] if isinstance(scenario, str) else scenario
        rng = random.Random(seed)
        layout = generate_layout(data, rng)

        bundle = rules.active_bundle("base")
        deck: list[DevCard] = []
        for card, n in bundle.dev_deck_composition.items():
            deck += [card] * n
        rng.shuffle(deck)

        order = list(range(num_players)) + list(reversed(range(num_players)))
        nv, ne = board.num_vertices(), board.num_edges()
        robber = layout.desert_hex if layout.desert_hex is not None else 0

        return State(
            board=board,
            phase=Phase.SETUP,
            current_player=order[0],
            settlements=[EMPTY] * nv,
            roads=[EMPTY] * ne,
            resources=[{r: 0 for r in Resource} for _ in range(num_players)],
            robber_hex=robber,
            move_log=[],
            bank={r: 19 for r in Resource},
            dev_deck=deck,
            last_roll=None,
            setup_progress=0,
            rng_state=rng.getstate(),
            layout=layout,
            variant="base",
            cities=[EMPTY] * nv,
            dev_cards=[{} for _ in range(num_players)],
            new_dev_cards=[{} for _ in range(num_players)],
            played_knights=[0] * num_players,
            pending_discards={},
            awaiting_setup_road=None,
            setup_order=order,
        )

    # --- thin delegators ---------------------------------------------------

    @staticmethod
    def legal_moves(state) -> list:
        return rules.legal_moves(state)

    @staticmethod
    def apply(state, move, in_place: bool = False):
        return rules.apply(state, move, in_place=in_place)

    @staticmethod
    def is_terminal(state) -> bool:
        return rules.is_terminal(state)

    @staticmethod
    def winner(state):
        return rules.winner(state)

    @staticmethod
    def victory_points(state, player) -> int:
        return rules.victory_points(state, player)

    # --- privacy filter ----------------------------------------------------

    @staticmethod
    def view(state, player: int) -> PlayerView:
        others = [q for q in range(state.num_players) if q != player]
        return PlayerView(
            board=state.board,
            layout=state.layout,
            phase=state.phase,
            current_player=state.current_player,
            settlements=tuple(state.settlements),
            cities=tuple(state.cities),
            roads=tuple(state.roads),
            robber_hex=state.robber_hex,
            bank=dict(state.bank),
            last_roll=state.last_roll,
            longest_road_holder=state.longest_road_holder,
            largest_army_holder=state.largest_army_holder,
            played_knights=tuple(state.played_knights),
            my_resources=dict(state.resources[player]),
            my_dev_cards={**state.dev_cards[player]},
            opponent_resource_counts={q: sum(state.resources[q].values()) for q in others},
            opponent_dev_card_counts={q: _hidden_dev_count(state, q) for q in others},
            legal=tuple(rules.legal_moves(state)) if player == state.current_player else (),
        )

    # --- replay ------------------------------------------------------------

    @staticmethod
    def replay(scenario, num_players, seed, moves):
        s = Game.new(scenario, num_players, seed)
        for i, m in enumerate(moves):
            if m not in rules.legal_moves(s):
                raise ReplayError(f"move {i} illegal during replay: {m!r}")
            s = rules.apply(s, m, in_place=True)
        return s
