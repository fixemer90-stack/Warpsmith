# Task 5.1 Re-check — charge destination and engagement identity

Task file: `docs/remediation/task-05-01-fix-charge-destination-and-engagement-identity.md`
Date: 2026-05-19
Reviewer: Hermes (gpt-5.3-codex)

## Verdict

APPROVED 2026-05-19.

## What was verified

1) Charge destination never occupies enemy cell
- Reviewed `backend/engine/scenario.py::_charge_phase()`.
- Logic enumerates all 8 adjacent cells around target, bounds-checks, sorts by charger distance, and selects first unoccupied cell via `get_unit_at_position()`.
- If all adjacent cells are occupied, charge is skipped with explicit failure log.

2) Engagement identity uses runtime IDs
- Charge logs include `format_event_identity(actor_id=unit.unit_id, target_id=closest.unit_id)`.
- Melee logs include `format_event_identity(actor_id=attacking_unit.unit_id, target_id=enemy_unit.unit_id)`.

3) Same-name mirrored units engage independently
- Runtime IDs (`p1:...` vs `p2:...`) are used across movement/combat entry points.
- Regression tests in `tests/test_movement.py` cover same-name mirrored engagement.

4) Melee target scoping is opponent-only
- Reviewed `backend/engine/scenario.py::_resolve_melee_combat()`.
- Attacker owner is resolved first; enemy search is limited to opponent player's units.

## Re-check results

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_movement.py tests/test_scenario.py -q
# 13 passed

uv run python -m pytest tests/ -q
# 622 passed, 3 skipped, 60 warnings

uv run ruff check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py
# All checks passed

uv run ruff format --check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py
# 3 files already formatted

git diff --check -- backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py
# clean
```

## Notes

- Updated task verification counters in the task file to match current re-check outputs.
- No code changes were required in this review cycle.
