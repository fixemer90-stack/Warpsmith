---
title: "CR-24 — Final integration regression gate"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-24
tags: [requirements, code-review, atomic-review]
---

# CR-24 — Final integration regression gate

**Objective:** финально подтвердить, что review/fix cycle не сломал продукт.

**Files:**
- Scope: whole repo
- Output: `docs/reviews/YYYY-MM-DD/CR-24-final-regression-gate.md`

**Steps:**
1. Выполнить `uv run ruff check .`.
2. Выполнить `uv run ruff format --check .`.
3. Выполнить `node -c web/static/team_builder.js`.
4. Выполнить `node -c web/static/scenario_setup.js`.
5. Выполнить `node -c web/static/battlefield_map.js`.
6. Выполнить `uv run python -m pytest tests/ -q`.
7. Запустить server без reload и проверить `/api/health`.
8. Browser smoke key pages: `/`, `/team-builder`, `/scenario-setup`, `/my-rosters`, `/result/<known_or_generated_game_id>` if available.
9. Записать final verdict and remaining accepted debt.

**Acceptance:** final gate report создан; release readiness verdict explicit.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-10/CR-24-final-integration-regression-gate.md`

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

- **Verdict:** Request Changes — executable gates pass, but release readiness is blocked by unresolved/untriaged CR debt (37 prior Critical + 111 prior Important) and a reproduced result VP consistency issue.
- **Critical:** 1
- **Important:** 1
- **Suggestions:** 1
- **Blocked by:** unresolved Critical/Important CR debt, result final VP snapshot mismatch
- **Completed at:** 2026-05-10

## Triage summary

- [CR-24 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-24)
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

Task 4.3 fixed and Phase 4 checkpoint closed. Full suite: `604 passed, 3 skipped`. Ruff/format/diff-check clean.

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



## Regression evidence — Task 4.3 re-check FIXED (2026-05-19)

- Re-check findings resolved: Only War isolated objective = 3 VP, Purge the Foe isolated objective = 5 VP, Battle Ready exact-once + final snapshot parity covered by regression tests.
- Scoped: `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q` → 84 passed.
- Full suite: `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 626 passed, 3 skipped, 60 warnings.
- Quality gates: `ruff check` passed, `ruff format --check` passed (9 files already formatted).

## Regression evidence — Task 6.2 (2026-05-19)

- Task 6.2 replay/result attribution and parsing checks executed as part of the final regression trajectory.
- Re-check found and fixed two final-gate gaps: actual VP logs with totals/Battle Ready wording parsed as `info`, and result charge cards still using the stale `player2` prefix heuristic.
- Same-name attribution, actual VP log parsing, and Player 2 charge visibility are now covered by scoped+full regression runs plus a JS owner-lookup probe.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_parse_log_events.py tests/test_result_screen.py tests/test_replay.py tests/test_round_viewer.py -q` → 61 passed, 0 failed.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 633 passed, 3 skipped, 0 failed.
- `node -c web/static/result_chart.js` → passed.
- JS `chargeCount()` owner-lookup probe → `chargeCount OK`.
- `uv run ruff check .` → All checks passed.
- `uv run ruff format --check .` → 108 files already formatted.

## Regression evidence — Task 6.1 (final snapshot/result gate)

Date: 2026-05-19

Task 6.1 re-check fixed the reproduced result VP consistency issue for authoritative final snapshots: stale summary VP/winner fields no longer outrank final_state, and replay persistence keeps post-game scoring in the final persisted snapshot.

Verification: focused suite `66 passed`; full suite `630 passed, 3 skipped`; Ruff check/format clean; diff-check clean for Task 6.1 touched files.

## Regression evidence — Task 6.3 (2026-05-19)

- Added repeatable final-gate smoke script (`scripts/smoke_final_gate.py`) to replace ad-hoc `/tmp` replay probes.
- Gate validates deterministic VP authority parity across runtime, replay API, results API, and result page wiring, using isolated DB state.
- Added automated regression test (`tests/test_final_gate_smoke.py`) to ensure smoke gate remains executable.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python scripts/smoke_final_gate.py` → exit 0.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_final_gate_smoke.py tests/test_result_screen.py tests/test_replay.py -q` → 46 passed, 0 failed.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 633 passed, 3 skipped, 0 failed.
- `uv run ruff check scripts/smoke_final_gate.py tests/test_final_gate_smoke.py` → All checks passed.
- `uv run ruff format --check scripts/smoke_final_gate.py tests/test_final_gate_smoke.py` → 2 files already formatted.
