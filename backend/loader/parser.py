"""Parse YAML frontmatter and markdown tables into Unit and Weapon models."""

import contextlib
import logging
import re
from pathlib import Path
from typing import Any

import frontmatter

from backend.loader.schema import ensure_list, parse_bool, parse_model_count, parse_optional_int
from backend.model.unit import Unit, WargearSlot, Weapon, parse_dice_expression

logger = logging.getLogger(__name__)

# ── Header-aware column mapping for weapon tables ────────────────

# Maps header cell keywords (lowercase) to canonical column names
_HEADER_ALIASES: dict[str, str] = {
    "name": "name",
    "weapon": "name",
    "оружие": "name",
    "type": "type",
    "тип": "type",
    "range": "range",
    "дальность": "range",
    "дальн": "range",
    "a": "attacks",
    "attacks": "attacks",
    "атаки": "attacks",
    "bs": "skill",
    "ws": "skill",
    "bs/ws": "skill",
    "skill": "skill",
    "меткость": "skill",
    "s": "strength",
    "strength": "strength",
    "сила": "strength",
    "ap": "ap",
    "d": "damage",
    "damage": "damage",
    "урон": "damage",
    "особенности": "abilities",
    "abilities": "abilities",
    "способности": "abilities",
}


def _map_header_columns(header_cells: list[str]) -> dict[str, int]:
    """Map header column names to their 0-based cell index.

    Returns a dict like {'name': 0, 'range': 2, 'attacks': 3, ...}
    Skips headers that don't match any known alias.
    """
    mapping: dict[str, int] = {}
    for idx, cell in enumerate(header_cells):
        key = cell.strip().lower()
        canonical = _HEADER_ALIASES.get(key)
        if canonical and canonical not in mapping:
            mapping[canonical] = idx
    return mapping


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
    "tags": "tags",
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

    # Skip non-unit concept pages (weapon descriptions, wargear, etc.)
    if metadata.get("type") != "entity" and not re.search(
        r"\|\s*M\s*\|\s*T\s*\|\s*SV\s*\|", post.content
    ):
        logger.debug("Skipping non-unit page: %s", filepath)
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
    # Auto-detect Warlord: любой Character может быть Warlord
    explicit_warlord = metadata.get("can_be_warlord")
    if explicit_warlord is not None:
        kwargs["can_be_warlord"] = parse_bool(explicit_warlord)
    else:
        keywords = kwargs.get("keywords", [])
        tags = [str(t) for t in ensure_list(metadata.get("tags", []))]
        all_tags = {t.lower() for t in keywords + tags}
        kwargs["can_be_warlord"] = "character" in all_tags
    kwargs["is_leader"] = parse_bool(metadata.get("is_leader", False))
    kwargs["wargear_options"] = _parse_wargear_options(metadata.get("wargear_options", []))
    # F4.2: Extended wargear system
    kwargs["squad_size"] = metadata.get("squad_size", {"min": 1, "max": 1, "step": 1})
    kwargs["extended_wargear_options"] = ensure_list(metadata.get("extended_wargear_options", []))
    kwargs["nob_options"] = ensure_list(metadata.get("nob_options", []))

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
        range_value = _clean_range(str(raw_weapon.get("range", "0")))
        is_ranged = range_value.lower() not in ("melee", "—", "", "ближний")

        skill_raw = str(raw_weapon.get("skill", "5+")).replace("+", "").strip()
        if skill_raw.lower() in ("", "—", "n/a", "-"):
            skill_raw = "6"
        tags = [
            str(tag).strip().lower().replace(" ", "_")
            for tag in ensure_list(raw_weapon.get("tags", []))
        ]
        abilities = [str(item).strip() for item in ensure_list(raw_weapon.get("abilities", []))]

        # Handle strength with dice expressions (e.g. "2D6", "D6")
        strength_raw = str(raw_weapon.get("strength", "3")).strip()
        try:
            strength = int(strength_raw)
        except ValueError:
            dice = parse_dice_expression(strength_raw)
            strength = _avg_dice(dice)

        # Handle non-numeric AP (e.g. "—")
        ap_raw = str(raw_weapon.get("ap", "0")).strip()
        try:
            ap = int(ap_raw)
        except ValueError:
            ap = 0

        if is_ranged:
            try:
                range_max = int(range_value)
            except ValueError:
                range_max = 0
        else:
            range_max = None

        return Weapon(
            name=str(raw_weapon.get("name", "")).strip().strip("*"),
            type="ranged" if is_ranged else "melee",
            range_max=range_max if is_ranged else None,
            attacks_dice=parse_dice_expression(str(raw_weapon.get("attacks", "1"))),
            skill=int(skill_raw),
            strength=strength,
            ap=ap,
            damage_dice=parse_dice_expression(str(raw_weapon.get("damage", "1"))),
            tags=tags,
            abilities=abilities,
        )
    except Exception as exc:
        logger.warning("Failed to parse weapon %s: %s", raw_weapon, exc)
        return None


