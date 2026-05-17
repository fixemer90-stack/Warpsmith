---
title: "Task 4.1 — Assert 5-phase 10e loop invariants"
parent: remediation-plan
status: completed
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

- [x] GamePhase has exactly 5 members.
- [x] Battle-shock runs in Command, not separate Morale.
- [x] Round increments after Fight only.
- [x] Phase progression uses one canonical ordered phase list.
- [x] Autoplay/scenario code consumes the same phase order, not duplicated hardcoded lists.
- [x] Replay/snapshot phase names match the canonical GamePhase values.
- [x] No tests or UI paths expect a separate Morale phase.
- [x] Do not fix this by aliasing Morale/Battle-shock to Command while keeping them as phase enum members.
- [x] Tests cover GamePhase having exactly five members, phase order being Command -> Movement -> Shooting -> Charge -> Fight, advancing from Fight moving to the next player/round boundary as designed, battle-shock hooks running during Command phase, no separate Morale phase appearing in snapshots/replay/scenario progression, and autoplay completing a full turn using only the five phases.

## Phase loop contract

- [x] GamePhase MUST contain exactly `COMMAND`, `MOVEMENT`, `SHOOTING`, `CHARGE`, and `FIGHT`.
- [x] GamePhase MUST NOT contain `MORALE`, `BATTLESHOCK`, `PSYCHIC`, or `END` as runtime phase loop enum members.
- [x] Battle-shock is resolved as a Command phase step.
- [x] Round advances only after both players complete Fight phase, or after the engine's existing full-round boundary if turns are modeled differently.

## Non-goals

- [x] Full battle-shock rules implementation is not in scope.
- [x] Mission scoring redesign is not in scope.
- [x] Turn/round persistence redesign is not in scope unless required to remove invalid phase states.

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

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py -q`

### Verification results (2026-05-17)

```bash
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py -q
80 passed, 12 warnings in 8.20s

$ uv run python -m pytest tests/ -q
593 passed, 3 skipped, 60 warnings in 53.49s

$ uv run ruff check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
All checks passed!

$ uv run ruff format --check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
6 files already formatted

$ git diff --check -- backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
(clean)
```

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] Phase checkpoint artifact N/A — Task 4.1 does not complete Phase 4; Tasks 4.2 and 4.3 remain.
- [x] `git diff --check` passes for touched files.

## Code review — 2026-05-17

Review file: `docs/reviews/2026-05-17/task-04-01-assert-5-phase-10e-loop-invariants-review.md`

**Verdict: REQUEST CHANGES → FIXED 2026-05-17.**

All 5 findings resolved:

| Finding | Fix |
|---------|-----|
| Ruff/format gates failed | Formatted and lint-fixed Task 4.1 touched Python files. |
| Verification evidence stale | Re-ran focused suite (`80 passed`), full suite (`593 passed, 3 skipped`), lint, format, and diff-check; updated task and CR evidence. |
| Test coverage AC not fully proven | Added canonical phase-order export test, scenario full-round phase-log test, replay/autoplay snapshot phase-value test, and autoplay full-turn five-phase invariant test. |
| Shared phase-order contract incomplete | Added `GAME_PHASE_ORDER` in `backend/state/game_state.py`; `GameState.next_phase()` and `Scenario.run_round()` now consume it. |
| Closure artifacts incomplete | Synced task file, source plan, index, review Resolution, and CR-08/CR-10/CR-14/CR-24 regression evidence. |
