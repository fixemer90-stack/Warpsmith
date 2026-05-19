---
title: "Task 6.1 — Persist authoritative final snapshot"
parent: remediation-plan
status: completed
phase: "6 — Replay/result authoritative state"
task_id: "6.1"
source: remediation-plan.md
---

# Task 6.1 — Persist authoritative final snapshot

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [5.3 — Fix terrain/LoS movement-related blockers](task-05-03-fix-terrain-los-movement-related-blockers.md)
**Next:** [6.2 — Fix event parsing and summary attribution](task-06-02-fix-event-parsing-and-summary-attribution.md)

## Phase context

**Phase:** 6 — Replay/result authoritative state
**Purpose:** make persisted replay and result pages derive from one authoritative final state.
**Primary CRs:** CR-14, CR-18, CR-24.
**Dependencies:** Phase 5 checkpoint

## Objective

final replay/result state includes all post-game scoring and final unit state.

## Acceptance criteria

- [x] Battle Ready VP is included in final persisted state.
- [x] `/api/results/{game_id}` and `/result/{game_id}` show same final VP.
- [x] VP chart/stat cards use the same authoritative source.

## Files likely touched

- `backend/engine/ai/autoplay.py`
- `backend/engine/replay.py`
- `web/routes/api_replays.py`
- `web/static/replay_viewer.js`
- `web/static/result_chart.js`
- `web/templates/result.html`
- `tests/test_replay.py`
- `tests/test_round_viewer.py`
- `tests/test_result_screen.py`

## Verification

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_autoplay.py tests/test_replay.py tests/test_result_screen.py -q` → 66 passed, 12 warnings.
- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 630 passed, 3 skipped, 60 warnings.
- [x] `uv run ruff check backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_autoplay.py tests/test_result_screen.py tests/test_replay.py` → All checks passed.
- [x] `uv run ruff format --check backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_autoplay.py tests/test_result_screen.py tests/test_replay.py` → 5 files already formatted.
- [x] `node -c web/static/result_chart.js` → syntax OK.
- [x] `git diff --check -- backend/engine/ai/autoplay.py web/routes/api_replays.py web/static/result_chart.js web/templates/result.html tests/test_autoplay.py tests/test_result_screen.py tests/test_replay.py` → clean.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [x] `git diff --check` passes for touched files.

## Re-check — 2026-05-19

Verdict: FIXED after re-check.

Finding fixed:
- `/api/results/{game_id}` still preserved stale `summary.final_victory_points` and stale `summary.winner` when `summary.final_state` was authoritative. This could make API consumers and the result page prefer stale post-game scoring metadata even though the final snapshot was correct.

Resolution:
- `web/routes/api_replays.py` now overwrites `summary.final_victory_points` from authoritative `final_state.victory_points` and recomputes `summary.winner` from the same source, including draws.
- Added `test_results_api_overrides_stale_summary_vp_and_winner` to lock the stale-summary regression.
- Custom persistence probe confirmed `GameState` VP, last replay `end_state.victory_points`, `summary.final_victory_points`, saved replay, and loaded replay all match: `{"state_vp": {"1": 13, "2": 10}, "persisted_vp": {"1": 13, "2": 10}}`.

Re-check verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_autoplay.py tests/test_replay.py tests/test_result_screen.py -q` → 66 passed, 12 warnings.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 630 passed, 3 skipped, 60 warnings.
- `uv run ruff check backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_autoplay.py tests/test_result_screen.py tests/test_replay.py` → All checks passed.
- `uv run ruff format --check backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_autoplay.py tests/test_result_screen.py tests/test_replay.py` → 5 files already formatted.
- `git diff --check -- backend/engine/ai/autoplay.py web/routes/api_replays.py web/static/result_chart.js web/templates/result.html tests/test_autoplay.py tests/test_result_screen.py tests/test_replay.py` → clean.