def _clean_range(value: str) -> str:
    """Clean a range value: remove quotes, strip Ranged/Melee prefix, handle non-numeric."""
    cleaned = value.replace('"', "").replace("\u201c", "").replace("\u201d", "").strip()

    # Extract numeric prefix from strings like "Ranged 36", "Ranged 24"
    match = re.match(r"(\d+)", cleaned)
    if match:
        return match.group(1)

    # Return the cleaned value as-is (may be "Melee", "—", etc.)
    return cleaned


def _avg_dice(dice: tuple[int, int, int]) -> int:
    """Calculate average of a dice expression."""
    count, sides, modifier = dice
    if count == 0:
        return modifier
    return int(count * (sides + 1) / 2 + modifier)


def _parse_weapons_from_markdown(body: str) -> tuple[list[Weapon], list[Weapon]]:
    table_pattern = r"\|(.+)\|\n\|[-:| ]+\|\n((?:\|.+\|\n?)*)"
    ranged: list[Weapon] = []
    melee: list[Weapon] = []

    for match in re.finditer(table_pattern, body):
        header = match.group(1).strip()
        header_cells = [c.strip() for c in header.split("|")]

        # Skip profile tables (those with M and T columns)
        if any(c.upper().startswith("M") for c in header_cells) and any(
            c.upper().startswith("T") for c in header_cells
        ):
            continue

        # Map column indices by header name (supports English, Russian, 8 or 9 columns)
        col = _map_header_columns(header_cells)

        # Must have at minimum: name, range/attacks/skill/strength/ap/damage
        required = {"name", "range", "attacks", "skill", "strength", "ap", "damage"}
        if not required.issubset(col):
            continue

        rows_text = match.group(2)
        for row in rows_text.strip().splitlines():
            cells = [cell.strip() for cell in row.split("|")[1:-1]]

            # Skip rows that don't cover required columns
            max_col = max(col.values())
            if len(cells) <= max_col:
                continue

            # Extract abilities from the abilities column (if present)
            abilities = []
            if "abilities" in col and col["abilities"] < len(cells):
                ab_cell = cells[col["abilities"]]
                if ab_cell and ab_cell != "—":
                    abilities = [
                        item.strip().strip("[]")
                        for item in re.split(r"[,\n]", ab_cell)
                        if item.strip() and item.strip() != "—"
                    ]

            weapon_data: dict[str, Any] = {
                "name": cells[col["name"]] if col["name"] < len(cells) else "",
                "range": cells[col["range"]] if col["range"] < len(cells) else "0",
                "attacks": cells[col["attacks"]] if col["attacks"] < len(cells) else "1",
                "skill": cells[col["skill"]] if col["skill"] < len(cells) else "5+",
                "strength": cells[col["strength"]] if col["strength"] < len(cells) else "3",
                "ap": cells[col["ap"]] if col["ap"] < len(cells) else "0",
                "damage": cells[col["damage"]] if col["damage"] < len(cells) else "1",
                "abilities": abilities,
                "tags": [],
            }

            weapon = _build_weapon(weapon_data)
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
            abilities = [
                item.strip() for item in match.group("abilities").split(",") if item.strip()
            ]

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

    if not kwargs.get("keywords"):
        kwargs["keywords"] = _parse_keywords_from_markdown(body)

    if "category" not in metadata:
        category = _infer_category(kwargs.get("keywords", []), metadata)
        kwargs["category"] = category

    # Second pass: auto-detect Warlord from body keywords
    if not kwargs.get("can_be_warlord"):
        body_keywords = _parse_keywords_from_markdown(body)
        if "character" in {kw.lower() for kw in body_keywords}:
            kwargs["can_be_warlord"] = True


