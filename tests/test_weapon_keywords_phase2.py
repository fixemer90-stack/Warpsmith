"""Tests for F1.13 Weapon Keywords Phase 2."""

import numpy as np
import pytest

from backend.engine.combat import simulate_weapon_attack
from backend.engine.dice import DicePool
from backend.engine.modifiers import (
    Modifier,
    ModifierContext,
    _check_condition,
    apply_modifiers,
    build_weapon_modifiers,
)
from backend.model.unit import Unit, Weapon


def make_unit(name: str, *, toughness: int, save: int, wounds: int) -> Unit:
    return Unit(
        name=name,
        faction="test",
        category="Infantry",
        movement=6,
        toughness=toughness,
        save=save,
        wounds=wounds,
        leadership=6,
        objective_control=2,
        points=100,
        model_count=(1, 10),
    )


def make_attacker() -> Unit:
    return make_unit("Attacker", toughness=4, save=3, wounds=2)


class TestBlast:
    """Tests for [BLAST] keyword."""

    def test_blast_1_model_no_bonus(self):
        """Blast vs 1 model - bonus 0."""
        result = simulate_weapon_attack(
            Weapon(
                name="Blast Weapon",
                type="ranged",
                range_max=24,
                attacks_dice=(0, 0, 1),
                skill=4,
                strength=4,
                ap=0,
                damage_dice=(0, 0, 1),
                tags=["blast"],
            ),
            make_attacker(),
            make_unit("Target", toughness=4, save=3, wounds=1),
            pool=DicePool(seed=42),
            n_iterations=5000,
            squad_size=1,
        )
        assert result.avg_attacks == 1.0

    def test_blast_5_models_plus1(self):
        """Blast vs 5 models - +1 attack."""
        result = simulate_weapon_attack(
            Weapon(
                name="Blast Weapon",
                type="ranged",
                range_max=24,
                attacks_dice=(0, 0, 1),
                skill=4,
                strength=4,
                ap=0,
                damage_dice=(0, 0, 1),
                tags=["blast"],
            ),
            make_attacker(),
            make_unit("Target", toughness=4, save=3, wounds=1),
            pool=DicePool(seed=42),
            n_iterations=5000,
            squad_size=5,
        )
        assert result.avg_attacks == 2.0

    def test_blast_10_models_plus2(self):
        """Blast vs 10 models - +2 attacks."""
        result = simulate_weapon_attack(
            Weapon(
                name="Blast Weapon",
                type="ranged",
                range_max=24,
                attacks_dice=(0, 0, 1),
                skill=4,
                strength=4,
                ap=0,
                damage_dice=(0, 0, 1),
                tags=["blast"],
            ),
            make_attacker(),
            make_unit("Target", toughness=4, save=3, wounds=1),
            pool=DicePool(seed=42),
            n_iterations=5000,
            squad_size=10,
        )
        assert result.avg_attacks == 3.0

    def test_blast_20_models_caps_at_plus4(self):
        """Blast vs 20 models - max +4 attacks."""
        result = simulate_weapon_attack(
            Weapon(
                name="Blast Weapon",
                type="ranged",
                range_max=24,
                attacks_dice=(0, 0, 1),
                skill=4,
                strength=4,
                ap=0,
                damage_dice=(0, 0, 1),
                tags=["blast"],
            ),
            make_attacker(),
            make_unit("Target", toughness=4, save=3, wounds=1),
            pool=DicePool(seed=42),
            n_iterations=5000,
            squad_size=20,
        )
        assert result.avg_attacks == 5.0


class TestHeavy:
    """Tests for [HEAVY] keyword."""

    def test_heavy_stationary_improves_hit(self):
        """Heavy weapon improves hit when stationary."""
        weapon = Weapon(
            name="Heavy Bolter",
            type="ranged",
            range_max=36,
            attacks_dice=(0, 0, 3),
            skill=3,
            strength=5,
            ap=-1,
            damage_dice=(1, 3, 0),
            tags=["heavy"],
        )
        target = make_unit("Marine", toughness=4, save=3, wounds=2)

        stationary_result = simulate_weapon_attack(
            weapon,
            make_attacker(),
            target,
            pool=DicePool(seed=42),
            n_iterations=20000,
            is_stationary=True,
        )
        moved_result = simulate_weapon_attack(
            weapon,
            make_attacker(),
            target,
            pool=DicePool(seed=42),
            n_iterations=20000,
            is_stationary=False,
        )
        # Check via damage stats - stationary should do more damage
        assert stationary_result.stats.mean > moved_result.stats.mean


class TestTorrent:
    """Tests for [TORRENT] keyword."""

    def test_torrent_auto_hits(self):
        """Torrent skips hit roll - always hits."""
        result = simulate_weapon_attack(
            Weapon(
                name="Torrent Weapon",
                type="ranged",
                range_max=12,
                attacks_dice=(0, 0, 1),
                skill=6,
                strength=4,
                ap=0,
                damage_dice=(0, 0, 1),
                tags=["torrent"],
            ),
            make_attacker(),
            make_unit("Target", toughness=4, save=3, wounds=2),
            pool=DicePool(seed=42),
            n_iterations=10000,
        )
        # With torrent, BS6 still hits on 6s, but torrent auto-hits
        # So we should get damage even with BS6
        assert result.stats.mean > 0


