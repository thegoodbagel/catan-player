# src/engine/rules.py
#
# The rulebook as data (Chapter 5) plus the three front-door operations built on
# top of it: legal_moves (Chapter 6), apply (Chapter 7), and scoring/winner
# (Chapter 8). The engine holds no game-specific rules of its own; a
# "variant bundle" is one game's rulebook, gathered into a single record the
# engine reads. Base Catan is registered as the BASE bundle below.

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Optional

from engine.types import Phase, Resource, DevCard, EMPTY
from engine.moves import (
    PlaceSetupSettlement, PlaceSetupRoad, Roll,
    BuildRoad, BuildSettlement, BuildCity,
    BuyDevCard, PlayKnight, PlayRoadBuilding, PlayYearOfPlenty, PlayMonopoly,
    BankTrade, PortTrade, MoveRobber, Discard, EndTurn,
)


# ==========================================================================
# The variant bundle and its registry
# ==========================================================================

@dataclass(frozen=True)
class VariantBundle:
    name: str
    phases: tuple                        # which turn phases exist
    generators: dict                     # phase -> function listing legal moves
    effects: dict                        # move type -> function carrying it out
    vp_sources: tuple                    # functions that each contribute points
    # --- tunable configuration, not magic numbers buried in code ---
    vp_target: int                       # points needed to win
    build_costs: dict                    # move type -> required resources
    piece_limits: dict                   # {"road": 15, "settlement": 5, "city": 4}
    dev_deck_composition: dict = field(default_factory=dict)
    discard_limit: int = 7
    longest_road_min: int = 5
    largest_army_min: int = 3
    bank_trade_ratio: int = 4


VARIANTS: dict[str, VariantBundle] = {}


def register_variant(bundle: VariantBundle) -> None:
    VARIANTS[bundle.name] = bundle


def active_bundle(state_or_name) -> VariantBundle:
    """Find the rulebook for a game. Accepts a variant name, or a State-like
    object carrying a `.variant` name."""
    name = state_or_name if isinstance(state_or_name, str) else state_or_name.variant
    return VARIANTS[name]


# Kept for backward compatibility with early-chapter tests that imported it.
def _todo(*args, **kwargs):
    raise NotImplementedError("this rule is implemented in a later chapter")


# ==========================================================================
# Exceptions
# ==========================================================================

class IllegalMove(Exception):
    """Raised by apply() when a move is not in legal_moves(state)."""


class GameOver(Exception):
    """Raised by apply() when the game has already ended."""


# ==========================================================================
# Small, pure helpers shared by generators and effects
# ==========================================================================

def can_afford(state, p, cost: dict) -> bool:
    have = state.resources[p]
    return all(have.get(res, 0) >= need for res, need in cost.items())


def occupied(state, v: int) -> bool:
    return state.settlements[v] != EMPTY or state.cities[v] != EMPTY


def owner_of_vertex(state, v: int) -> int:
    if state.settlements[v] != EMPTY:
        return state.settlements[v]
    if state.cities[v] != EMPTY:
        return state.cities[v]
    return EMPTY


def occupied_by_opponent(state, v: int, p: int) -> bool:
    o = owner_of_vertex(state, v)
    return o != EMPTY and o != p


def count_pieces(state, p, kind: str) -> int:
    if kind == "road":
        return sum(1 for o in state.roads if o == p)
    if kind == "settlement":
        return sum(1 for o in state.settlements if o == p)
    if kind == "city":
        return sum(1 for o in state.cities if o == p)
    raise ValueError(kind)


def _piece_available(state, p, kind: str) -> bool:
    return count_pieces(state, p, kind) < active_bundle(state).piece_limits[kind]


# --- placement predicates -------------------------------------------------

def can_place_settlement(state, v: int) -> bool:
    """The distance rule: the vertex is empty and no neighbour is occupied."""
    if occupied(state, v):
        return False
    board = state.board
    return not any(occupied(state, n) for n in board.vertex_neighbors(v))


def _connects_to_player(state, p, v: int) -> bool:
    """Whether player p may extend a road from vertex v: they own a building or
    road there, and no opponent building sits on v to block continuity."""
    if occupied_by_opponent(state, v, p):
        return False
    if state.settlements[v] == p or state.cities[v] == p:
        return True
    return any(state.roads[e] == p for e in state.board.vertex_edges(v))


