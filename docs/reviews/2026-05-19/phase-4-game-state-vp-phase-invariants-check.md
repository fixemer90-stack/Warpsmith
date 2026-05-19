# Phase 4 re-check — Game state / VP / phase invariants

Date: 2026-05-19
Verdict: REQUEST CHANGES → FIXED 2026-05-19
Scope: Phase 4 (`task-04-01`, `task-04-02`, `task-04-03`) and source-plan/index/CR closure surfaces.

## Resolution

All blocking findings from the earlier re-check are fixed.

| # | Finding | Resolution |
|---|---|---|
| 1 | Only War isolated objective scoring was 5 instead of 3. | Removed hardcoded progressive lead bonus from canonical progressive paths (`score_progressive()` and `Mission.calculate_victory_points()`), so scoring is mission-defined via `vp_per_objective`. Added regression: `tests/test_mission.py::test_only_war_isolated_objective_scores_3_vp`. |
| 2 | Purge the Foe isolated objective scoring was 0 instead of 5. | Updated Purge the Foe mission config to objective-control scoring (`scoring_rule="standard"`, `vp_per_objective=5`) and kept 5-objective dynamic layout. Added regression: `tests/test_mission.py::test_purge_the_foe_isolated_objective_scores_5_vp`. |
| 3 | Battle Ready exact-once/final replay-result coverage missing. | Added regressions in `tests/test_autoplay.py`: `test_battle_ready_applies_exactly_once` and `test_final_snapshot_contains_battle_ready_vp`. Added idempotent runtime helper `_apply_battle_ready_once()` in autoplay path. |
| 4 | Closure surfaces disagreed. | Synced Task 4.3 status/checkboxes/verification, `docs/remediation/remediation-plan.md` Phase 4 block + checkpoint, and `docs/remediation/index.md` row 4.3. |

## Re-check results

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q
# 84 passed

rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q
# 626 passed, 3 skipped, 60 warnings

uv run ruff check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py
# All checks passed

uv run ruff format --check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py
# 9 files already formatted
```

## Current status

Phase 4 blockers from this review cycle are closed.
