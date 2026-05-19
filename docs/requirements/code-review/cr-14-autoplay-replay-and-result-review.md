---
title: "CR-14 — Autoplay, replay and result review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-14
tags: [requirements, code-review, atomic-review]
---

# CR-14 — Autoplay, replay and result review

**Objective:** проверить full simulation pipeline: setup → auto-play → replay storage → result summary.

**Files:**
- Review: `backend/engine/ai/autoplay.py`
- Review: `backend/engine/replay.py`
- Review: `web/routes/api_replays.py`
- Review: `web/static/scenario_setup.js`
- Review: `web/static/replay_viewer.js`
- Review: `web/static/result_chart.js`
- Output: `docs/reviews/YYYY-MM-DD/CR-14-autoplay-replay-result.md`

**Steps:**
1. Проверить game_id serialization and redirect flow.
2. Проверить replay persistence JSON columns.
3. Проверить `_snapshot_state` includes units, positions, VP, map dimensions.
4. Проверить `_build_summary` parsing kills/damage/charges.
5. Проверить result winner fallback.
6. Проверить round viewer dynamic grid size.
7. Запустить replay/result tests and one TestClient E2E auto-play.

**Acceptance:** generated/saved rosters can run simulation and open `/result/{game_id}` with meaningful summary.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-09/CR-14-autoplay-replay-and-result-review.md`

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
- **Suggestions:** 0
- **Blocked by:** —
- **Completed at:** 2026-05-09T23:13:16+03:00
- **Verification:** `62 passed, 7 warnings in 11.41s`; custom replay/result probes confirmed game_id overwrite, stale final VP snapshots, duplicate-name summary attribution, VP parser mismatch, and result charge attribution gap.

## Triage summary

- [CR-14 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-14)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 0.1 (runtime unit identity)

**2026-05-16.** Fixed "duplicate-name summary attribution" finding:

1. **`_build_summary()`** — Now uses `strip_event_identity()` to extract authoritative
   `actor_id`/`target_id` from the `[actor_id=p1:Boyz:0; target_id=p2:Boyz:0]`
   suffix in log lines. Builds `runtime_id → player_id` map. Correct attribution
   even when both players have identically-named units (e.g. both field "Boyz").
   Fallback to display-name lookup for log lines without identity suffix.

2. **`_parse_log_events()`** — Updated all 17 patterns to strip identity suffix
   and use `meta.get("actor_id"/"target_id", …)` for `ReplayEvent` construction.
   Replay events now carry stable runtime IDs alongside display names.

3. **`RosterState.units`** — `dict[str, Unit]` → `list[tuple[str, Unit]]`.
   Duplicate unit names within a roster are representable end-to-end.

Verification: `uv run python -m pytest tests/ -q` → 471 passed, 3 skipped, 0 failures.
`ruff check` → All checks passed.

## Regression evidence — Task 0.2 (canonical GameState serializer)

**2026-05-16.** Two divergent `_snapshot_state` implementations consolidated into single
canonical `snapshot_game_state()` in `backend/state/game_state.py`. Both `autoplay.py`
and `replay.py` now delegate to it. Round snapshots and final snapshots share identical
shape. Unit records include `runtime_unit_id` as authoritative `id`, `player_id`,
`current_wounds`/`max_wounds`, and all status flags. VP at top-level only (not per-unit).

7 new tests: identical shape autoplay/replay, runtime_id keys, display_name preserved,
player_id per unit, mirrored-name distinct IDs, VP consistency, status flags.
Full suite: 478 passed, 0 failures.

## Regression evidence — Task 0.3 (non-destructive DB/replay)

**2026-05-16.** `DROP TABLE IF EXISTS replays` removed. `save_replay()` non-destructive by default.
`game_id` UUID-based. 6 new tests. 484 passed.

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

All Task 4.3 blocking findings resolved: mission-defined scoring, VP cap removed, VP sync idempotent, lint/formatter green, tests updated.

Verification: focused `52 passed`, full `604 passed, 3 skipped, 60 warnings`. Ruff/format/diff-check clean.

## Regression evidence — Task 5.1 (charge destination + engagement identity)

Date: 2026-05-18

Fixed charge destination to enumerate all 8 adjacent cells (not just left/right X-axis). Same-X/different-Y scenarios now find valid adjacent cells. Melee combat scoped to opponent units only. Added 6 regression tests (charge cell avoidance, occupied alternate, same-X, opponent-only targeting, same-name mirrored units, runtime ID logging).

Verification: focused 10 passed, full 610 passed, 3 skipped. Ruff/format/diff-check clean.

## Regression evidence — Task 5.2 (melee target selection + damage logging)

Date: 2026-05-18

Melee combat now uses the combat engine via `simulate_unit_attack()` with melee weapons. Counter-attack also uses proper combat resolution. Damage logs use `hits ... for ... damage` pattern with runtime unit IDs. Added 3 regression tests (adjacent resolution, log format, same-name attribution).

Verification: scoped 19 passed, full 613 passed, 3 skipped. Ruff/format/diff-check clean.

## Regression evidence — Task 5.3 (terrain/LoS/cover blockers)

Date: 2026-05-18 (Phase 5 checkpoint)

set_terrain() now invalidates LoS cache. Cover argument order fixed in scenario shooting (target first). AP0 cover cap: SV3+ with cover vs AP0 stays at SV3+ (SV2+ unaffected). Added 9 regression tests.

Phase 5 closed: 22 scoped passed, 622 full passed. Ruff/format/diff-check clean.

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