def buildable_road_edges(state, p) -> list[int]:
    board = state.board
    out = []
    for e in range(board.num_edges()):
        if state.roads[e] != EMPTY:
            continue
        a, b = board.edge_vertices(e)
        if _connects_to_player(state, p, a) or _connects_to_player(state, p, b):
            out.append(e)
    return out


def buildable_settlement_vertices(state, p) -> list[int]:
    board = state.board
    out = []
    for v in range(board.num_vertices()):
        if not can_place_settlement(state, v):
            continue
        if any(state.roads[e] == p for e in board.vertex_edges(v)):
            out.append(v)
    return out


def buildable_city_vertices(state, p) -> list[int]:
    return [v for v in range(state.board.num_vertices())
            if state.settlements[v] == p]


# --- ports ----------------------------------------------------------------

def owned_ports(state, p) -> list:
    if state.layout is None:
        return []
    board = state.board
    out = []
    for port in state.layout.ports:
        for v in board.port_vertices(port.hex, port.direction):
            if owner_of_vertex(state, v) == p:
                out.append(port)
                break
    return out


def port_ratio(state, p, resource) -> Optional[int]:
    """Best (lowest) trade ratio the player can get for `resource` through an
    owned port, or None if they own no relevant port."""
    best = None
    for port in owned_ports(state, p):
        if port.resource is None:
            r = 3
        elif port.resource == resource:
            r = 2
        else:
            continue
        best = r if best is None else min(best, r)
    return best


# ==========================================================================
# Legal-move generation (Chapter 6)
# ==========================================================================

def legal_moves(state) -> list:
    gens = active_bundle(state).generators
    gen = gens.get(state.phase)
    if gen is None:                    # e.g. GAME_OVER: nothing is legal
        return []
    return gen(state)


def gen_setup_moves(state) -> list:
    board = state.board
    if state.awaiting_setup_road is None:      # place a settlement next
        return [PlaceSetupSettlement(v)
                for v in range(board.num_vertices())
                if can_place_settlement(state, v)]
    v = state.awaiting_setup_road              # place a road touching vertex v
    return [PlaceSetupRoad(e)
            for e in board.vertex_edges(v)
            if state.roads[e] == EMPTY]


def gen_roll_moves(state) -> list:
    moves = [Roll()]
    p = state.current_player
    # a single pre-roll knight is the only dev card playable before the roll
    if not state.dev_played_this_turn and _hand(state, p).get(DevCard.KNIGHT, 0) > 0:
        moves.append(PlayKnight())
    return moves


def gen_discard_moves(state) -> list:
    q = min(state.pending_discards)            # resolve owing players in order
    count = state.pending_discards[q]
    return [Discard(q, cards) for cards in _discard_options(state.resources[q], count)]


def gen_robber_moves(state) -> list:
    board = state.board
    moves = []
    for h in range(board.num_hexes()):
        if h == state.robber_hex:
            continue
        victims = _robber_victims(state, h)
        if victims:
            for q in victims:
                moves.append(MoveRobber(h, q))
        else:
            moves.append(MoveRobber(h, None))
    return moves


def gen_main_moves(state) -> list:
    p = state.current_player
    bundle = active_bundle(state)
    costs = bundle.build_costs
    moves = [EndTurn()]                         # always permitted -> never deadlocks

    if can_afford(state, p, costs[BuildRoad]) and _piece_available(state, p, "road"):
        for e in buildable_road_edges(state, p):
            moves.append(BuildRoad(e))
    if can_afford(state, p, costs[BuildSettlement]) and _piece_available(state, p, "settlement"):
        for v in buildable_settlement_vertices(state, p):
            moves.append(BuildSettlement(v))
    if can_afford(state, p, costs[BuildCity]) and _piece_available(state, p, "city"):
        for v in buildable_city_vertices(state, p):
            moves.append(BuildCity(v))
    if can_afford(state, p, costs[BuyDevCard]) and state.dev_deck:
        moves.append(BuyDevCard())

    moves += _playable_dev_moves(state)
    moves += _trade_moves(state, p)
    return moves


