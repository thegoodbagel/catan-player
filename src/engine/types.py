# src/engine/types.py
from enum import Enum, IntEnum

class Phase(Enum):
    SETUP = "setup"
    ROBBER = "robber"               # can be reached by:
                                    # 1) playing dev card before roll 
                                    # 2) rolling a seven
                                    # 3) playing a dev card after roll
    ROLL = "roll"
    DISCARD = "discard"
    BUILD = "build"                 # includes:
                                    # 1) playing dev cards
                                    # 2) building stuff
                                    # 3) trading (bank & player)
    GAME_OVER = "game_over"

class Resource(Enum):
    WOOD = "wood"
    BRICK = "brick"
    SHEEP = "sheep"
    WHEAT = "wheat"
    ORE = "ore"

class DevCard(Enum):
    KNIGHT = "knight"
    VICTORY_POINT = "victory_point"
    ROAD_BUILDING = "road_building"
    YEAR_OF_PLENTY = "year_of_plenty"
    MONOPOLY = "monopoly"

class Pieces(Enum):
    SETTLEMENT = "settlement"
    CITY = "city"
    ROAD = "road"

class Color(Enum):
    ORANGE = "Orange"
    RED = "Red"
    WHITE = "White"
    BLUE = "Blue"


class Direction(IntEnum):
    """The six edges of a hex, in fixed order.
       Previxed by H for hex.
    """
    E = 0       # east
    NE = 1      # north-east
    NW = 2      # north-west
    W = 3       # west
    SW = 4      # south-west
    SE = 5      # south-east


# Axial (dq, dr) offset for each direction, indexed by the Direction value.
# The neighbour of hex (q, r) in direction d is (q + dq, r + dr).
HEX_DIRECTION_OFFSETS = (
    (+1,  0),   # Direction.E
    (+1, -1),   # Direction.NE
    ( 0, -1),   # Direction.NW
    (-1,  0),   # Direction.W
    (-1, +1),   # Direction.SW
    ( 0, +1),   # Direction.SE
)



