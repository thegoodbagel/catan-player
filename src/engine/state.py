# src/engine/state.py
from __future__ import annotations   # lets forward references not be quoted
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
import copy as _copy

from engine.types import Phase, Resource, DevCard, EMPTY

# temporary since board.py is empty
if TYPE_CHECKING:
    from engine.board import Board

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
    setup_progress: int # to clarify?
    rng_state: object                    # random.Random().getstate() for replay


    def copy(self) -> State:
        new = _copy.copy(self)                            # shallow copy
        new.settlements = list(self.settlements)          # deep copy
        new.roads = list(self.roads)                      # deep copy
        new.resources = [dict(r) for r in self.resources] # deep copy
        new.bank = dict(self.bank)                        # deep copy
        new.dev_deck = list(self.dev_deck)                # deep copy
        new.move_log = list(self.move_log)                # deep copy
        # board, phase, current_player, robber_hex, last_roll, setup_progress,
        # rng_state are immutable or shared, so no copy is needed.
        return new
