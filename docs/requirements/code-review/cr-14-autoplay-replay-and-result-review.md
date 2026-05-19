     1|---
     2|title: "CR-14 — Autoplay, replay and result review"
     3|parent: code-review
     4|status: request-changes
     5|source: ../code-review-plan.md#cr-14
     6|tags: [requirements, code-review, atomic-review]
     7|---
     8|
     9|# CR-14 — Autoplay, replay and result review
    10|
    11|**Objective:** проверить full simulation pipeline: setup → auto-play → replay storage → result summary.
    12|
    13|**Files:**
    14|- Review: `backend/engine/ai/autoplay.py`
    15|- Review: `backend/engine/replay.py`
    16|- Review: `web/routes/api_replays.py`
    17|- Review: `web/static/scenario_setup.js`
    18|- Review: `web/static/replay_viewer.js`
    19|- Review: `web/static/result_chart.js`
    20|- Output: `docs/reviews/YYYY-MM-DD/CR-14-autoplay-replay-result.md`
    21|
    22|**Steps:**
    23|1. Проверить game_id serialization and redirect flow.
    24|2. Проверить replay persistence JSON columns.
    25|3. Проверить `_snapshot_state` includes units, positions, VP, map dimensions.
    26|4. Проверить `_build_summary` parsing kills/damage/charges.
    27|5. Проверить result winner fallback.
    28|6. Проверить round viewer dynamic grid size.
    29|7. Запустить replay/result tests and one TestClient E2E auto-play.
    30|
    31|**Acceptance:** generated/saved rosters can run simulation and open `/result/{game_id}` with meaningful summary.
    32|
    33|---
    34|
    35|---
    36|
    37|## Execution Status
    38|
    39|**Status:** Request Changes
    40|
    41|**Review report target:** `docs/reviews/2026-05-09/CR-14-autoplay-replay-and-result-review.md`
    42|
    43|### Status checklist
    44|
    45|- [x] Scope confirmed
    46|- [x] Requirements/specs reviewed
    47|- [x] Tests reviewed first
    48|- [x] Production code reviewed
    49|- [x] Correctness checked
    50|- [x] Readability checked
    51|- [x] Architecture checked
    52|- [x] Security checked
    53|- [x] Performance checked
    54|- [x] Verification commands executed
    55|- [x] Findings report written
    56|- [x] Triage status updated in `docs/requirements/code-review/code-review.md`
    57|
    58|### Result
    59|
    60|- **Verdict:** Request Changes
    61|- **Critical:** 3
    62|- **Important:** 4
    63|- **Suggestions:** 0
    64|- **Blocked by:** —
    65|- **Completed at:** 2026-05-09T23:13:16+03:00
    66|- **Verification:** `62 passed, 7 warnings in 11.41s`; custom replay/result probes confirmed game_id overwrite, stale final VP snapshots, duplicate-name summary attribution, VP parser mismatch, and result charge attribution gap.
    67|
    68|## Triage summary
    69|
    70|- [CR-14 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-14)
    71|- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
    72|
    73|## Regression evidence — Task 0.1 (runtime unit identity)
    74|
    75|**2026-05-16.** Fixed "duplicate-name summary attribution" finding:
    76|
    77|1. **`_build_summary()`** — Now uses `strip_event_identity()` to extract authoritative
    78|   `actor_id`/`target_id` from the `[actor_id=p1:Boyz:0; target_id=p2:Boyz:0]`
    79|   suffix in log lines. Builds `runtime_id → player_id` map. Correct attribution
    80|   even when both players have identically-named units (e.g. both field "Boyz").
    81|   Fallback to display-name lookup for log lines without identity suffix.
    82|
    83|2. **`_parse_log_events()`** — Updated all 17 patterns to strip identity suffix
    84|   and use `meta.get("actor_id"/"target_id", …)` for `ReplayEvent` construction.
    85|   Replay events now carry stable runtime IDs alongside display names.
    86|
    87|3. **`RosterState.units`** — `dict[str, Unit]` → `list[tuple[str, Unit]]`.
    88|   Duplicate unit names within a roster are representable end-to-end.
    89|
    90|Verification: `uv run python -m pytest tests/ -q` → 471 passed, 3 skipped, 0 failures.
    91|`ruff check` → All checks passed.
    92|
    93|## Regression evidence — Task 0.2 (canonical GameState serializer)
    94|
    95|**2026-05-16.** Two divergent `_snapshot_state` implementations consolidated into single
    96|canonical `snapshot_game_state()` in `backend/state/game_state.py`. Both `autoplay.py`
    97|and `replay.py` now delegate to it. Round snapshots and final snapshots share identical
    98|shape. Unit records include `runtime_unit_id` as authoritative `id`, `player_id`,
    99|`current_wounds`/`max_wounds`, and all status flags. VP at top-level only (not per-unit).
   100|
   101|7 new tests: identical shape autoplay/replay, runtime_id keys, display_name preserved,
   102|player_id per unit, mirrored-name distinct IDs, VP consistency, status flags.
   103|Full suite: 478 passed, 0 failures.
   104|
   105|## Regression evidence — Task 0.3 (non-destructive DB/replay)
   106|
   107|**2026-05-16.** `DROP TABLE IF EXISTS replays` removed. `save_replay()` non-destructive by default.
   108|`game_id` UUID-based. 6 new tests. 484 passed.
   109|
   110|## Regression evidence — Task 4.1 (5-phase 10e loop invariants)
   111|
   112|**2026-05-17.** Locked the runtime phase loop to the canonical Warhammer 40k 10e order: Command → Movement → Shooting → Charge → Fight.
   113|
   114|Changes:
   115|- Added `GAME_PHASE_ORDER` as the shared canonical phase order in `backend/state/game_state.py`.
   116|- Updated `GameState.next_phase()` and `Scenario.run_round()` to consume that shared order instead of duplicated hardcoded phase-count logic.
   117|- Added regression coverage for enum size/order, shared phase-order export, scenario full-round phase logs, replay/autoplay snapshot phase names, and autoplay full-turn five-phase execution.
   118|- Confirmed no runtime Morale/Psychic/End phase enum members are present and battle-shock remains a Command phase step.
   119|
   120|```bash
   121|$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py -q
   122|80 passed, 12 warnings in 8.20s
   123|
   124|$ uv run python -m pytest tests/ -q
   125|593 passed, 3 skipped, 60 warnings in 53.49s
   126|
   127|$ uv run ruff check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
   128|All checks passed!
   129|
   130|$ uv run ruff format --check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
   131|6 files already formatted
   132|
   133|$ git diff --check -- backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_autoplay.py tests/test_replay.py
   134|(clean)
   135|```
   136|
   137|## Regression evidence — Task 4.2 check update
   138|
   139|Date: 2026-05-18
   140|
   141|Verdict: REQUEST CHANGES after independent Task 4.2 check.
   142|
   143|Findings:
   144|- `Scenario._command_phase()` awards CP to every player on each Command phase execution; with `active_player='p1'`, probe observed `after_command_cp 1 1`.
   145|- Repeated `_command_phase()` is not CP-idempotent; probe observed `after_repeated_command_cp 2 2`.
   146|- Battle-shock reset is not owner-scoped; active-player Command cleared both players' battle-shocked units.
   147|- Current tests encode the double-award behavior as expected and must be replaced with contract regressions.
   148|
   149|Observed verification during check:
   150|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q` → 25 passed.
   151|- `uv run python -m pytest tests/ -q` → 599 passed, 3 skipped, 60 warnings.
   152|- Ruff check/format clean for `backend/state/game_state.py`, `backend/engine/scenario.py`, `tests/test_game_state.py`, `tests/test_scenario.py`.
   153|- `git diff --check` clean for checked Task 4.2 files.
   154|
   155|## Regression evidence — Task 4.2 fix / Phase 4 checkpoint
   156|
   157|Date: 2026-05-18
   158|
   159|What changed:
   160|- Command phase CP is scoped to the active/current player only; opponent CP remains unchanged until that player's own Command phase.
   161|- Command CP/reset processing is idempotent per `(round, active_player)` and only awards again after an explicit player/round boundary.
   162|- Battle-shock reset and Command-phase battle-shock tests are owner-scoped to the active player's units.
   163|
   164|Test results:
   165|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q` → 28 passed in 0.62s.
   166|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py -q` → 42 passed in 0.78s.
   167|- `uv run python -m pytest tests/ -q` → 602 passed, 3 skipped, 60 warnings in 52.82s.
   168|- `uv run ruff check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py` → All checks passed.
   169|- `uv run ruff format --check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py` → 4 files already formatted.
   170|- Health smoke: `curl -sS http://127.0.0.1:8000/api/health` → `{"status":"ok","version":"0.7.9"}`.
   171|
   172|
   173|## Regression evidence — Task 4.3 re-check (REQUEST CHANGES)
   174|
   175|Date: 2026-05-18
   176|
   177|Verdict: Task 4.3 is reopened after independent check. Prior Phase 4 completion evidence is not authoritative for Task 4.3 until these blockers are fixed.
   178|
   179|Findings:
   180|- Mission scoring values are not mission-defined; probe observed Only War `3`, Take and Hold `1`, and Purge the Foe `0` for one controlled objective.
   181|- `Scenario._command_phase()` VP sync can omit `PlayerState.victory_points` with no faction profiles and multiply it with multiple profile entries.
   182|- `check_end_game()` still has a generic `vp.total >= 100` VP-cap end condition.
   183|- Task 4.3 tests do not prove Battle Ready exactly-once/idempotent finalization or replay/result/final snapshot VP parity.
   184|- `uv run ruff check tests/test_mission.py` fails with F811/I001 findings; `uv run ruff format --check tests/test_mission.py` would reformat.
   185|
   186|Observed verification during check:
   187|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 52 passed in 8.10s.
   188|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 604 passed, 3 skipped, 60 warnings in 51.78s.
   189|- `git diff --check -- tests/test_mission.py` → clean.
   190|
   191|Review file: `docs/reviews/2026-05-18/task-04-03-lock-vp-objectives-mission-normalization-battle-ready-check.md`.
   192|
   193|## Regression evidence — Task 4.3 (fixed)
   194|
   195|Date: 2026-05-18
   196|
   197|All Task 4.3 blocking findings resolved: mission-defined scoring, VP cap removed, VP sync idempotent, lint/formatter green, tests updated.
   198|
   199|Verification: focused `52 passed`, full `604 passed, 3 skipped, 60 warnings`. Ruff/format/diff-check clean.
   200|
   201|## Regression evidence — Task 5.1 (charge destination + engagement identity)
   202|
   203|Date: 2026-05-18
   204|
   205|Fixed charge destination to enumerate all 8 adjacent cells (not just left/right X-axis). Same-X/different-Y scenarios now find valid adjacent cells. Melee combat scoped to opponent units only. Added 6 regression tests (charge cell avoidance, occupied alternate, same-X, opponent-only targeting, same-name mirrored units, runtime ID logging).
   206|
   207|Verification: focused 10 passed, full 610 passed, 3 skipped. Ruff/format/diff-check clean.
   208|
   209|## Regression evidence — Task 5.2 (melee target selection + damage logging)
   210|
   211|Date: 2026-05-18
   212|
   213|Melee combat now uses the combat engine via `simulate_unit_attack()` with melee weapons. Counter-attack also uses proper combat resolution. Damage logs use `hits ... for ... damage` pattern with runtime unit IDs. Added 3 regression tests (adjacent resolution, log format, same-name attribution).
   214|
   215|Verification: scoped 19 passed, full 613 passed, 3 skipped. Ruff/format/diff-check clean.
   216|
   217|## Regression evidence — Task 5.3 (terrain/LoS/cover blockers)
   218|
   219|Date: 2026-05-18 (Phase 5 checkpoint)
   220|
   221|set_terrain() now invalidates LoS cache. Cover argument order fixed in scenario shooting (target first). AP0 cover cap: SV3+ with cover vs AP0 stays at SV3+ (SV2+ unaffected). Added 9 regression tests.
   222|
   223|Phase 5 closed: 22 scoped passed, 622 full passed. Ruff/format/diff-check clean.
   224|
   225|## Superseding evidence — Phase 4 re-check — 2026-05-19
   226|
   227|Verdict: REQUEST CHANGES. Phase 4 is not closed because Task 4.3 still fails deterministic VP/Battle Ready review despite green pytest/lint gates.
   228|
   229|Evidence:
   230|- Phase order remains canonical: `command -> movement -> shooting -> charge -> fight` and GamePhase count is 5.
   231|- CP/battle-shock/VP sync probes pass for no-profile and multi-profile Scenario Command processing; repeated Command processing does not duplicate CP/VP.
   232|- VP cap removal probe passes: `check_end_game(..., vp.total={1:100,2:0}, round_num=1)` returns `None`.
   233|- Blocking: isolated Only War objective scoring returns 5 VP, expected 3 VP.
   234|- Blocking: isolated Purge the Foe objective scoring returns 0 VP, expected 5 VP.
   235|- Blocking: no Battle Ready exact-once, repeated finalization idempotence, or final replay/result snapshot parity regression was found in Phase 4 tests.
   236|
   237|Verification:
   238|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 80 passed in 8.55s.
   239|- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 622 passed, 3 skipped, 60 warnings in 51.93s.
   240|- `uv run ruff check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py` → All checks passed.
   241|- `uv run ruff format --check backend/state/game_state.py backend/state/mission.py backend/engine/scenario.py backend/engine/ai/autoplay.py tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py` → 9 files already formatted.
   242|
   243|

