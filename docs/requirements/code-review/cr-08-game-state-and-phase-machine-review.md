     1|---
     2|title: "CR-08 — Game state and phase machine review"
     3|parent: code-review
     4|status: request-changes
     5|source: ../code-review-plan.md#cr-08
     6|tags: [requirements, code-review, atomic-review]
     7|---
     8|
     9|# CR-08 — Game state and phase machine review
    10|
    11|**Objective:** проверить 10th Edition game loop, phase transitions, round counting, CP, battle-shock.
    12|
    13|**Files:**
    14|- Review: `backend/state/game_state.py`
    15|- Review: `backend/engine/scenario.py`
    16|- Review: phase/game-loop tests
    17|- Output: `docs/reviews/YYYY-MM-DD/CR-08-game-state-phase-machine.md`
    18|
    19|**Steps:**
    20|1. Проверить enum фаз: Command, Movement, Shooting, Charge, Fight.
    21|2. Проверить `max_phases_per_round` и off-by-one по `max_rounds`.
    22|3. Проверить CP старт/генерацию/cap.
    23|4. Проверить battle-shock timing and reset.
    24|5. Проверить `is_engaged`, `has_advanced`, death state transitions.
    25|6. Проверить game over logic.
    26|7. Запустить phase/game-loop tests.
    27|
    28|**Acceptance:** нет возврата к 6 фазам, VP-cap early game over, CP=6 или premature round ending.
    29|
    30|---
    31|
    32|---
    33|
    34|## Execution Status
    35|
    36|**Status:** Request Changes
    37|
    38|**Review report target:** `docs/reviews/YYYY-MM-DD/CR-08-game-state-and-phase-machine-review.md`
    39|
    40|### Status checklist
    41|
    42|- [x] Scope confirmed
    43|- [x] Requirements/specs reviewed
    44|- [x] Tests reviewed first
    45|- [x] Production code reviewed
    46|- [x] Correctness checked
    47|- [x] Readability checked
    48|- [x] Architecture checked
    49|- [x] Security checked
    50|- [x] Performance checked
    51|- [x] Verification commands executed
    52|- [x] Findings report written
    53|- [x] Triage status updated in `docs/requirements/code-review/code-review.md`
    54|
    55|### Result
    56|
    57|- **Verdict:** Request Changes
    58|- **Critical:** 3
    59|- **Important:** 4
    60|- **Suggestions:** 1
    61|- **Blocked by:** —
    62|- **Report:** `docs/reviews/2026-05-09/CR-08-game-state-and-phase-machine-review.md`
    63|- **Completed at:** 2026-05-09
    64|
    65|## Triage summary
    66|
    67|- [CR-08 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-08)
    68|- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
    69|
    70|## Regression evidence — Task 4.1 (5-phase 10e loop invariants)
    71|
    72|**2026-05-17.** Locked the runtime phase loop to the canonical Warhammer 40k 10e order: Command → Movement → Shooting → Charge → Fight.
    73|
    74|Changes:
    75|- Added `GAME_PHASE_ORDER` as the shared canonical phase order in `backend/state/game_state.py`.
    76|- Updated `GameState.next_phase()` and `Scenario.run_round()` to consume that shared order instead of duplicated hardcoded phase-count logic.
    77|- Added regression coverage for enum size/order, shared phase-order export, scenario full-round phase logs, replay/autoplay snapshot phase names, and autoplay full-turn five-phase execution.
    78|- Confirmed no runtime Morale/Psychic/End phase enum members are present and battle-shock remains a Command phase step.
    79|
    80|```bash
    81|$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py -q
    82|80 passed, 12 warnings in 8.20s
    83|
    84|$ uv run python -m pytest tests/ -q
    85|593 passed, 3 skipped, 60 warnings in 53.49s
    86|
    87|$ uv run ruff check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
    88|All checks passed!
    89|
    90|$ uv run ruff format --check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
    91|6 files already formatted
    92|
    93|$ git diff --check -- backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
    94|(clean)
    95|```
    96|
    97|## Regression evidence — Task 4.2 (CP and battle-shock reset semantics)
    98|
    99|**2026-05-17.** Validated CP generation, battle-shock reset timing, and round-boundary flag resets.
   100|
   101|Changes:
   102|- No code changes needed — CP starts at 0, both players gain +1 in simultaneous-turn Command phase, battle-shock clears only during Command, `has_advanced` resets at round boundary, no Warlord CP.
   103|- Added 7 contract tests: `test_both_players_start_with_zero_cp`, `test_active_player_gains_cp_on_command`, `test_no_warlord_cp_bonus`, `test_cp_not_double_awarded_on_repeated_command`, `test_battle_shock_clears_in_command_phase`, `test_battle_shock_persists_through_non_command_phases`, `test_has_advanced_resets_at_new_round_boundary`.
   104|
   105|```
   106|$ uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q
   107|24 passed in 0.57s
   108|
   109|$ uv run python -m pytest tests/ -q
   110|590 passed, 3 skipped, 60 warnings in 56.18s
   111|```
   112|
   113|## Regression evidence — Task 4.2 check update
   114|
   115|Date: 2026-05-18
   116|
   117|Verdict: REQUEST CHANGES after independent Task 4.2 check.
   118|
   119|Findings:
   120|- `Scenario._command_phase()` awards CP to every player on each Command phase execution; with `active_player='p1'`, probe observed `after_command_cp 1 1`.
   121|- Repeated `_command_phase()` is not CP-idempotent; probe observed `after_repeated_command_cp 2 2`.
   122|- Battle-shock reset is not owner-scoped; active-player Command cleared both players' battle-shocked units.
   123|- Current tests encode the double-award behavior as expected and must be replaced with contract regressions.
   124|
   125|Observed verification during check:
   126|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q` → 25 passed.
   127|- `uv run python -m pytest tests/ -q` → 599 passed, 3 skipped, 60 warnings.
   128|- Ruff check/format clean for `backend/state/game_state.py`, `backend/engine/scenario.py`, `tests/test_game_state.py`, `tests/test_scenario.py`.
   129|- `git diff --check` clean for checked Task 4.2 files.
   130|
   131|## Regression evidence — Task 4.2 fix / Phase 4 checkpoint
   132|
   133|Date: 2026-05-18
   134|
   135|What changed:
   136|- Command phase CP is scoped to the active/current player only; opponent CP remains unchanged until that player's own Command phase.
   137|- Command CP/reset processing is idempotent per `(round, active_player)` and only awards again after an explicit player/round boundary.
   138|- Battle-shock reset and Command-phase battle-shock tests are owner-scoped to the active player's units.
   139|
   140|Test results:
   141|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q` → 28 passed in 0.62s.
   142|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py -q` → 42 passed in 0.78s.
   143|- `uv run python -m pytest tests/ -q` → 602 passed, 3 skipped, 60 warnings in 52.82s.
   144|- `uv run ruff check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py` → All checks passed.
   145|- `uv run ruff format --check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py` → 4 files already formatted.
   146|- Health smoke: `curl -sS http://127.0.0.1:8000/api/health` → `{"status":"ok","version":"0.7.9"}`.
   147|
   148|
   149|## Regression evidence — Task 4.3 re-check (REQUEST CHANGES)
   150|
   151|Date: 2026-05-18
   152|
   153|Verdict: Task 4.3 is reopened after independent check. Prior Phase 4 completion evidence is not authoritative for Task 4.3 until these blockers are fixed.
   154|
   155|Findings:
   156|- Mission scoring values are not mission-defined; probe observed Only War `3`, Take and Hold `1`, and Purge the Foe `0` for one controlled objective.
   157|- `Scenario._command_phase()` VP sync can omit `PlayerState.victory_points` with no faction profiles and multiply it with multiple profile entries.
   158|- `check_end_game()` still has a generic `vp.total >= 100` VP-cap end condition.
   159|- Task 4.3 tests do not prove Battle Ready exactly-once/idempotent finalization or replay/result/final snapshot VP parity.
   160|- `uv run ruff check tests/test_mission.py` fails with F811/I001 findings; `uv run ruff format --check tests/test_mission.py` would reformat.
   161|
   162|Observed verification during check:
   163|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 52 passed in 8.10s.
   164|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 604 passed, 3 skipped, 60 warnings in 51.78s.
   165|- `git diff --check -- tests/test_mission.py` → clean.
   166|
   167|Review file: `docs/reviews/2026-05-18/task-04-03-lock-vp-objectives-mission-normalization-battle-ready-check.md`.
   168|
   169|## Regression evidence — Task 4.3 (fixed)
   170|
   171|Date: 2026-05-18
   172|
   173|All Task 4.3 blocking findings resolved. `MissionConfig` now carries `vp_per_objective` (Only War=3, Take and Hold=5, Purge the Foe=5). `check_end_game()` VP cap removed. VP sync in `_command_phase()` is now idempotent (direct assignment from vp_tracker.total). Ruff/format gates green. Tests updated for new scoring values.
   174|
   175|Verification: focused `52 passed`, full `604 passed, 3 skipped, 60 warnings`. Ruff check/format clean. `git diff --check` clean.
   176|
   177|## Superseding evidence — Phase 4 re-check — 2026-05-19
   178|
   179|Verdict: REQUEST CHANGES. Phase 4 is not closed because Task 4.3 still fails deterministic VP/Battle Ready review despite green pytest/lint gates.
   180|
   181|Evidence:
   182|- Phase order remains canonical: `command -> movement -> shooting -> charge -> fight` and GamePhase count is 5.
   183|- CP/battle-shock/VP sync probes pass for no-profile and multi-profile Scenario Command processing; repeated Command processing does not duplicate CP/VP.
   184|- VP cap removal probe passes: `check_end_game(..., vp.total={1:100,2:0}, round_num=1)` returns `None`.
   185|- Blocking: isolated Only War objective scoring returns 5 VP, expected 3 VP.
   186|- Blocking: isolated Purge the Foe objective scoring returns 0 VP, expected 5 VP.
   187|- Blocking: no Battle Ready exact-once, repeated finalization idempotence, or final replay/result snapshot parity regression was found in Phase 4 tests.
   188|
   189|Verification:
   190|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 80 passed in 8.55s.
   191|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 622 passed, 3 skipped, 60 warnings in 51.93s.
   192|- `uv run ruff check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py` → All checks passed.
   193|- `uv run ruff format --check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py` → 9 files already formatted.
   194|
   195|

## Regression evidence — Task 4.3 re-check FIXED (2026-05-19)

- Re-check findings resolved: Only War isolated objective = 3 VP, Purge the Foe isolated objective = 5 VP, Battle Ready exact-once + final snapshot parity covered by regression tests.
- Scoped: `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 84 passed.
- Full suite: `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 626 passed, 3 skipped, 60 warnings.
- Quality gates: `ruff check` passed, `ruff format --check` passed (9 files already formatted).

