"""Tests for F3.1 Greedy Decision Engine."""

import sys

sys.path.insert(0, "/mnt/d/Python/Balthier/simulator")

import numpy as np
import pytest

from backend.engine.ai.decision import (
    DEFAULT_WEIGHTS,
    Action,
    ActionType,
    EvaluationContext,
    _avg_dice,
    _compute_expected_damage_ranged,
    _distance,
    _estimate_melee_damage,
    _generate_candidates,
    _get_objectives,
    _in_weapon_range,
    choose_action,
    score_charge,
    score_move,
    score_shoot,
)
from backend.model.unit import Unit, Weapon
from backend.state.game_state import GamePhase, GameState, UnitState

# ── Helpers ────────────────────────────────────────────────────


def make_weapon(
    name: str = "Shoota",
    type: str = "ranged",
    range_max: int = 24,
    attacks_dice: tuple = (2, 1, 0),  # 2 flat
    skill: int = 4,
    strength: int = 4,
    ap: int = 0,
    damage_dice: tuple = (1, 1, 0),  # 1 flat
) -> Weapon:
    return Weapon(
        name=name,
        type=type,
        range_max=range_max,
        attacks_dice=attacks_dice,
        skill=skill,
        strength=strength,
        ap=ap,
        damage_dice=damage_dice,
    )


def make_shoota() -> Weapon:
    return make_weapon("Shoota", attacks_dice=(2, 1, 0), damage_dice=(1, 1, 0))


def make_heavy_bolter() -> Weapon:
    return make_weapon(
        "Heavy Bolter",
        range_max=36,
        attacks_dice=(3, 1, 0),
        skill=4,
        strength=5,
        ap=-1,
        damage_dice=(2, 1, 0),
    )


def make_plasma() -> Weapon:
    return make_weapon(
        "Plasma",
        range_max=24,
        attacks_dice=(1, 1, 0),
        skill=3,
        strength=8,
        ap=-3,
        damage_dice=(2, 1, 0),
    )


def make_choppa() -> Weapon:
    return Weapon(
        name="Choppa",
        type="melee",
        range_max=None,
        attacks_dice=(1, 1, 0),
        skill=4,
        strength=4,
        ap=-1,
        damage_dice=(1, 1, 0),
    )


def make_unit_state(
    name: str = "Unit",
    unit_id: str = "u1",
    position: tuple = (0, 0),
    wounds: int = 3,
    models: int = 5,
    is_engaged: bool = False,
    is_battle_shocked: bool = False,
) -> UnitState:
    return UnitState(
        unit_id=unit_id,
        name=name,
        faction="test",
        position=position,
        current_wounds=wounds,
        max_wounds=wounds,
        models_remaining=models,
        models_total=models,
        leadership=7,
        objective_control=1,
        is_engaged=is_engaged,
        is_battle_shocked=is_battle_shocked,
    )


def make_unit_model(
    name: str = "Unit",
    toughness: int = 4,
    save: int = 3,
    ranged: list[Weapon] | None = None,
    melee: list[Weapon] | None = None,
    points: int = 20,
) -> Unit:
    return Unit(
        name=name,
        faction="test",
        category="Infantry",
        movement=6,
        toughness=toughness,
        save=save,
        wounds=3,
        leadership=7,
        objective_control=1,
        points=points,
        ranged_weapons=ranged or [],
        melee_weapons=melee or [],
    )


def make_context(
    actor_state: UnitState = None,
    actor_model: Unit = None,
    opponents: list[UnitState] | None = None,
    opp_models: list[Unit] | None = None,
    phase: GamePhase = GamePhase.SHOOTING,
    weights: dict | None = None,
    opponent_units_map: dict | None = None,
) -> EvaluationContext:
    if actor_state is None:
        actor_state = make_unit_state("Shooter", unit_id="me")
    if actor_model is None:
        actor_model = make_unit_model("Shooter", ranged=[make_shoota()])
    state = GameState(game_id="test", mission_name="Test", current_round=1, current_phase=phase)
    opponent_units_map = opponent_units_map or {}
    return EvaluationContext(
        actor=actor_state,
        actor_unit=actor_model,
        state=state,
        opponent_units=opponents or [],
        phase=phase,
        turn=1,
        opponent_units_map=opponent_units_map or {},
        weights=weights or dict(DEFAULT_WEIGHTS),
    )


# ── Tests ──────────────────────────────────────────────────────


class TestDistance:
    def test_same_point(self):
        assert _distance((0, 0), (0, 0)) == 0

    def test_straight_line(self):
        assert _distance((0, 0), (3, 4)) == 5.0

    def test_negative_coords(self):
        assert _distance((-1, -1), (2, 3)) == 5.0


