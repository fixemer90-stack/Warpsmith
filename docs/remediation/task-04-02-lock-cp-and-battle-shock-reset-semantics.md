---
title: "Task 4.2 — Lock CP and battle-shock reset semantics"
parent: remediation-plan
status: completed
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

- [x] Both players start the game with 0 CP.
- [x] Each player gains exactly +1 CP at the start of their own Command phase unless a future explicit rule modifies this.
- [x] CP gain happens once per player turn, not once per phase transition and not once per full battle round.
- [x] Repeated Command phase processing is idempotent for CP unless the call explicitly advances turn state.
- [x] The opponent does not gain CP during the active player's Command phase.
- [x] There is no Warlord-based starting CP and no Warlord-based bonus CP.
- [x] `is_battle_shocked` is cleared only during that unit owner's Command phase reset step.
- [x] Battle-shock reset does not occur during Movement, Shooting, Charge, or Fight.
- [x] `has_advanced` is cleared at the start of a new battle round before any unit acts.
- [x] Round-level flags and turn-level flags are reset at separate explicit boundaries.
- [x] Do not hide old Warlord CP behavior behind default config or compatibility paths.

## Acceptance criteria

- [x] Both players start with 0 CP.
- [x] Active player gains +1 CP on their own Command phase.
- [x] Opponent does not gain CP during active player Command phase.
- [x] No Warlord CP bonus is applied.
- [x] CP gain happens once per player turn, not once per phase transition or full round.
- [x] Repeated Command phase processing is idempotent for CP unless explicitly advancing turn state.
- [x] `is_battle_shocked` clears in Command only, during that unit owner's Command phase reset step.
- [x] `is_battle_shocked` remains set through Movement, Shooting, Charge, and Fight.
- [x] `has_advanced` resets at the new battle-round boundary before any unit acts.
- [x] Round-level flags and turn-level flags are reset at separate explicit boundaries.

## Tests

- [x] Both players start with 0 CP.
- [x] Player gains +1 CP on own Command phase.
- [x] Opponent does not gain CP during active player Command phase.
- [x] No Warlord CP bonus is applied.
- [x] Battle-shock clears in Command only.
- [x] Battle-shock remains set through non-Command phases.
- [x] `has_advanced` clears at new round boundary.
- [x] CP is not double-awarded when snapshots, replay, or autoplay touch Command logic.

## Non-goals

- [x] Stratagem CP spending/refund rules are not in scope.
- [x] Faction-specific CP generation is not in scope.
- [x] Full battle-shock test/rules implementation is not in scope.

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

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q`
- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py -q`
- [x] `uv run python -m pytest tests/ -q`
- [x] `uv run ruff check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py`
- [x] `uv run ruff format --check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py`
- [x] `git diff --check -- backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py docs/remediation/task-04-02-lock-cp-and-battle-shock-reset-semantics.md docs/remediation/remediation-plan.md docs/remediation/index.md docs/reviews/2026-05-18/task-04-02-lock-cp-and-battle-shock-reset-semantics-review.md docs/reviews/2026-05-10/triage-summary.md docs/requirements/code-review/code-review.md docs/requirements/code-review/cr-08-game-state-and-phase-machine-review.md docs/requirements/code-review/cr-10-mission-objectives-and-vp-review.md docs/requirements/code-review/cr-14-autoplay-replay-and-result-review.md docs/requirements/code-review/cr-24-final-integration-regression-gate.md`
- [x] `curl -sS http://127.0.0.1:8000/api/health`

### Verification results (2026-05-18)

```text
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q
28 passed in 0.62s

$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py -q
42 passed in 0.78s

$ uv run python -m pytest tests/ -q
602 passed, 3 skipped, 60 warnings in 52.82s

$ uv run ruff check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py
All checks passed!

$ uv run ruff format --check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py
4 files already formatted

$ git diff --check -- backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py docs/remediation/task-04-02-lock-cp-and-battle-shock-reset-semantics.md docs/remediation/task-04-03-lock-vp-objectives-mission-normalization-battle-ready.md docs/remediation/remediation-plan.md docs/remediation/index.md docs/reviews/2026-05-18/task-04-02-lock-cp-and-battle-shock-reset-semantics-review.md docs/reviews/2026-05-10/triage-summary.md docs/requirements/code-review/code-review.md docs/requirements/code-review/cr-08-game-state-and-phase-machine-review.md docs/requirements/code-review/cr-10-mission-objectives-and-vp-review.md docs/requirements/code-review/cr-14-autoplay-replay-and-result-review.md docs/requirements/code-review/cr-24-final-integration-regression-gate.md
(clean)

$ curl -sS http://127.0.0.1:8000/api/health
{"status":"ok","version":"0.7.9"}
```

Deterministic probe after fix:

```text
start_cp 0 0
after_command_cp 1 0
after_command_shock False True
after_repeated_command_cp 1 0
after_repeated_command_shock False True
shock_after_movement True True
shock_after_shooting True True
shock_after_charge True True
shock_after_fight True True
after_p2_command_cp 1 1
after_p2_command_shock True False
```

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [x] `git diff --check` passes for touched files.

## Code review — 2026-05-18

Review file: `docs/reviews/2026-05-18/task-04-02-lock-cp-and-battle-shock-reset-semantics-review.md`

**Verdict: REQUEST CHANGES → FIXED 2026-05-18.**

All 5 findings resolved:

| Finding | Fix |
| --- | --- |
| Command phase awarded CP to all players | `Scenario._command_phase()` now resolves a single active command owner via `GameState.active_player`, command priority, or first player fallback; CP is awarded only to that owner. |
| Command CP was not idempotent | `Scenario` tracks processed `(round, active_player)` Command turns and skips duplicate CP/reset processing until the active player or round changes. |
| Battle-shock reset cleared all owners | Command reset now clears `is_battle_shocked` only on the active owner's units; `_battle_shock_tests()` is scoped to the active owner. |
| Tests encoded the bug | Replaced contradictory expectations and added regressions for opponent CP, explicit next-player Command CP, owner-scoped battle-shock reset, and CP cap behavior. |
| Closure artifacts were stale | Synced task file, review resolution, source plan, index, CR-08/10/14/24 evidence, triage summary, and code-review checkpoint evidence with current verification. |
