---
title: "Task 0.3 — Stop destructive DB/replay behavior before further fixes"
parent: remediation-plan
status: pending
phase: "0 — Canonical Data + Runtime State Stabilization"
task_id: "0.3"
source: remediation-plan.md
---

# Task 0.3 — Stop destructive DB/replay behavior before further fixes

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [0.2 — Normalize GameState serialization boundaries](task-00-02-normalize-gamestate-serialization-boundaries.md)
**Next:** [1.1 — Create content contract tests](task-01-01-create-content-contract-tests.md)

## Phase context

**Phase:** 0 — Canonical Data + Runtime State Stabilization
**Purpose:** establish stable runtime identity and canonical game state before touching validators, combat, movement, replay, or AI.
**Primary CRs:** CR-05, CR-06, CR-12, CR-14, CR-20.
**Dependencies:** [0.2 — Normalize GameState serialization boundaries](task-00-02-normalize-gamestate-serialization-boundaries.md)

## Objective

remove data-loss risks that can hide later regressions.

## Acceptance criteria

- [ ] Existing replay rows survive app startup and DB initialization.
- [ ] Startup and migration code are additive/non-destructive by default.
- [ ] No startup path deletes, truncates, or recreates replay tables containing existing data unless running an explicit isolated test reset path.
- [ ] Replay identity is generated independently from simulation seed.
- [ ] Simulation seed may be stored as replay metadata, but MUST NOT be reused as durable `replay_id` by default.
- [ ] Replay save fails with a controlled error on duplicate `replay_id` by default.
- [ ] Replay overwrite is allowed only when caller passes explicit `overwrite=True` / `replace=True`.
- [ ] Fixed seed produces repeatable simulation behavior but distinct durable replay ids across separate save attempts unless `replay_id` is explicitly provided.
- [ ] Test fixtures may reset DB only through isolated test setup helpers, not production startup/migration code.
- [ ] Do not solve this by disabling tests or by changing tests to accept replay deletion.
- [ ] Tests cover database initialization preserving existing replay rows, duplicate `replay_id` save failing by default, duplicate `replay_id` save succeeding only with explicit overwrite, same fixed seed creating different replay ids across separate save attempts, replay metadata storing seed when provided, and production startup path not calling destructive reset helpers.

## Replay persistence contract

- Replay identity MUST be generated independently from simulation seed.
- Simulation seed MAY be stored as replay metadata.
- Replay save MUST fail on duplicate `replay_id` by default.
- Replay overwrite is allowed only when caller passes explicit `overwrite=True` / `replace=True`.
- Startup and migration code MUST be additive/non-destructive by default.
- No startup path may delete, truncate, or recreate replay tables containing existing data unless running an explicit test reset path.

## Non-goals

- Replay schema redesign is not in scope.
- Replay playback logic changes are not in scope except where required to preserve/load existing replay ids.

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

- [ ] `uv run python -m pytest tests/test_replay.py tests/test_db*.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
