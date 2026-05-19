---
title: "Task 5.1 — Fix charge destination and engagement identity"
parent: remediation-plan
status: completed
phase: "5 — Movement / charge / melee identity"
task_id: "5.1"
source: remediation-plan.md
---

# Task 5.1 — Fix charge destination and engagement identity

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [4.3 — Lock VP, objectives, mission normalization, Battle Ready](task-04-03-lock-vp-objectives-mission-normalization-battle-ready.md)
**Next:** [5.2 — Fix melee target selection and damage logging](task-05-02-fix-melee-target-selection-and-damage-logging.md)

## Phase context

**Phase:** 5 — Movement / charge / melee identity
**Purpose:** make movement, charge, engagement, melee damage, and unit identity coherent before replay/result and AI.
**Primary CRs:** CR-09, CR-11, CR-14, CR-15.
**Dependencies:** Phase 4 checkpoint

## Objective

charge moves to adjacent legal cell and marks scoped units as engaged.

## Acceptance criteria

- [x] Charge never attempts to occupy enemy cell.
- [x] Engagement uses runtime ids, not names.
- [x] Same-name mirrored units can engage independently.

## Resolution

### AC 1 — charge destination

`_charge_phase()` charge destination logic replaced. Instead of the old left/right-only heuristic that could land on the enemy cell when X coords matched, the new code:
- Enumerates all 8 adjacent cells around the target
- Filters to map bounds
- Sorts by distance from charger
- Picks the first unoccupied cell
- If no adjacent cell is free, logs a failure and moves on

### AC 2 — engagement uses runtime IDs

`_resolve_melee_combat()` now correctly scopes to opponent units only. Previously scanned ALL players' units, which could target friendly units. Now identifies the attacker's own player, finds the opponent, and only checks opponent units for adjacency.

Charge and fight log entries already used `format_event_identity(actor_id=..., target_id=...)` which carries runtime unit IDs. This pattern was verified consistent.

### AC 3 — same-name mirrored units

Runtime unit IDs (e.g. `p1:Boyz:0` vs `p2:Boyz:0`) are already the authoritative keys in `PlayerState.units`, `move_unit()`, `deal_damage()`, and all log identity tags. Same-name units on opposite sides are distinguished by their player-prefixed runtime ID. Added regression tests confirming independent engagement.

## Files likely touched

- `backend/engine/scenario.py` — charge destination, melee target scoping
- `tests/test_movement.py` — new regression tests (6 tests)
- `tests/test_scenario.py` — existing tests unchanged, still pass

## Verification

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_movement.py tests/test_scenario.py -q` → 13 passed.
- [x] `uv run python -m pytest tests/ -q` → 622 passed, 3 skipped, 60 warnings.
- [x] `uv run ruff check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py` → All checks passed.
- [x] `uv run ruff format --check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py` → 3 files already formatted.
- [x] `git diff --check -- backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py` → clean.

## Code review — 2026-05-19

Review file: `docs/reviews/2026-05-19/task-05-01-fix-charge-destination-and-engagement-identity-check.md`

**Verdict: APPROVED 2026-05-19.**

- Charge destination logic in `_charge_phase()` enumerates all 8 adjacent cells, filters map bounds, and only picks an unoccupied cell.
- Melee target selection in `_resolve_melee_combat()` is scoped to opponent units only.
- Runtime ID identity logging is present for charge and melee events via `format_event_identity(actor_id=..., target_id=...)`.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] Phase checkpoint N/A — Task 5.2 remains before Phase 5 checkpoint.
- [x] `git diff --check` passes for touched files.
