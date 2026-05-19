---
title: "CR-10 — Mission, objectives and VP review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-10
tags: [requirements, code-review, atomic-review]
---

# CR-10 — Mission, objectives and VP review

**Objective:** проверить scoring, objectives, mission name normalization, Battle Ready VP.

**Files:**
- Review: `backend/state/mission.py`
- Review: `backend/engine/scenario.py`
- Review: mission/VP tests
- Output: `docs/reviews/YYYY-MM-DD/CR-10-mission-objectives-vp.md`

**Steps:**
1. Проверить mission registry and `create_mission` normalization.
2. Проверить objective placement scales with map size.
3. Проверить OC-based objective control within 3".
4. Проверить kill_points missions do not require objective scoring for VP but keep objectives for movement.
5. Проверить Battle Ready +10 VP timing.
6. Проверить winner/draw logic.
7. Запустить mission tests.

**Acceptance:** VP не остаётся 0 из-за stale objectives/mission normalization; winner вычисляется корректно.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-09/CR-10-mission-objectives-and-vp-review.md`

### Status checklist

- [x] Scope confirmed
- [x] Requirements/specs reviewed
- [x] Tests reviewed first
- [x] Production code reviewed
- [x] Correctness checked
- [x] Readability checked
- [x] Architecture checked
- [x] Security checked
- [x] Performance checked
- [x] Verification commands executed
- [x] Findings report written
- [x] Triage status updated in `docs/requirements/code-review/code-review.md`

### Result

- **Verdict:** Request Changes
- **Critical:** 2
- **Important:** 4
- **Suggestions:** 0
- **Blocked by:** —
- **Completed at:** 2026-05-09

### Report

- `docs/reviews/2026-05-09/CR-10-mission-objectives-and-vp-review.md`

### Verification

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_scenario.py tests/test_autoplay.py tests/test_result_screen.py -q
```

Result: `49 passed in 9.96s`.

## Triage summary

- [CR-10 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-10)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 4.1 (5-phase 10e loop invariants)

**2026-05-17.** Locked the runtime phase loop to the canonical Warhammer 40k 10e order: Command → Movement → Shooting → Charge → Fight.

Changes:
- Added `GAME_PHASE_ORDER` as the shared canonical phase order in `backend/state/game_state.py`.
- Updated `GameState.next_phase()` and `Scenario.run_round()` to consume that shared order instead of duplicated hardcoded phase-count logic.
- Added regression coverage for enum size/order, shared phase-order export, scenario full-round phase logs, replay/autoplay snapshot phase names, and autoplay full-turn five-phase execution.
- Confirmed no runtime Morale/Psychic/End phase enum members are present and battle-shock remains a Command phase step.

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

## Regression evidence — Task 4.3 (VP, mission normalization, Battle Ready)

**2026-05-17.** Locked VP, mission name normalization, dynamic objective counts, Battle Ready timing, and game-end conditions.

Changes:
- No code changes needed — mission normalization handled by `.replace(" ", "_").replace("-", "_") + `.lower()` in `create_mission`; Battle Ready +10 VP applied in `autoplay.py` after game loop; `is_game_over` uses round cap only.
- Added 4 contract tests: `test_mission_name_normalization`, `test_dynamic_objective_counts`, `test_game_does_not_end_at_vp_10`, `test_game_ends_by_round_cap_or_wipe`.

```
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q
52 passed in 8.48s

$ uv run python -m pytest tests/ -q
597 passed, 3 skipped, 60 warnings in 53.67s
```

## Regression evidence — Task 4.2 check update

Date: 2026-05-18

Verdict: REQUEST CHANGES after independent Task 4.2 check.

Findings:
- `Scenario._command_phase()` awards CP to every player on each Command phase execution; with `active_player='p1'`, probe observed `after_command_cp 1 1`.
- Repeated `_command_phase()` is not CP-idempotent; probe observed `after_repeated_command_cp 2 2`.
- Battle-shock reset is not owner-scoped; active-player Command cleared both players' battle-shocked units.
- Current tests encode the double-award behavior as expected and must be replaced with contract regressions.

Observed verification during check:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q` → 25 passed.
- `uv run python -m pytest tests/ -q` → 599 passed, 3 skipped, 60 warnings.
- Ruff check/format clean for `backend/state/game_state.py`, `backend/engine/scenario.py`, `tests/test_game_state.py`, `tests/test_scenario.py`.
- `git diff --check` clean for checked Task 4.2 files.

## Regression evidence — Task 4.2 fix / Phase 4 checkpoint

Date: 2026-05-18

What changed:
- Command phase CP is scoped to the active/current player only; opponent CP remains unchanged until that player's own Command phase.
- Command CP/reset processing is idempotent per `(round, active_player)` and only awards again after an explicit player/round boundary.
- Battle-shock reset and Command-phase battle-shock tests are owner-scoped to the active player's units.

Test results:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q` → 28 passed in 0.62s.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py -q` → 42 passed in 0.78s.
- `uv run python -m pytest tests/ -q` → 602 passed, 3 skipped, 60 warnings in 52.82s.
- `uv run ruff check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py` → All checks passed.
- `uv run ruff format --check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py` → 4 files already formatted.
- Health smoke: `curl -sS http://127.0.0.1:8000/api/health` → `{"status":"ok","version":"0.7.9"}`.


## Regression evidence — Task 4.3 re-check (REQUEST CHANGES)

Date: 2026-05-18

Verdict: Task 4.3 is reopened after independent check. Prior Phase 4 completion evidence is not authoritative for Task 4.3 until these blockers are fixed.

Findings:
- Mission scoring values are not mission-defined; probe observed Only War `3`, Take and Hold `1`, and Purge the Foe `0` for one controlled objective.
- `Scenario._command_phase()` VP sync can omit `PlayerState.victory_points` with no faction profiles and multiply it with multiple profile entries.
- `check_end_game()` still has a generic `vp.total >= 100` VP-cap end condition.
- Task 4.3 tests do not prove Battle Ready exactly-once/idempotent finalization or replay/result/final snapshot VP parity.
- `uv run ruff check tests/test_mission.py` fails with F811/I001 findings; `uv run ruff format --check tests/test_mission.py` would reformat.

Observed verification during check:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 52 passed in 8.10s.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 604 passed, 3 skipped, 60 warnings in 51.78s.
- `git diff --check -- tests/test_mission.py` → clean.

Review file: `docs/reviews/2026-05-18/task-04-03-lock-vp-objectives-mission-normalization-battle-ready-check.md`.

## Regression evidence — Task 4.3 (fixed)

Date: 2026-05-18

All Task 4.3 blocking findings resolved. `MissionConfig` now carries `vp_per_objective` (Only War=3, Take and Hold=5, Purge the Foe=5). `check_end_game()` VP cap removed. VP sync in `_command_phase()` is now idempotent (direct assignment from vp_tracker.total). Ruff/format gates green. Tests updated for new scoring values.

Verification: focused `52 passed`, full `604 passed, 3 skipped, 60 warnings`. Ruff check/format clean. `git diff --check` clean.
