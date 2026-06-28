# tests/test_board_adjacency.py
from engine.board import load_board

def test_hex_vertex_tables_agree():
    board = load_board("standard")
    for h in range(board.num_hexes()):
        for v in board.hex_vertices(h):
            assert h in board.vertex_hexes(v)   # if hex says it touches v, v must agree