# --- generation helpers ---------------------------------------------------

def _hand(state, p) -> dict:
    return state.dev_cards[p]


def _playable_dev_moves(state) -> list:
    """Dev-card plays available in the main phase (at most one per turn)."""
    p = state.current_player
    if state.dev_played_this_turn:
        return []
    hand = _hand(state, p)
    moves = []
    if hand.get(DevCard.KNIGHT, 0) > 0:
        moves.append(PlayKnight())
    if hand.get(DevCard.MONOPOLY, 0) > 0:
        for r in Resource:
            moves.append(PlayMonopoly(r))
    if hand.get(DevCard.YEAR_OF_PLENTY, 0) > 0:
        for r1, r2 in itertools.combinations_with_replacement(list(Resource), 2):
            moves.append(PlayYearOfPlenty(r1, r2))
    if hand.get(DevCard.ROAD_BUILDING, 0) > 0 and _piece_available(state, p, "road"):
        moves += _road_building_moves(state, p)
    return moves


def _road_building_moves(state, p) -> list:
    """All (edge1, edge2) placements for a Road Building card, computed without
    mutating state: after placing edge1, edge2 may be any edge that was already
    buildable or that edge1 newly connects."""
    board = state.board
    first = buildable_road_edges(state, p)
    base = set(first)
    moves = []
    for e1 in first:
        second = set(base)
        for v in board.edge_vertices(e1):
            if occupied_by_opponent(state, v, p):
                continue
            for ee in board.vertex_edges(v):
                if state.roads[ee] == EMPTY:
                    second.add(ee)
        second.discard(e1)
        if second:
            for e2 in sorted(second):
                moves.append(PlayRoadBuilding(e1, e2))
        else:
            moves.append(PlayRoadBuilding(e1, None))
    return moves


def _trade_moves(state, p) -> list:
    have = state.resources[p]
    bank = state.bank
    bundle = active_bundle(state)
    moves = []
    for give in Resource:
        ratio = port_ratio(state, p, give)
        for receive in Resource:
            if receive == give or bank.get(receive, 0) <= 0:
                continue
            if have.get(give, 0) >= bundle.bank_trade_ratio:
                moves.append(BankTrade(give, receive))
            if ratio is not None and have.get(give, 0) >= ratio:
                moves.append(PortTrade(give, receive))
    return moves


def _discard_options(hand: dict, count: int) -> list:
    """Every distinct multiset of `count` cards drawable from `hand`, as a sorted
    tuple of (Resource, count) pairs."""
    resources = list(Resource)
    caps = [hand.get(r, 0) for r in resources]
    results = []

    def rec(i, remaining, chosen):
        if i == len(resources):
            if remaining == 0:
                results.append(tuple(
                    (resources[j], chosen[j])
                    for j in range(len(resources)) if chosen[j] > 0
                ))
            return
        for take in range(0, min(caps[i], remaining) + 1):
            rec(i + 1, remaining - take, chosen + [take])

    rec(0, count, [])
    return results


def _robber_victims(state, h: int) -> list:
    p = state.current_player
    board = state.board
    victims = set()
    for v in board.hex_vertices(h):
        o = owner_of_vertex(state, v)
        if o != EMPTY and o != p and sum(state.resources[o].values()) > 0:
            victims.add(o)
    return sorted(victims)


# ==========================================================================
# Applying moves (Chapter 7)
# ==========================================================================

def apply(state, move, in_place: bool = False):
    if is_terminal(state):
        raise GameOver()
    if move not in legal_moves(state):            # (1) validate
        raise IllegalMove(move)

    s = state if in_place else state.copy()       # (2) fast vs. safe path

    effect = active_bundle(s).effects[type(move)] # (3) look up what it does
    next_phase = effect(s, move)                  #     ... and do it (mutates s)

    s.phase = next_phase                          # (4) advance phase, record move
    s.move_log.append(move)
    if winner(s) is not None:
        s.phase = Phase.GAME_OVER
    return s


# --- money helpers --------------------------------------------------------

def _pay(state, p, cost: dict) -> None:
    for res, n in cost.items():
        state.resources[p][res] -= n
        state.bank[res] += n


