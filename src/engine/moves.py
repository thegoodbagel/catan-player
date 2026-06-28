# src/engine/moves.py
from dataclasses import dataclass
from typing import Optional
from engine.types import *

@dataclass(frozen=True)
class BuildSettlement:
    vertex: int

@dataclass(frozen=True)
class BuildCity:
    vertex: int

@dataclass(frozen=True)
class BuildRoad:
    edge: int

@dataclass(frozen=True)
class PlayDevCard:
    cardType: DevCard

@dataclass(frozen=True)
class Monopoly:
    take: Resource

@dataclass(frozen=True)
class MoveRobber:
    hex: int

@dataclass(frozen=True)
class BankTrade:
    give: Resource
    receive: Resource

@dataclass(frozen=True)
class PortTrade:
    give: Resource
    receive: Resource

@dataclass(frozen=True)
class EndTurn:
    pass