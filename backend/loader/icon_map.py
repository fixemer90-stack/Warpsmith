"""
Маппинг категорий юнитов → SVG-иконки, цвета, подписи.
Используется на фронте для отображения карточек юнитов.
"""

import os
from pathlib import Path

ICONS_DIR = Path(__file__).parent.parent.parent / "web" / "static" / "icons"

ICON_MAP = {
    "epic-hero": "epic-hero.svg",
    "character": "character.svg",
    "psyker": "psyker.svg",
    "medic": "medic.svg",
    "battleline": "battleline.svg",
    "elite": "elite.svg",
    "infantry": "infantry.svg",
    "transport": "transport.svg",
    "vehicle": "vehicle.svg",
    "walker": "walker.svg",
    "dreadnought": "dreadnought.svg",
    "speed-freek": "speed-freek.svg",
    "battlesuit": "battlesuit.svg",
    "monster": "monster.svg",
    "titanic": "titanic.svg",
    "fly": "fly.svg",
    "artillery": "artillery.svg",
    "legends": "legends.svg",
}

CATEGORY_ORDER = [
    "epic-hero", "character", "psyker", "medic", "battleline", "elite",
    "infantry", "transport", "vehicle", "walker", "dreadnought",
    "battlesuit", "speed-freek", "monster", "titanic", "fly", "artillery", "legends",
]

CATEGORY_LABELS = {
    "epic-hero": "Epic Heroes", "character": "Characters", "psyker": "Psykers",
    "medic": "Medics", "battleline": "Battleline", "elite": "Elites",
    "infantry": "Infantry", "transport": "Dedicated Transports",
    "vehicle": "Vehicles", "walker": "Walkers", "dreadnought": "Dreadnoughts",
    "battlesuit": "Battlesuits", "speed-freek": "Speed Freeks",
    "monster": "Monsters", "titanic": "Titanic", "fly": "Flyers",
    "artillery": "Artillery", "legends": "Legends",
}

CATEGORY_COLORS = {
    "epic-hero": "#a855f7", "character": "#a855f7", "psyker": "#ec4899",
    "medic": "#22c55e", "battleline": "#22c55e", "elite": "#eab308",
    "infantry": "#6b7280", "transport": "#3b82f6", "vehicle": "#3b82f6",
    "walker": "#f97316", "dreadnought": "#f97316", "battlesuit": "#06b6d4",
    "speed-freek": "#ef4444", "monster": "#ef4444", "titanic": "#dc2626",
    "fly": "#8b5cf6", "artillery": "#78716c", "legends": "#555555",
}


def get_icon_url(category: str) -> str:
    """Вернуть URL иконки для категории юнита."""
    icon = ICON_MAP.get(category, "infantry.svg")
    return f"/static/icons/{icon}"


def get_icon_html(category: str, size: int = 24, class_name: str = "") -> str:
    """Вернуть inline SVG как HTML-строку."""
    filename = ICON_MAP.get(category, "infantry.svg")
    svg_path = ICONS_DIR / filename
    if not svg_path.exists():
        return f'<!-- icon {filename} not found -->'
    try:
        svg = svg_path.read_text()
    except Exception:
        return ''
    svg = svg.replace(
        '<svg ',
        f'<svg width="{size}" height="{size}" class="{class_name}" ',
        1,
    )
    return svg


def get_card_style(category: str) -> str:
    """Вернуть CSS-стиль для карточки юнита по категории."""
    color = CATEGORY_COLORS.get(category, "#6b7280")
    return f"border-left: 3px solid {color};"


def get_icon_svg_map() -> dict[str, str]:
    """Загрузить все SVG в словарь (для inline-вставки на фронте)."""
    svg_map = {}
    for cat, filename in ICON_MAP.items():
        path = ICONS_DIR / filename
        if path.exists():
            svg_map[cat] = path.read_text()
    return svg_map