def _gain(state, p, resource, n: int = 1) -> int:
    """Move up to n of a resource from the bank to player p (bank never negative)."""
    take = min(n, state.bank.get(resource, 0))
    state.bank[resource] -= take
    state.resources[p][resource] += take
    return take


# --- setup effects --------------------------------------------------------

def eff_setup_settlement(s, move) -> Phase:
    p = s.current_player
    s.settlements[move.vertex] = p
    s.awaiting_setup_road = move.vertex
    # the second settlement each player places grants starting resources
    if s.setup_progress >= s.num_players:
        for h in s.board.vertex_hexes(move.vertex):
            res = s.layout.hex_resource[h]
            if res is not None:
                _gain(s, p, res, 1)
    return Phase.SETUP


def eff_setup_road(s, move) -> Phase:
    s.roads[move.edge] = s.current_player
    s.awaiting_setup_road = None
    s.setup_progress += 1
    if s.setup_progress >= 2 * s.num_players:
        s.current_player = 0
        return Phase.ROLL
    s.current_player = s.setup_order[s.setup_progress]
    return Phase.SETUP


# --- roll / production -----------------------------------------------------

def _rng(s) -> random.Random:
    rng = random.Random()
    rng.setstate(s.rng_state)
    return rng


def _save_rng(s, rng) -> None:
    s.rng_state = rng.getstate()


def eff_roll(s, move) -> Phase:
    rng = _rng(s)
    d1, d2 = rng.randint(1, 6), rng.randint(1, 6)
    _save_rng(s, rng)
    s.last_roll = (d1, d2)
    total = d1 + d2
    if total == 7:
        limit = active_bundle(s).discard_limit
        s.pending_discards = {
            q: sum(s.resources[q].values()) // 2
            for q in range(s.num_players)
            if sum(s.resources[q].values()) > limit
        }
        return Phase.DISCARD if s.pending_discards else Phase.ROBBER
    _distribute_production(s, total)
    return Phase.BUILD


def _distribute_production(s, total: int) -> None:
    board, layout = s.board, s.layout
    for h in range(board.num_hexes()):
        if layout.hex_number[h] != total or h == s.robber_hex:
            continue
        res = layout.hex_resource[h]
        if res is None:
            continue
        for v in board.hex_vertices(h):
            if s.settlements[v] != EMPTY:
                _gain(s, s.settlements[v], res, 1)
            elif s.cities[v] != EMPTY:
                _gain(s, s.cities[v], res, 2)


# --- discard / robber ------------------------------------------------------

def eff_discard(s, move) -> Phase:
    for res, n in move.cards:
        s.resources[move.player][res] -= n
        s.bank[res] += n
    del s.pending_discards[move.player]
    return Phase.DISCARD if s.pending_discards else Phase.ROBBER


def eff_move_robber(s, move) -> Phase:
    s.robber_hex = move.hex
    if move.steal_from is not None:
        cards = [r for r, n in s.resources[move.steal_from].items() for _ in range(n)]
        if cards:
            rng = _rng(s)
            r = rng.choice(cards)
            _save_rng(s, rng)
            s.resources[move.steal_from][r] -= 1
            s.resources[s.current_player][r] += 1
    return Phase.BUILD


# --- build effects ---------------------------------------------------------

def eff_build_road(s, move) -> Phase:
    p = s.current_player
    _pay(s, p, active_bundle(s).build_costs[BuildRoad])
    s.roads[move.edge] = p
    recompute_longest_road(s)
    return Phase.BUILD


def eff_build_settlement(s, move) -> Phase:
    p = s.current_player
    _pay(s, p, active_bundle(s).build_costs[BuildSettlement])
    s.settlements[move.vertex] = p
    recompute_longest_road(s)      # an opponent's new building can cut a road
    return Phase.BUILD


def eff_build_city(s, move) -> Phase:
    p = s.current_player
    _pay(s, p, active_bundle(s).build_costs[BuildCity])
    s.settlements[move.vertex] = EMPTY   # the settlement is upgraded
    s.cities[move.vertex] = p
    return Phase.BUILD


# --- dev-card effects ------------------------------------------------------

