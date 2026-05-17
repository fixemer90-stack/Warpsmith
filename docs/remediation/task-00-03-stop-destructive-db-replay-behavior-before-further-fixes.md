---
title: Task 0.3 — Stop destructive DB/replay behavior before further fixes
parent: remediation-plan
status: completed
phase: 0 — Canonical Data + Runtime State Stabilization
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

- [x] Existing replay rows survive app startup and DB initialization.
- [x] Startup and migration code are additive/non-destructive by default.
- [x] No startup path deletes, truncates, or recreates replay tables containing existing data unless running an explicit isolated test reset path.
- [x] Replay identity is generated independently from simulation seed.
- [x] Simulation seed may be stored as replay metadata, but MUST NOT be reused as durable `replay_id` by default.
- [x] Replay save fails with a controlled error on duplicate `replay_id` by default.
- [x] Replay overwrite is allowed only when caller passes explicit `overwrite=True` / `replace=True`.
- [x] Fixed seed produces repeatable simulation behavior but distinct durable replay ids across separate save attempts unless `replay_id` is explicitly provided.
- [x] Test fixtures may reset DB only through isolated test setup helpers, not production startup/migration code.
- [x] Do not solve this by disabling tests or by changing tests to accept replay deletion.
- [x] Tests cover database initialization preserving existing replay rows, duplicate `replay_id` save failing by default, duplicate `replay_id` save succeeding only with explicit overwrite, same fixed seed creating different replay ids across separate save attempts, replay metadata storing seed when provided, and production startup path not calling destructive reset helpers.

## Replay persistence contract

- Replay identity MUST be generated independently from simulation seed.
- Simulation seed MAY be stored as replay metadata.
- Replay save MUST fail on duplicate `replay_id` by default.
- Replay overwrite is allowed only when caller passes explicit `overwrite=True` / `replace=True`.
- Startup and migration code MUST be additive/non-destructive by default.
- No startup path may delete, truncate, or recreate replay tables containing existing data unless running an explicit test reset path.

## Verification

- [x] `uv run python -m pytest tests/ -q` — 502 passed, 3 skipped.
- [x] `uv run ruff check backend/db/database.py backend/engine/replay.py backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_replay.py` — All checks passed.
- [x] `uv run ruff format` — clean.
- [x] `git diff --check` — passes (exit 0).

## Implementation

**Completed 2026-05-16.** Three data-loss risks eliminated:

1. **DROP TABLE removed** — `database.py:migrate()` no longer drops replays table.
   `test_db_init_preserves_existing_replay_rows` — replay survives migrate().

2. **save_replay INSERT by default** — `INSERT` (IntegrityError on dup).
   `overwrite=True` for explicit replacement.
   `test_save_replay_fails_on_duplicate_by_default`, `test_save_replay_succeeds_with_overwrite`.

3. **game_id independent from seed** — `f"auto_{uuid.uuid4().hex[:12]}"`.
   `test_same_seed_produces_different_replay_ids` — real autoplay integration:
   calls `run_auto_game()` twice with seed=4242, asserts distinct UUID game_ids.

6 tests. `test_production_startup_no_destructive_reset` asserts migrate() source is clean.

## Code review — 2026-05-16

**Verdict:** request changes → **FIXED 2026-05-16**.
**Report:** [../reviews/2026-05-16/task-00-03-stop-destructive-db-replay-behavior-before-further-fixes-review.md](../reviews/2026-05-16/task-00-03-stop-destructive-db-replay-behavior-before-further-fixes-review.md)

- ✅ Important 1: CRLF fixed, `git diff --check` passes (exit 0).
- ✅ Important 2: `test_same_seed_produces_different_replay_ids` calls real autoplay path.
- ✅ Suggestion 1: `code-review.md` intentionally not updated — Phase checkpoint in `triage-summary.md`.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md` and affected CR artifacts. *(Phase 0 checkpoint recorded)*
- [x] `git diff --check` passes for touched files.

### Phase 0 checkpoint

Phase 0 is **complete**. All three tasks (0.1, 0.2, 0.3) finished and review-approved.
Established: stable runtime unit identity, canonical GameState serialization, non-destructive DB/replay persistence.
