# Code review — Task 5.2 — Fix melee target selection and damage logging

Date: 2026-05-19
Task: `docs/remediation/task-05-02-fix-melee-target-selection-and-damage-logging.md`
Verdict: REQUEST CHANGES → FIXED 2026-05-19

## Scope

Reviewed Task 5.2 against its acceptance criteria:

- Adjacent melee attacks resolve.
- Damage log/event uses `hits ... for ... damage` or structured equivalent.
- Summary attribution is not name-based.

Files checked:

- `backend/engine/scenario.py`
- `backend/state/runtime_id.py`
- `web/routes/api_replays.py`
- `tests/test_movement.py`
- `tests/test_scenario.py`
- `tests/test_result_screen.py`
- `docs/remediation/task-05-02-fix-melee-target-selection-and-damage-logging.md`
- `docs/remediation/remediation-plan.md`
- `docs/remediation/index.md`

## Verdict

REQUEST CHANGES. Melee target scoping itself is improved, but Task 5.2 cannot be accepted because the logged melee hit is not parsed as a structured damage/shoot/fight event and result attribution can still fall back to target/name-derived data rather than the attacker runtime ID.

## Findings

| # | Severity | Finding | Evidence | Required fix |
|---|---|---|---|---|
| 1 | Important | Melee hit logs are not parsed as structured damage events. | `_resolve_melee_combat()` logs `Boyz hits Boyz for 1 damage in melee [actor_id=...; target_id=...]`, but `_parse_log_events()` only matches `^... hits ... for ... damage$` after stripping identity. The deterministic probe parsed the melee hit as generic `info`, not damage/fight/shoot. | Either change the log text to the parser contract (`hits ... for ... damage`) and carry melee via metadata/phase, or update `_parse_log_events()` to parse `... damage in melee` as a structured fight/damage event with actor_id/target_id. Add a regression. |
| 2 | Important | Summary attribution is still not proven non-name-based for melee damage. | The same probe produced a parsed `damage` event from `Boyz took 1 damage [target_id=p2:Boyz:0]` with `actor_id=p2:Boyz:0` / no attacker source, plus the actual attacker hit line became `info`. With same-name `Boyz` units, downstream summaries cannot attribute melee damage to `p1:Boyz:0`. | Add replay/result parser regression where same-name melee damage is attributed to the attacker runtime ID (`actor_id=p1:Boyz:0`, `target_id=p2:Boyz:0`) and contributes to the correct player summary. |
| 3 | Important | Quality gate is red for the claimed touched set. | `git diff --check -- backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py ...` fails on `tests/test_result_screen.py` CRLF/trailing-whitespace lines. | Normalize/fix the touched file set or remove the stale modified CRLF file from the task closure surface, then rerun `git diff --check`. |
| 4 | Important | Source plan/index claimed Task 5.2 complete while the source plan's Phase 5 block was stale. | Task file and index showed `[x]`, but `remediation-plan.md` still had Task 5.2 unchecked before this review. | Keep Task 5.2 marked `changes_requested` until the parser/attribution regression and closure surfaces are fixed. |

## Deterministic probe

```bash
uv run python - <<'PY'
from backend.engine.scenario import Scenario
from backend.state.game_state import GameState, PlayerState, UnitState
from web.routes.api_replays import _parse_log_events

state=GameState(game_id='probe', mission_name='', map_width=6, map_height=4)
p1=PlayerState('p1','P1','orks')
p2=PlayerState('p2','P2','orks')
att=UnitState('p1:Boyz:0','Boyz','orks',(1,1),10,10,1,1,6,1)
friendly=UnitState('p1:Gretchin:0','Gretchin','orks',(1,2),10,10,1,1,6,1)
enemy=UnitState('p2:Boyz:0','Boyz','orks',(2,1),10,10,1,1,6,1)
p1.units={att.unit_id:att, friendly.unit_id:friendly}
p2.units={enemy.unit_id:enemy}
state.players={'p1':p1,'p2':p2}
sc=Scenario(state)
start=len(state.game_log)
sc._resolve_melee_combat(att)
logs=state.game_log[start:]
print('logs:')
for l in logs: print(l)
print('wounds', {'attacker':att.current_wounds,'friendly':friendly.current_wounds,'enemy':enemy.current_wounds})
events=_parse_log_events(logs, 1)
print('events', len(events))
for e in events: print(e.event_type, e.phase, e.actor_id, e.actor_name, e.target_id, e.target_name, e.result_value)
PY
```

