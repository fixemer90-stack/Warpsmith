# Code review — Task 5.3 — Fix terrain/LoS movement-related blockers

Date: 2026-05-19
Verdict: REQUEST CHANGES

## Scope reviewed

- Task artifact: `docs/remediation/task-05-03-fix-terrain-los-movement-related-blockers.md`
- Implementation: `backend/state/map.py`, `backend/engine/combat.py`, `backend/engine/scenario.py`
- Tests: `tests/test_terrain.py`, `tests/test_scenario.py`
- Closure artifacts: `docs/remediation/remediation-plan.md`, `docs/remediation/index.md`, CR-09/11/14/15 evidence surfaces

## Behavioral review

Approved behavior:

- `BattlefieldMap.set_terrain()` updates the terrain cell and calls `clear_los_cache()`.
- The scenario shooting path calls `_has_cover(target.position, unit.position, terrain, target_cat)`, i.e. defender/target first and shooter second.
- Runtime save resolution and `compute_save()` use the pre-cover save value for the AP0 cover cap, so SV3+ with AP0 cover stays 3+, SV2+ is not degraded, and SV4+ can improve to 3+.
- Regression coverage exists for cache invalidation, cover argument order, AP0 cap behavior, SV2+ non-degradation, non-AP0 cover, and Ignores Cover.

No production-code blocker was found for the three Task 5.3 acceptance criteria.

## Findings

### Important — Phase 5 checkpoint claim is invalid while Task 5.2 is reopened

Task 5.3 claimed Phase 5 completion, but Task 5.2 is currently `changes_requested` with parser/attribution/diff-check blockers. A later task that claims the phase checkpoint must not remain `completed` solely on a stale phase-complete claim while an earlier dependency in the same phase is open.

Required state until Task 5.2 is fixed:

- Task 5.3 frontmatter: `status: changes_requested`.
- Task 5.3 behavioral AC may stay checked.
- Task 5.3 phase-checkpoint completion requirement must be unchecked with a request-changes annotation.
- Phase 5 source/index surfaces must not present Task 5.3 as completing Phase 5.

### Important — Verification count was stale

The task recorded the full suite as `622 passed, 3 skipped`; the current re-check observed `626 passed, 3 skipped, 60 warnings`. Stale verification numbers are a closure metadata defect even when code behavior is correct.

## Re-check results

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_terrain.py tests/test_scenario.py -q
# 13 passed in 0.49s

uv run python -m pytest tests/ -q
# 626 passed, 3 skipped, 60 warnings in 50.82s

uv run ruff check backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_terrain.py
# All checks passed!

uv run ruff format --check backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_terrain.py
# 4 files already formatted

git diff --check -- backend/state/map.py backend/engine/combat.py backend/engine/scenario.py tests/test_terrain.py
# clean
```

## Resolution applied during review

- Updated Task 5.3 verification count from 622 to 626 passed.
- Downgraded Task 5.3 status to `changes_requested` because the Phase 5 checkpoint claim is dependency-gated by Task 5.2.
- Unchecked the Task 5.3 phase-checkpoint completion requirement and added the request-changes reason.
- Updated the source plan and index so Phase 5 does not appear closed through Task 5.3 while Task 5.2 is open.
- Added superseding CR evidence to CR-09/11/14/15.
