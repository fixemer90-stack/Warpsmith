---
title: "Task 5.3 — Fix terrain/LoS movement-related blockers"
parent: remediation-plan
status: changes_requested
phase: "5 — Movement / charge / melee identity"
task_id: "5.3"
source: remediation-plan.md
---

# Task 5.3 — Fix terrain/LoS movement-related blockers

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [5.2 — Fix melee target selection and damage logging](task-05-02-fix-melee-target-selection-and-damage-logging.md)
**Next:** [6.1 — Persist authoritative final snapshot](task-06-01-persist-authoritative-final-snapshot.md)

## Phase context

**Phase:** 5 — Movement / charge / melee identity
**Purpose:** make movement, charge, engagement, melee damage, and unit identity coherent before replay/result and AI.
**Primary CRs:** CR-09, CR-11, CR-14, CR-15.
**Dependencies:** [5.2 — Fix melee target selection and damage logging](task-05-02-fix-melee-target-selection-and-damage-logging.md)

## Objective

terrain/LoS cache and cover integration do not corrupt movement/shooting assumptions.

## Acceptance criteria

- [x] `set_terrain()` invalidates LoS cache.
- [x] Cover helper argument order is correct.
- [x] AP0 cover cap is enforced.

## Resolution

### AC 1 — `set_terrain()` invalidates LoS cache

`BattlefieldMap.set_terrain()` now calls `self.clear_los_cache()` after modifying the terrain array. This ensures cached LoS results are invalidated when terrain changes, preventing stale LoS responses.

### AC 2 — cover helper argument order

`_has_cover(target_pos, shooter_pos, terrain_map, target_category)` was called with swapped arguments in `scenario.py`'s shooting phase. Fixed: `_has_cover(target.position, unit.position, terrain, target_cat)` — target (defender) position first, shooter (attacker) position second.

### AC 3 — AP0 cover cap

In both `_resolve_wound_chain` and `compute_save`: when AP=0, cover cannot improve the save beyond 3+. SV2+ already beats the cap so it's unaffected. SV3+ with cover vs AP0 stays at 3+. SV4+ with cover vs AP0 becomes 3+. The cap only restricts saves originally 3+ or worse from being improved to 2+.

## Files likely touched

- `backend/state/map.py` — `set_terrain()` → `clear_los_cache()`
- `backend/engine/combat.py` — AP0 cover cap, `compute_save` arg
- `backend/engine/scenario.py` — cover arg order fix
- `tests/test_terrain.py` — 9 new regression tests

## Verification

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_terrain.py tests/test_scenario.py -q` → 13 passed.
- [x] `uv run python -m pytest tests/ -q` → 626 passed, 3 skipped, 60 warnings.
- [x] `uv run ruff check backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_terrain.py` → All checks passed.
- [x] `uv run ruff format --check backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_terrain.py` → 4 files already formatted.
- [x] `git diff --check -- backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_terrain.py` → clean.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [ ] Phase checkpoint synced — Task 5.3 completes Phase 5. *(Request changes 2026-05-19: Task 5.2 is reopened, so Phase 5 is not closed; source plan/index/CR checkpoint claims must not say complete yet.)*
- [x] `git diff --check` passes for touched files.

## Code review — 2026-05-19

Review file: `../reviews/2026-05-19/task-05-03-fix-terrain-los-movement-related-blockers-review.md`

**Verdict: REQUEST CHANGES.**

Behavioral AC pass, but closure metadata is stale/dependency-gated:

| Finding | Severity | Evidence | Required fix |
| --- | --- | --- | --- |
| Phase 5 checkpoint claim is invalid while Task 5.2 is reopened | Important | Task 5.2 is `changes_requested` with parser/attribution/diff-check blockers; Task 5.3 completion requirement claimed it completed Phase 5. | Keep Task 5.3 in `changes_requested` until Task 5.2 is fixed and the Phase 5 checkpoint can be synced. |
| Verification count was stale | Important | Current full suite is 626 passed, 3 skipped, 60 warnings; task recorded 622 passed. | Updated this task verification to the current run. |

Re-check results: scoped 13 passed; full 626 passed, 3 skipped; Ruff/format/diff-check clean for Task 5.3 touched files.
