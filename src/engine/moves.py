# src/engine/moves.py
#
# Pure-data moves (Design B): a Move only *describes intent*. It never mutates
# anything — all mutation happens in rules.apply. Frozen dataclasses give us
# hashing and equality for free, which is exactly what the move log needs to
# replay deterministically.

from dataclasses import dataclass
from typing import Optional

from engine.types import Resource


# --- setup phase ----------------------------------------------------------

@dataclass(frozen=True)
class PlaceSetupSettlement:
    vertex: int


@dataclass(frozen=True)
class PlaceSetupRoad:
    edge: int


# --- roll -----------------------------------------------------------------

@dataclass(frozen=True)
class Roll:
    pass


# --- building -------------------------------------------------------------

@dataclass(frozen=True)
class BuildRoad:
    edge: int


@dataclass(frozen=True)
class BuildSettlement:
    vertex: int


@dataclass(frozen=True)
class BuildCity:
    vertex: int


# --- development cards ----------------------------------------------------

@dataclass(frozen=True)
class BuyDevCard:
    pass


@dataclass(frozen=True)
class PlayKnight:
    pass


@dataclass(frozen=True)
class PlayRoadBuilding:
    edge1: int
    edge2: Optional[int] = None      # None when only one legal placement exists


@dataclass(frozen=True)
class PlayYearOfPlenty:
    first: Resource
    second: Resource


@dataclass(frozen=True)
class PlayMonopoly:
    resource: Resource


# --- trading (bank / port only; no player-to-player trades in v1) ----------

@dataclass(frozen=True)
class BankTrade:
    give: Resource
    receive: Resource


@dataclass(frozen=True)
class PortTrade:
    give: Resource
    receive: Resource


# --- robber / discard -----------------------------------------------------

@dataclass(frozen=True)
class MoveRobber:
    hex: int
    steal_from: Optional[int] = None   # player id to steal from, or None


@dataclass(frozen=True)
class Discard:
    player: int
    cards: tuple            # sorted tuple of (Resource, count) pairs


# --- turn -----------------------------------------------------------------

@dataclass(frozen=True)
class EndTurn:
    pass
