"""Parse YAML frontmatter and markdown tables into Unit and Weapon models."""

import logging
import re
from pathlib import Path
from typing import Any

import frontmatter

from backend.loader.schema import ensure_list, parse_bool, parse_model_count, parse_optional_int
from backend.model.unit import Unit, WargearSlot, Weapon, parse_dice_expression

logger = logging.getLogger(__name__)

DIRECT_FIELDS = {
    "title": "name",
    "movement": "movement",
    "toughness": "toughness",
    "save": "save",
    "wounds": "wounds",
    "leadership": "leadership",
    "objective_control": "objective_control",
    "points": "points",
    "edition": "edition",
    "category": "category",
}

LIST_FIELDS = {
    "keywords": "keywords",
    "faction_keywords": "faction_keywords",
    "abilities": "abilities",
    "leader_for": "leader_for",
    "transports": "transports",
}


def parse_unit(filepath: Path) -> Unit | None:
    """Parse a wiki markdown file into a Unit instance."""
    try:
        post = frontmatter.load(str(filepath))
    except Exception as exc:
        logger.error("Failed to parse %s: %s", filepath, exc)
        return None

    metadata = post.metadata
    title = metadata.get("title")
    if not title:
        logger.warning("No title in %s", filepath)
        return None

    kwargs: dict[str, Any] = {
        "name": str(title),
        "faction": str(metadata.get("faction") or filepath.parent.name),
        "category": str(metadata.get("category", "Infantry")),
    }

    for yaml_key, attr_name in DIRECT_FIELDS.items():
        if yaml_key == "title" or yaml_key not in metadata:
            continue
        kwargs[attr_name] = metadata[yaml_key]

    for yaml_key, attr_name in LIST_FIELDS.items():
        kwargs[attr_name] = [str(item) for item in ensure_list(metadata.get(yaml_key, []))]

    kwargs["invulnerable_save"] = parse_optional_int(metadata.get("invulnerable_save"))
    kwargs["feel_no_pain"] = parse_optional_int(metadata.get("feel_no_pain"))
    kwargs["model_count"] = parse_model_count(metadata.get("model_count", (1, 1)))
    kwargs["is_epic_hero"] = parse_bool(metadata.get("is_epic_hero", False))
    kwargs["can_be_warlord"] = parse_bool(metadata.get("can_be_warlord", False))
    kwargs["is_leader"] = parse_bool(metadata.get("is_leader", False))
    kwargs["wargear_options"] = _parse_wargear_options(metadata.get("wargear_options", []))

    weapons_data = metadata.get("weapons", [])
    ranged_weapons, melee_weapons = _parse_weapons_from_frontmatter(ensure_list(weapons_data))
    if not ranged_weapons and not melee_weapons:
        ranged_weapons, melee_weapons = _parse_weapons_from_markdown(post.content)
    if not ranged_weapons and not melee_weapons:
        ranged_weapons, melee_weapons = _parse_weapons_from_bullets(post.content)

    kwargs["ranged_weapons"] = ranged_weapons
    kwargs["melee_weapons"] = melee_weapons
    _fill_missing_unit_fields(kwargs, metadata, post.content)

    try:
        return Unit(**kwargs)
    except Exception as exc:
        logger.warning("Failed to build unit from %s: %s", filepath, exc)
        return None


def _parse_wargear_options(data: list[Any]) -> list[WargearSlot]:
    slots: list[WargearSlot] = []
    for item in ensure_list(data):
        if not isinstance(item, dict):
            continue
        try:
            slots.append(
                WargearSlot(
                    slot_name=str(item.get("slot_name", "")),
                    choices=[str(choice) for choice in ensure_list(item.get("choices", []))],
                    default_index=int(item.get("default_index", 0)),
                )
            )
        except Exception as exc:
            logger.warning("Failed to parse wargear option %s: %s", item, exc)
    return slots


def _parse_weapons_from_frontmatter(data: list[Any]) -> tuple[list[Weapon], list[Weapon]]:
    ranged: list[Weapon] = []
    melee: list[Weapon] = []

    for raw_weapon in data:
        if not isinstance(raw_weapon, dict):
            continue
        weapon = _build_weapon(raw_weapon)
        if weapon is None:
            continue
        if weapon.type == "ranged":
            ranged.append(weapon)
        else:
            melee.append(weapon)

    return ranged, melee


def _build_weapon(raw_weapon: dict[str, Any]) -> Weapon | None:
    try:
        range_value = str(raw_weapon.get("range", "0")).replace('"', "").strip()
        is_ranged = range_value.lower() != "melee"
        range_max = int(range_value) if is_ranged and range_value else 0
        skill_raw = str(raw_weapon.get("skill", "5+")).replace("+", "").strip()
        tags = [str(tag).strip().lower().replace(" ", "_") for tag in ensure_list(raw_weapon.get("tags", []))]
        abilities = [str(item).strip() for item in ensure_list(raw_weapon.get("abilities", []))]

        return Weapon(
            name=str(raw_weapon.get("name", "")).strip(),
            type="ranged" if is_ranged else "melee",
            range_max=range_max if is_ranged else None,
            attacks_dice=parse_dice_expression(str(raw_weapon.get("attacks", "1"))),
            skill=int(skill_raw),
            strength=int(raw_weapon.get("strength", 3)),
            ap=int(raw_weapon.get("ap", 0)),
            damage_dice=parse_dice_expression(str(raw_weapon.get("damage", "1"))),
            tags=tags,
            abilities=abilities,
        )
    except Exception as exc:
        logger.warning("Failed to parse weapon %s: %s", raw_weapon, exc)
        return None


