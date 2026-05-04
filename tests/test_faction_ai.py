"""Tests for F3.2 — Faction AI Profiles."""

import sys
import tempfile
from pathlib import Path

import pytest

from backend.engine.ai.faction_ai import (
    DEFAULT_WEIGHTS,
    FactionAIProfile,
    _is_behavior_active,
    _parse_profile,
    clear_cache,
    get_target_multiplier,
    get_weights,
    load_profile,
    mark_behavior_used,
)
from backend.state.game_state import GamePhase

# ── Helpers ─────────────────────────────────────────────────────


def _make_faction_file(tmp_path: Path, faction_id: str, ai_yaml: str) -> Path:
    """Create a temporary faction wiki file with ai: section."""
    faction_dir = tmp_path / "factions"
    faction_dir.mkdir(parents=True, exist_ok=True)
    filepath = faction_dir / f"{faction_id}.md"
    content = f"""---
title: {faction_id}
{ai_yaml}
---

# {faction_id}
"""
    filepath.write_text(content)
    return filepath


SAMPLE_ORK_YAML = """ai:
  weights:
    kill_efficiency: 1.0
    charge_aggression: 1.5
    survival_risk: 0.3
    objective_value: 0.6
    threat_reduction: 0.7
  behaviors:
    - id: waaagh
      description: "Waaagh! bonus"
      trigger:
        phase: command
        round_min: 2
        round_max: 3
        cooldown: 0
      effects:
        weights_override:
          charge_aggression: 2.5
          survival_risk: 0.1
    - id: ere_we_go
      description: "Charge reroll"
      trigger:
        phase: charge
        round_min: 1
        round_max: 20
        cooldown: 1
      effects:
        action_override: charge
  target_priority:
    monster: 1.2
    vehicle: 1.1
  deployment:
    front_line: ["battleline", "infantry"]
"""


SAMPLE_PROFILE_WITHOUT_AI = """tags: [test]
"""


# ── Tests ───────────────────────────────────────────────────────


