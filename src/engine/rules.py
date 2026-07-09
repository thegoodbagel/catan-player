# AI-generated
# src/engine/rules.py
#
# The rulebook as data (Chapter 5). The engine holds no game-specific rules; a
# "variant bundle" is one game's rulebook, gathered into a single record the
# engine reads. This chapter builds the bundle SHAPE and a registry, and
# registers a BASE bundle whose rule functions are placeholders. The real logic
# (generators, effects, victory-point sources) arrives in later chapters.

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from engine.types import Phase, Resource
from engine.moves import BuildRoad, BuildSettlement, BuildCity


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


# --- registry: register bundles, look them up by name ---------------------

VARIANTS: dict[str, VariantBundle] = {}


def register_variant(bundle: VariantBundle) -> None:
    VARIANTS[bundle.name] = bundle


def active_bundle(state_or_name) -> VariantBundle:
    """Find the rulebook for a game. Accepts a variant name, or a State-like
    object carrying a `.variant` name."""
    name = state_or_name if isinstance(state_or_name, str) else state_or_name.variant
    return VARIANTS[name]


# --- placeholder rule functions (filled in later chapters) ----------------

def _todo(*args, **kwargs):
    raise NotImplementedError("this rule is implemented in a later chapter")


# --- base Catan bundle -----------------------------------------------------

BASE = VariantBundle(
    name="base",
    phases=(Phase.SETUP, Phase.ROLL, Phase.DISCARD, Phase.ROBBER, Phase.BUILD),
    generators={Phase.BUILD: _todo},        # real generators arrive in Chapter 6
    effects={                                # real effects arrive in Chapter 7
        BuildRoad: _todo,
        BuildSettlement: _todo,
        BuildCity: _todo,
    },
    vp_sources=(_todo,),                     # real sources arrive in Chapter 8
    vp_target=10,
    build_costs={
        BuildRoad: {Resource.WOOD: 1, Resource.BRICK: 1},
        BuildSettlement: {
            Resource.WOOD: 1, Resource.BRICK: 1,
            Resource.SHEEP: 1, Resource.WHEAT: 1,
        },
        BuildCity: {Resource.WHEAT: 2, Resource.ORE: 3},
    },
    piece_limits={"road": 15, "settlement": 5, "city": 4},
)

register_variant(BASE)
