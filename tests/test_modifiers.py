import numpy as np

from backend.engine.modifiers import (
    AntiKeyword,
    CriticalEffect,
    Modifier,
    ModifierContext,
    apply_modifiers,
    build_weapon_modifiers,
    handle_critical_hit,
    parse_anti_tag,
    resolve_anti_wound,
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


def make_context(
    *,
    weapon: Weapon | None = None,
    distance: int | None = 12,
    is_stationary: bool = False,
    squad_size: int = 1,
) -> ModifierContext:
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


def test_lethal_hits_does_not_auto_succeed() -> None:
    """Lethal Hits does not make hits auto-succeed — it only auto-wounds on Critical Hits."""
    mods = [Modifier("hit_roll", "lethal_hits")]
    result = apply_modifiers("hit_roll", 4, mods, make_context(), np.random.default_rng(42))
    assert result.auto_success is False


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

    assert near.target_value == 4
    assert far.target_value == 3


def test_build_weapon_modifiers_maps_tags() -> None:
    weapon = make_weapon(
        tags=["torrent", "sustained_hits_2", "lethal_hits", "devastating_wounds", "ignores_cover"]
    )
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


def test_handle_critical_hit_sustained() -> None:
    weapon = make_weapon(tags=["sustained_hits_1"])
    modifiers = build_weapon_modifiers(weapon)

    critical = handle_critical_hit(
        type("Roll", (), {"is_crit": True})(), "hit_roll", modifiers, None
    )

    assert critical == CriticalEffect(extra_attacks=1)


def test_handle_critical_hit_lethal() -> None:
    weapon = make_weapon(tags=["lethal_hits"])
    modifiers = build_weapon_modifiers(weapon)

    critical = handle_critical_hit(
        type("Roll", (), {"is_crit": True})(), "hit_roll", modifiers, None
    )

    assert critical.auto_wound is True


def test_handle_critical_hit_devastating() -> None:
    weapon = make_weapon(tags=["devastating_wounds"])
    modifiers = build_weapon_modifiers(weapon)

    critical = handle_critical_hit(
        type("Roll", (), {"is_crit": True})(), "wound_roll", modifiers, None
    )

    assert critical.ignore_save is True


def test_parse_anti_tag() -> None:
    anti = parse_anti_tag("anti_infantry_4")

    assert anti == AntiKeyword(threshold=4, target_keyword="Infantry")


def test_resolve_anti_wound() -> None:
    anti = AntiKeyword(threshold=4, target_keyword="Infantry")
    defender = make_unit()
    defender.keywords.append("Infantry")

    assert resolve_anti_wound(4, anti, defender) is True
    assert resolve_anti_wound(3, anti, defender) is False


def test_build_weapon_modifiers_supports_blast() -> None:
    weapon = make_weapon(tags=["blast"])
    modifiers = build_weapon_modifiers(weapon)

    assert any(mod.target == "attack_count" and mod.operation == "blast_bonus" for mod in modifiers)


# ── Lethal Hits semantics tests (task-03-01) ──


class SequenceRNG:
    """Returns values from a sequence, one per call. Repeats last value if exhausted."""

    def __init__(self, *values: int):
        self._values = list(values)
        self._idx = 0

    def integers(self, low: int, high: int | None = None, size: int | None = None):
        del low, high
        val = self._values[min(self._idx, len(self._values) - 1)]
        self._idx += 1
        if size is None:
            return val
        return np.full(size, val, dtype=int)


class SequencePool:
    """DicePool-like that uses a SequenceRNG for deterministic multi-roll tests."""

    def __init__(self, *values: int):
        self.values = values

    def simulate(self, func, n: int):
        result = np.zeros(n, dtype=int)
        for i in range(n):
            rng = SequenceRNG(*self.values)
            result[i] = func(rng)
        return result


def test_plain_natural_6_requires_wound_roll() -> None:
    """Natural 6 to hit without Lethal Hits does NOT auto-wound.
    Hit=6 succeeds; Wound roll=1 fails → 0 damage."""
    from backend.engine.combat import _resolve_attack_chain, _resolve_hit_roll

    weapon = Weapon(
        name="Test Gun",
        type="ranged",
        range_max=24,
        attacks_dice=(0, 0, 1),
        skill=4,
        strength=4,
        ap=0,
        damage_dice=(0, 0, 1),
        tags=[],  # No Lethal Hits
    )
    attacker = make_unit("Attacker")
    defender = make_unit("Defender")
    defender.toughness = 10  # S4 vs T10 → wounds on 6+
    all_mods = build_weapon_modifiers(weapon)
    ctx = ModifierContext(attacker, defender, weapon, 12, False, 1)

    # Hit=6 (success, crit), Wound=1 (fail)
    rng = SequenceRNG(6, 1)
    hit_result, _ = _resolve_hit_roll(rng, weapon, all_mods, ctx)
    assert hit_result.success, "Natural 6 should hit"
    assert hit_result.is_crit, "Natural 6 is a Critical Hit"

    damage = _resolve_attack_chain(rng, weapon, defender, all_mods, ctx)
    assert damage == 0, "Without Lethal Hits, natural 6 hit still requires wound roll"


def test_lethal_hits_natural_6_auto_wounds() -> None:
    """Lethal Hits + natural 6 hit skips wound roll and deals damage."""
    from backend.engine.combat import _resolve_attack_chain

    weapon = Weapon(
        name="Lethal Gun",
        type="ranged",
        range_max=24,
        attacks_dice=(0, 0, 1),
        skill=4,
        strength=4,
        ap=-2,
        damage_dice=(0, 0, 1),
        tags=["lethal_hits"],
    )
    attacker = make_unit("Attacker")
    defender = make_unit("Defender")
    defender.toughness = 10  # Would need 6+ to wound, but Lethal Hits skips that
    all_mods = build_weapon_modifiers(weapon)
    ctx = ModifierContext(attacker, defender, weapon, 12, False, 1)

    # Hit=6 (success, crit) → Lethal Hits triggers auto-wound → save/damage
    # Save: SV3+ with AP-2 = 5+, roll 2 fails → damage 1
    rng = SequenceRNG(6, 2, 0)
    damage = _resolve_attack_chain(rng, weapon, defender, all_mods, ctx)
    assert damage == 1, "Lethal Hits natural 6 should auto-wound and deal damage"


def test_lethal_hits_non_6_normal_wound_roll() -> None:
    """Lethal Hits on a non-critical hit (roll 4) still requires normal wound roll."""
    from backend.engine.combat import _resolve_attack_chain

    weapon = Weapon(
        name="Lethal Gun",
        type="ranged",
        range_max=24,
        attacks_dice=(0, 0, 1),
        skill=4,
        strength=4,
        ap=0,
        damage_dice=(0, 0, 1),
        tags=["lethal_hits"],
    )
    attacker = make_unit("Attacker")
    defender = make_unit("Defender")
    defender.toughness = 8  # S4 vs T8 → wounds on 6+
    all_mods = build_weapon_modifiers(weapon)
    ctx = ModifierContext(attacker, defender, weapon, 12, False, 1)

    # Hit=4 (success, not crit), Wound=3 (fail: 3 < 6) → 0 damage
    rng = SequenceRNG(4, 3)
    damage = _resolve_attack_chain(rng, weapon, defender, all_mods, ctx)
    assert damage == 0, (
        "Lethal Hits should NOT auto-wound on non-6 hits — wound roll must succeed normally"
    )


def test_plain_critical_hit_no_auto_wound_without_lethal() -> None:
    """A Critical Hit (natural 6) without Lethal Hits does NOT auto-wound.
    Wound roll fails → 0 damage."""
    from backend.engine.combat import _resolve_attack_chain, _resolve_hit_roll

    weapon = Weapon(
        name="Basic Gun",
        type="ranged",
        range_max=24,
        attacks_dice=(0, 0, 1),
        skill=4,
        strength=4,
        ap=0,
        damage_dice=(0, 0, 1),
        tags=[],  # No special rules
    )
    attacker = make_unit("Attacker")
    defender = make_unit("Defender")
    defender.toughness = 8  # S4 vs T8 → wounds on 6+
    all_mods = build_weapon_modifiers(weapon)
    ctx = ModifierContext(attacker, defender, weapon, 12, False, 1)

    # Hit=6 (critical), Wound=2 (fail) → 0 damage
    rng = SequenceRNG(6, 2)
    hit_result, _ = _resolve_hit_roll(rng, weapon, all_mods, ctx)
    assert hit_result.success and hit_result.is_crit, "Should hit critically"
    damage = _resolve_attack_chain(rng, weapon, defender, all_mods, ctx)
    assert damage == 0, "Plain Critical Hit should NOT auto-wound — wound roll still required"


def test_lethal_hits_bypasses_wound_but_proceeds_to_save() -> None:
    """Lethal Hits auto-wound still goes through save/damage steps normally."""
    from backend.engine.combat import _resolve_attack_chain

    weapon = Weapon(
        name="Lethal Gun",
        type="ranged",
        range_max=24,
        attacks_dice=(0, 0, 1),
        skill=4,
        strength=4,
        ap=0,
        damage_dice=(0, 0, 1),
        tags=["lethal_hits"],
    )
    attacker = make_unit("Attacker")
    defender = make_unit("Defender")
    defender.toughness = 10
    all_mods = build_weapon_modifiers(weapon)
    ctx = ModifierContext(attacker, defender, weapon, 12, False, 1)

    # Hit=6 (crit, Lethal triggers), Save=6 (passes SV3+ → saved) → 0 damage
    rng = SequenceRNG(6, 6)
    damage = _resolve_attack_chain(rng, weapon, defender, all_mods, ctx)
    assert damage == 0, "Lethal Hits auto-wound should still be saveable"


def test_mixed_attack_pool_lethal_hits() -> None:
    """Two attacks: one natural 6 (Lethal auto-wound), one normal hit (roll to wound)."""
    from backend.engine.combat import _resolve_attack_chain

    weapon = Weapon(
        name="Lethal Gun",
        type="ranged",
        range_max=24,
        attacks_dice=(0, 0, 2),  # 2 attacks
        skill=4,
        strength=4,
        ap=-2,
        damage_dice=(0, 0, 1),
        tags=["lethal_hits"],
    )
    attacker = make_unit("Attacker")
    defender = make_unit("Defender")
    defender.toughness = 8  # S4 vs T8 → wounds on 6+
    all_mods = build_weapon_modifiers(weapon)
    ctx = ModifierContext(attacker, defender, weapon, 12, False, 1)

    # Attack 1: Hit=6 (crit → auto-wound), Save=2 (fail SV5+ after AP-2) → damage
    # Attack 2: Hit=4 (success, not crit), Wound=6 (success), Save=6 (pass) → saved
    pool = SequencePool(6, 2, 4, 6, 6)
    result = pool.simulate(
        lambda rng: _resolve_attack_chain(rng, weapon, defender, all_mods, ctx), 10
    )
    assert np.all(result == 1), (
        f"Mixed pool: expected 1 damage (only lethal auto-wound gets through save), got {result}"
    )


def test_lethal_hits_with_devastating_wounds_no_save_bypass() -> None:
    """Lethal Hits auto-wound is NOT a Critical Wound — Devastating Wounds does NOT trigger.
    Save applies normally even when the weapon has both Lethal Hits and Devastating Wounds."""
    from backend.engine.combat import _resolve_attack_chain

    weapon = Weapon(
        name="Lethal+Dev Gun",
        type="ranged",
        range_max=24,
        attacks_dice=(0, 0, 1),
        skill=4,
        strength=4,
        ap=0,
        damage_dice=(0, 0, 1),
        tags=["lethal_hits", "devastating_wounds"],
    )
    attacker = make_unit("Attacker")
    defender = make_unit("Defender")
    defender.toughness = 10
    all_mods = build_weapon_modifiers(weapon)
    ctx = ModifierContext(attacker, defender, weapon, 12, False, 1)

    # Hit=6 (crit → Lethal Hits auto-wound, NOT a critical wound)
    # Devastating Wounds should NOT trigger (no wound roll was made)
    # Save=6 (passes SV3+ → saved) → 0 damage
    rng = SequenceRNG(6, 6)
    damage = _resolve_attack_chain(rng, weapon, defender, all_mods, ctx)
    assert damage == 0, (
        "Lethal Hits auto-wound with Devastating Wounds should still allow normal save. "
        "Devastating Wounds only triggers on actual Critical Wound rolls."
    )
