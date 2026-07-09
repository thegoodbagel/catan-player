# AI-generated
# src/engine/board.py
#
# The immutable board geometry. load_board() turns a scenario (hex coordinates)
# into integer-id lookup tables the rest of the engine uses, so no other module
# ever touches coordinates.
#
# How ids are derived (see docs/conventions.md for the short version):
#   - Each corner is named by the SET of hexes meeting there:
#       corner(H, i) = {H, neighbour i, neighbour i+1}   (two consecutive sides)
#     The same physical corner yields the same set from any hex, so equal sets
#     collapse to one id automatically (dedup). Off-board neighbours still go in
#     the set, so boundary corners work with no special case.
#   - Each edge is named the same way with two hexes: {H, neighbour i}.
# The one requirement is that HEX_DIRECTION_OFFSETS lists the six sides in
# rotational order, which it does.

from __future__ import annotations

from dataclasses import dataclass

from engine.types import Direction, HEX_DIRECTION_OFFSETS
from engine.board_data import SCENARIOS, STANDARD_BOARD


class InvalidScenario(Exception):
    """Raised when a scenario's data is internally inconsistent."""


@dataclass(frozen=True)
class Board:
    """Immutable board geometry: coordinate-free integer-id lookup tables."""

    coords: tuple[tuple[int, int], ...]        # hex id -> (q, r)
    _hex_vertices: tuple[tuple[int, ...], ...]  # hex id -> its 6 vertex ids
    _hex_edges: tuple[tuple[int, ...], ...]     # hex id -> its 6 edge ids
    _vertex_hexes: tuple[tuple[int, ...], ...]  # vertex id -> the 1..3 hexes on it
    _edge_vertices: tuple[tuple[int, int], ...] # edge id -> its 2 endpoint vertices
    _vertex_neighbors: tuple[tuple[int, ...], ...]  # vertex id -> adjacent vertices
    _hex_neighbors: tuple[tuple[int, ...], ...]     # hex id -> adjacent hexes

    # --- counts ---
    def num_hexes(self) -> int:
        return len(self.coords)

    def num_vertices(self) -> int:
        return len(self._vertex_hexes)

    def num_edges(self) -> int:
        return len(self._edge_vertices)

    # --- lookups ---
    def hex_coord(self, h: int) -> tuple[int, int]:
        return self.coords[h]

    def hex_vertices(self, h: int) -> tuple[int, ...]:
        return self._hex_vertices[h]

    def hex_edges(self, h: int) -> tuple[int, ...]:
        return self._hex_edges[h]

    def hex_neighbors(self, h: int) -> tuple[int, ...]:
        return self._hex_neighbors[h]

    def vertex_hexes(self, v: int) -> tuple[int, ...]:
        return self._vertex_hexes[v]

    def vertex_neighbors(self, v: int) -> tuple[int, ...]:
        return self._vertex_neighbors[v]

    def edge_vertices(self, e: int) -> tuple[int, int]:
        return self._edge_vertices[e]

    # --- ports: resolve a (hex, side) position to its edge and vertices ---
    def edge_of(self, h: int, direction: Direction) -> int:
        return self._hex_edges[h][int(direction)]

    def port_vertices(self, h: int, direction: Direction) -> tuple[int, int]:
        return self._edge_vertices[self.edge_of(h, direction)]


