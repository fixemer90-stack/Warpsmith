import numpy as np
import pytest

from backend.model.unit import Weapon, dice_expr_to_str, parse_dice_expression, resolve_dice


def test_parse_dice_expression() -> None:
    assert parse_dice_expression("D6") == (1, 6, 0)
    assert parse_dice_expression("2D3") == (2, 3, 0)
    assert parse_dice_expression("D6+2") == (1, 6, 2)
    assert parse_dice_expression("3") == (0, 0, 3)
    assert parse_dice_expression("2D3+1") == (2, 3, 1)
    assert parse_dice_expression("Melee") == (0, 0, 0)


def test_resolve_dice() -> None:
    rng = np.random.default_rng(42)

    d6 = resolve_dice((1, 6, 0), rng)
    fixed = resolve_dice((0, 0, 3), rng)
    two_d3_plus_one = resolve_dice((2, 3, 1), rng)

    assert 1 <= d6 <= 6
    assert fixed == 3
    assert 3 <= two_d3_plus_one <= 7


def test_dice_expr_to_str() -> None:
    assert dice_expr_to_str((1, 6, 0)) == "D6"
    assert dice_expr_to_str((2, 3, 1)) == "2D3+1"
    assert dice_expr_to_str((0, 0, 3)) == "3"


def test_weapon_ranged_fields() -> None:
    weapon = Weapon(
        name="Shoota",
        type="ranged",
        range_max=18,
        attacks_dice=(0, 0, 3),
        skill=5,
        strength=4,
        ap=0,
        damage_dice=(0, 0, 1),
        tags=["assault"],
    )

    assert weapon.range_max == 18
    assert weapon.attacks_dice == (0, 0, 3)
    assert weapon.damage_dice == (0, 0, 1)
    assert weapon.tags == ["assault"]


def test_weapon_melee_rejects_range() -> None:
    with pytest.raises(ValueError, match="melee weapons must not define range_max"):
        Weapon(
            name="Power Fist",
            type="melee",
            range_max=1,
            attacks_dice=(0, 0, 3),
            skill=4,
            strength=8,
            ap=-2,
            damage_dice=(0, 0, 2),
        )
