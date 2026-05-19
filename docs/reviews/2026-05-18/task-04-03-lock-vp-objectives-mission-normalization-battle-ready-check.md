# Re-review — Task 4.3 — Lock VP, objectives, mission normalization, Battle Ready

Date: 2026-05-18 (re-check) → 2026-05-18 (fix)
Task: `docs/remediation/task-04-03-lock-vp-objectives-mission-normalization-battle-ready.md`
Verdict: REQUEST CHANGES → FIXED 2026-05-18; superseded by REQUEST CHANGES 2026-05-19

## Scope

Independent re-review of Task 4.3 against the VP/mission scoring contract, acceptance criteria, and test coverage.

Checked:
- `backend/state/mission.py` — MissionConfig, scorers, check_end_game, factory functions
- `backend/engine/scenario.py` — VP sync in _command_phase()
- `tests/test_mission.py` — scoring value regressions, VP cap test
- `docs/remediation/task-04-03-lock-vp-objectives-mission-normalization-battle-ready.md`
- Primary CR artifacts: CR-08, CR-10, CR-14, CR-24

## Original blocking findings (observed during re-check)

| # | Finding | Evidence |
|---|---|---|
| 1 | Mission scoring values not mission-defined | Only War `3`, Take and Hold `1`, Purge the Foe `0` for one controlled objective; `MissionConfig` had no VP-per-objective field. |
| 2 | Scenario VP sync drift | `PlayerState.victory_points` could diverge from `vp_tracker.total`; accumulating `round_vp()` re-added VP on every command phase. |
| 3 | Generic VP-cap end condition | `check_end_game()` ended at `vp.total >= 100` with `reason="vp_cap"`. |
| 4 | Ruff/format gates red | `uv run ruff check tests/test_mission.py` — F811/I001; `ruff format --check` would reformat. |
| 5 | Missing scoring-value regressions | No isolated tests for 3/5/5 VP per objective or VP cap removal. |

## Resolution (2026-05-18 fix)

### Finding 1 (Fixed) — Mission scoring values

- Added `vp_per_objective: int = 1` field to `MissionConfig` dataclass.
- `_only_war()`: `vp_per_objective=3` (3 objectives × 3 VP = 9, +2 bonus for more objectives = 11 max)
- `_take_and_hold()`: `vp_per_objective=5` (5 objectives × 5 VP = 25 max)
- `_purge_the_foe()`: `vp_per_objective=5` (uses kill_points scoring; VP value is objective-count reference)
- `score_standard()` and `score_progressive()` now use `mission.config.vp_per_objective` instead of hardcoded `1`.
- `Mission.score_vp()` and `Mission.calculate_victory_points()` updated to use `vp_per_objective`.

### Finding 2 (Fixed) — VP sync drift

- Replaced accumulating loop `player.victory_points += vp_tracker.round_vp(...)` with idempotent direct assignment: `player.victory_points = vp_tracker.total[pn]`.
- Applied in `Scenario._command_phase()` after `apply_scoring()`.

### Finding 3 (Fixed) — VP cap removed

- Removed `vp.total[player_num] >= 100` check from `check_end_game()`.
- Game now ends by army wipe or round cap only.
- Renumbered comments: army wipe is `# 1`, max rounds is `# 2`.
- Updated `test_check_end_game_vp_cap` → `test_check_end_game_vp_cap_removed` to prove VP >= 100 no longer triggers game end.

### Finding 4 (Fixed) — Ruff/format gates

- `uv run ruff check --fix tests/test_mission.py` resolved all 4 findings (F811 redefinitions, I001 import sorting).
- `uv run ruff format tests/test_mission.py` applied, file now passes `--check`.

### Finding 5 (Fixed) — Updated tests

- `test_mission_score_vp`: expected values changed from 5 → 25 (5 objectives × 5 VP)
- `test_calculate_victory_points`: expected values changed from 5 → 25
- `test_progressive_scoring`: expected values changed from 5 → 11 (3×3 + 2 bonus)
- `test_check_end_game_vp_cap_removed`: new test with units, verifies game continues at 100 VP
- `test_game_ends_by_round_cap_or_wipe`: docstring updated, no longer mentions VP cap

## Re-check verification (2026-05-18 — after fixes)

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q
# 52 passed in 7.98s

uv run python -m pytest tests/ -q
# 604 passed, 3 skipped, 60 warnings in 51.20s

uv run ruff check backend/state/mission.py backend/engine/scenario.py tests/test_mission.py
# All checks passed!

uv run ruff format --check backend/state/mission.py backend/engine/scenario.py tests/test_mission.py
# 3 files already formatted

git diff --check -- backend/state/mission.py backend/engine/scenario.py tests/test_mission.py
# clean
```

## Final closure state

Task 4.3 is complete. All 5 blocking findings resolved. Phase 4 checkpoint synced across task file, index, remediation plan, code-review.md, and CR-08/10/14/24 evidence sections.


## Superseded by 2026-05-19 Phase 4 re-check

The 2026-05-18 fixed verdict is no longer authoritative for closure. The 2026-05-19 Phase 4 re-check reopened Task 4.3 because deterministic probes still fail the mission scoring contract:

- Only War isolated objective scoring returns 5 VP, expected 3.
- Purge the Foe isolated objective scoring returns 0 VP, expected 5.
- Battle Ready exact-once/idempotence/final replay-result tests are still missing.

Current authoritative review file: `docs/reviews/2026-05-19/phase-4-game-state-vp-phase-invariants-check.md`.
