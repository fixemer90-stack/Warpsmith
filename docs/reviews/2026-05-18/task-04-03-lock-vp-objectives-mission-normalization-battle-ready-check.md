# Task 4.3 — Lock VP, objectives, mission normalization, Battle Ready — check 2026-05-18

## Verdict

REQUEST CHANGES.

## Scope checked

Task file: `docs/remediation/task-04-03-lock-vp-objectives-mission-normalization-battle-ready.md`

Primary CRs: CR-08, CR-10, CR-14, CR-24.

Reviewed code/tests:
- `backend/state/mission.py`
- `backend/engine/scenario.py`
- `backend/engine/ai/autoplay.py`
- `backend/state/game_state.py`
- `tests/test_mission.py`
- `tests/test_autoplay.py`
- `tests/test_result_screen.py`

## Blocking findings

### 1. Mission scoring values are not mission-defined and Take and Hold/Purge the Foe do not award the required VP values

Acceptance criteria require objective scoring values to come from normalized mission definitions and dynamic objectives to award: Only War 3 VP, Take and Hold 5 VP, Purge the Foe 5 VP.

Observed implementation:
- `MissionConfig` has no per-objective VP value/mission definition field.
- `score_standard()` and `Mission.score_vp()` hardcode `+1` per controlled objective.
- `score_progressive()` hardcodes `objectives controlled + 2 if ahead`; it only produces 3 VP for a single Only War objective by coincidence.
- `score_kill_points()` ignores objective control entirely for Purge the Foe, so a controlled Purge objective awards 0 VP.

Deterministic probe:

```text
Only War {'p1': 3, 'p2': 0}
Take and Hold {'p1': 1, 'p2': 0}
Purge the Foe {'p1': 0, 'p2': 0}
```

Required fix:
- Add a shared normalized mission definition/lookup that carries the scoring contract, including objective VP value and objective count.
- Route runtime scoring through that definition for Only War, Take and Hold, and Purge the Foe.
- Add tests that isolate one controlled objective per mission and assert 3/5/5 VP respectively.

### 2. Scenario Command phase does not synchronize the authoritative VP source consistently and can multiply VP by profile entries

`Scenario._command_phase()` calls `apply_scoring()` and records the correct `VPTracker`, but the compatibility sync to `PlayerState.victory_points` is incorrectly nested inside the `for player_id, profile in self._faction_profiles.items()` loop.

Observed behavior:
- With no faction profiles, `VPTracker` records scoring but `PlayerState.victory_points` remains 0, so snapshots/result consumers using `PlayerState.victory_points` miss authoritative scoring.
- With four profile entries, the same round VP is added four times.

Deterministic probe:

```text
scenario tracker total {1: 1, 2: 0} player VP {'p1': 0, 'p2': 0}
scenario profiles tracker total {1: 1, 2: 0} player VP {'p1': 4, 'p2': 0}
```

Required fix:
- Move the VP sync out of the profile loop and make it idempotent per scoring event.
- Add a regression test covering both no-profile and multi-profile scenarios so final snapshots/result totals match the authoritative VP tracker exactly once.

### 3. Game end logic still has an arbitrary VP threshold

Task 4.3 acceptance criteria require game termination to be driven by round cap, army wipe/table state, and explicit mission-end conditions, not arbitrary VP thresholds.

Observed implementation in `backend/state/mission.py::check_end_game()` still ends the game when a player reaches `vp.total[player_num] >= 100` with reason `vp_cap`. That is a generic VP threshold rather than a mission-specific explicit end condition.

Required fix:
- Remove the generic VP cap from default end-game logic, or move mission-specific caps into explicit mission definitions/end conditions.
- Replace `test_check_end_game_vp_cap`/related expectations so they do not legitimize arbitrary threshold termination.

### 4. Claimed quality gates are stale/red

The task file says Ruff passed for `tests/test_mission.py`, but re-running the claimed gate fails.

Observed:

```bash
$ uv run ruff check tests/test_mission.py
F811 Redefinition of unused `GameState` at tests/test_mission.py:1102
I001 Import block is un-sorted or un-formatted at tests/test_mission.py:1121
F811 Redefinition of unused `GameState` at tests/test_mission.py:1122
F811 Redefinition of unused `UnitState` at tests/test_mission.py:1125
Found 4 errors.

$ uv run ruff format --check tests/test_mission.py
Would reformat: tests/test_mission.py
1 file would be reformatted
```

Required fix:
- Clean up duplicate/local imports in `tests/test_mission.py`.
- Re-run and update task verification from the latest successful lint/format run.

### 5. The tests added for Task 4.3 do not cover the claimed behavior

Task 4.3 claims tests for Battle Ready exactly-once behavior, repeated finalization idempotence, final replay/result snapshot including Battle Ready VP, and the 3/5/5 mission objective VP values. The current added tests only cover mission name aliases, objective counts, VP>=10 not ending the game via `GameState.is_game_over`, and round-cap/wipe examples.

Required fix:
- Add tests for Battle Ready +10 in final authoritative state and repeated finalization/idempotence.
- Add tests proving replay/result/final snapshot totals match after Battle Ready.
- Add scoring-value tests that fail on the current Take and Hold/Purge behavior.

## Verification run during check

```bash
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q
52 passed in 8.10s

$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q
604 passed, 3 skipped, 60 warnings in 51.78s

$ uv run ruff check tests/test_mission.py
FAILED — 4 Ruff findings (F811/I001/F811/F811)

$ uv run ruff format --check tests/test_mission.py
FAILED — would reformat tests/test_mission.py

$ git diff --check -- tests/test_mission.py
clean
```

## Closure action taken

- Task 4.3 is downgraded to `status: changes_requested`.
- Source plan/index Phase 4 row is downgraded for Task 4.3.
- Phase 4 checkpoint claims are no longer authoritative until Task 4.3 is fixed and re-verified.
