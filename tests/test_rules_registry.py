# AI-generated
# tests/test_rules_registry.py
#
# Tests the variant registry wiring (Chapter 5): a BASE bundle is registered and
# findable by name, its config is readable, and a new variant can be added by
# registering data alone — without touching engine logic.

from dataclasses import replace
from types import SimpleNamespace

import pytest

from engine.rules import (
    VariantBundle,
    VARIANTS,
    register_variant,
    active_bundle,
    BASE,
    _todo,
)
from engine.moves import BuildRoad, BuildSettlement
from engine.types import Resource, Phase


def test_base_is_registered_and_found_by_name():
    assert active_bundle("base") is BASE
    assert VARIANTS["base"] is BASE


def test_active_bundle_accepts_a_state_like_object():
    fake_state = SimpleNamespace(variant="base")
    assert active_bundle(fake_state) is BASE


def test_base_config_is_readable():
    assert BASE.vp_target == 10
    assert BASE.build_costs[BuildRoad] == {Resource.WOOD: 1, Resource.BRICK: 1}
    assert BASE.piece_limits["settlement"] == 5
    assert Phase.BUILD in BASE.phases


def test_rule_slots_are_stubs_for_now():
    # placeholders should exist but refuse to run until later chapters fill them
    with pytest.raises(NotImplementedError):
        BASE.effects[BuildSettlement]()


def test_new_variant_is_just_data():
    # a "speed" game is base with a lower target — no engine logic changes
    speed = replace(BASE, name="speed", vp_target=5)
    register_variant(speed)
    assert active_bundle("speed").vp_target == 5
    assert active_bundle("speed").build_costs == BASE.build_costs
