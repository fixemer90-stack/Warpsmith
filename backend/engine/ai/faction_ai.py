"""
F3.2 — Faction AI Profiles: Wiki-driven Behaviour System.

Загружает AI профили из YAML `ai:` секции wiki/factions/<faction>.md
и предоставляет функции для применения faction-specific weights,
behaviors, target_priority и deployment к Greedy Decision Engine (F3.1).

Новый .md файл с ai: секцией = новая фракция с уникальным AI.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter

from backend.state.game_state import GamePhase

from .decision import Action

logger = logging.getLogger(__name__)

# ── Data Model ─────────────────────────────────────────────────


@dataclass
class BehaviorTrigger:
    """Условия активации поведения."""

    phase: str = "any"
    condition: str = ""
    cooldown: int = 0
    round_min: int = 1
    round_max: int = 20


@dataclass
class BehaviorEffects:
    """Эффекты при активации поведения."""

    weights_override: dict[str, float] = field(default_factory=dict)
    tags_buff: list[str] = field(default_factory=list)
    action_override: str | None = None


@dataclass
class Behavior:
    """Одно фракционное поведение с триггерами и эффектами."""

    id: str
    description: str = ""
    trigger: BehaviorTrigger = field(default_factory=BehaviorTrigger)
    effects: BehaviorEffects = field(default_factory=BehaviorEffects)
    last_used_round: int = 0  # runtime state, не из YAML


@dataclass
class FactionAIProfile:
    """Полный AI профиль фракции из wiki/factions/<faction>.md."""

    faction_id: str
    weights: dict[str, float] = field(default_factory=dict)
    behaviors: list[Behavior] = field(default_factory=list)
    target_priority: dict[str, float] = field(default_factory=dict)
    deployment: dict[str, list[str]] = field(default_factory=dict)


# ── Defaults ────────────────────────────────────────────────────

DEFAULT_WEIGHTS: dict[str, float] = {
    "kill_efficiency": 1.0,
    "charge_aggression": 1.0,
    "survival_risk": 0.5,
    "objective_value": 0.6,
    "threat_reduction": 0.8,
}

PROFILE_CACHE: dict[str, FactionAIProfile] = {}


# ── Profile loading ─────────────────────────────────────────────


def load_profile(faction_id: str, wiki_path: Path | None = None) -> FactionAIProfile | None:
    """Загрузить AI профиль из wiki/factions/<faction_id>.md.

    Args:
        faction_id: ID фракции (например 'orks', 'tau', 'adeptus-mechanicus')
        wiki_path: Путь к корню wiki vault. Если None, использует registry.

    Returns:
        FactionAIProfile или None если профиль не найден.
    """
    # Cache check
    cache_key = f"{faction_id}:{wiki_path}"
    if cache_key in PROFILE_CACHE:
        return PROFILE_CACHE[cache_key]

    if wiki_path is None:
        from backend.loader.registry import registry

        if registry is None or not hasattr(registry, "wiki_path") or not registry.wiki_path:
            logger.warning("No wiki path available, cannot load AI profile for %s", faction_id)
            return None
        wiki_path = registry.wiki_path

    faction_file = wiki_path / "factions" / f"{faction_id}.md"
    if not faction_file.exists():
        # Try case-insensitive + relaxed match
        parent = faction_file.parent
        if parent.exists():
            # Normalize faction_id: remove spaces, hyphens, apostrophes
            norm_id = faction_id.lower().replace("-", "").replace(" ", "").replace("'", "")
            for f in parent.iterdir():
                if f.is_file() and f.suffix == ".md":
                    stem = f.stem.lower().replace("-", "").replace(" ", "").replace("'", "")
                    if stem == norm_id or norm_id in stem or stem in norm_id:
                        faction_file = f
                        break
        if not faction_file.exists():
            logger.warning("Faction file not found: %s", faction_file)
            return None

    try:
        post = frontmatter.load(str(faction_file))
    except Exception as exc:
        logger.error("Failed to parse faction file %s: %s", faction_file, exc)
        return None

    ai_data = post.metadata.get("ai", {})
    if not ai_data:
        logger.info("No ai: section in %s, using defaults", faction_file)
        return None

    profile = _parse_profile(faction_id, ai_data)
    PROFILE_CACHE[cache_key] = profile
    return profile


def _parse_profile(faction_id: str, ai_data: dict) -> FactionAIProfile:
    """Распарсить YAML ai: секцию в FactionAIProfile."""
    weights = dict(DEFAULT_WEIGHTS)
    weights.update(ai_data.get("weights", {}))

    behaviors = []
    for b_data in ai_data.get("behaviors", []):
        trigger_data = b_data.get("trigger", {})
        effects_data = b_data.get("effects", {})

        behavior = Behavior(
            id=b_data.get("id", "unknown"),
            description=b_data.get("description", ""),
            trigger=BehaviorTrigger(
                phase=trigger_data.get("phase", "any"),
                condition=trigger_data.get("condition", ""),
                cooldown=int(trigger_data.get("cooldown", 0)),
                round_min=int(trigger_data.get("round_min", 1)),
                round_max=int(trigger_data.get("round_max", 20)),
            ),
            effects=BehaviorEffects(
                weights_override=effects_data.get("weights_override", {}),
                tags_buff=effects_data.get("tags_buff", []),
                action_override=effects_data.get("action_override"),
            ),
        )
        behaviors.append(behavior)

    target_priority = ai_data.get("target_priority", {})
    deployment = ai_data.get("deployment", {})

    return FactionAIProfile(
        faction_id=faction_id,
        weights=weights,
        behaviors=behaviors,
        target_priority=target_priority,
        deployment=deployment,
    )


def clear_cache() -> None:
    """Очистить кеш профилей. Нужно при перезагрузке wiki."""
    PROFILE_CACHE.clear()


# ── Active behaviors ────────────────────────────────────────────


def _is_behavior_active(
    behavior: Behavior,
    phase: GamePhase,
    turn: int,
) -> bool:
    """Проверить, активен ли behavior в текущем контексте."""
    phase_ok = behavior.trigger.phase in ("any", phase.value)
    if not phase_ok:
        return False

    round_ok = behavior.trigger.round_min <= turn <= behavior.trigger.round_max
    if not round_ok:
        return False

    # Если behavior уже использован и cooldown = 0 — одноразовый
    if behavior.trigger.cooldown == 0 and behavior.last_used_round > 0:
        return False

    # Если cooldown > 0 — проверяем, прошло ли достаточно раундов
    if (
        behavior.trigger.cooldown > 0
        and behavior.last_used_round > 0
        and turn - behavior.last_used_round <= behavior.trigger.cooldown
    ):
        return False

    # Валидация phase
    known_phases = {p.value for p in GamePhase} | {"any"}
    if behavior.trigger.phase not in known_phases:
        logger.warning(
            "Unknown phase '%s' in behavior '%s', ignoring", behavior.trigger.phase, behavior.id
        )
        return False

    return True


def get_weights(
    profile: FactionAIProfile,
    phase: GamePhase,
    turn: int,
) -> dict[str, float]:
    """Вернуть актуальные weights с учётом активных behaviors.

    Args:
        profile: FactionAIProfile фракции
        phase: Текущая фаза игры
        turn: Текущий раунд

    Returns:
        dict[str, float] — weights с применёнными overrides от активных behaviors
    """
    weights = dict(profile.weights)

    for b in profile.behaviors:
        if _is_behavior_active(b, phase, turn):
            has_negative = any(v < 0 for v in b.effects.weights_override.values())
            if has_negative:
                logger.warning("Behavior '%s' has negative weight overrides, skipping", b.id)
                continue
            weights.update(b.effects.weights_override)
            # Auto-mark as used so one-shot/cooldown behaviors work correctly
            mark_behavior_used(profile, b.id, turn)

    return weights


def get_target_multiplier(
    profile: FactionAIProfile,
    target_keywords: set[str],
) -> float:
    """Вернуть множитель приоритета для цели по её keywords.

    Берётся максимальное совпадение среди target_priority.
    Если совпадений нет — возвращается 1.0 (нейтрально).
    """
    best = 1.0
    for kw in target_keywords:
        kw_lower = kw.lower().replace(" ", "-")
        if kw_lower in profile.target_priority:
            best = max(best, profile.target_priority[kw_lower])
    return best


def mark_behavior_used(profile: FactionAIProfile, behavior_id: str, turn: int) -> None:
    """Отметить behavior как использованный в данном раунде."""
    for b in profile.behaviors:
        if b.id == behavior_id:
            b.last_used_round = turn
            return


def get_active_behavior_override(
    profile: FactionAIProfile,
    phase: GamePhase,
    turn: int,
) -> str | None:
    """Вернуть action_override от первого активного behavior, у которого он есть."""
    for b in profile.behaviors:
        if _is_behavior_active(b, phase, turn) and b.effects.action_override:
            return b.effects.action_override
    return None


# ── Integration with F3.1 ──────────────────────────────────────


def choose_action_with_faction_ai(
    actor_unit,
    ctx,
) -> Action | None:
    """Выбрать действие через F3.1 Greedy Engine с учётом faction AI профиля.

    Загружает AI профиль фракции и обновляет ctx.weights перед вызовом choose_action.

    Args:
        actor_unit: Unit dataclass атакующего юнита
        ctx: EvaluationContext с состоянием игры

    Returns:
        Action или None, если действие не найдено
    """
    from backend.engine.ai.decision import choose_action
    from backend.loader.registry import registry

    if registry is None:
        return choose_action(ctx.actor, actor_unit, ctx)

    profile = load_profile(ctx.actor.faction, registry.wiki_path)
    if profile is not None:
        # Обновляем weights из профиля с учётом активных behaviors
        ctx.weights = get_weights(profile, ctx.phase, ctx.turn)

        # Проверяем action_override от активных behaviors
        override = get_active_behavior_override(profile, ctx.phase, ctx.turn)
        if override:
            logger.debug(
                "Behavior override for %s: forcing action '%s'", ctx.actor.unit_id, override
            )

    return choose_action(ctx.actor, actor_unit, ctx)
