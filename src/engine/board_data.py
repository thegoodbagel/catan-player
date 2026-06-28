STANDARD_BOARD = {
    "meta":  {"name": "standard", "player_counts": [3, 4], "vp_target": 10, 
    "vp_methods": {
        "settlement" : 1,
        "city" : 2,
        "longest_road" : 2,
        "largest_army" : 2
    }},

    "hexes": [
        {"coord": [0, -2], "type" : "land"}, # could also be sea
        {"coord": [1, -2], "type" : "land"},
        {"coord": [2, -2], "type" : "land"},
        {"coord": [-1, -1], "type" : "land"},
        # ... 19 hex positions total ...
    ],

    "terrain_supply": {
        "wood": 4, "sheep": 4, "wheat": 4, "brick": 3, "ore": 3, "desert": 1,
    },

    # The number tokens in their fixed placement order (the A..R sequence,
    # 18 of them — one per non-desert hex)
    "number_order": [5, 2, 6, 3, 8, 10, 9, 12, 11, 4, 8, 10, 9, 4, 5, 6, 3, 11],

    # The order to walk hex positions when laying tokens: a spiral from an outer
    # corner inward counterclockwise, skipping the desert
    "token_spiral": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],

    "ports": [
        {"vertices": [0, 1], "ratio": 3, "resource": None},      # generic 3:1
        {"vertices": [3, 4], "ratio": 2, "resource": "wheat"},   # specific 2:1
        # ...
    ],
    "rules": "base",
}