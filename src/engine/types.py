# src/engine/types.py
from enum import Enum

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

