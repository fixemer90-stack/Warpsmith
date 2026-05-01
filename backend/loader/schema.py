"""Validation and coercion helpers for wiki frontmatter."""

from typing import Any


def parse_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in {"", "none", "-"}:
        return None
    return int(str(value).replace("+", "").strip())


def parse_model_count(value: Any) -> tuple[int, int]:
    if isinstance(value, tuple) and len(value) == 2:
        return (int(value[0]), int(value[1]))
    if isinstance(value, list) and len(value) == 2:
        return (int(value[0]), int(value[1]))
    if isinstance(value, str):
        normalized = value.replace(" ", "")
        if "-" in normalized:
            min_count, max_count = normalized.split("-", 1)
            return (int(min_count), int(max_count))
        count = int(normalized)
        return (count, count)
    return (1, 1)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]