def _find_m_column_index(header_line: str) -> int:
    """Find the 0-based column index of the M (Movement) column in a profile table header.

    Handles tables like | M | T | SV | ... | or | Type | M | T | ... |
    """
    cells = [c.strip() for c in header_line.split("|")]
    for i, cell in enumerate(cells):
        if cell.upper() == "M":
            return i
    return -1


def _parse_profile_from_markdown(body: str) -> dict[str, int]:
    """Parse the unit profile table (M/T/SV/W/LD/OC) from markdown body.

    Handles:
    - Standard 6-column tables: | M | T | SV | W | LD | OC |
    - 7-column tables with INV: | M | T | SV | W | LD | OC | INV |
    - Tables with a leading Type column: | Type | M | T | SV | W | LD | OC | INV |
    - Fortifications with '-' for movement
    - Non-standard 7th column names (e.g. 'Размер')
    """
    lines = body.split("\n")
    for i, line in enumerate(lines):
        # Find a line containing | M | (could be at any position in the row)
        if not re.search(r"\|\s*M\s*\|", line, re.IGNORECASE):
            continue
        # Check this isn't a weapon table by verifying M isn't followed by WEAPON-like headers
        m_col = _find_m_column_index(line)
        if m_col < 0:
            continue

        # Found the header line. Skip separator line.
        if i + 1 >= len(lines):
            break
        separator = lines[i + 1]
        if not re.match(r"^\|[-| :]+\|", separator):
            continue

        # Next non-empty line that starts with | is data
        data_line = ""
        for j in range(i + 2, len(lines)):
            candidate = lines[j].strip()
            if candidate.startswith("|"):
                data_line = candidate
                break
            elif candidate == "":
                continue
            else:
                break

        if not data_line:
            continue

        # Find M column position
        m_col = _find_m_column_index(line)

        # Parse data row cells
        data_cells = [c.strip() for c in data_line.split("|")]

        if m_col < 0 or m_col + 5 >= len(data_cells) - 1:
            continue

        # Extract and clean values
        raw_values = []
        for k in range(6):
            cell = data_cells[m_col + k].replace('"', "").replace("+", "").strip()
            if cell == "-":
                raw_values.append(0)  # Fortifications with no movement
            else:
                try:
                    raw_values.append(int(cell))
                except ValueError:
                    raw_values.append(0)

        result = {
            "movement": raw_values[0],
            "toughness": raw_values[1],
            "save": raw_values[2],
            "wounds": raw_values[3],
            "leadership": raw_values[4],
            "objective_control": raw_values[5],
        }

        # Check for INV column (M+6 should be in range)
        if m_col + 6 < len(data_cells) - 1:
            inv_raw = data_cells[m_col + 6].strip()
            # Only treat as INV if it's a number (with optional +)
            if inv_raw and not any(c.isalpha() for c in inv_raw):
                inv_str = inv_raw.replace("+", "").strip()
                with contextlib.suppress(ValueError):
                    result["invulnerable_save"] = int(inv_str)

        return result

    return {}


