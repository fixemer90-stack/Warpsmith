# Review: Task 4.1 — Assert 5-phase 10e loop invariants

Date: 2026-05-17
Reviewer: Hermes
Task file: `docs/remediation/task-04-01-assert-5-phase-10e-loop-invariants.md`

## Verdict

REQUEST CHANGES → FIXED 2026-05-17.

Initial re-review found stale verification, Ruff/format failures, incomplete closure artifacts, and missing replay/autoplay phase-loop coverage. The Resolution section below documents the 2026-05-17 fixes and successful re-check results.

## Findings

### 1. Important — Ruff and format gates fail on the claimed touched test file

Evidence:

```bash
$ uv run ruff check tests/test_game_state.py backend/state/game_state.py
I001 [*] Import block is un-sorted or un-formatted
   --> tests/test_game_state.py:400:5
...
Found 1 error.
[*] 1 fixable with the `--fix` option.

$ ruff format --check tests/test_game_state.py
Would reformat: tests/test_game_state.py
1 file would be reformatted
```

This directly contradicts the task file's Verification section, which records Ruff and format as clean.

Required before marking complete:
- Format/fix `tests/test_game_state.py`.
- Re-run Ruff and format checks.
- Update verification evidence from the last successful run.

### 2. Important — Verification evidence is stale and under-reported

The task records:

```text
17 passed in 0.53s
583 passed, 3 skipped, 60 warnings in 54.19s
```

Re-review observed:

```bash
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q
24 passed in 0.55s

$ uv run python -m pytest tests/ -q
590 passed, 3 skipped, 60 warnings in 54.40s
```

The stale numbers are likely due later tests being added to `tests/test_game_state.py`, but the task/CR evidence must be updated to the latest successful run before completion.

### 3. Important — Marked test coverage AC is not actually satisfied

The task marks this acceptance criterion complete:

> Tests cover GamePhase having exactly five members, phase order being Command -> Movement -> Shooting -> Charge -> Fight, advancing from Fight moving to the next player/round boundary as designed, battle-shock hooks running during Command phase, no separate Morale phase appearing in snapshots/replay/scenario progression, and autoplay completing a full turn using only the five phases.

Actual tests cover enum size/order, Fight -> Command round advance, summary phase values, and battle-shock Command/non-Command behavior. I did not find Task 4.1 tests that explicitly prove:

- no separate Morale phase appears in replay snapshots;
- scenario progression emits/uses only canonical phase values across a full round;
- autoplay completes a full turn using only the five phases.

Evidence from the review scan:

```text
tests/test_game_state.py relevant tests:
- test_game_phase_has_exactly_five_members
- test_game_phase_order_canonical
- test_game_phase_transition_from_fight_advances_round
- test_no_morale_phase_in_enum
- test_game_summary_phase_name_matches_enum_value
- later Task 4.2 CP/battle-shock reset tests

tests/test_scenario.py relevant tests:
- test_run_round
- test_command_phase_cp_generation

tests/test_autoplay.py: no phase/autoplay-loop invariant test found
```

Required before marking complete:
- Add/verify focused tests for replay/snapshot phase values and autoplay full-turn phase-loop behavior, or adjust the AC if that coverage belongs to a later task.

### 4. Important — Scenario still has a hardcoded phase count instead of consuming a shared ordered phase contract

`GameState.next_phase()` uses `list(GamePhase)`, but `Scenario.run_round()` still uses a duplicated hardcoded count:

```python
max_phases_per_round = 5  # COMMAND, MOVEMENT, SHOOTING, CHARGE, FIGHT
while phases_completed < max_phases_per_round and not self.state.is_game_over:
    self._execute_phase(self.state.current_phase)
    phases_completed += 1
    if not self.state.is_game_over:
        self.state.next_phase()
```

That works today, but it is not a single canonical ordered phase contract shared by scenario/autoplay. If `GamePhase` order/length changes, scenario loop behavior can drift from the enum without a local failure except for the dedicated test.

