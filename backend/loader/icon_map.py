"""
Маппинг категорий юнитов → SVG-иконки.
Используется на фронте для отображения карточек юнитов.
"""

ICON_MAP = {
    "character": "character.svg",  # 🪖 Командиры
    "battleline": "battleline.svg",  # ⚔️ Линейная пехота
    "elite": "elite.svg",  # ⭐ Элита
    "infantry": "infantry.svg",  # 👤 Простая пехота
    "vehicle": "vehicle.svg",  # 🚛 Техника
    "transport": "transport.svg",  # 🚌 Транспорт
    "walker": "walker.svg",  # 🦿 Ходячая техника
    "monster": "monster.svg",  # 🦣 Монстры
    "dreadnought": "dreadnought.svg",  # 💀 Дредноуты
    "titanic": "titanic.svg",  # 🏗 Титаны
    "speed-freek": "speed-freek.svg",  # 🏍 Скоростная техника
    "flyer": "flyer.svg",  # ✈️ Летающие
    "artillery": "artillery.svg",  # 💥 Артиллерия
    "psyker": "psyker.svg",  # 🔮 Псайкеры
    "medic": "medic.svg",  # 🏥 Медики
    "epic-hero": "epic-hero.svg",  # 👑 Эпические герои
}

CATEGORY_ORDER = [
    "epic-hero",
    "character",
    "psyker",
    "medic",
    "battleline",
    "elite",
    "infantry",
    "transport",
    "vehicle",
    "walker",
    "dreadnought",
    "speed-freek",
    "monster",
    "titanic",
    "flyer",
    "artillery",
]

CATEGORY_LABELS = {
    "character": "Characters",
    "battleline": "Battleline",
    "elite": "Elites",
    "infantry": "Infantry",
    "vehicle": "Vehicles",
    "transport": "Dedicated Transports",
    "walker": "Walkers",
    "monster": "Monsters",
    "dreadnought": "Dreadnoughts",
    "titanic": "Titanic",
    "speed-freek": "Speed Freeks",
    "flyer": "Flyers",
    "artillery": "Artillery",
    "psyker": "Psykers",
    "medic": "Medics",
    "epic-hero": "Epic Heroes",
}

CATEGORY_COLORS = {
    "epic-hero": "#a855f7",  # purple
    "character": "#a855f7",  # purple
    "psyker": "#ec4899",  # pink
    "medic": "#22c55e",  # green
    "battleline": "#22c55e",  # green
    "elite": "#eab308",  # yellow
    "infantry": "#6b7280",  # gray
    "transport": "#3b82f6",  # blue
    "vehicle": "#3b82f6",  # blue
    "walker": "#f97316",  # orange
    "dreadnought": "#f97316",  # orange
    "speed-freek": "#ef4444",  # red
    "monster": "#ef4444",  # red
    "titanic": "#dc2626",  # red-dark
    "flyer": "#8b5cf6",  # violet
    "artillery": "#78716c",  # stone
}


def get_icon_url(category: str) -> str:
    """Вернуть URL иконки для категории юнита."""
    icon = ICON_MAP.get(category, "infantry.svg")
    return f"/static/icons/{icon}"
