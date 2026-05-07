"""Plans: UserFeatures — централизованный Feature Gate.

Единственный источник правды — какие функции доступны пользователю.
"""

from typing import ClassVar, Optional


class UserFeatures:
    """Набор функций для конкретного пользователя."""

    # ── Определения планов ─────────────────────────────────────

    FREE: ClassVar[dict] = {
        "max_rosters": 3,
        "simulation_ai": "basic",  # упрощённая симуляция
        "export_enabled": False,
        "public_rosters_create": False,  # может только смотреть
        "public_rosters_view": True,
        "ads_enabled": True,
        "priority_simulation": False,
        "max_simulations_per_day": 3,
        "factions_unlocked": "all",  # все фракции, но с лимитами
    }

    PREMIUM: ClassVar[dict] = {
        "max_rosters": 999,
        "simulation_ai": "full",
        "export_enabled": True,
        "public_rosters_create": True,
        "public_rosters_view": True,
        "ads_enabled": False,
        "priority_simulation": True,
        "max_simulations_per_day": 999,
        "factions_unlocked": "all",
    }

    @classmethod
    def for_tier(cls, tier: str) -> dict:
        """Получить права по названию плана."""
        if tier == "premium":
            return cls.PREMIUM.copy()
        return cls.FREE.copy()

    @classmethod
    def for_user(cls, user) -> dict:
        """Получить права для объекта User."""
        tier = getattr(user, "tier", "free") if user else "free"
        return cls.for_tier(tier)


# ── Depends-функция для FastAPI ─────────────────────────────────


async def require_tier(min_tier: str = "premium"):
    """Фабрика Depends: require_tier('premium') → только для Premium."""

    def _checker(user=...):  # placeholder — биндится в routes
        ...

    return _checker
