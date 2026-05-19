---
title: "Task 5.2 — Fix melee target selection and damage logging"
parent: remediation-plan
status: completed
phase: "5 — Movement / charge / melee identity"
task_id: "5.2"
source: remediation-plan.md
---

# Task 5.2 — Fix melee target selection and damage logging

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [5.1 — Fix charge destination and engagement identity](task-05-01-fix-charge-destination-and-engagement-identity.md)
**Next:** [5.3 — Fix terrain/LoS movement-related blockers](task-05-03-fix-terrain-los-movement-related-blockers.md)

## Phase context

**Phase:** 5 — Movement / charge / melee identity
**Purpose:** make movement, charge, engagement, melee damage, and unit identity coherent before replay/result and AI.
**Primary CRs:** CR-09, CR-11, CR-14, CR-15.
**Dependencies:** [5.1 — Fix charge destination and engagement identity](task-05-01-fix-charge-destination-and-engagement-identity.md)

## Objective

melee resolves adjacent targets and logs parsable damage with actor/target identity.

## Acceptance criteria

- [x] Adjacent melee attacks resolve.
- [x] Damage log/event uses `hits ... for ... damage` or structured equivalent.
- [x] Summary attribution is not name-based.

## Resolution

### AC 1 — adjacent melee resolves

`_resolve_melee_combat()` now uses the combat engine via `simulate_unit_attack()` with melee weapons from the unit model. Falls back to simplified `max(1, models//2)` damage when no model or no melee weapons are available. Counter-attack (enemy strikes back) also uses the combat engine when models are available.

### AC 2 — damage log format

Melee logs use `"{name} hits {name} for {damage} damage in melee{identity}"` — consistent with the shooting damage pattern. The `identity` suffix carries runtime unit IDs.

### AC 3 — attribution not name-based

All melee log entries include `format_event_identity(actor_id=..., target_id=...)` tags with authoritative runtime unit IDs (`p1:Boyz:0`, `p2:Boyz:0`). Same-name units on opposite sides are disambiguated by their player-prefixed runtime IDs.

## Files likely touched

- `backend/engine/scenario.py` — `_resolve_melee_combat()` rewritten to use combat engine
- `tests/test_movement.py` — 3 new melee regression tests

## Verification

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_scenario.py tests/test_result_screen.py tests/test_movement.py -q` → 19 passed.
- [x] `uv run python -m pytest tests/ -q` → 613 passed, 3 skipped, 60 warnings.
- [x] `uv run ruff check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py` → All checks passed.
- [x] `uv run ruff format --check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py` → 4 files already formatted.
- [x] `git diff --check -- backend/engine/scenario.py tests/test_movement.py` → clean.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] Phase checkpoint N/A — Task 5.3 remains before Phase 5 checkpoint.
- [x] `git diff --check` passes for touched files.
