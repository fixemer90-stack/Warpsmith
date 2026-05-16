---
title: "Task 4.1 — Assert 5-phase 10e loop invariants"
parent: remediation-plan
status: pending
phase: "4 — Game state / VP / phase invariants"
task_id: "4.1"
source: remediation-plan.md
---

# Task 4.1 — Assert 5-phase 10e loop invariants

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [3.3 — Fix Sustained Hits resolution](task-03-03-fix-sustained-hits-resolution.md)
**Next:** [4.2 — Lock CP and battle-shock reset semantics](task-04-02-lock-cp-and-battle-shock-reset-semantics.md)

## Phase context

**Phase:** 4 — Game state / VP / phase invariants
**Purpose:** lock 10e phase flow, CP/VP, battle-shock, objective control, and end-game invariants.
**Primary CRs:** CR-08, CR-10, CR-14, CR-24.
**Dependencies:** Phase 2, 3 checkpoint

## Objective

Command -> Movement -> Shooting -> Charge -> Fight only.

## Acceptance criteria

- [ ] GamePhase has exactly 5 members.
- [ ] Battle-shock runs in Command, not separate Morale.
- [ ] Round increments after Fight only.

## Files likely touched

- `backend/state/game_state.py`
- `backend/state/mission.py`
- `backend/engine/scenario.py`
- `backend/engine/ai/autoplay.py`
- `tests/test_game_state.py`
- `tests/test_scenario.py`
- `tests/test_mission*.py`
- `tests/test_autoplay.py`

## Verification

- [ ] `uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