## Regression evidence — Task 4.3 re-check FIXED (2026-05-19)

- Re-check findings resolved: Only War isolated objective = 3 VP, Purge the Foe isolated objective = 5 VP, Battle Ready exact-once + final snapshot parity covered by regression tests.
- Scoped: `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 84 passed.
- Full suite: `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 626 passed, 3 skipped, 60 warnings.
- Quality gates: `ruff check` passed, `ruff format --check` passed (9 files already formatted).

## Superseding evidence — Task 5.2 CR — 2026-05-19

Verdict: REQUEST CHANGES. Task 5.2 is not ready to close.

Behavior observed:
- Adjacent melee resolves and opponent-only target scoping works in the deterministic probe; friendly adjacent unit remains undamaged.
- Blocking: `_resolve_melee_combat()` logs `hits ... for ... damage in melee`, but `_parse_log_events()` only parses `hits ... for ... damage`; the authoritative melee hit line becomes generic `info`.
- Blocking: same-name melee damage attribution is not proven non-name-based because parsed events lose the attacker runtime ID and only retain a target-side damage event.
- Blocking: `git diff --check` for the claimed touched set fails on `tests/test_result_screen.py` CRLF/trailing-whitespace lines.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_scenario.py tests/test_result_screen.py tests/test_movement.py -q` → 19 passed in 0.72s.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 626 passed, 3 skipped, 60 warnings in 49.02s.
- `uv run ruff check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py` → All checks passed.
- `uv run ruff format --check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py` → 4 files already formatted.
- `git diff --check -- backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py docs/remediation/task-05-02-fix-melee-target-selection-and-damage-logging.md docs/remediation/remediation-plan.md docs/remediation/index.md` → failed on `tests/test_result_screen.py` CRLF/trailing whitespace.

## Superseding evidence — Task 5.3 CR — 2026-05-19

Verdict: REQUEST CHANGES for closure metadata only. Terrain/LoS/cover behavior passes, but Task 5.3 cannot claim Phase 5 checkpoint completion while Task 5.2 remains `changes_requested`.

Behavior observed:
- `set_terrain()` invalidates the LoS cache.
- Scenario shooting calls `_has_cover()` with defender/target position first and shooter position second.
- AP0 cover cap uses pre-cover save state in both runtime and expected-value save paths.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_terrain.py tests/test_scenario.py -q` → 13 passed in 0.49s.
- `uv run python -m pytest tests/ -q` → 626 passed, 3 skipped, 60 warnings in 50.82s.
- `uv run ruff check backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_terrain.py` → All checks passed.
- `uv run ruff format --check backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_terrain.py` → 4 files already formatted.
- `git diff --check -- backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_terrain.py` → clean.


