---
title: "Task 0.1 — Define runtime unit identity contract"
parent: remediation-plan
status: pending
phase: "0 — Canonical Data + Runtime State Stabilization"
task_id: "0.1"
source: remediation-plan.md
---

# Task 0.1 — Define runtime unit identity contract

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** none
**Next:** [0.2 — Normalize GameState serialization boundaries](task-00-02-normalize-gamestate-serialization-boundaries.md)

## Phase context

**Phase:** 0 — Canonical Data + Runtime State Stabilization
**Purpose:** establish stable runtime identity and canonical game state before touching validators, combat, movement, replay, or AI.
**Primary CRs:** CR-05, CR-06, CR-12, CR-14, CR-20.
**Dependencies:** none

## Objective

every runtime unit has a stable unique id independent of display name.

## Acceptance criteria

- [ ] Runtime unit ids are the only authoritative keys for runtime state maps, replay events, AI action selection, and persistence boundaries.
- [ ] Display names are UI/log metadata only; display name remains available separately and MUST NOT be used as a state-map key.
- [ ] Runtime ids are unique within a game.
- [ ] Runtime ids are stable across serialization, deserialization, save/load, and replay reconstruction.
- [ ] Runtime ids are not derived from `display_name` alone.
- [ ] Runtime ids include player/roster scope, canonical unit id or roster slot id, and occurrence index, e.g. `p1:<canonical_unit_id>:<index>` or equivalent documented format.
- [ ] State maps are keyed by `runtime_unit_id`, not `display_name`.
- [ ] Replay events reference `runtime_unit_id`, with display labels included only as denormalized readable metadata where needed.
- [ ] AI/autoplay selects and acts on units by `runtime_unit_id`.
- [ ] Database persistence preserves `runtime_unit_id` across save/load.
- [ ] Duplicate unit names across players no longer collide in state maps.
- [ ] Tests cover same display name in both armies, two identical units in one roster, save/load preserving runtime ids, replay using runtime ids instead of display names, and AI/autoplay not collapsing same-name units.

## Runtime unit id contract

- Runtime unit id MUST be unique within a game.
- Runtime unit id MUST be stable across serialization/deserialization/replay.
- Runtime unit id MUST NOT be derived from `display_name` alone.
- Runtime unit id SHOULD be composed from player scope, canonical unit id or roster slot id, and occurrence index.
- Runtime unit id format MUST be documented in code/tests, for example `p1:<canonical_unit_id>:<index>`.
- Display name MUST remain separate and MUST NOT be used as map key.
- Runtime unit ids are the only authoritative keys for runtime state maps, replay events, AI action selection, and persistence boundaries.

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

- [ ] `uv run python -m pytest tests/test_game_state.py tests/test_autoplay.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
