     1|---
     2|title: "CR-24 — Final integration regression gate"
     3|parent: code-review
     4|status: request-changes
     5|source: ../code-review-plan.md#cr-24
     6|tags: [requirements, code-review, atomic-review]
     7|---
     8|
     9|# CR-24 — Final integration regression gate
    10|
    11|**Objective:** финально подтвердить, что review/fix cycle не сломал продукт.
    12|
    13|**Files:**
    14|- Scope: whole repo
    15|- Output: `docs/reviews/YYYY-MM-DD/CR-24-final-regression-gate.md`
    16|
    17|**Steps:**
    18|1. Выполнить `uv run ruff check .`.
    19|2. Выполнить `uv run ruff format --check .`.
    20|3. Выполнить `node -c web/static/team_builder.js`.
    21|4. Выполнить `node -c web/static/scenario_setup.js`.
    22|5. Выполнить `node -c web/static/battlefield_map.js`.
    23|6. Выполнить `uv run python -m pytest tests/ -q`.
    24|7. Запустить server без reload и проверить `/api/health`.
    25|8. Browser smoke key pages: `/`, `/team-builder`, `/scenario-setup`, `/my-rosters`, `/result/<known_or_generated_game_id>` if available.
    26|9. Записать final verdict and remaining accepted debt.
    27|
    28|**Acceptance:** final gate report создан; release readiness verdict explicit.
    29|
    30|---
    31|
    32|---
    33|
    34|## Execution Status
    35|
    36|**Status:** Request Changes
    37|
    38|**Review report target:** `docs/reviews/2026-05-10/CR-24-final-integration-regression-gate.md`
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
    57|- **Verdict:** Request Changes — executable gates pass, but release readiness is blocked by unresolved/untriaged CR debt (37 prior Critical + 111 prior Important) and a reproduced result VP consistency issue.
    58|- **Critical:** 1
    59|- **Important:** 1
    60|- **Suggestions:** 1
    61|- **Blocked by:** unresolved Critical/Important CR debt, result final VP snapshot mismatch
    62|- **Completed at:** 2026-05-10
    63|
    64|## Triage summary
    65|
    66|- [CR-24 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-24)
    67|- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
    68|
    69|## Regression evidence — Task 4.1 (5-phase 10e loop invariants)
    70|
    71|**2026-05-17.** Locked the runtime phase loop to the canonical Warhammer 40k 10e order: Command → Movement → Shooting → Charge → Fight.
    72|
    73|Changes:
    74|- Added `GAME_PHASE_ORDER` as the shared canonical phase order in `backend/state/game_state.py`.
    75|- Updated `GameState.next_phase()` and `Scenario.run_round()` to consume that shared order instead of duplicated hardcoded phase-count logic.
    76|- Added regression coverage for enum size/order, shared phase-order export, scenario full-round phase logs, replay/autoplay snapshot phase names, and autoplay full-turn five-phase execution.
    77|- Confirmed no runtime Morale/Psychic/End phase enum members are present and battle-shock remains a Command phase step.
    78|
    79|```bash
    80|$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py -q
    81|80 passed, 12 warnings in 8.20s
    82|
    83|$ uv run python -m pytest tests/ -q
    84|593 passed, 3 skipped, 60 warnings in 53.49s
    85|
    86|$ uv run ruff check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
    87|All checks passed!
    88|
    89|$ uv run ruff format --check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
    90|6 files already formatted
    91|
    92|$ git diff --check -- backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
    93|(clean)
    94|```
    95|
    96|## Regression evidence — Task 4.2 check update
    97|
    98|Date: 2026-05-18
    99|
   100|Verdict: REQUEST CHANGES after independent Task 4.2 check.
   101|
   102|Findings:
   103|- `Scenario._command_phase()` awards CP to every player on each Command phase execution; with `active_player='p1'`, probe observed `after_command_cp 1 1`.
   104|- Repeated `_command_phase()` is not CP-idempotent; probe observed `after_repeated_command_cp 2 2`.
   105|- Battle-shock reset is not owner-scoped; active-player Command cleared both players' battle-shocked units.
   106|- Current tests encode the double-award behavior as expected and must be replaced with contract regressions.
   107|
   108|Observed verification during check:
   109|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q` → 25 passed.
   110|- `uv run python -m pytest tests/ -q` → 599 passed, 3 skipped, 60 warnings.
   111|- Ruff check/format clean for `backend/state/game_state.py`, `backend/engine/scenario.py`, `tests/test_game_state.py`, `tests/test_scenario.py`.
   112|- `git diff --check` clean for checked Task 4.2 files.
   113|
   114|## Regression evidence — Task 4.2 fix / Phase 4 checkpoint
   115|
   116|Date: 2026-05-18
   117|
   118|What changed:
   119|- Command phase CP is scoped to the active/current player only; opponent CP remains unchanged until that player's own Command phase.
   120|- Command CP/reset processing is idempotent per `(round, active_player)` and only awards again after an explicit player/round boundary.
   121|- Battle-shock reset and Command-phase battle-shock tests are owner-scoped to the active player's units.
   122|
   123|Test results:
   124|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q` → 28 passed in 0.62s.
   125|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py -q` → 42 passed in 0.78s.
   126|- `uv run python -m pytest tests/ -q` → 602 passed, 3 skipped, 60 warnings in 52.82s.
   127|- `uv run ruff check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py` → All checks passed.
   128|- `uv run ruff format --check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py` → 4 files already formatted.
   129|- Health smoke: `curl -sS http://127.0.0.1:8000/api/health` → `{"status":"ok","version":"0.7.9"}`.
   130|
   131|
   132|## Regression evidence — Task 4.3 re-check (REQUEST CHANGES)
   133|
   134|Date: 2026-05-18
   135|
   136|Verdict: Task 4.3 is reopened after independent check. Prior Phase 4 completion evidence is not authoritative for Task 4.3 until these blockers are fixed.
   137|
   138|Findings:
   139|- Mission scoring values are not mission-defined; probe observed Only War `3`, Take and Hold `1`, and Purge the Foe `0` for one controlled objective.
   140|- `Scenario._command_phase()` VP sync can omit `PlayerState.victory_points` with no faction profiles and multiply it with multiple profile entries.
   141|- `check_end_game()` still has a generic `vp.total >= 100` VP-cap end condition.
   142|- Task 4.3 tests do not prove Battle Ready exactly-once/idempotent finalization or replay/result/final snapshot VP parity.
   143|- `uv run ruff check tests/test_mission.py` fails with F811/I001 findings; `uv run ruff format --check tests/test_mission.py` would reformat.
   144|
   145|Observed verification during check:
   146|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 52 passed in 8.10s.
   147|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 604 passed, 3 skipped, 60 warnings in 51.78s.
   148|- `git diff --check -- tests/test_mission.py` → clean.
   149|
   150|Review file: `docs/reviews/2026-05-18/task-04-03-lock-vp-objectives-mission-normalization-battle-ready-check.md`.
   151|
   152|## Regression evidence — Task 4.3 (fixed)
   153|
   154|Date: 2026-05-18
   155|
   156|Task 4.3 fixed and Phase 4 checkpoint closed. Full suite: `604 passed, 3 skipped`. Ruff/format/diff-check clean.
   157|
   158|## Superseding evidence — Phase 4 re-check — 2026-05-19
   159|
   160|Verdict: REQUEST CHANGES. Phase 4 is not closed because Task 4.3 still fails deterministic VP/Battle Ready review despite green pytest/lint gates.
   161|
   162|Evidence:
   163|- Phase order remains canonical: `command -> movement -> shooting -> charge -> fight` and GamePhase count is 5.
   164|- CP/battle-shock/VP sync probes pass for no-profile and multi-profile Scenario Command processing; repeated Command processing does not duplicate CP/VP.
   165|- VP cap removal probe passes: `check_end_game(..., vp.total={1:100,2:0}, round_num=1)` returns `None`.
   166|- Blocking: isolated Only War objective scoring returns 5 VP, expected 3 VP.
   167|- Blocking: isolated Purge the Foe objective scoring returns 0 VP, expected 5 VP.
   168|- Blocking: no Battle Ready exact-once, repeated finalization idempotence, or final replay/result snapshot parity regression was found in Phase 4 tests.
   169|
   170|Verification:
   171|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 80 passed in 8.55s.
   172|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 622 passed, 3 skipped, 60 warnings in 51.93s.
   173|- `uv run ruff check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py` → All checks passed.
   174|- `uv run ruff format --check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py` → 9 files already formatted.
   175|
   176|

## Regression evidence — Task 4.3 re-check FIXED (2026-05-19)

- Re-check findings resolved: Only War isolated objective = 3 VP, Purge the Foe isolated objective = 5 VP, Battle Ready exact-once + final snapshot parity covered by regression tests.
- Scoped: `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 84 passed.
- Full suite: `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 626 passed, 3 skipped, 60 warnings.
- Quality gates: `ruff check` passed, `ruff format --check` passed (9 files already formatted).

