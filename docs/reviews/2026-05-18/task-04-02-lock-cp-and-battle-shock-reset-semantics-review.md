# Review — Task 4.2: Lock CP and battle-shock reset semantics

Date: 2026-05-18
Verdict: REQUEST CHANGES → FIXED 2026-05-18

## Scope

Independent check of `docs/remediation/task-04-02-lock-cp-and-battle-shock-reset-semantics.md` against its CP/reset contract, implementation, tests, and closure artifacts.

## Original blocking findings (fixed)

### Important 1 — Command phase awards CP to every player, not only the active player

Task contract requires:

- active player gains +1 CP on their own Command phase;
- opponent does not gain CP during active player Command phase;
- CP gain happens once per player turn, not once per full phase pass.

Original implementation at review time in `backend/engine/scenario.py::_command_phase()` loops over all players and increments each player's CP on every Command phase execution:

```python
for player in self.state.players.values():
    cp_gain = 1
    ...
    player.command_points += cp_gain
```

Deterministic probe with `game.active_player = "p1"`:

```text
start_cp 0 0
after_command_cp 1 1
```

Expected under the task contract: `p1=1`, `p2=0` for p1's Command phase.

### Important 2 — Command phase is not idempotent for CP

Task contract requires repeated Command phase processing to be idempotent unless the call explicitly advances turn state.

Original behavior at review time:

```text
after_command_cp 1 1
after_repeated_command_cp 2 2
```

The regression test originally documented the opposite behavior and passes while contradicting the task AC:

```python
# Calling _command_phase again would double-award ...
scenario._command_phase()
assert p1.command_points == cp_after_first + 1
```

This is a test-quality blocker: the test encodes the bug as expected behavior.

### Important 3 — Battle-shock reset clears every player's units, not only the unit owner's Command phase

Task contract requires `is_battle_shocked` to clear only during that unit owner's Command phase reset step. Original `_command_phase()` cleared battle-shock for every unit of every player:

```python
for player in self.state.players.values():
    for unit in player.units.values():
        unit.is_battle_shocked = False
```

Probe with `active_player = "p1"` and both players battle-shocked:

```text
after_command_shock False False
```

Expected under the task contract: p1 owner's units clear; p2 owner's units remain battle-shocked until p2's own Command phase.

### Important 4 — Closure artifacts are inconsistent/stale

- Task frontmatter uses `status: complete`, while the remediation workflow expects `completed` for completed tasks and `changes_requested` for blockers.
- `docs/remediation/remediation-plan.md` still has all Task 4.2 checkboxes unchecked, while the task file says everything is complete.
- `docs/remediation/index.md` shows Task 4.2 checked even though source plan and implementation disagree.
- Primary CRs are CR-08, CR-10, CR-14, CR-24, but Task 4.2 regression evidence was found only in CR-08.
- Verification numbers are stale: task records focused `24 passed` and full `590 passed`; current observed results are focused `25 passed` and full `599 passed, 3 skipped`.

## Verification performed

```text
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q
25 passed in 0.45s

uv run python -m pytest tests/ -q
599 passed, 3 skipped, 60 warnings in 48.63s

uv run ruff check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py
All checks passed!

uv run ruff format --check backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py
4 files already formatted

git diff --check -- backend/state/game_state.py backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py docs/remediation/task-04-02-lock-cp-and-battle-shock-reset-semantics.md docs/remediation/remediation-plan.md docs/remediation/index.md
clean

curl -sS http://127.0.0.1:8000/api/health
{"status":"ok","version":"0.7.9"}
```

Deterministic probe:

```text
start_cp 0 0
after_command_cp 1 1
after_command_shock False False
after_repeated_command_cp 2 2
shock_after_movement True True
shock_after_shooting True True
shock_after_charge True True
shock_after_fight True True
round_after_fight 2 command advanced False False
```

## Required before marking complete (completed)

- Make Command phase CP award scoped to the active/current player turn instead of all players.
- Track Command phase processing so repeated calls do not double-award CP unless the engine explicitly advances to another player turn/Command boundary.
- Clear battle-shock only for the owner whose Command phase is being processed.
- Replace the contradictory `test_cp_not_double_awarded_on_repeated_command` expectation with the actual idempotency contract.
- Add tests for opponent CP not changing and opponent battle-shock not clearing during active player's Command phase.
- Re-run scoped tests, full suite, Ruff check, Ruff format check, diff check, and health smoke.
- Sync task/source-plan/index/CR evidence with current results after the fix.


## Resolution

### Command phase awards CP to every player (Fixed)

- `Scenario._command_phase()` now resolves the active Command owner from `GameState.active_player`, command priority, or first player fallback.
- Only that active player receives the 10e +1 CP Command award; the opponent remains unchanged until their own Command phase.

### Command phase is not idempotent for CP (Fixed)

- Added `Scenario._processed_command_turns` keyed by `(current_round, active_player_id)`.
- Repeated processing of the same player's Command phase skips duplicate CP/reset work; changing `active_player` or advancing the round is the explicit boundary for another award.

### Battle-shock reset clears every player's units (Fixed)

- Command reset now clears `is_battle_shocked` only for the active owner's units.
- `_battle_shock_tests()` is scoped to the same active owner so opponent units are not accidentally cleared by the Command-phase test step.

### Tests encode the bug (Fixed)

- Replaced tests that expected simultaneous CP awards and double-awards.
- Added/updated regressions for active-player CP, opponent CP unchanged, explicit next-player Command award, idempotency, owner-scoped battle-shock reset, and CP cap behavior.

### Closure artifacts are inconsistent/stale (Fixed)

- Synced `task-04-02-lock-cp-and-battle-shock-reset-semantics.md`, `remediation-plan.md`, `index.md`, CR-08/10/14/24 evidence, `triage-summary.md`, and `code-review.md` with the fixed verdict and current verification counts.

### Re-check results

```text
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py -q
28 passed in 0.62s

$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py -q
42 passed in 0.78s

$ uv run python -m pytest tests/ -q
602 passed, 3 skipped, 60 warnings in 52.82s

$ uv run ruff check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py
All checks passed!

$ uv run ruff format --check backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py
4 files already formatted

$ git diff --check -- backend/engine/scenario.py tests/test_game_state.py tests/test_scenario.py tests/test_f2_7_battle_shock_cp_stratagems.py docs/remediation/task-04-02-lock-cp-and-battle-shock-reset-semantics.md docs/remediation/task-04-03-lock-vp-objectives-mission-normalization-battle-ready.md docs/remediation/remediation-plan.md docs/remediation/index.md docs/reviews/2026-05-18/task-04-02-lock-cp-and-battle-shock-reset-semantics-review.md docs/reviews/2026-05-10/triage-summary.md docs/requirements/code-review/code-review.md docs/requirements/code-review/cr-08-game-state-and-phase-machine-review.md docs/requirements/code-review/cr-10-mission-objectives-and-vp-review.md docs/requirements/code-review/cr-14-autoplay-replay-and-result-review.md docs/requirements/code-review/cr-24-final-integration-regression-gate.md
(clean)

$ curl -sS http://127.0.0.1:8000/api/health
{"status":"ok","version":"0.7.9"}
```

Deterministic probe after fix:

```text
start_cp 0 0
after_command_cp 1 0
after_command_shock False True
after_repeated_command_cp 1 0
after_repeated_command_shock False True
shock_after_movement True True
shock_after_shooting True True
shock_after_charge True True
shock_after_fight True True
after_p2_command_cp 1 1
after_p2_command_shock True False
```
