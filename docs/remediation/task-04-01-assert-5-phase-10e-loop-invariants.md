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
- [ ] Phase progression uses one canonical ordered phase list.
- [ ] Autoplay/scenario code consumes the same phase order, not duplicated hardcoded lists.
- [ ] Replay/snapshot phase names match the canonical GamePhase values.
- [ ] No tests or UI paths expect a separate Morale phase.
- [ ] Do not fix this by aliasing Morale/Battle-shock to Command while keeping them as phase enum members.
- [ ] Tests cover GamePhase having exactly five members, phase order being Command -> Movement -> Shooting -> Charge -> Fight, advancing from Fight moving to the next player/round boundary as designed, battle-shock hooks running during Command phase, no separate Morale phase appearing in snapshots/replay/scenario progression, and autoplay completing a full turn using only the five phases.

## Phase loop contract

- [ ] GamePhase MUST contain exactly `COMMAND`, `MOVEMENT`, `SHOOTING`, `CHARGE`, and `FIGHT`.
- [ ] GamePhase MUST NOT contain `MORALE`, `BATTLESHOCK`, `PSYCHIC`, or `END` as runtime phase loop enum members.
- [ ] Battle-shock is resolved as a Command phase step.
- [ ] Round advances only after both players complete Fight phase, or after the engine's existing full-round boundary if turns are modeled differently.

## Non-goals

- [ ] Full battle-shock rules implementation is not in scope.
- [ ] Mission scoring redesign is not in scope.
- [ ] Turn/round persistence redesign is not in scope unless required to remove invalid phase states.

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
