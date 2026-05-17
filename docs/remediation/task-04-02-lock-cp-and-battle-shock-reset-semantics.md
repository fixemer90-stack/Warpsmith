---
title: "Task 4.2 — Lock CP and battle-shock reset semantics"
parent: remediation-plan
status: pending
phase: "4 — Game state / VP / phase invariants"
task_id: "4.2"
source: remediation-plan.md
---

# Task 4.2 — Lock CP and battle-shock reset semantics

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [4.1 — Assert 5-phase 10e loop invariants](task-04-01-assert-5-phase-10e-loop-invariants.md)
**Next:** [4.3 — Lock VP, objectives, mission normalization, Battle Ready](task-04-03-lock-vp-objectives-mission-normalization-battle-ready.md)

## Phase context

**Phase:** 4 — Game state / VP / phase invariants
**Purpose:** lock 10e phase flow, CP/VP, battle-shock, objective control, and end-game invariants.
**Primary CRs:** CR-08, CR-10, CR-14, CR-24.
**Dependencies:** [4.1 — Assert 5-phase 10e loop invariants](task-04-01-assert-5-phase-10e-loop-invariants.md)

## Objective

CP starts at 0, each player gains CP only at the start of their own Command phase, and reset semantics are split across explicit turn and round boundaries.

## CP / reset semantics contract

- [ ] Both players start the game with 0 CP.
- [ ] Each player gains exactly +1 CP at the start of their own Command phase unless a future explicit rule modifies this.
- [ ] CP gain happens once per player turn, not once per phase transition and not once per full battle round.
- [ ] Repeated Command phase processing is idempotent for CP unless the call explicitly advances turn state.
- [ ] The opponent does not gain CP during the active player’s Command phase.
- [ ] There is no Warlord-based starting CP and no Warlord-based bonus CP.
- [ ] `is_battle_shocked` is cleared only during that unit owner’s Command phase reset step.
- [ ] Battle-shock reset does not occur during Movement, Shooting, Charge, or Fight.
- [ ] `has_advanced` is cleared at the start of a new battle round before any unit acts.
- [ ] Round-level flags and turn-level flags are reset at separate explicit boundaries.
- [ ] Do not hide old Warlord CP behavior behind default config or compatibility paths.

## Acceptance criteria

- [ ] Both players start with 0 CP.
- [ ] Active player gains +1 CP on their own Command phase.
- [ ] Opponent does not gain CP during active player Command phase.
- [ ] No Warlord CP bonus is applied.
- [ ] CP gain happens once per player turn, not once per phase transition or full round.
- [ ] Repeated Command phase processing is idempotent for CP unless explicitly advancing turn state.
- [ ] `is_battle_shocked` clears in Command only, during that unit owner’s Command phase reset step.
- [ ] `is_battle_shocked` remains set through Movement, Shooting, Charge, and Fight.
- [ ] `has_advanced` resets at the new battle-round boundary before any unit acts.
- [ ] Round-level flags and turn-level flags are reset at separate explicit boundaries.

## Tests

- [ ] Both players start with 0 CP.
- [ ] Player gains +1 CP on own Command phase.
- [ ] Opponent does not gain CP during active player Command phase.
- [ ] No Warlord CP bonus is applied.
- [ ] Battle-shock clears in Command only.
- [ ] Battle-shock remains set through non-Command phases.
- [ ] `has_advanced` clears at new round boundary.
- [ ] CP is not double-awarded when snapshots, replay, or autoplay touch Command logic.

## Non-goals

- [ ] Stratagem CP spending/refund rules are not in scope.
- [ ] Faction-specific CP generation is not in scope.
- [ ] Full battle-shock test/rules implementation is not in scope.

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
