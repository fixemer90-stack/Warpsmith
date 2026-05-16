---
title: Task 0.2 — Normalize GameState serialization boundaries
parent: remediation-plan
status: completed
phase: 0 — Canonical Data + Runtime State Stabilization
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

## Verification

- [x] `uv run python -m pytest tests/ -q` — 502 passed, 3 skipped.
- [x] `uv run ruff check backend/state/game_state.py backend/engine/ai/autoplay.py backend/engine/replay.py tests/test_replay.py` — All checks passed.
- [x] `uv run ruff format` — clean.
- [x] `git diff --check` — passes.

## Implementation

**Completed 2026-05-16.** Two divergent `_snapshot_state` implementations consolidated:

1. **Canonical serializer** — `snapshot_game_state()` + `_unit_snapshot()` in `backend/state/game_state.py`.
   Single source of truth. Unit records include: `runtime_unit_id`, `display_name`,
   `canonical_unit_id`, `owner_id`, `player_id` + legacy `id`/`name` aliases for JS.

2. **autoplay.py** — `_snapshot_state` delegates to `snapshot_game_state()`.

3. **replay.py** — `_snapshot_state` and `_unit_snapshot` delegate to canonical versions.

4. **Battle Ready VP** — Re-snapshotted after +10 VP applied.

5. **Tests** — `test_canonical_snapshot_explicit_contract_fields`, `test_battle_ready_vp_in_final_snapshot`, + existing 7 tests.

## Code review — 2026-05-16

**Verdict:** request changes → **FIXED 2026-05-16**.
**Report:** [../reviews/2026-05-16/task-00-02-normalize-gamestate-serialization-boundaries-review.md](../reviews/2026-05-16/task-00-02-normalize-gamestate-serialization-boundaries-review.md)

- ✅ Important 1: Explicit contract fields added (`runtime_unit_id`, `display_name`, `canonical_unit_id`, `owner_id`).
- ✅ Important 2: Battle Ready VP reflected in final persisted snapshot.
- ✅ Suggestion 1: `replay._unit_snapshot(unit)` derives `player_id` from runtime_id.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md` and affected CR artifacts. *(Phase 0 checkpoint recorded in triage-summary.md)*
- [x] `git diff --check` passes for touched files.
