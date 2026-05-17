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