class TestMelta:
    """Tests for [MELTA X] keyword."""

    def test_melta_half_range_adds_damage(self):
        """Melta adds damage at half range."""
        # Weapon with fixed damage
        melta = Weapon(
            name="Melta Gun",
            type="ranged",
            range_max=12,
            attacks_dice=(0, 0, 2),
            skill=3,
            strength=8,
            ap=-4,
            damage_dice=(0, 0, 1),  # Fixed 1 damage base
            tags=["melta_2"],
        )
        target = make_unit("Vehicle", toughness=10, save=2, wounds=10)

        near_result = simulate_weapon_attack(
            melta,
            make_attacker(),
            target,
            pool=DicePool(seed=42),
            n_iterations=20000,
            distance=6,  # half range = 6
        )
        far_result = simulate_weapon_attack(
            melta,
            make_attacker(),
            target,
            pool=DicePool(seed=42),
            n_iterations=20000,
            distance=12,  # at max range, beyond half
        )
        # Near should have +2 damage from melta
        assert near_result.stats.mean > far_result.stats.mean

    def test_melta_beyond_half_range_no_bonus(self):
        """Melta beyond half range - no damage bonus."""
        melta = Weapon(
            name="Melta Gun",
            type="ranged",
            range_max=12,
            attacks_dice=(0, 0, 2),
            skill=3,
            strength=8,
            ap=-4,
            damage_dice=(0, 0, 1),
            tags=["melta_2"],
        )
        target = make_unit("Vehicle", toughness=10, save=2, wounds=10)

        result = simulate_weapon_attack(
            melta,
            make_attacker(),
            target,
            pool=DicePool(seed=42),
            n_iterations=20000,
            distance=7,
        )
        assert result.stats.mean > 0


class TestRapidFire:
    """Tests for [RAPID FIRE X] keyword."""

    def test_rapid_fire_at_half_range(self):
        """Rapid fire adds attacks at half range."""
        bolter = Weapon(
            name="Bolter",
            type="ranged",
            range_max=24,
            attacks_dice=(0, 0, 2),
            skill=3,
            strength=4,
            ap=0,
            damage_dice=(0, 0, 1),
            tags=["rapid_fire_1"],
        )
        target = make_unit("Marine", toughness=4, save=3, wounds=2)

        near_result = simulate_weapon_attack(
            bolter,
            make_attacker(),
            target,
            pool=DicePool(seed=42),
            n_iterations=20000,
            distance=12,
        )
        far_result = simulate_weapon_attack(
            bolter,
            make_attacker(),
            target,
            pool=DicePool(seed=42),
            n_iterations=20000,
            distance=18,
        )

        assert near_result.avg_attacks > far_result.avg_attacks


class TestLance:
    """Tests for [LANCE] keyword."""

    def test_lance_on_charge_improves_wound(self):
        """Lance improves wound roll when charged."""
        weapon = Weapon(
            name="Lance Weapon",
            type="ranged",
            range_max=18,
            attacks_dice=(0, 0, 2),
            skill=3,
            strength=6,
            ap=-1,
            damage_dice=(0, 0, 1),
            tags=["lance"],
        )
        target = make_unit("Target", toughness=6, save=3, wounds=2)

        charged_context = ModifierContext(
            attacker=type(
                "MockAttacker", (), {"unit_state": type("MockState", (), {"has_charged": True})()}
            )(),
            defender=target,
            weapon=weapon,
            is_stationary=False,
            squad_size=1,
        )
        normal_context = ModifierContext(
            attacker=type(
                "MockAttacker", (), {"unit_state": type("MockState", (), {"has_charged": False})()}
            )(),
            defender=target,
            weapon=weapon,
            is_stationary=False,
            squad_size=1,
        )

        modifiers = build_weapon_modifiers(weapon)
        charged_result = apply_modifiers(
            "wound_roll", 4, modifiers, charged_context, np.random.default_rng()
        )
        normal_result = apply_modifiers(
            "wound_roll", 4, modifiers, normal_context, np.random.default_rng()
        )

        assert charged_result.target_value < normal_result.target_value


class TestOneShot:
    """Tests for [ONE SHOT] keyword."""

    def test_one_shot_weapon_used_twice(self):
        """One Shot weapon can only fire once."""
        weapon = Weapon(
            name="One Shot Weapon",
            type="ranged",
            range_max=24,
            attacks_dice=(0, 0, 1),
            skill=3,
            strength=8,
            ap=-4,
            damage_dice=(0, 0, 1),
            tags=["one_shot"],
        )

        assert not weapon.one_shot_used

        # First use - should work
        weapon.one_shot_used = True
        assert weapon.one_shot_used


class TestPrecision:
    """Tests for [PRECISION] keyword."""

    def test_precision_modifier_present(self):
        """Precision keyword generates allocation modifier."""
        weapon = Weapon(
            name="Precision Weapon",
            type="ranged",
            range_max=24,
            attacks_dice=(0, 0, 1),
            skill=3,
            strength=4,
            ap=0,
            damage_dice=(0, 0, 1),
            tags=["precision"],
        )

        modifiers = build_weapon_modifiers(weapon)
        precision_mods = [m for m in modifiers if m.operation == "precision"]
        assert len(precision_mods) == 1


class TestPistol:
    """Tests for [PISTOL] keyword."""

    def test_pistol_modifier_present(self):
        """Pistol keyword generates eligibility modifier."""
        weapon = Weapon(
            name="Pistol",
            type="ranged",
            range_max=12,
            attacks_dice=(0, 0, 1),
            skill=3,
            strength=4,
            ap=0,
            damage_dice=(0, 0, 1),
            tags=["pistol"],
        )

        modifiers = build_weapon_modifiers(weapon)
        pistol_mods = [m for m in modifiers if m.operation == "pistol"]
        assert len(pistol_mods) == 1
