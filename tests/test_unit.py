import pytest

from backend.model.unit import Unit, WargearSlot


def make_unit(**overrides: object) -> Unit:
    data = {
        "name": "Tactical Marine",
        "faction": "adeptus_astartes",
        "category": "Infantry",
        "movement": 6,
        "toughness": 4,
        "save": 3,
        "wounds": 2,
        "leadership": 6,
        "objective_control": 2,
        "points": 90,
        "model_count": (5, 10),
    }
    data.update(overrides)
    return Unit(**data)


def test_effective_toughness() -> None:
    marine = make_unit(toughness=4)

    assert marine.effective_toughness(8) == 2
    assert marine.effective_toughness(5) == 3
    assert marine.effective_toughness(4) == 4
    assert marine.effective_toughness(3) == 5
    assert marine.effective_toughness(2) == 6


def test_best_save_with_invulnerable_save() -> None:
    terminator = make_unit(name="Terminator", save=2, invulnerable_save=4)

    assert terminator.best_save(-3) == 4
    assert terminator.best_save(-1) == 3


def test_max_wounds_in_squad() -> None:
    marine = make_unit(wounds=2)

    assert marine.max_wounds_in_squad(5) == 10
    assert marine.max_wounds_in_squad(10) == 20


@pytest.mark.parametrize("save", [1, 8])
def test_invalid_save_rejected(save: int) -> None:
    """Test that invalid save values are rejected."""
    with pytest.raises(ValueError, match="save must be between 2 and 7"):
        make_unit(save=save)


def test_optional_fields_and_wargear_slot_defaults() -> None:
    unit = make_unit(
        invulnerable_save=4,
        feel_no_pain=5,
        wargear_options=[
            WargearSlot(
                slot_name="ranged_1",
                choices=["shoota", "big shoota"],
            )
        ],
        transports=["Trukk"],
    )

    assert unit.invulnerable_save == 4
    assert unit.feel_no_pain == 5
    assert unit.wargear_options[0].default_index == 0
    assert unit.transports == ["Trukk"]