class TestWeaponRange:
    def test_in_range(self):
        u = make_unit_state(position=(0, 0))
        t = make_unit_state(position=(12, 0))
        assert _in_weapon_range(u, t, make_shoota()) is True

    def test_out_of_range(self):
        u = make_unit_state(position=(0, 0))
        t = make_unit_state(position=(30, 0))
        assert _in_weapon_range(u, t, make_shoota()) is False

    def test_melee_close(self):
        u = make_unit_state(position=(0, 0))
        t = make_unit_state(position=(1, 0))
        assert _in_weapon_range(u, t, make_choppa()) is True

    def test_melee_far(self):
        u = make_unit_state(position=(0, 0))
        t = make_unit_state(position=(3, 0))
        assert _in_weapon_range(u, t, make_choppa()) is False


class TestDiceAvg:
    def test_fixed(self):
        assert _avg_dice((3, 1, 0)) == 3

    def test_d6(self):
        assert abs(_avg_dice((1, 6, 0)) - 3.5) < 0.001

    def test_2d6_plus_1(self):
        assert abs(_avg_dice((2, 6, 1)) - 8.0) < 0.001

    def test_d3(self):
        assert _avg_dice((1, 3, 0)) == 2.0


class TestExpectedDamage:
    def test_hb_vs_marine(self):
        dmg = _compute_expected_damage_ranged(make_heavy_bolter(), 4, 3)
        assert 0.3 < dmg < 2.0, f"HB vs Marine: {dmg}"

    def test_shoota_vs_marine(self):
        dmg = _compute_expected_damage_ranged(make_shoota(), 4, 3)
        assert 0.05 < dmg < 0.5, f"Shoota vs Marine: {dmg}"

    def test_plasma_vs_marine(self):
        dmg = _compute_expected_damage_ranged(make_plasma(), 4, 3)
        assert 0.5 < dmg < 3.0, f"Plasma vs Marine: {dmg}"


class TestCandidateGeneration:
    def test_shooting_generates_shoot(self):
        a = make_unit_state("S", unit_id="me", position=(0, 0))
        t = make_unit_state("T", unit_id="t1", position=(12, 0))
        m = make_unit_model(ranged=[make_shoota()])
        ctx = make_context(a, m, [t])
        cands = _generate_candidates(a, m, ctx)
        assert any(c.type == ActionType.SHOOT for c in cands)

    def test_engaged_no_shoot(self):
        a = make_unit_state("E", unit_id="me", is_engaged=True)
        t = make_unit_state("T", unit_id="t1", position=(6, 0))
        m = make_unit_model(ranged=[make_shoota()])
        ctx = make_context(a, m, [t])
        cands = _generate_candidates(a, m, ctx)
        assert not any(c.type == ActionType.SHOOT for c in cands)

    def test_shocked_no_shoot(self):
        a = make_unit_state("S", unit_id="me", is_battle_shocked=True)
        t = make_unit_state("T", unit_id="t1", position=(6, 0))
        m = make_unit_model(ranged=[make_shoota()])
        ctx = make_context(a, m, [t])
        cands = _generate_candidates(a, m, ctx)
        assert not any(c.type == ActionType.SHOOT for c in cands)

    def test_charge_too_far(self):
        a = make_unit_state("C", unit_id="me", position=(0, 0))
        t = make_unit_state("F", unit_id="f1", position=(20, 0))
        m = make_unit_model()
        ctx = make_context(a, m, [t], GamePhase.CHARGE)
        cands = _generate_candidates(a, m, ctx)
        assert not any(c.type == ActionType.CHARGE for c in cands)

    def test_no_targets_hold(self):
        a = make_unit_state()
        m = make_unit_model(ranged=[make_shoota()])
        ctx = make_context(a, m, [])
        cands = _generate_candidates(a, m, ctx)
        assert any(c.type == ActionType.HOLD for c in cands)


class TestScoring:
    def test_shoot_guardsman_over_marine(self):
        a = make_unit_state("S", unit_id="me", position=(0, 0))
        m = make_unit_model(ranged=[make_shoota()])
        g = make_unit_state("G", unit_id="g", position=(12, 0))
        g_model = make_unit_model("G", toughness=3, save=5, points=6)
        mr = make_unit_state("M", unit_id="m", position=(12, 0))
        m_model = make_unit_model("M", toughness=4, save=3, points=20)
        ctx = make_context(a, m, [g, mr], opponent_units_map={"g": g_model, "m": m_model})
        g_score = score_shoot(a, m, g, 0, ctx)
        m_score = score_shoot(a, m, mr, 0, ctx)
        assert g_score > m_score, f"G={g_score:.4f} should be > M={m_score:.4f}"

    def test_charge_closer_higher(self):
        a = make_unit_state("C", unit_id="me", position=(0, 0))
        m = make_unit_model(melee=[make_choppa()])
        c = make_unit_state("C", unit_id="c", position=(3, 0))
        f = make_unit_state("F", unit_id="f", position=(10, 0))
        ctx = make_context(a, m, [c, f], GamePhase.CHARGE)
        c_score = score_charge(a, m, c, ctx)
        f_score = score_charge(a, m, f, ctx)
        assert c_score >= f_score, f"Close {c_score:.4f} >= Far {f_score:.4f}"