def _parse_weapons_from_markdown(body: str) -> tuple[list[Weapon], list[Weapon]]:
    table_pattern = r"\|(.+)\|\n\|[-:| ]+\|\n((?:\|.+\|\n?)*)"
    match = re.search(table_pattern, body)
    if not match:
        return [], []

    rows_text = match.group(2)
    ranged: list[Weapon] = []
    melee: list[Weapon] = []

    for row in rows_text.strip().splitlines():
        cells = [cell.strip() for cell in row.split("|")[1:-1]]
        if len(cells) < 7:
            continue

        abilities = []
        if len(cells) > 7 and cells[7] != "-":
            abilities = [item.strip() for item in cells[7].split(",") if item.strip()]

        weapon = _build_weapon(
            {
                "name": cells[0],
                "range": cells[1],
                "attacks": cells[2],
                "skill": cells[3],
                "strength": cells[4],
                "ap": cells[5],
                "damage": cells[6],
                "abilities": abilities,
                "tags": [],
            }
        )
        if weapon is None:
            continue
        if weapon.type == "ranged":
            ranged.append(weapon)
        else:
            melee.append(weapon)

    return ranged, melee


def _parse_weapons_from_bullets(body: str) -> tuple[list[Weapon], list[Weapon]]:
    pattern = (
        r"\*\*(?P<name>[^*]+)\*\*\s*"
        r"\((?P<type>Ranged|Melee),\s*"
        r"(?P<range>[^,]+),\s*"
        r"A(?P<attacks>[^,]+),\s*"
        r"(?P<skill_label>BS|WS)(?P<skill>[^,]+),\s*"
        r"S(?P<strength>[^,]+),\s*"
        r"AP(?P<ap>[^,]+),\s*"
        r"D(?P<damage>[^,\)]+)"
        r"(?:,\s*(?P<abilities>[^\)]+))?"
        r"\)"
    )
    ranged: list[Weapon] = []
    melee: list[Weapon] = []

    for match in re.finditer(pattern, body):
        abilities = []
        if match.group("abilities"):
            abilities = [item.strip() for item in match.group("abilities").split(",") if item.strip()]

        weapon = _build_weapon(
            {
                "name": match.group("name").strip(),
                "range": match.group("range").strip().replace('"', ""),
                "attacks": match.group("attacks").strip(),
                "skill": match.group("skill").strip(),
                "strength": match.group("strength").strip(),
                "ap": match.group("ap").strip(),
                "damage": match.group("damage").strip(),
                "abilities": abilities,
                "tags": [],
            }
        )
        if weapon is None:
            continue
        if weapon.type == "ranged":
            ranged.append(weapon)
        else:
            melee.append(weapon)

    return ranged, melee


def _fill_missing_unit_fields(kwargs: dict[str, Any], metadata: dict[str, Any], body: str) -> None:
    profile = _parse_profile_from_markdown(body)
    for field_name, value in profile.items():
        kwargs.setdefault(field_name, value)

    if kwargs.get("model_count") == (1, 1):
        model_count = _parse_model_count_from_markdown(body)
        if model_count is not None:
            kwargs["model_count"] = model_count

    if kwargs.get("points", 0) == 0:
        points = _parse_points_from_markdown(body)
        if points is not None:
            kwargs["points"] = points

    if not kwargs.get("keywords"):
        kwargs["keywords"] = _parse_keywords_from_markdown(body)

    if "category" not in metadata:
        category = _infer_category(kwargs.get("keywords", []), metadata)
        kwargs["category"] = category


def _parse_profile_from_markdown(body: str) -> dict[str, int]:
    match = re.search(
        r"\|\s*M\s*\|\s*T\s*\|\s*SV\s*\|\s*W\s*\|\s*LD\s*\|\s*OC\s*\|\s*\n"
        r"\|[-| :]+\|\s*\n"
        r"\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|",
        body,
        re.IGNORECASE,
    )
    if not match:
        return {}

    values = [cell.strip().replace('"', "").replace("+", "") for cell in match.groups()]
    return {
        "movement": int(values[0]),
        "toughness": int(values[1]),
        "save": int(values[2]),
        "wounds": int(values[3]),
        "leadership": int(values[4]),
        "objective_control": int(values[5]),
    }


def _parse_model_count_from_markdown(body: str) -> tuple[int, int] | None:
    match = re.search(r"Размер отряда:\*\*\s*(\d+)[–-](\d+)", body)
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)))


def _parse_points_from_markdown(body: str) -> int | None:
    match = re.search(r"\*\*Очки:\*\*\s*(\d+)", body)
    if not match:
        return None
    return int(match.group(1))


def _parse_keywords_from_markdown(body: str) -> list[str]:
    match = re.search(r"##\s+Ключевые слова\s*\n\n`([^`]+)`", body, re.IGNORECASE)
    if not match:
        return []
    return [item.strip().title() for item in match.group(1).split(",") if item.strip()]


def _infer_category(keywords: list[str], metadata: dict[str, Any]) -> str:
    normalized_keywords = {keyword.lower() for keyword in keywords}
    metadata_tags = {str(tag).lower() for tag in ensure_list(metadata.get("tags", []))}
    combined = normalized_keywords | metadata_tags
    if "battleline" in combined:
        return "Battleline"
    if "vehicle" in combined:
        return "Vehicle"
    if "monster" in combined:
        return "Monster"
    return "Infantry"
