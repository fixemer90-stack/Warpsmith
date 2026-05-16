---
title: "Task 6.1 — Persist authoritative final snapshot"
parent: remediation-plan
status: pending
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

- [ ] Battle Ready VP is included in final persisted state.
- [ ] `/api/results/{game_id}` and `/result/{game_id}` show same final VP.
- [ ] VP chart/stat cards use the same authoritative source.

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

- [ ] `uv run python -m pytest tests/test_replay.py tests/test_result_screen.py -q`
- [ ] Deterministic generated replay smoke.

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