Observed output:

```text
logs:
Boyz took 1 damage [target_id=p2:Boyz:0]
Boyz hits Boyz for 1 damage in melee [actor_id=p1:Boyz:0; target_id=p2:Boyz:0]
wounds {'attacker': 10, 'friendly': 10, 'enemy': 9}
events 2
damage  p2:Boyz:0 Boyz None None 1.0
info    None None None
```

Interpretation:

- Adjacent melee resolves and the friendly unit is not damaged.
- The authoritative attacker hit line is not parsed as a structured event.
- The parsed damage event is target-side only and cannot support non-name-based attacker attribution.

## Verification run

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_scenario.py tests/test_result_screen.py tests/test_movement.py -q
# 19 passed in 0.72s

rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q
# 626 passed, 3 skipped, 60 warnings in 49.02s

uv run ruff check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py
# All checks passed!

uv run ruff format --check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py
# 4 files already formatted

git diff --check -- backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py docs/remediation/task-05-02-fix-melee-target-selection-and-damage-logging.md docs/remediation/remediation-plan.md docs/remediation/index.md
# FAIL: tests/test_result_screen.py CRLF/trailing whitespace lines 1-71
```

## Required before approval

1. Make melee hit logs parse into structured replay/result events with attacker and target runtime IDs.
2. Add a regression for same-name melee damage attribution through `_parse_log_events()` / result summary path.
3. Fix `git diff --check` for the claimed touched file set.
4. Update Task 5.2, remediation-plan, index, and CR-09/11/14/15 evidence after green scoped/full/lint/format/diff gates.


## Resolution (2026-05-19)

- Finding 1 fixed: `_parse_log_events()` now parses `... hits ... for ... damage in melee` as structured `fight` events (`phase="fight"`, `detail="melee_hit"`) with runtime IDs from identity metadata.
- Finding 2 fixed: same-name runtime-ID attribution regression added in `tests/test_replay.py::test_parse_log_events_uses_runtime_ids_when_metadata_present` and `tests/test_parse_log_events.py::test_parses_melee_hits_as_structured_fight_events_with_runtime_ids`.
- Finding 3 fixed: CRLF removed from `tests/test_result_screen.py`; `git diff --check` passes for touched closure set.
- Finding 4 fixed: Task/index/remediation-plan status surfaces synchronized to FIXED.

Verification rerun:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_parse_log_events.py tests/test_replay.py tests/test_scenario.py tests/test_result_screen.py tests/test_movement.py -q` → 65 passed.
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 627 passed, 3 skipped, 60 warnings.
- `uv run ruff check web/routes/api_replays.py tests/test_parse_log_events.py tests/test_replay.py tests/test_result_screen.py tests/test_scenario.py tests/test_movement.py` → All checks passed.
- `uv run ruff format --check web/routes/api_replays.py tests/test_parse_log_events.py tests/test_replay.py tests/test_result_screen.py tests/test_scenario.py tests/test_movement.py` → already formatted.
- `git diff --check -- web/routes/api_replays.py tests/test_parse_log_events.py tests/test_replay.py tests/test_result_screen.py tests/test_scenario.py tests/test_movement.py docs/remediation/task-05-02-fix-melee-target-selection-and-damage-logging.md docs/remediation/remediation-plan.md docs/remediation/index.md docs/reviews/2026-05-19/task-05-02-fix-melee-target-selection-and-damage-logging-review.md` → clean.