def _parse_model_count_from_markdown(body: str) -> tuple[int, int] | None:
    match = re.search(r"Размер отряда:\*\*\s*(\d+)[–-](\d+)", body)
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)))


def _parse_points_from_markdown(body: str) -> int | None:
    """Parse unit points from markdown body.

    Supports multiple formats found in wiki files:
    1. **Очки:** 80  or  **Очки:** 80 (10 моделей) / 160 (20 моделей)
    2. **Points:** 125  or  **Points:** 155 | **Role:** ...
    3. **85 pts**  or  **280 points**  or  **30 очков**  (standalone bold)
    4. Tables with a Points/Очки column:
       | Состав | Points |    | Model | Points |
       |:---|---:|        |-------|:------:|
       | 5 Flash Gitz | 135 |    | Painboy | 55 |
    """
    # Pattern 1: Russian **Очки:** (existing)
    match = re.search(r"\*\*Очки:\*\*\s*(\d+)", body)
    if match:
        return int(match.group(1))

    # Pattern 2: English **Points:**
    match = re.search(r"\*\*Points:\*\*\s*(\d+)", body)
    if match:
        return int(match.group(1))

    # Pattern 3: Bold number with pts/points/очков suffix (standalone)
    # e.g. **85 pts**, **280 points**, **30 очков**
    match = re.search(r"\*\*(\d+)\s*(?:pts|points|очков)\*\*", body)
    if match:
        return int(match.group(1))

    # Pattern 4: Table with Points/Очки column
    # Find the column index of the Points/Очки header, then extract
    # the value from that column in the first data row.
    lines = body.split("\n")
    for i, line in enumerate(lines):
        if not re.match(r"^\|[-:| ]+\|$", line):
            continue
        if i < 1 or i + 1 >= len(lines):
            continue
        header = lines[i - 1].strip()
        header_cells = [c.strip() for c in header.split("|")]
        # Find which column contains "Points" or "Очки" or "очк"
        points_col = -1
        for ci, cell in enumerate(header_cells):
            if re.search(r"(Points|Очки|очк)", cell, re.IGNORECASE):
                points_col = ci
                break
        if points_col < 0:
            continue

        # Find the first data row after the separator
        for j in range(i + 1, len(lines)):
            candidate = lines[j].strip()
            if not candidate:
                continue
            if re.match(r"^\|[-:| ]+\|$", candidate):
                continue
            if not candidate.startswith("|"):
                continue
            # Extract data cells and get the points column value
            data_cells = [c.strip() for c in candidate.split("|")]
            if points_col < len(data_cells):
                cell_value = data_cells[points_col]
                # Remove bold markers and extract first number
                cell_clean = cell_value.replace("*", "").replace("~", "").strip()
                nums = re.findall(r"\b(\d+)\b", cell_clean)
                if nums:
                    return int(nums[0])
            break

    return None


def _parse_keywords_from_markdown(body: str) -> list[str]:
    match = re.search(r"##\s+Ключевые слова\s*\n\n`([^`]+)`", body, re.IGNORECASE)
    if not match:
        return []
    return [item.strip().title() for item in match.group(1).split(",") if item.strip()]


def _infer_category(keywords: list[str], metadata: dict[str, Any]) -> str:
    normalized_keywords = {keyword.lower() for keyword in keywords}
    metadata_tags = {str(tag).lower() for tag in ensure_list(metadata.get("tags", []))}
    combined = normalized_keywords | metadata_tags
    # Legends — отдельная категория (можно исключить из ростера)
    if str(metadata.get("status", "")).lower() == "legends" or "legends" in combined:
        return "Legends"
    if "epic-hero" in combined or "epic hero" in combined:
        return "Epic Hero"
    if "battleline" in combined:
        return "Battleline"
    if "character" in combined:
        return "Character"
    if "transport" in combined:
        return "Transport"
    if "vehicle" in combined:
        return "Vehicle"
    if "monster" in combined:
        return "Monster"
    return "Infantry"
