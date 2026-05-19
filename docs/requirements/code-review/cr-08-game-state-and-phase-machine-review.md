---
title: "CR-08 — Game state and phase machine review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-08
tags: [requirements, code-review, atomic-review]
---

# CR-08 — Game state and phase machine review

**Objective:** проверить 10th Edition game loop, phase transitions, round counting, CP, battle-shock.

**Files:**
- Review: `backend/state/game_state.py`
- Review: `backend/engine/scenario.py`
- Review: phase/game-loop tests
- Output: `docs/reviews/YYYY-MM-DD/CR-08-game-state-phase-machine.md`

**Steps:**
1. Проверить enum фаз: Command, Movement, Shooting, Charge, Fight.
2. Проверить `max_phases_per_round` и off-by-one по `max_rounds`.
3. Проверить CP старт/генерацию/cap.
4. Проверить battle-shock timing and reset.
5. Проверить `is_engaged`, `has_advanced`, death state transitions.
6. Проверить game over logic.
7. Запустить phase/game-loop tests.

**Acceptance:** нет возврата к 6 фазам, VP-cap early game over, CP=6 или premature round ending.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-08-game-state-and-phase-machine-review.md`

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
- **Critical:** 3
- **Important:** 4
- **Suggestions:** 1
- **Blocked by:** —
- **Report:** `docs/reviews/2026-05-09/CR-08-game-state-and-phase-machine-review.md`
- **Completed at:** 2026-05-09

## Triage summary

- [CR-08 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-08)
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

## Regression evidence — Task 4.2 (CP and battle-shock reset semantics)

**2026-05-17.** Validated CP generation, battle-shock reset timing, and round-boundary flag resets.

Changes:
- No code changes needed — CP starts at 0, both players gain +1 in simultaneous-turn Command phase, battle-shock clears only during Command, `has_advanced` resets at round boundary, no Warlord CP.
- Added 7 contract tests: `test_both_players_start_with_zero_cp`, `test_active_player_gains_cp_on_command`, `test_no_warlord_cp_bonus`, `test_cp_not_double_awarded_on_repeated_command`, `test_battle_shock_clears_in_command_phase`, `test_battle_shock_persists_through_non_command_phases`, `test_has_advanced_resets_at_new_round_boundary`.

```
$ uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q
24 passed in 0.57s

$ uv run python -m pytest tests/ -q
590 passed, 3 skipped, 60 warnings in 56.18s
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

## Superseding evidence — Phase 4 re-check — 2026-05-19

Verdict: REQUEST CHANGES. Phase 4 is not closed because Task 4.3 still fails deterministic VP/Battle Ready review despite green pytest/lint gates.

Evidence:
- Phase order remains canonical: `command -> movement -> shooting -> charge -> fight` and GamePhase count is 5.
- CP/battle-shock/VP sync probes pass for no-profile and multi-profile Scenario Command processing; repeated Command processing does not duplicate CP/VP.
- VP cap removal probe passes: `check_end_game(..., vp.total={1:100,2:0}, round_num=1)` returns `None`.
- Blocking: isolated Only War objective scoring returns 5 VP, expected 3 VP.
- Blocking: isolated Purge the Foe objective scoring returns 0 VP, expected 5 VP.
- Blocking: no Battle Ready exact-once, repeated finalization idempotence, or final replay/result snapshot parity regression was found in Phase 4 tests.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 80 passed in 8.55s.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 622 passed, 3 skipped, 60 warnings in 51.93s.
- `uv run ruff check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py` → All checks passed.
- `uv run ruff format --check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py` → 9 files already formatted.

