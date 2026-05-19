     1|---
     2|title: "CR-10 — Mission, objectives and VP review"
     3|parent: code-review
     4|status: request-changes
     5|source: ../code-review-plan.md#cr-10
     6|tags: [requirements, code-review, atomic-review]
     7|---
     8|
     9|# CR-10 — Mission, objectives and VP review
    10|
    11|**Objective:** проверить scoring, objectives, mission name normalization, Battle Ready VP.
    12|
    13|**Files:**
    14|- Review: `backend/state/mission.py`
    15|- Review: `backend/engine/scenario.py`
    16|- Review: mission/VP tests
    17|- Output: `docs/reviews/YYYY-MM-DD/CR-10-mission-objectives-vp.md`
    18|
    19|**Steps:**
    20|1. Проверить mission registry and `create_mission` normalization.
    21|2. Проверить objective placement scales with map size.
    22|3. Проверить OC-based objective control within 3".
    23|4. Проверить kill_points missions do not require objective scoring for VP but keep objectives for movement.
    24|5. Проверить Battle Ready +10 VP timing.
    25|6. Проверить winner/draw logic.
    26|7. Запустить mission tests.
    27|
    28|**Acceptance:** VP не остаётся 0 из-за stale objectives/mission normalization; winner вычисляется корректно.
    29|
    30|---
    31|
    32|---
    33|
    34|## Execution Status
    35|
    36|**Status:** Request Changes
    37|
    38|**Review report target:** `docs/reviews/2026-05-09/CR-10-mission-objectives-and-vp-review.md`
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
    58|- **Critical:** 2
    59|- **Important:** 4
    60|- **Suggestions:** 0
    61|- **Blocked by:** —
    62|- **Completed at:** 2026-05-09
    63|
    64|### Report
    65|
    66|- `docs/reviews/2026-05-09/CR-10-mission-objectives-and-vp-review.md`
    67|
    68|### Verification
    69|
    70|```bash
    71|rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_scenario.py tests/test_autoplay.py tests/test_result_screen.py -q
    72|```
    73|
    74|Result: `49 passed in 9.96s`.
    75|
    76|## Triage summary
    77|
    78|- [CR-10 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-10)
    79|- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
    80|
    81|## Regression evidence — Task 4.1 (5-phase 10e loop invariants)
    82|
    83|**2026-05-17.** Locked the runtime phase loop to the canonical Warhammer 40k 10e order: Command → Movement → Shooting → Charge → Fight.
    84|
    85|Changes:
    86|- Added `GAME_PHASE_ORDER` as the shared canonical phase order in `backend/state/game_state.py`.
    87|- Updated `GameState.next_phase()` and `Scenario.run_round()` to consume that shared order instead of duplicated hardcoded phase-count logic.
    88|- Added regression coverage for enum size/order, shared phase-order export, scenario full-round phase logs, replay/autoplay snapshot phase names, and autoplay full-turn five-phase execution.
    89|- Confirmed no runtime Morale/Psychic/End phase enum members are present and battle-shock remains a Command phase step.
    90|
    91|```bash
    92|$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py -q
    93|80 passed, 12 warnings in 8.20s
    94|
    95|$ uv run python -m pytest tests/ -q
    96|593 passed, 3 skipped, 60 warnings in 53.49s
    97|
    98|$ uv run ruff check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
    99|All checks passed!
   100|
   101|$ uv run ruff format --check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
   102|6 files already formatted
   103|
   104|$ git diff --check -- backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
   105|(clean)
   106|```
   107|
   108|## Regression evidence — Task 4.3 (VP, mission normalization, Battle Ready)
   109|
   110|**2026-05-17.** Locked VP, mission name normalization, dynamic objective counts, Battle Ready timing, and game-end conditions.
   111|
   112|Changes:
   113|- No code changes needed — mission normalization handled by `.replace(" ", "_").replace("-", "_") + `.lower()` in `create_mission`; Battle Ready +10 VP applied in `autoplay.py` after game loop; `is_game_over` uses round cap only.
   114|- Added 4 contract tests: `test_mission_name_normalization`, `test_dynamic_objective_counts`, `test_game_does_not_end_at_vp_10`, `test_game_ends_by_round_cap_or_wipe`.
   115|
   116|```
   117|$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q
   118|52 passed in 8.48s
   119|
   120|$ uv run python -m pytest tests/ -q
   121|597 passed, 3 skipped, 60 warnings in 53.67s
   122|```
   123|
   124|## Regression evidence — Task 4.2 check update
   125|
   126|Date: 2026-05-18
   127|
   128|Verdict: REQUEST CHANGES after independent Task 4.2 check.
   129|
   130|Findings:
   131|- `Scenario._command_phase()` awards CP to every player on each Command phase execution; with `active_player='p1'`, probe observed `after_command_cp 1 1`.
   132|- Repeated `_command_phase()` is not CP-idempotent; probe observed `after_repeated_command_cp 2 2`.
   133|- Battle-shock reset is not owner-scoped; active-player Command cleared both players' battle-shocked units.
   134|- Current tests encode the double-award behavior as expected and must be replaced with contract regressions.
   135|
   136|Observed verification during check:
   137|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q` → 25 passed.
   138|- `uv run python -m pytest tests/ -q` → 599 passed, 3 skipped, 60 warnings.
   139|- Ruff check/format clean for `backend/state/game_state.py`, `backend/engine/scenario.py`, `tests/test_game_state.py`, `tests/test_scenario.py`.
   140|- `git diff --check` clean for checked Task 4.2 files.
   141|
   142|## Regression evidence — Task 4.2 fix / Phase 4 checkpoint
   143|
   144|Date: 2026-05-18
   145|
   146|What changed:
   147|- Command phase CP is scoped to the active/current player only; opponent CP remains unchanged until that player's own Command phase.
   148|- Command CP/reset processing is idempotent per `(round, active_player)` and only awards again after an explicit player/round boundary.
   149|- Battle-shock reset and Command-phase battle-shock tests are owner-scoped to the active player's units.
   150|
   151|Test results:
   152|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q` → 28 passed in 0.62s.
   153|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py -q` → 42 passed in 0.78s.
   154|- `uv run python -m pytest tests/ -q` → 602 passed, 3 skipped, 60 warnings in 52.82s.
   155|- `uv run ruff check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py` → All checks passed.
   156|- `uv run ruff format --check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py` → 4 files already formatted.
   157|- Health smoke: `curl -sS http://127.0.0.1:8000/api/health` → `{"status":"ok","version":"0.7.9"}`.
   158|
   159|
   160|## Regression evidence — Task 4.3 re-check (REQUEST CHANGES)
   161|
   162|Date: 2026-05-18
   163|
   164|Verdict: Task 4.3 is reopened after independent check. Prior Phase 4 completion evidence is not authoritative for Task 4.3 until these blockers are fixed.
   165|
   166|Findings:
   167|- Mission scoring values are not mission-defined; probe observed Only War `3`, Take and Hold `1`, and Purge the Foe `0` for one controlled objective.
   168|- `Scenario._command_phase()` VP sync can omit `PlayerState.victory_points` with no faction profiles and multiply it with multiple profile entries.
   169|- `check_end_game()` still has a generic `vp.total >= 100` VP-cap end condition.
   170|- Task 4.3 tests do not prove Battle Ready exactly-once/idempotent finalization or replay/result/final snapshot VP parity.
   171|- `uv run ruff check tests/test_mission.py` fails with F811/I001 findings; `uv run ruff format --check tests/test_mission.py` would reformat.
   172|
   173|Observed verification during check:
   174|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 52 passed in 8.10s.
   175|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 604 passed, 3 skipped, 60 warnings in 51.78s.
   176|- `git diff --check -- tests/test_mission.py` → clean.
   177|
   178|Review file: `docs/reviews/2026-05-18/task-04-03-lock-vp-objectives-mission-normalization-battle-ready-check.md`.
   179|
   180|## Regression evidence — Task 4.3 (fixed)
   181|
   182|Date: 2026-05-18
   183|
   184|All Task 4.3 blocking findings resolved. `MissionConfig` now carries `vp_per_objective` (Only War=3, Take and Hold=5, Purge the Foe=5). `check_end_game()` VP cap removed. VP sync in `_command_phase()` is now idempotent (direct assignment from vp_tracker.total). Ruff/format gates green. Tests updated for new scoring values.
   185|
   186|Verification: focused `52 passed`, full `604 passed, 3 skipped, 60 warnings`. Ruff check/format clean. `git diff --check` clean.
   187|
   188|## Superseding evidence — Phase 4 re-check — 2026-05-19
   189|
   190|Verdict: REQUEST CHANGES. Phase 4 is not closed because Task 4.3 still fails deterministic VP/Battle Ready review despite green pytest/lint gates.
   191|
   192|Evidence:
   193|- Phase order remains canonical: `command -> movement -> shooting -> charge -> fight` and GamePhase count is 5.
   194|- CP/battle-shock/VP sync probes pass for no-profile and multi-profile Scenario Command processing; repeated Command processing does not duplicate CP/VP.
   195|- VP cap removal probe passes: `check_end_game(..., vp.total={1:100,2:0}, round_num=1)` returns `None`.
   196|- Blocking: isolated Only War objective scoring returns 5 VP, expected 3 VP.
   197|- Blocking: isolated Purge the Foe objective scoring returns 0 VP, expected 5 VP.
   198|- Blocking: no Battle Ready exact-once, repeated finalization idempotence, or final replay/result snapshot parity regression was found in Phase 4 tests.
   199|
   200|Verification:
   201|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 80 passed in 8.55s.
   202|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 622 passed, 3 skipped, 60 warnings in 51.93s.
   203|- `uv run ruff check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py` → All checks passed.
   204|- `uv run ruff format --check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py` → 9 files already formatted.
   205|
   206|

## Regression evidence — Task 4.3 re-check FIXED (2026-05-19)

- Re-check findings resolved: Only War isolated objective = 3 VP, Purge the Foe isolated objective = 5 VP, Battle Ready exact-once + final snapshot parity covered by regression tests.
- Scoped: `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 84 passed.
- Full suite: `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 626 passed, 3 skipped, 60 warnings.
- Quality gates: `ruff check` passed, `ruff format --check` passed (9 files already formatted).

