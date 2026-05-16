"""
Runtime unit identity contract — Task 0.1 (remediation-plan.md).

Defines the canonical format for runtime unit IDs used across:
- state maps (PlayerState.units)
- replay events (ReplayEvent.actor_id / target_id)
- AI action selection
- persistence boundaries
- unit_model lookup dicts (Scenario._unit_models)

CONTRACT (see docs/remediation/task-00-01-define-runtime-unit-identity-contract.md):
  - Runtime unit ID MUST be unique within a game.
  - Runtime unit ID MUST be stable across serialization/deserialization/replay.
  - Runtime unit ID MUST NOT be derived from display_name alone.
  - Runtime unit ID format: `p<player_num>:<canonical_id>:<index>`
  - Display name MUST remain separate and MUST NOT be used as a state-map key.
  - Runtime unit IDs are the only authoritative keys for runtime state maps,
    replay events, AI action selection, and persistence boundaries.

Format:   p{player_num}:{canonical_id}:{index}

Examples:
  p1:Nobz:0           — Player 1, Nobz unit, first occurrence
  p2:Fire Warriors:0   — Player 2, Fire Warriors unit, first occurrence
  p1:Gretchin:0        — Player 1, Gretchin, first occurrence
  p1:Gretchin:1        — Player 1, Gretchin, second occurrence (duplicate in roster)
"""

# ── Public API ──────────────────────────────────────────────────────────

RUNTIME_UNIT_ID_SEPARATOR = ":"
_EVENT_IDENTITY_PREFIX = "["
_EVENT_IDENTITY_SUFFIX = "]"


def format_event_identity(actor_id: str | None = None, target_id: str | None = None) -> str:
    """Return log metadata that carries authoritative runtime unit IDs.

    The human-readable log prefix remains display-name based, while this suffix
    lets replay/result parsers recover stable runtime IDs without using display
    labels as keys. Empty IDs are omitted.
    """
    parts = []
    if actor_id:
        parts.append(f"actor_id={actor_id}")
    if target_id:
        parts.append(f"target_id={target_id}")
    if not parts:
        return ""
    return f" {_EVENT_IDENTITY_PREFIX}{'; '.join(parts)}{_EVENT_IDENTITY_SUFFIX}"


def strip_event_identity(line: str) -> tuple[str, dict[str, str]]:
    """Split a log line into human-readable text and runtime-id metadata.

    Metadata format: ``... [actor_id=p1:Boyz:0; target_id=p2:Boyz:0]``.
    IDs may contain spaces, so parsing is delimiter-based on ``;`` rather than
    whitespace.
    """
    stripped = line.strip()
    if not stripped.endswith(_EVENT_IDENTITY_SUFFIX):
        return stripped, {}

    start = stripped.rfind(_EVENT_IDENTITY_PREFIX)
    if start == -1:
        return stripped, {}

    meta_text = stripped[start + 1 : -1]
    metadata: dict[str, str] = {}
    for part in meta_text.split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key in {"actor_id", "target_id"} and value:
            metadata[key] = value

    if not metadata:
        return stripped, {}
    return stripped[:start].rstrip(), metadata


def make_runtime_unit_id(player_id: str, canonical_id: str, index: int) -> str:
    """Produce a stable runtime unit ID.

    Args:
        player_id:   Player identifier — '1' or '2' (or 'p1'/'p2').
                     The 'p' prefix is stripped if present.
        canonical_id: Canonical unit name / roster slot id (e.g. 'Nobz').
        index:        Occurrence index — 0-based counter for duplicates
                     of the same canonical unit within one player's roster.

    Returns:
        Runtime unit ID string, e.g. 'p1:Nobz:0'.
    """
    pid = player_id.lstrip("pP")
    return f"p{pid}{RUNTIME_UNIT_ID_SEPARATOR}{canonical_id}{RUNTIME_UNIT_ID_SEPARATOR}{index}"


def parse_runtime_unit_id(runtime_id: str) -> dict[str, str | int]:
    """Parse a runtime unit ID into its components.

    Returns dict with keys: player_num (int), canonical_id (str), index (int).

    Raises ValueError if the format is invalid.
    """
    parts = runtime_id.split(RUNTIME_UNIT_ID_SEPARATOR)
    if len(parts) != 3 or not parts[0].startswith("p"):
        msg = (
            f"Invalid runtime unit ID '{runtime_id}'. "
            f"Expected format: p<player_num>:<canonical_id>:<index>"
        )
        raise ValueError(msg)
    try:
        player_num = int(parts[0][1:])
    except ValueError:
        msg = f"Invalid player number in runtime unit ID '{runtime_id}'"
        raise ValueError(msg) from None
    if not parts[1]:
        msg = f"Invalid runtime unit ID '{runtime_id}': canonical_id must not be empty"
        raise ValueError(msg)
    try:
        index = int(parts[2])
    except ValueError:
        msg = f"Invalid index in runtime unit ID '{runtime_id}'"
        raise ValueError(msg) from None
    return {"player_num": player_num, "canonical_id": parts[1], "index": index}


def is_valid_runtime_unit_id(runtime_id: str) -> bool:
    """Check whether a string conforms to the runtime unit ID format."""
    try:
        parse_runtime_unit_id(runtime_id)
    except ValueError:
        return False
    return True
