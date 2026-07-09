# src/engine/board_data.py
#
# Static board representation. 
# - Hexes are represented with axial coordinates (q, r). 
# - Vertices and Edges are derived in load_board from the hexes
# - Ports are referenced with (hex, dir), which
#   load_board will resolve to two vertex IDs

from engine.types import Direction

STANDARD_BOARD = {
    "meta": {
        "name": "standard",
        "player_counts": [3, 4],
        "vp_target": 10,
        "vp_methods": {
            "settlement": 1,
            "city": 2,
            "longest_road": 2,
            "largest_army": 2,
        },
    },

    # The 19 hex positions in row-major order (top row first). Hex ID == index.
    # Axial (q, r) anchored so the top-left hex is (0, 0); r increases downward.
    # "type" is "land" for every base-game hex; "sea" is reserved for variants.
    "hexes": [
        # row r = 0  (ids 0-2)
        {"coord": [0, 0], "type": "land"},
        {"coord": [1, 0], "type": "land"},
        {"coord": [2, 0], "type": "land"},
        # row r = 1  (ids 3-6)
        {"coord": [-1, 1], "type": "land"},
        {"coord": [0, 1], "type": "land"},
        {"coord": [1, 1], "type": "land"},
        {"coord": [2, 1], "type": "land"},
        # row r = 2  (ids 7-11)
        {"coord": [-2, 2], "type": "land"},
        {"coord": [-1, 2], "type": "land"},
        {"coord": [0, 2], "type": "land"},
        {"coord": [1, 2], "type": "land"},
        {"coord": [2, 2], "type": "land"},
        # row r = 3  (ids 12-15)
        {"coord": [-2, 3], "type": "land"},
        {"coord": [-1, 3], "type": "land"},
        {"coord": [0, 3], "type": "land"},
        {"coord": [1, 3], "type": "land"},
        # row r = 4  (ids 16-18)
        {"coord": [-2, 4], "type": "land"},
        {"coord": [-1, 4], "type": "land"},
        {"coord": [0, 4], "type": "land"},
    ],

    # The bag of terrain tiles shuffled across the 19 positions at setup:
    # 4 wood, 4 sheep, 4 wheat, 3 brick, 3 ore, 1 desert = 19.
    "hex_resources": {
        "wood": 4, "sheep": 4, "wheat": 4, "brick": 3, "ore": 3, "desert": 1,
    },

    # The 18 number tokens in their fixed placement order (the A..R sequence,
    # one per non-desert hex). Setup lays these along a spiral whose starting
    # corner and winding direction are chosen at random, skipping the desert.
    # The spiral path is generated at setup, not stored here.
    "hex_numbers": [5, 2, 6, 3, 8, 10, 9, 12, 11, 4, 8, 10, 9, 4, 5, 6, 3, 11],

    # Fixed port POSITIONS only — each is a coastal edge given as a hex id plus a
    # side Direction. The ratio/resource is NOT fixed here; it is drawn from
    # "port_supply" at setup (variable harbors).
    "port_positions": [
        {"hex": 0,  "dir": Direction.NW},   # (0, 0)
        {"hex": 2,  "dir": Direction.NE},   # (2, 0)
        {"hex": 6,  "dir": Direction.E},    # (2, 1)
        {"hex": 11, "dir": Direction.E},    # (2, 2)
        {"hex": 15, "dir": Direction.SE},   # (1, 3)
        {"hex": 17, "dir": Direction.SE},   # (-1, 4)
        {"hex": 16, "dir": Direction.SW},   # (-2, 4)
        {"hex": 12, "dir": Direction.W},    # (-2, 3)
        {"hex": 7,  "dir": Direction.W},    # (-2, 2)
    ],

    "port_supply": [
        {"ratio": 3, "resource": None},
        {"ratio": 3, "resource": None},
        {"ratio": 3, "resource": None},
        {"ratio": 3, "resource": None},
        {"ratio": 2, "resource": "wood"},
        {"ratio": 2, "resource": "brick"},
        {"ratio": 2, "resource": "sheep"},
        {"ratio": 2, "resource": "wheat"},
        {"ratio": 2, "resource": "ore"},
    ],

    "rules": "base",
}

# Scenarios load_board can look up by name.
SCENARIOS = {
    "standard": STANDARD_BOARD,
    "base": STANDARD_BOARD,
}
