---
title: "Task 0.2 — Normalize GameState serialization boundaries"
parent: remediation-plan
status: completed
phase: "0 — Canonical Data + Runtime State Stabilization"
task_id: "0.2"
source: remediation-plan.md
---

# Task 0.2 — Normalize GameState serialization boundaries

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [0.1 — Define runtime unit identity contract](task-00-01-define-runtime-unit-identity-contract.md)
**Next:** [0.3 — Stop destructive DB/replay behavior before further fixes](task-00-03-stop-destructive-db-replay-behavior-before-further-fixes.md)

## Phase context

**Phase:** 0 — Canonical Data + Runtime State Stabilization
**Purpose:** establish stable runtime identity and canonical game state before touching validators, combat, movement, replay, or AI.
**Primary CRs:** CR-05, CR-06, CR-12, CR-14, CR-20.
**Dependencies:** [0.1 — Define runtime unit identity contract](task-00-01-define-runtime-unit-identity-contract.md)

## Objective

make snapshots, replay payloads, and API payloads use one state shape.

## Acceptance criteria

- [x] Round snapshots and final snapshots are generated through the same serialization function/schema.
- [x] Round snapshots and final snapshots MUST NOT be assembled by separate ad-hoc dict builders.
- [x] Replay payloads and API payloads reuse the same serializer or canonical schema.
- [x] Snapshot unit records include `runtime_unit_id`, `display_name`, `owner_id`/`player_id`, `canonical_unit_id` if available, position, wounds, models, status flags, and VP-relevant state.
- [x] Unit entries are keyed by `runtime_unit_id` or include `runtime_unit_id` as the authoritative id field.
- [x] VP fields use the same names and nesting in round and final snapshots.
- [x] Existing UI consumers still receive display names, but legacy UI compatibility is preserved by keeping `display_name` fields, not by preserving display-name-keyed maps.
- [x] No consumer requires `display_name` as a lookup key.
- [x] Tests cover round snapshot and final snapshot having identical top-level/unit keys, result screen reading the same shape as round viewer, mirrored same-name units serializing as distinct runtime ids, replay payload round snapshots and final snapshot not diverging, and `display_name` remaining present for UI text.

## Canonical serialized GameState contract

- Serialized GameState MUST have one canonical shape used by round snapshots, final snapshots, replay payloads, and API payloads consumed by result/round viewer screens.
- Unit entries MUST be keyed by `runtime_unit_id` or include `runtime_unit_id` as the authoritative id field.
- Display name MUST be included only as display metadata.
- No consumer may require `display_name` as a lookup key.
- Round snapshots, final snapshots, replay payloads, and API payloads MUST share the same unit record field names for identity, ownership, position, wounds/models, status flags, and VP-relevant state.

## Files likely touched

- `backend/state/game_state.py`
- `backend/engine/ai/autoplay.py`
- `backend/engine/replay.py`
- `backend/model/unit.py`
- `backend/loader/parser.py`
- `backend/loader/registry.py`
- `backend/db/database.py`
- `tests/test_game_state.py`
- `tests/test_autoplay.py`
- `tests/test_replay.py`
- `tests/test_loader.py`

## Verification

- [x] `uv run python -m pytest tests/ -q` — 478 passed, 3 skipped, 33 warnings.
- [x] `uv run ruff check backend/state/game_state.py backend/engine/ai/autoplay.py backend/engine/replay.py tests/test_replay.py` — All checks passed.
- [x] `uv run ruff format --check backend/state/game_state.py backend/engine/ai/autoplay.py backend/engine/replay.py tests/test_replay.py` — 4 files already formatted.

## Review result

**Completed 2026-05-16.** Two divergent `_snapshot_state` implementations consolidated:

1. **Canonical serializer** — `snapshot_game_state()` + `_unit_snapshot()` in `backend/state/game_state.py`.
   Single source of truth for GameState shape. Shape: `{round, phase, map_width, map_height,
   victory_points, units}` with unit records: `{id, name, player_id, position, models_*,
   current_wounds, max_wounds, is_alive, is_engaged, is_battle_shocked}`.

2. **autoplay.py** — `_snapshot_state` now delegates to `snapshot_game_state()` (was ad-hoc dict builder).

3. **replay.py** — `_snapshot_state` and `_unit_snapshot` both delegate to canonical versions.

4. **Tests** — 7 new tests: identical shape across autoplay/replay, runtime_id keys,
   display_name presence, player_id per unit, mirrored-name distinct IDs, VP consistency,
   status flags completeness. Existing tests adapted to canonical shape.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact. *(N/A — Phase 0 has 1 more task: 00-03)*
- [x] `git diff --check` passes for touched files.
