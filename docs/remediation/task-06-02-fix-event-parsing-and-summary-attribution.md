---
title: "Task 6.2 — Fix event parsing and summary attribution"
parent: remediation-plan
status: pending
phase: "6 — Replay/result authoritative state"
task_id: "6.2"
source: remediation-plan.md
---

# Task 6.2 — Fix event parsing and summary attribution

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [6.1 — Persist authoritative final snapshot](task-06-01-persist-authoritative-final-snapshot.md)
**Next:** [6.3 — Add repeatable final gate smoke script](task-06-03-add-repeatable-final-gate-smoke-script.md)

## Phase context

**Phase:** 6 — Replay/result authoritative state
**Purpose:** make persisted replay and result pages derive from one authoritative final state.
**Primary CRs:** CR-14, CR-18, CR-24.
**Dependencies:** [6.1 — Persist authoritative final snapshot](task-06-01-persist-authoritative-final-snapshot.md)

## Objective

result summaries derive from scoped ids/structured events, not ambiguous display names.

## Acceptance criteria

- [ ] Kills/damage/charges attributed correctly in same-faction/same-name games.
- [ ] VP logs with totals and Battle Ready parse as VP events or are represented by structured final state.
- [ ] Player 2 charge card can show non-zero normal events.

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

- [ ] `uv run python -m pytest tests/test_result_screen.py tests/test_replay.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