Required before marking complete:
- Introduce/use a single canonical phase order helper/constant, or at minimum derive per-round phase count from the canonical order rather than a literal `5`.
- Ensure scenario/autoplay tests fail if a duplicated phase count/list drifts.

### 5. Important — Closure artifacts are incomplete

Observed closure gaps:

- `docs/remediation/task-04-01-assert-5-phase-10e-loop-invariants.md` still has unchecked `Phase loop contract` and `Non-goals` checkboxes despite frontmatter `status: complete`.
- `docs/remediation/remediation-plan.md` Task 4.1 block remains entirely unchecked.
- `docs/remediation/index.md` marks Task 4.1 `[x]` even though source plan and task internals disagree.
- Regression evidence exists only in CR-08. Task 4.1 Primary CRs are CR-08, CR-10, CR-14, and CR-24, so CR-10/CR-14/CR-24 are missing Task 4.1 evidence.
- CR-08 evidence has stale verification counts (`17 passed`, `583 passed`) and should be updated after fixes.

Required before marking complete:
- Sync task file, remediation plan, index, and all Primary CR evidence after the actual verification gates pass.

## Re-check results

```bash
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q
24 passed in 0.55s

$ uv run python -m pytest tests/ -q
590 passed, 3 skipped, 60 warnings in 54.40s

$ uv run ruff check tests/test_game_state.py backend/state/game_state.py
FAILED: I001 import block is un-sorted/un-formatted in tests/test_game_state.py

$ ruff format --check tests/test_game_state.py
FAILED: 1 file would be reformatted

$ git diff --check -- tests/test_game_state.py
clean
```

## Positive observations

- `GamePhase` currently has exactly five members: `COMMAND`, `MOVEMENT`, `SHOOTING`, `CHARGE`, `FIGHT`.
- No runtime `GamePhase.MORALE`, `MORALE =`, `_morale_phase`, `GamePhase.PSYCHIC`, or `GamePhase.END` implementation was found in the reviewed runtime files.
- Battle-shock is implemented as a Command phase step in `Scenario._command_phase()`.
- Full pytest suite is green despite the closure/lint/coverage blockers.

## Resolution

### Ruff and format gates fail (Fixed)

- Formatted/lint-fixed the Task 4.1 touched Python files.
- `tests/test_game_state.py` import ordering is now clean.
- `ruff check` and `ruff format --check` pass for all touched files.

### Verification evidence stale and under-reported (Fixed)

- Re-ran the expanded focused suite after code/test fixes: `80 passed, 12 warnings in 8.20s`.
- Re-ran the full suite: `593 passed, 3 skipped, 60 warnings in 53.49s`.
- Updated task and CR evidence with current counts.

### Marked test coverage AC not actually satisfied (Fixed)

- Added `test_game_phase_order_export_is_canonical` for the shared phase order contract.
- Extended `test_run_round` to assert scenario executes exactly the canonical five phase logs and no Morale phase.
- Added `test_autoplay_full_turn_uses_only_canonical_five_phases` for autoplay round logs and start/end snapshots.
- Added `test_canonical_snapshot_phase_uses_game_phase_values_only` for replay/autoplay snapshot phase serialization.

### Scenario hardcoded phase count (Fixed)

- Added `GAME_PHASE_ORDER` in `backend/state/game_state.py` as the canonical runtime phase order.
- Updated `GameState.next_phase()` and `Scenario.run_round()` to consume `GAME_PHASE_ORDER` instead of separate list/literal phase count logic.

### Closure artifacts incomplete (Fixed)

- Restored task status to `completed` and marked all Task 4.1 AC/contract/non-goal/completion checkboxes.
- Synced `docs/remediation/remediation-plan.md` and `docs/remediation/index.md`.
- Added/updated Task 4.1 regression evidence in CR-08, CR-10, CR-14, and CR-24.

### Re-check results

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