def eff_buy_dev(s, move) -> Phase:
    p = s.current_player
    _pay(s, p, active_bundle(s).build_costs[BuyDevCard])
    card = s.dev_deck.pop()
    s.new_dev_cards[p][card] = s.new_dev_cards[p].get(card, 0) + 1
    return Phase.BUILD


def eff_play_knight(s, move) -> Phase:
    p = s.current_player
    s.dev_cards[p][DevCard.KNIGHT] -= 1
    s.played_knights[p] += 1
    s.dev_played_this_turn = True
    _recompute_largest_army(s)
    return Phase.ROBBER


def eff_play_road_building(s, move) -> Phase:
    p = s.current_player
    s.roads[move.edge1] = p
    if move.edge2 is not None:
        s.roads[move.edge2] = p
    s.dev_cards[p][DevCard.ROAD_BUILDING] -= 1
    s.dev_played_this_turn = True
    recompute_longest_road(s)
    return Phase.BUILD


def eff_play_year_of_plenty(s, move) -> Phase:
    p = s.current_player
    _gain(s, p, move.first, 1)
    _gain(s, p, move.second, 1)
    s.dev_cards[p][DevCard.YEAR_OF_PLENTY] -= 1
    s.dev_played_this_turn = True
    return Phase.BUILD


def eff_play_monopoly(s, move) -> Phase:
    p = s.current_player
    taken = 0
    for q in range(s.num_players):
        if q == p:
            continue
        taken += s.resources[q][move.resource]
        s.resources[q][move.resource] = 0
    s.resources[p][move.resource] += taken
    s.dev_cards[p][DevCard.MONOPOLY] -= 1
    s.dev_played_this_turn = True
    return Phase.BUILD


# --- trade effects ---------------------------------------------------------

def eff_bank_trade(s, move) -> Phase:
    p = s.current_player
    ratio = active_bundle(s).bank_trade_ratio
    s.resources[p][move.give] -= ratio
    s.bank[move.give] += ratio
    s.resources[p][move.receive] += 1
    s.bank[move.receive] -= 1
    return Phase.BUILD


def eff_port_trade(s, move) -> Phase:
    p = s.current_player
    ratio = port_ratio(s, p, move.give)
    s.resources[p][move.give] -= ratio
    s.bank[move.give] += ratio
    s.resources[p][move.receive] += 1
    s.bank[move.receive] -= 1
    return Phase.BUILD


# --- end turn --------------------------------------------------------------

def eff_end_turn(s, move) -> Phase:
    p = s.current_player
    # dev cards bought this turn become playable next turn
    for card, n in s.new_dev_cards[p].items():
        s.dev_cards[p][card] = s.dev_cards[p].get(card, 0) + n
    s.new_dev_cards[p] = {}
    s.dev_played_this_turn = False
    s.last_roll = None
    s.current_player = (p + 1) % s.num_players
    return Phase.ROLL


# ==========================================================================
# Scoring, winner, and the two bonuses (Chapter 8)
# ==========================================================================

def victory_points(state, p) -> int:
    return sum(source(state, p) for source in active_bundle(state).vp_sources)


def vp_from_buildings(state, p) -> int:
    s = sum(1 for owner in state.settlements if owner == p)
    c = sum(2 for owner in state.cities if owner == p)
    return s + c


def vp_from_vp_cards(state, p) -> int:
    n = state.dev_cards[p].get(DevCard.VICTORY_POINT, 0)
    n += state.new_dev_cards[p].get(DevCard.VICTORY_POINT, 0)
    return n


def vp_from_longest_road(state, p) -> int:
    return 2 if state.longest_road_holder == p else 0


def vp_from_largest_army(state, p) -> int:
    return 2 if state.largest_army_holder == p else 0


def winner(state):
    p = state.current_player
    if victory_points(state, p) >= active_bundle(state).vp_target:
        return p
    return None


def is_terminal(state) -> bool:
    return state.phase == Phase.GAME_OVER or winner(state) is not None


# --- longest road: longest simple path over each player's road subgraph ----