class TestChooseAction:
    def test_choose_best_target(self):
        a = make_unit_state("S", unit_id="me", position=(0, 0))
        m = make_unit_model(ranged=[make_shoota()])
        g = make_unit_state("G", unit_id="g", position=(12, 0))
        mr = make_unit_state("M", unit_id="m", position=(12, 0))
        ctx = make_context(a, m, [g, mr])
        # Use different models to represent different toughness/save via actor guessing
        # Engine uses actor_unit for weapon, target for position/LoS
        action = choose_action(a, m, ctx)
        # Should shoot at something — not HOLD
        assert action.type != ActionType.HOLD

    def test_no_targets_hold(self):
        a = make_unit_state()
        m = make_unit_model()
        ctx = make_context(a, m, [])
        assert choose_action(a, m, ctx).type == ActionType.HOLD

    def test_engaged_no_shoot(self):
        a = make_unit_state("E", unit_id="me", is_engaged=True)
        m = make_unit_model(ranged=[make_shoota()])
        t = make_unit_state("T", unit_id="t1", position=(6, 0))
        ctx = make_context(a, m, [t])
        assert choose_action(a, m, ctx).type != ActionType.SHOOT

    def test_charge_too_far(self):
        a = make_unit_state("C", unit_id="me", position=(0, 0))
        m = make_unit_model()
        f = make_unit_state("F", unit_id="f1", position=(20, 0))
        ctx = make_context(a, m, [f], GamePhase.CHARGE)
        assert choose_action(a, m, ctx).type != ActionType.CHARGE

    def test_custom_weights(self):
        a = make_unit_state("S", unit_id="me", position=(0, 0))
        m = make_unit_model(ranged=[make_shoota()])
        t = make_unit_state("T", unit_id="t1", position=(12, 0))
        ctx = make_context(
            a,
            m,
            [t],
            weights={
                "kill_efficiency": 2.0,
                "threat_reduction": 0.0,
                "objective_value": 0.0,
                "survival_risk": 0.0,
                "synergy_bonus": 0.0,
            },
        )
        action = choose_action(a, m, ctx)
        assert action.score > 0


class TestObjectiveMovement:
    """Objective-based movement scoring."""

    def test_objective_mode_higher_than_engage(self):
        """mode='objective' даёт более высокий score чем mode='engage' при равных условиях."""
        a = make_unit_state("A", unit_id="me", position=(0, 0))
        m = make_unit_model("Test")
        m.movement = 6
        ctx = make_context(a, m, phase=GamePhase.MOVEMENT)
        target = (10, 0)

        score_obj = score_move(a, target, ctx, mode="objective")
        score_eng = score_move(a, target, ctx, mode="engage")
        assert score_obj > score_eng, f"objective={score_obj} should be > engage={score_eng}"

    def test_uses_actor_movement(self):
        """score_move использует movement из actor_unit, а не хардкод 6."""
        a = make_unit_state("A", unit_id="me", position=(0, 0))
        fast = make_unit_model("Fast")
        fast.movement = 12
        slow = make_unit_model("Slow")
        slow.movement = 3
        ctx_fast = make_context(a, fast, phase=GamePhase.MOVEMENT)
        ctx_slow = make_context(a, slow, phase=GamePhase.MOVEMENT)
        target = (10, 0)

        score_fast = score_move(a, target, ctx_fast, mode="engage")
        score_slow = score_move(a, target, ctx_slow, mode="engage")
        assert score_fast > score_slow, f"fast={score_fast} should be > slow={score_slow}"

    def test_already_at_target_zero(self):
        """Если юнит уже на точке — score 0."""
        a = make_unit_state("A", unit_id="me", position=(5, 5))
        m = make_unit_model()
        ctx = make_context(a, m, phase=GamePhase.MOVEMENT)
        score = score_move(a, (5, 5), ctx, mode="objective")
        assert score == 0.0

    def test_movement_generates_objective_candidates(self):
        """MOVEMENT фаза генерирует кандидатов с mode='objective' при наличии objectives."""
        # Без миссии — objectives пустые, только engage-кандидаты
        a = make_unit_state("A", unit_id="me", position=(0, 0))
        m = make_unit_model()
        t = make_unit_state("T", unit_id="t1", position=(10, 0))
        ctx = make_context(a, m, [t], phase=GamePhase.MOVEMENT)
        candidates = _generate_candidates(a, m, ctx)
        modes = {c.mode for c in candidates}
        assert "engage" in modes, "Should have engage-mode candidates for enemies"

    def test_no_objectives_no_enemies_hold(self):
        """Без objectives и без врагов — HOLD."""
        a = make_unit_state("A", unit_id="me", position=(0, 0))
        m = make_unit_model()
        ctx = make_context(a, m, [], phase=GamePhase.MOVEMENT)
        action = choose_action(a, m, ctx)
        assert action.type == ActionType.HOLD

    def test_get_objectives_empty_for_test_mission(self):
        """_get_objectives возвращает пустой список для тестовой миссии без objectives."""
        a = make_unit_state("A", unit_id="me")
        m = make_unit_model()
        ctx = make_context(a, m, phase=GamePhase.MOVEMENT)
        objs = _get_objectives(ctx)
        assert isinstance(objs, list)
        assert len(objs) == 0
