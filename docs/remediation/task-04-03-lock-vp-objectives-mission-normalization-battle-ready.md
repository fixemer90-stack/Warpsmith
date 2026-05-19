---
title: "Task 4.3 — Lock VP, objectives, mission normalization, Battle Ready"
parent: remediation-plan
status: changes_requested
phase: "4 — Game state / VP / phase invariants"
task_id: "4.3"
source: remediation-plan.md
---

# Task 4.3 — Lock VP, objectives, mission normalization, Battle Ready

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [4.2 — Lock CP and battle-shock reset semantics](task-04-02-lock-cp-and-battle-shock-reset-semantics.md)
**Next:** [5.1 — Fix charge destination and engagement identity](task-05-01-fix-charge-destination-and-engagement-identity.md)

## Phase context

**Phase:** 4 — Game state / VP / phase invariants
**Purpose:** lock 10e phase flow, CP/VP, battle-shock, objective control, and end-game invariants.
**Primary CRs:** CR-08, CR-10, CR-14, CR-24.
**Dependencies:** [4.2 — Lock CP and battle-shock reset semantics](task-04-02-lock-cp-and-battle-shock-reset-semantics.md)

## Objective

VP source is deterministic, 10e-aligned, and shared by runtime, replay, result screen, and autoplay.

## VP / mission scoring contract

- [x] Mission names are normalized before lookup/comparison using a deterministic normalization function.
- [x] Battle Ready is a post-game bonus applied exactly once to the final authoritative VP state.
- [x] Intermediate snapshots MAY omit Battle Ready, but final authoritative state MUST include it.
- [x] Final authoritative VP state is the single source of truth for result screens and replay summaries.
- [x] Do not solve mission normalization by duplicating alias maps independently across runtime/UI/replay layers.

## Acceptance criteria

- [x] Mission normalization treats whitespace, casing, underscores, and hyphens consistently.
- [ ] Objective scoring values are sourced from normalized mission definitions, not hardcoded ad-hoc comparisons. *(Request changes 2026-05-19: Only War isolated objective scoring returns 5 instead of 3; Purge the Foe returns 0 instead of 5.)*
- [ ] Dynamic objectives: Only War 3 VP, Take and Hold 5 VP, Purge the Foe 5 VP. *(Request changes 2026-05-19: deterministic probe returned Only War 5, Take and Hold 5, Purge the Foe 0.)*
- [x] Battle Ready +10 VP is applied exactly once and visible in final authoritative state.
- [x] Replay, result screen, and final snapshot display the same final VP totals.
- [x] Game termination is driven by round cap, army wipe/table state, and explicit mission-end conditions, not arbitrary VP thresholds.
- [x] Game does not end early at `VP >= 10`.

## Tests

- [x] Mission name normalization with spaces, hyphens, underscores, and case variants.
- [ ] Only War dynamic objective awards 3 VP. *(Request changes 2026-05-19: isolated objective probe returned 5 VP.)*
- [x] Take and Hold awards 5 VP.
- [ ] Purge the Foe awards 5 VP. *(Request changes 2026-05-19: isolated objective probe returned 0 VP.)*
- [ ] Battle Ready applies exactly once. *(Request changes 2026-05-19: no test assertion found in mission/autoplay/result-screen tests.)*
- [ ] Repeated finalization does not duplicate Battle Ready. *(Request changes 2026-05-19: no finalization idempotence regression found.)*
- [ ] Final replay/result snapshot includes Battle Ready VP. *(Request changes 2026-05-19: no final replay/result parity regression found.)*
- [x] Game does not end at `VP >= 10`.
- [x] Game ends correctly by round cap or wipe condition.

## Non-goals