def longest_road_length(state, p) -> int:
    board = state.board
    own = [e for e in range(board.num_edges()) if state.roads[e] == p]

    def dfs(edge, visited_edges, came_from_vertex) -> int:
        best = len(visited_edges)
        for v in board.edge_vertices(edge):
            if v == came_from_vertex:
                continue                            # don't walk straight back
            if occupied_by_opponent(state, v, p):
                continue                            # enemy building cuts the path
            for nxt in board.vertex_edges(v):
                if state.roads[nxt] == p and nxt not in visited_edges:
                    best = max(best, dfs(nxt, visited_edges | {nxt}, v))
        return best

    return max((dfs(e, {e}, None) for e in own), default=0)


def recompute_longest_road(state) -> None:
    bundle = active_bundle(state)
    minimum = bundle.longest_road_min
    lengths = [longest_road_length(state, p) for p in range(state.num_players)]
    holder = state.longest_road_holder

    if holder != EMPTY and lengths[holder] < minimum:
        holder = EMPTY

    best = max(lengths, default=0)
    if best >= minimum:
        leaders = [p for p, ln in enumerate(lengths) if ln == best]
        if holder == EMPTY:
            if len(leaders) == 1:
                holder = leaders[0]
        elif lengths[holder] < best and len(leaders) == 1:
            holder = leaders[0]        # someone strictly overtook the holder
    state.longest_road_holder = holder


def _recompute_largest_army(state) -> None:
    bundle = active_bundle(state)
    minimum = bundle.largest_army_min
    counts = state.played_knights
    holder = state.largest_army_holder
    best = max(counts, default=0)
    if best >= minimum:
        leaders = [p for p, c in enumerate(counts) if c == best]
        if holder == EMPTY:
            if len(leaders) == 1:
                holder = leaders[0]
        elif counts[holder] < best and len(leaders) == 1:
            holder = leaders[0]
    state.largest_army_holder = holder


# ==========================================================================
# The base Catan bundle
# ==========================================================================

BASE = VariantBundle(
    name="base",
    phases=(Phase.SETUP, Phase.ROLL, Phase.DISCARD, Phase.ROBBER, Phase.BUILD),
    generators={
        Phase.SETUP: gen_setup_moves,
        Phase.ROLL: gen_roll_moves,
        Phase.DISCARD: gen_discard_moves,
        Phase.ROBBER: gen_robber_moves,
        Phase.BUILD: gen_main_moves,
    },
    effects={
        PlaceSetupSettlement: eff_setup_settlement,
        PlaceSetupRoad: eff_setup_road,
        Roll: eff_roll,
        BuildRoad: eff_build_road,
        BuildSettlement: eff_build_settlement,
        BuildCity: eff_build_city,
        BuyDevCard: eff_buy_dev,
        PlayKnight: eff_play_knight,
        PlayRoadBuilding: eff_play_road_building,
        PlayYearOfPlenty: eff_play_year_of_plenty,
        PlayMonopoly: eff_play_monopoly,
        BankTrade: eff_bank_trade,
        PortTrade: eff_port_trade,
        MoveRobber: eff_move_robber,
        Discard: eff_discard,
        EndTurn: eff_end_turn,
    },
    vp_sources=(
        vp_from_buildings,
        vp_from_vp_cards,
        vp_from_longest_road,
        vp_from_largest_army,
    ),
    vp_target=10,
    build_costs={
        BuildRoad: {Resource.WOOD: 1, Resource.BRICK: 1},
        BuildSettlement: {
            Resource.WOOD: 1, Resource.BRICK: 1,
            Resource.SHEEP: 1, Resource.WHEAT: 1,
        },
        BuildCity: {Resource.WHEAT: 2, Resource.ORE: 3},
        BuyDevCard: {Resource.ORE: 1, Resource.SHEEP: 1, Resource.WHEAT: 1},
    },
    piece_limits={"road": 15, "settlement": 5, "city": 4},
    dev_deck_composition={
        DevCard.KNIGHT: 14,
        DevCard.VICTORY_POINT: 5,
        DevCard.ROAD_BUILDING: 2,
        DevCard.YEAR_OF_PLENTY: 2,
        DevCard.MONOPOLY: 2,
    },
    discard_limit=7,
    longest_road_min=5,
    largest_army_min=3,
    bank_trade_ratio=4,
)

register_variant(BASE)
