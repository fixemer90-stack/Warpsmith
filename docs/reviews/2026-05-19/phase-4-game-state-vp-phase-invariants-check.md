# Phase 4 re-check — Game state / VP / phase invariants

Date: 2026-05-19
Verdict: REQUEST CHANGES
Scope: Phase 4 (`task-04-01`, `task-04-02`, `task-04-03`) and source-plan/index/CR closure surfaces.

## Summary

Phase 4 is not ready to close. Task 4.1 and Task 4.2 remain supported by the current probes and scoped tests, but Task 4.3 still fails core VP/Battle Ready acceptance criteria and the source plan still has unchecked Phase 4 boxes.

## Blocking findings

| # | Finding | Evidence |
|---|---|---|
| 1 | Only War isolated objective scoring is not the required 3 VP. | Deterministic probe with one controlled Only War objective returned `{'p1': 5, 'p2': 0}` because progressive scoring adds a +2 lead bonus. Task 4.3 requires `Only War 3 VP`. |
| 2 | Purge the Foe isolated objective scoring is not the required 5 VP. | Deterministic probe with one controlled Purge the Foe objective returned `{'p1': 0, 'p2': 0}`. `score_kill_points()` still ignores objective control / `vp_per_objective` for this contract. |
| 3 | Battle Ready exact-once/final replay-result coverage is still missing. | Test scan found no `Battle Ready`/`battle_ready` assertions in `tests/test_mission.py`, `tests/test_autoplay.py`, or `tests/test_result_screen.py`; only production code in `autoplay.py` mentions the bonus. |
| 4 | Closure surfaces disagree. | Task 4.3 frontmatter/index claimed completed, while `docs/remediation/remediation-plan.md` still had Task 4.3 `REQUEST CHANGES` and 10 unchecked Phase 4 boxes before this re-check update. |

## Passing evidence observed during this re-check

- Canonical phase order probe: `['command', 'movement', 'shooting', 'charge', 'fight']`, enum count `5`.
- Scenario VP sync probe now passes for no-profile and multi-profile cases: tracker `{1: 5, 2: 0}` and `PlayerState.victory_points {'p1': 5, 'p2': 0}`; repeated Command processing does not duplicate CP/VP.
- Generic VP cap probe now passes: `check_end_game(..., vp.total={1:100,2:0}, round_num=1)` returned `None`.
- Take and Hold isolated objective probe now passes: `{'p1': 5, 'p2': 0}`.

## Commands run

```bash
uv run python - <<'PY'
# deterministic Phase 4 probes for phase order, mission VP values, VP sync, VP cap
PY
# phase_order ['command', 'movement', 'shooting', 'charge', 'fight'] enum_count 5
# mission_score Only War {'p1': 5, 'p2': 0}
# mission_score Take and Hold {'p1': 5, 'p2': 0}
# mission_score Purge the Foe {'p1': 0, 'p2': 0}
# vp_sync no_profiles {1: 5, 2: 0} {'p1': 5, 'p2': 0} {'p1': 1, 'p2': 0}
# vp_sync_repeat no_profiles {1: 5, 2: 0} {'p1': 5, 'p2': 0} {'p1': 1, 'p2': 0}
# vp_sync profiles {1: 5, 2: 0} {'p1': 5, 'p2': 0} {'p1': 1, 'p2': 0}
# vp_sync_repeat profiles {1: 5, 2: 0} {'p1': 5, 'p2': 0} {'p1': 1, 'p2': 0}
# vp_cap_check None

rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q
# 80 passed in 8.55s

rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q
# 622 passed, 3 skipped, 60 warnings in 51.93s

uv run ruff check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py
# All checks passed!

uv run ruff format --check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py
# 9 files already formatted
```

## Required before Phase 4 can close

- Fix canonical mission scoring so isolated objective probes return Only War `3`, Take and Hold `5`, and Purge the Foe `5` from mission definitions.
- Add regression tests for those exact isolated values.
- Add Battle Ready exact-once, repeated finalization idempotence, and final replay/result snapshot parity tests.
- Re-run scoped Phase 4 tests, full suite, Ruff check, Ruff format check, and `git diff --check`.
- Then update Task 4.3, `remediation-plan.md`, `index.md`, CR-08/10/14/24 evidence, `code-review.md`, and triage summary to a consistent completed state.