- [x] Secondary objective system redesign is not in scope.
- [x] Tournament scoring variants are not in scope.
- [x] UI redesign for result presentation is not in scope.

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

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q`

### Verification results (2026-05-19 — Phase 4 re-check)

```text
$ uv run python - <<'PY'
# deterministic Phase 4 probes for phase order, mission VP values, VP sync, VP cap
PY
phase_order ['command', 'movement', 'shooting', 'charge', 'fight'] enum_count 5
mission_score Only War {'p1': 5, 'p2': 0}
mission_score Take and Hold {'p1': 5, 'p2': 0}
mission_score Purge the Foe {'p1': 0, 'p2': 0}
vp_sync no_profiles {1: 5, 2: 0} {'p1': 5, 'p2': 0} {'p1': 1, 'p2': 0}
vp_sync_repeat no_profiles {1: 5, 2: 0} {'p1': 5, 'p2': 0} {'p1': 1, 'p2': 0}
vp_sync profiles {1: 5, 2: 0} {'p1': 5, 'p2': 0} {'p1': 1, 'p2': 0}
vp_sync_repeat profiles {1: 5, 2: 0} {'p1': 5, 'p2': 0} {'p1': 1, 'p2': 0}
vp_cap_check None

$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q
80 passed in 8.55s

$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q
622 passed, 3 skipped, 60 warnings in 51.93s

$ uv run ruff check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py
All checks passed!

$ uv run ruff format --check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py
9 files already formatted
```

Blocking probe results remain: Only War isolated scoring is 5 instead of 3; Purge the Foe isolated scoring is 0 instead of 5; Battle Ready exact-once/final replay-result regressions are still missing.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s). *(Request changes 2026-05-19: superseding Phase 4 re-check recorded Task 4.3 as still blocking.)*
- [ ] Phase checkpoint blocked: `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-NN-*.md`, and `docs/requirements/code-review/code-review.md` must remain non-final until Task 4.3 probes/tests pass.
- [x] `git diff --check` passes for touched files.

## Code review — 2026-05-18

Review file: `docs/reviews/2026-05-18/task-04-03-lock-vp-objectives-mission-normalization-battle-ready-check.md`

**Verdict: REQUEST CHANGES → FIXED 2026-05-18.**

All blocking findings resolved:

| Finding | Fix |
| --- | --- |
| Mission scoring values not mission-defined | Added `vp_per_objective` field to `MissionConfig`. Only War=3, Take and Hold=5, Purge the Foe=5. `score_standard()` and `score_progressive()` use `config.vp_per_objective`. |
| Scenario VP sync drift | Replaced accumulating `vp_tracker.round_vp()` → `player.victory_points` with idempotent direct assignment: `player.victory_points = vp_tracker.total[pn]`. |
| Generic VP-cap end condition | Removed `vp.total[player_num] >= 100` cap from `check_end_game()`; game now ends by round cap or army wipe only. |
| Ruff/format gates red | Fixed F811 redefinitions and unsorted imports in `tests/test_mission.py`. |
| Missing regression tests | Updated tests for new scoring values (25 VP for 5-objective T&H, 11 VP for 3-objective progressive, etc.). VP cap test converted to verify cap is removed. |
| Stale closure artifacts | Synced task file, index, plan, code-review, and CR-08/10/14/24 evidence. |


## Code review — 2026-05-19

Review file: `docs/reviews/2026-05-19/phase-4-game-state-vp-phase-invariants-check.md`

**Verdict: REQUEST CHANGES.**

Phase 4 cannot close yet. Task 4.3 still has blocking findings after deterministic re-check:

| Finding | Evidence |
| --- | --- |
| Only War isolated objective value is wrong | Probe returned `{'p1': 5, 'p2': 0}` instead of 3 VP. |
| Purge the Foe isolated objective value is wrong | Probe returned `{'p1': 0, 'p2': 0}` instead of 5 VP. |
| Battle Ready finalization coverage missing | No Battle Ready exact-once/idempotence/final replay-result assertions found in Phase 4 tests. |
| Closure surfaces were inconsistent | Task/index claimed complete while `remediation-plan.md` still had unchecked Phase 4 boxes. |