class TestProfileLoading:
    def test_load_ork_profile(self):
        """Загрузка Ork AI профиля из wiki даёт weights.charge_aggression == 1.5."""
        profile = load_profile("orks")
        assert profile is not None
        assert profile.weights["charge_aggression"] == 1.5

    def test_load_tau_profile(self):
        """Загрузка Tau AI профиля."""
        profile = load_profile("tau")
        assert profile is not None
        # Tau has low charge_aggression
        assert profile.weights["charge_aggression"] <= 0.5

    def test_load_admech_profile(self):
        """Загрузка AdMech AI профиля."""
        profile = load_profile("adeptus-mechanicus")
        assert profile is not None
        assert len(profile.behaviors) > 0

    def test_no_ai_section_falls_back_to_defaults(self):
        """Фракция без ai: секции возвращает None."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _make_faction_file(tmp_path, "test_faction", SAMPLE_PROFILE_WITHOUT_AI)
            profile = load_profile("test_faction", tmp_path)
            assert profile is None

    def test_nonexistent_faction_returns_none(self):
        """Несуществующая фракция возвращает None."""
        profile = load_profile("nonexistent-faction")
        assert profile is None


class TestBehaviorActivation:
    def test_behavior_waaagh_activates_in_round_2(self):
        """Waaagh! активен в раунд 2, фаза command."""
        profile = load_profile("orks")
        weights = get_weights(profile, GamePhase.COMMAND, 2)
        assert weights["charge_aggression"] == 2.5  # overridden

    def test_behavior_waaagh_not_active_in_round_1(self):
        """Waaagh! НЕ активен в раунд 1 (round_min=2)."""
        profile = load_profile("orks")
        weights = get_weights(profile, GamePhase.COMMAND, 1)
        # Should be base weight, not overridden
        assert weights["charge_aggression"] == 1.5

    def test_behavior_waaagh_not_active_wrong_phase(self):
        """Waaagh! НЕ активен в фазе shooting (trigger: command)."""
        profile = load_profile("orks")
        weights = get_weights(profile, GamePhase.SHOOTING, 2)
        assert weights["charge_aggression"] == 1.5  # base, not overridden

    def test_behavior_cooldown_respects_gap(self):
        """Behavior не активируется, если cooldown не прошёл."""
        profile = load_profile("orks")
        # Find ere_we_go behavior (cooldown=1)
        ere_we_go = [b for b in profile.behaviors if b.id == "ere_we_go"][0]
        assert ere_we_go.trigger.cooldown == 1

        # Mark as used in round 1
        mark_behavior_used(profile, "ere_we_go", 1)

        # Should NOT activate in round 1 (same round)
        assert not _is_behavior_active(ere_we_go, GamePhase.CHARGE, 1)

        # Should NOT activate in round 2 (cooldown=1, only 1 round gap)
        assert not _is_behavior_active(ere_we_go, GamePhase.CHARGE, 2)

        # Should activate in round 3 (2 rounds gap > cooldown=1)
        assert _is_behavior_active(ere_we_go, GamePhase.CHARGE, 3)


class TestTargetPriority:
    def test_target_priority_vehicle_higher_than_infantry(self):
        """Против техники множитель выше, чем против пехоты (для Orks)."""
        profile = load_profile("orks")
        vehicle_mult = get_target_multiplier(profile, {"vehicle", "monster"})
        infantry_mult = get_target_multiplier(profile, {"infantry"})
        assert vehicle_mult >= infantry_mult

    def test_target_priority_fallback_to_1(self):
        """Неизвестный keyword возвращает множитель 1.0."""
        profile = load_profile("orks")
        mult = get_target_multiplier(profile, {"unknown_keyword_xyz"})
        assert mult == 1.0

    def test_target_priority_max_is_used(self):
        """Из нескольких keywords выбирается максимальный множитель."""
        profile = load_profile("orks")
        mult = get_target_multiplier(profile, {"infantry", "monster"})
        assert mult == 1.2  # monster has 1.2


class TestWeights:
    def test_ork_vs_tau_weights_differ(self):
        """Орки и Тау имеют разные weights."""
        ork = load_profile("orks")
        tau = load_profile("tau")
        assert ork.weights["charge_aggression"] != tau.weights["charge_aggression"]

    def test_profile_merges_with_defaults(self):
        """Профиль содержит все DEFAULT_WEIGHTS ключи + свои."""
        profile = load_profile("orks")
        for key in DEFAULT_WEIGHTS:
            assert key in profile.weights, f"Missing default weight: {key}"

    def test_negative_weights_are_rejected(self):
        """Отрицательные веса в behavior не применяются."""
        bad_yaml = """ai:
  weights:
    kill_efficiency: 1.0
  behaviors:
    - id: bad_behavior
      description: "Negative weights test"
      trigger:
        phase: any
      effects:
        weights_override:
          kill_efficiency: -1.0
"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _make_faction_file(tmp_path, "test_bad", bad_yaml)
            profile = load_profile("test_bad", tmp_path)
            weights = get_weights(profile, GamePhase.COMMAND, 1)
            # Negative override should be skipped
            assert weights["kill_efficiency"] == 1.0


class TestActionOverride:
    def test_action_override_from_behavior(self):
        """Проверка action_override от активного behavior."""
        clear_cache()
        profile = load_profile("orks")
        from backend.engine.ai.faction_ai import get_active_behavior_override

        # Ere We Go активен в charge phase
        override = get_active_behavior_override(profile, GamePhase.CHARGE, 1)
        assert override == "charge"

    def test_action_override_not_active_wrong_phase(self):
        """Action override не возвращается, если не та фаза."""
        profile = load_profile("orks")
        from backend.engine.ai.faction_ai import get_active_behavior_override

        # Ere We Go НЕ активен в shooting phase
        override = get_active_behavior_override(profile, GamePhase.SHOOTING, 1)
        assert override is None


class TestDeployment:
    def test_deployment_layout_parses_correctly(self):
        """Поле deployment загружается как dict[str, list[str]]."""
        profile = load_profile("orks")
        assert "front_line" in profile.deployment
        assert isinstance(profile.deployment["front_line"], list)
        assert "battleline" in profile.deployment["front_line"]
