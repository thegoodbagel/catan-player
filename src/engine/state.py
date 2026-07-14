# src/engine/state.py
from __future__ import annotations   # lets forward references not be quoted
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional
import copy as _copy

from engine.types import Phase, Resource, DevCard, EMPTY

# temporary since board.py is empty
if TYPE_CHECKING:
    from engine.board import Board
    from engine.layout import Layout


@dataclass
class State:
    board: Board                       # shared immutable board
    phase: Phase
    current_player: int
    settlements: list[int]               # settlements[v] = owner, or -1 if empty
    roads: list[int]                     # roads[e] = owner, or -1
    resources: list[dict[Resource, int]] # resources[p][Resource.WOOD] = count
    robber_hex: int
    move_log: list
    bank: dict[Resource, int]            # bank[Resource.WOOD] = count in the bank
    dev_deck: list[DevCard]              # list[0] is bottom
    last_roll: tuple[int, int] | None
    setup_progress: int                  # index into the snake-draft order
    rng_state: object                    # random.Random().getstate() for replay

    # --- fields added in Chapters 5-9 (all defaulted so earlier construction
    #     and tests keep working) ---------------------------------------------
    layout: Layout | None = None         # per-game resource/number/port assignment
    variant: str = "base"                # which VariantBundle governs this game
    cities: list[int] = field(default_factory=list)      # cities[v] = owner or -1
    dev_cards: list[dict] = field(default_factory=list)  # playable hands per player
    new_dev_cards: list[dict] = field(default_factory=list)  # bought this turn
    played_knights: list[int] = field(default_factory=list)  # per player
    longest_road_holder: int = EMPTY
    largest_army_holder: int = EMPTY
    dev_played_this_turn: bool = False
    pending_discards: dict = field(default_factory=dict)  # player -> cards owed
    awaiting_setup_road: Optional[int] = None             # vertex needing a road
    setup_order: list[int] = field(default_factory=list)  # snake-draft player order

    @property
    def num_players(self) -> int:
        return len(self.resources)

    def copy(self) -> State:
        new = _copy.copy(self)                            # shallow copy
        new.settlements = list(self.settlements)          # deep copy
        new.roads = list(self.roads)                      # deep copy
        new.cities = list(self.cities)                    # deep copy
        new.resources = [dict(r) for r in self.resources] # deep copy
        new.bank = dict(self.bank)                        # deep copy
        new.dev_deck = list(self.dev_deck)                # deep copy
        new.move_log = list(self.move_log)                # deep copy
        new.dev_cards = [dict(h) for h in self.dev_cards]         # deep copy
        new.new_dev_cards = [dict(h) for h in self.new_dev_cards] # deep copy
        new.played_knights = list(self.played_knights)    # deep copy
        new.pending_discards = dict(self.pending_discards) # deep copy
        new.setup_order = list(self.setup_order)          # deep copy
        # board, layout are immutable/shared; scalars (phase, current_player,
        # robber_hex, last_roll, setup_progress, rng_state, holders, flags) are
        # immutable, so no copy is needed.
        return new