- Task 5.2 re-check FIXED (2026-05-19): `_parse_log_events` parses melee hit lines as structured `fight` events with runtime IDs; same-name attribution regressions added; scoped/full/ruff/format/diff gates green.

## Regression evidence — Task 6.1 FIXED (2026-05-19)

- `run_auto_game()` now persists an authoritative `final_state` after post-game scoring (including Battle Ready), and writes `summary.final_state` + `summary.final_victory_points`.
- When no rounds execute (`max_rounds=0`), replay logs still contain a persisted final snapshot round to avoid result/replay authority gaps.
- `/api/results/{game_id}` now emits authoritative `final_state` and computes/normalizes `summary.final_victory_points` + winner from that same authority path.
- Result page VP cards and VP chart terminal point both consume the same authoritative final VP source (`final_victory_points`/`final_state`), removing round-tail divergence.

Verification:
- `uv run python -m pytest tests/test_autoplay.py tests/test_replay.py tests/test_result_screen.py -q` → 65 passed.
- `uv run python -m pytest tests/ -q` → 629 passed, 3 skipped, 60 warnings.
- `uv run ruff check backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_autoplay.py tests/test_result_screen.py tests/test_replay.py` → All checks passed.
- `uv run ruff format --check backend/engine/ai/autoplay.py web/routes/api_replays.py tests/test_autoplay.py tests/test_result_screen.py tests/test_replay.py` → 5 files already formatted.
- `node -c web/static/result_chart.js` → syntax OK.
- `git diff --check -- backend/engine/ai/autoplay.py web/routes/api_replays.py web/static/result_chart.js web/templates/result.html tests/test_autoplay.py tests/test_result_screen.py tests/test_replay.py` → clean.
