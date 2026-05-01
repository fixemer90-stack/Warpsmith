import numpy as np

from backend.engine.modifiers import (
    Modifier,
    ModifierContext,
    apply_modifiers,
    build_weapon_modifiers,
    should_reroll,
)
from backend.model.unit import Unit, Weapon


def make_unit(name: str = "Marine") -> Unit:
    return Unit(
        name=name,
        faction="adeptus_astartes",
        category="Infantry",
        movement=6,
        toughness=4,
        save=3,
        wounds=2,
        leadership=6,
        objective_control=2,
        points=90,
        model_count=(5, 10),
    )


def make_weapon(*, tags: list[str] | None = None, range_max: int | None = 24) -> Weapon:
    return Weapon(
        name="Test Weapon",
        type="ranged" if range_max is not None else "melee",
        range_max=range_max,
        attacks_dice=(0, 0, 3),
        skill=4,
        strength=4,
        ap=0,
        damage_dice=(0, 0, 1),
        tags=tags or [],
    )


def make_context(*, weapon: Weapon | None = None, distance: int | None = 12, is_stationary: bool = False, squad_size: int = 1) -> ModifierContext:
    return ModifierContext(
        attacker=make_unit("Attacker"),
        defender=make_unit("Defender"),
        weapon=weapon or make_weapon(),
        distance=distance,
        is_stationary=is_stationary,
        squad_size=squad_size,
    )


def test_cap_modifier() -> None:
    mods = [Modifier("hit_roll", "add", 1), Modifier("hit_roll", "add", 1)]
    result = apply_modifiers("hit_roll", 4, mods, make_context(), np.random.default_rng(42))
    assert result.target_value == 3


def test_cancel_modifier() -> None:
    mods = [Modifier("hit_roll", "add", 1), Modifier("hit_roll", "subtract", 1)]
    result = apply_modifiers("hit_roll", 4, mods, make_context(), np.random.default_rng(42))
    assert result.target_value == 4


def test_sustained_hits() -> None:
    mods = [Modifier("hit_roll", "sustained_hits", 1)]
    result = apply_modifiers("hit_roll", 4, mods, make_context(), np.random.default_rng(42))
    assert result.extra_rolls == 1


def test_lethal_hits_sets_auto_success() -> None:
    mods = [Modifier("hit_roll", "lethal_hits")]
    result = apply_modifiers("hit_roll", 4, mods, make_context(), np.random.default_rng(42))
    assert result.auto_success is True


def test_auto_hit_sets_auto_success() -> None:
    mods = [Modifier("hit_roll", "auto_hit")]
    result = apply_modifiers("hit_roll", 4, mods, make_context(), np.random.default_rng(42))
    assert result.auto_success is True


def test_devastating_wounds_ignores_save() -> None:
    mods = [Modifier("wound_roll", "devastating_wounds")]
    result = apply_modifiers("wound_roll", 4, mods, make_context(), np.random.default_rng(42))
    assert result.ignore_save is True


def test_heavy_only_applies_when_stationary() -> None:
    weapon = make_weapon(tags=["heavy"])
    mods = build_weapon_modifiers(weapon)

    stationary = apply_modifiers(
        "hit_roll",
        4,
        mods,
        make_context(weapon=weapon, is_stationary=True),
        np.random.default_rng(42),
    )
    moved = apply_modifiers(
        "hit_roll",
        4,
        mods,
        make_context(weapon=weapon, is_stationary=False),
        np.random.default_rng(42),
    )

    assert stationary.target_value == 3
    assert moved.target_value == 4


def test_half_range_condition() -> None:
    weapon = make_weapon(range_max=24)
    mods = [Modifier("attack_count", "add", 1, condition={"half_range": True})]

    near = apply_modifiers(
        "attack_count",
        3,
        mods,
        make_context(weapon=weapon, distance=12),
        np.random.default_rng(42),
    )
    far = apply_modifiers(
        "attack_count",
        3,
        mods,
        make_context(weapon=weapon, distance=13),
        np.random.default_rng(42),
    )

    assert near.target_value == 2
    assert far.target_value == 3


def test_build_weapon_modifiers_maps_tags() -> None:
    weapon = make_weapon(tags=["torrent", "sustained_hits_2", "lethal_hits", "devastating_wounds", "ignores_cover"])
    mods = build_weapon_modifiers(weapon)

    assert any(mod.operation == "auto_hit" for mod in mods)
    assert any(mod.operation == "sustained_hits" and mod.value == 2 for mod in mods)
    assert any(mod.operation == "lethal_hits" for mod in mods)
    assert any(mod.operation == "devastating_wounds" for mod in mods)
    assert any(mod.operation == "ignore_cover" for mod in mods)


def test_twin_linked_grants_wound_reroll() -> None:
    weapon = make_weapon(tags=["twin-linked"])
    mods = build_weapon_modifiers(weapon)
    result = apply_modifiers(
        "wound_roll",
        4,
        mods,
        make_context(weapon=weapon),
        np.random.default_rng(42),
    )
    assert result.reroll is True


def test_should_reroll() -> None:
    assert should_reroll(1, 4, [Modifier("hit_roll", "reroll_ones_hit")], "hit_roll") is True
    assert should_reroll(2, 4, [Modifier("hit_roll", "reroll_ones_hit")], "hit_roll") is False
    assert should_reroll(3, 4, [Modifier("wound_roll", "reroll_wounds")], "wound_roll") is True