def _validate(data: dict) -> None:
    hexes = data["hexes"]
    coords = [tuple(h["coord"]) for h in hexes]
    if len(set(coords)) != len(coords):
        raise InvalidScenario("duplicate hex coordinates")

    land = [h for h in hexes if h.get("type", "land") == "land"]
    supply = data["hex_resources"]
    if sum(supply.values()) != len(land):
        raise InvalidScenario(
            f"resource supply ({sum(supply.values())}) != land hex count ({len(land)})"
        )

    desert = supply.get("desert", 0)
    numbers = data["hex_numbers"]
    if len(numbers) != len(land) - desert:
        raise InvalidScenario(
            f"{len(numbers)} number tokens for {len(land) - desert} numbered hexes"
        )
    if any(not (2 <= n <= 12) or n == 7 for n in numbers):
        raise InvalidScenario("number tokens must be in 2..12 and never 7")

    coordset = set(coords)
    seen_edges = set()
    for p in data["port_positions"]:
        h, d = p["hex"], p["dir"]
        if not (0 <= h < len(hexes)):
            raise InvalidScenario(f"port on unknown hex {h}")
        dq, dr = HEX_DIRECTION_OFFSETS[int(d)]
        q, r = coords[h]
        nb = (q + dq, r + dr)
        if nb in coordset:
            raise InvalidScenario(f"port on hex {h} facing land, not sea")
        edge_key = frozenset({(q, r), nb})
        if edge_key in seen_edges:
            raise InvalidScenario(f"two ports share the edge at hex {h}")
        seen_edges.add(edge_key)

    if len(data["port_supply"]) != len(data["port_positions"]):
        raise InvalidScenario("port supply size != number of port positions")


def load_board(scenario="standard") -> Board:
    """Build the immutable Board from a scenario name or a scenario dict."""
    data = SCENARIOS[scenario] if isinstance(scenario, str) else scenario
    _validate(data)

    coords = [tuple(h["coord"]) for h in data["hexes"]]
    coordset = set(coords)
    id_of = {c: i for i, c in enumerate(coords)}

    vkey_to_id: dict[frozenset, int] = {}
    ekey_to_id: dict[frozenset, int] = {}
    hex_vertices: list[tuple[int, ...]] = []
    hex_edges: list[tuple[int, ...]] = []
    edge_ends: dict[int, tuple[int, int]] = {}

    for (q, r) in coords:
        nbrs = [(q + dq, r + dr) for (dq, dr) in HEX_DIRECTION_OFFSETS]

        corner_ids = []
        for i in range(6):
            key = frozenset({(q, r), nbrs[i], nbrs[(i + 1) % 6]})
            corner_ids.append(vkey_to_id.setdefault(key, len(vkey_to_id)))
        hex_vertices.append(tuple(corner_ids))

        edge_ids = []
        for i in range(6):
            key = frozenset({(q, r), nbrs[i]})
            eid = ekey_to_id.setdefault(key, len(ekey_to_id))
            edge_ids.append(eid)
            # edge i runs between corner i-1 and corner i (both include nbr i)
            edge_ends.setdefault(eid, (corner_ids[(i - 1) % 6], corner_ids[i]))
        hex_edges.append(tuple(edge_ids))

    n_vertices = len(vkey_to_id)
    n_edges = len(ekey_to_id)

    # vertex -> the on-board hexes in its key (drop off-board phantoms)
    vertex_hexes: list[tuple[int, ...]] = [()] * n_vertices
    for key, vid in vkey_to_id.items():
        vertex_hexes[vid] = tuple(sorted(id_of[c] for c in key if c in coordset))

    edge_vertices = tuple(edge_ends[e] for e in range(n_edges))

    # vertex adjacency comes straight from the edges
    vn: list[set[int]] = [set() for _ in range(n_vertices)]
    for a, b in edge_vertices:
        vn[a].add(b)
        vn[b].add(a)
    vertex_neighbors = tuple(tuple(sorted(s)) for s in vn)

    hex_neighbors = tuple(
        tuple(id_of[(q + dq, r + dr)]
              for (dq, dr) in HEX_DIRECTION_OFFSETS
              if (q + dq, r + dr) in coordset)
        for (q, r) in coords
    )

    return Board(
        coords=tuple(coords),
        _hex_vertices=tuple(hex_vertices),
        _hex_edges=tuple(hex_edges),
        _vertex_hexes=tuple(vertex_hexes),
        _edge_vertices=edge_vertices,
        _vertex_neighbors=vertex_neighbors,
        _hex_neighbors=hex_neighbors,
    )
