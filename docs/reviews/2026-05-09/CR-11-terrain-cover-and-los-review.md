---
title: "CR-11 — Terrain, cover and LoS review"
status: request-changes
reviewed_at: 2026-05-09T22:34:24+03:00
reviewer: Hermes Agent
scope: terrain-cover-los
source_task: ../../requirements/code-review/cr-11-terrain-cover-and-los-review.md
---

# CR-11 — Terrain, cover and LoS review

## Verdict

REQUEST CHANGES

Current implementation is closer to a partial F2.13 baseline than F2.18 full terrain, but even the F2.13 baseline has blocking integration/correctness defects:

- shooting-phase cover calls `_has_cover()` with shooter/target arguments reversed;
- `compute_save()` / attack resolution allows AP0 cover to improve a 3+ save to 2+, contrary to F2.18/10e restriction;
- grid LoS does not implement the F2.13 documented ruins/woods blocking behavior;
- BattlefieldMap LoS cache is stale after terrain changes;
- Ignores Cover / Indirect Fire helpers exist but are not actually integrated into scenario shooting.

F2.18 full terrain is not implemented yet. That is recorded as planned gap, not as a regression by itself.

## Scope reviewed

Requirements/specs:

- `docs/features/f2.13-cover-terrain.md`
- `docs/features/f2.18-terrain-mechanics-10e.md`
- `docs/requirements/code-review/cr-11-terrain-cover-and-los-review.md`

Production code:

- `backend/state/map.py`
- `backend/state/line_of_sight.py`
- `backend/state/game_state.py`
- `backend/engine/combat.py`
- `backend/engine/scenario.py`
- `backend/engine/ai/deployment.py`

Tests:

- `tests/test_map.py`
- `tests/test_line_of_sight.py`
- `tests/test_combat.py`
- `tests/test_modifiers.py`
- `tests/test_deployment_ai.py`

## What is implemented now

Implemented / partially implemented:

- `TerrainType` enum includes: `OPEN_GROUND`, `DIFFICULT_TERRAIN`, `DANGEROUS_TERRAIN`, `IMPASSABLE`, `RUINS`, `WOODS`, `CRATER`, `BARRICADE`.
- `GameState.terrain_map` stores a grid of `TerrainType`.
- `BattlefieldMap` stores grid terrain and supports `set_terrain()`, `get_terrain()`, movement cost, pathing and basic LoS.
- `LineOfSightCalculator` has a second Bresenham/ray-cast implementation.
- `backend.engine.combat._has_cover()` has a simple grid-based cover helper.
- `backend.engine.combat.compute_save()` and `apply_indirect_fire()` helpers exist.
- `Scenario._shooting_phase()` computes `has_cover` and passes it to `simulate_unit_attack()`.

Not implemented as F2.18 full terrain:

- no `TerrainCategory` model;
- no `TerrainFeature` footprint/elevation model;
- no `terrain_features` collection on `BattlefieldMap`;
- no `terrain_at()` / `line_intersects_feature()` / `has_10e_visibility()` / `has_benefit_of_cover()` APIs;
- no category-specific crater/barricade/debris/hill/woods/ruins rules;
- no Plunging Fire;
- no barricade-specific 2" engagement range;
- no terrain effect replay events;
- no UI/data-driven feature effects from terrain categories.

Because `docs/features/f2.18-terrain-mechanics-10e.md` is `status: pending`, these missing F2.18 pieces are tracked below as planned gaps, not as immediate regressions.

## Verification commands

Focused test suite:

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_map.py tests/test_line_of_sight.py tests/test_combat.py tests/test_modifiers.py -q
```

Result:

```text
52 passed in 11.96s
```

Custom terrain/cover probes:

```bash
python3 - <<'PY'
import numpy as np
from backend.state.map import BattlefieldMap, TerrainType
from backend.state.line_of_sight import LineOfSightCalculator
from backend.engine.combat import _has_cover, compute_save, apply_indirect_fire

bf = BattlefieldMap.create_empty(5, 1)
bf.set_terrain(2, 0, TerrainType.RUINS)
print('battlefield_has_los_through_ruins', bf.has_los(0,0,4,0))
los = LineOfSightCalculator(bf)
print('calculator_has_los_through_ruins', los.has_line_of_sight((0,0),(4,0)))

terrain = np.full((5,5), TerrainType.OPEN_GROUND, dtype=object)
terrain[3,3] = TerrainType.WOODS
print('cover_if_target_in_woods_correct_arg_order', _has_cover((3,3),(0,0),terrain,'Infantry'))
print('cover_if_target_in_woods_scenario_arg_order', _has_cover((0,0),(3,3),terrain,'Infantry'))

print('compute_save_sv3_ap0_with_cover_prob', compute_save(3, True, False))
print('compute_save_sv3_ap0_with_cover_ignores_prob', compute_save(3, True, True))
print('indirect_no_los_cover_hit_prob_from_4plus', apply_indirect_fire(3/6, False, True))
PY
```

Observed:

```text
battlefield_has_los_through_ruins True
calculator_has_los_through_ruins True
cover_if_target_in_woods_correct_arg_order True
cover_if_target_in_woods_scenario_arg_order False
compute_save_sv3_ap0_with_cover_prob 0.8333333333333334
compute_save_sv3_ap0_with_cover_ignores_prob 0.6666666666666666
indirect_no_los_cover_hit_prob_from_4plus 0.1666666666666667
```

LoS cache probe:

```bash
python3 - <<'PY'
from backend.state.map import BattlefieldMap, TerrainType
bf=BattlefieldMap.create_empty(5,1)
print('initial_los', bf.has_los(0,0,4,0))
bf.set_terrain(2,0,TerrainType.IMPASSABLE)
print('after_set_impassable_cached_los', bf.has_los(0,0,4,0))
bf.clear_los_cache()
print('after_clear_cache_los', bf.has_los(0,0,4,0))
PY
```

Observed:

```text
initial_los True
after_set_impassable_cached_los True
after_clear_cache_los False
```

F2.18 implementation search:

```bash
python3 - <<'PY'
from pathlib import Path
for p in Path('backend').rglob('*.py'):
    s=p.read_text(errors='ignore')
    for needle in ['TerrainFeature','TerrainCategory','Plunging','engagement_range_inches','has_10e_visibility','line_intersects_feature']:
        if needle in s:
            print(p, needle)
PY
```

Observed: no output.

## Findings

### CR-11-C1 — Shooting phase passes `_has_cover()` arguments reversed, so common cover is not applied

Severity: Critical

Files:

- `backend/engine/scenario.py:547-565`
- `backend/engine/combat.py:571-606`

Evidence:

`_has_cover()` signature is:

```python
def _has_cover(target_pos, shooter_pos, terrain_map, target_category) -> bool:
```

But scenario shooting calls it as:

```python
_has_cover(unit.position, target.position, terrain, target_cat)
```

Here `unit.position` is the shooter and `target.position` is the target, so the helper checks the shooter's tile as if it were the target tile.

Probe:

```text
cover_if_target_in_woods_correct_arg_order True
cover_if_target_in_woods_scenario_arg_order False
```

Impact:

A target standing in woods/ruins can receive no cover during actual shooting resolution. This breaks the F2.13 baseline integration even though the helper can return the correct value when called manually with the correct argument order.

Recommendation:

- Change scenario call to `_has_cover(target.position, unit.position, terrain, target_cat)`.
- Add a shooting-phase regression test where defender stands on woods/ruins and combat receives `has_cover=True`.

### CR-11-C2 — Cover can improve a 3+ save to 2+ against AP0

Severity: Critical

Files:

- `backend/engine/combat.py:188-194`
- `backend/engine/combat.py:609-624`
- `docs/features/f2.18-terrain-mechanics-10e.md:157-181`, acceptance item 11

Evidence:

Probe:

```text
compute_save_sv3_ap0_with_cover_prob 0.8333333333333334
compute_save_sv3_ap0_with_cover_ignores_prob 0.6666666666666666
```

A 3+ save has probability 4/6 = 0.6666. The observed 5/6 = 0.8333 means cover changed 3+ to 2+ at AP0.

This violates the F2.18/10e restriction:

> cover must not improve a 3+ or better save to 2+ against AP 0.

Impact:

Marine-equivalent and better saves become too durable in cover against AP0 weapons. This materially changes combat outcomes and will skew automated simulations.

Recommendation:

- Implement a single `apply_cover_to_save_target()` helper matching F2.18.
- Apply AP and cover exactly once.
- Add tests:
  - 4+ AP0 cover -> 3+;
  - 3+ AP0 cover -> remains 3+;
  - 2+ AP0 cover -> remains 2+;
  - 3+ AP-1 cover -> effective 3+.

### CR-11-C3 — F2.13-documented ruins/woods LoS blocking is not implemented

Severity: Critical

Files:

- `docs/features/f2.13-cover-terrain.md:23-33`
- `backend/state/map.py:264-314`
- `backend/state/line_of_sight.py:37-52`

Evidence:

F2.13 says ruins and woods block LoS in the simplified baseline:

```text
ruins: +1 SV for INFANTRY (Cover) + blocks LoS
woods: +1 SV for all (Cover) + blocks LoS
```

Code only treats `TerrainType.IMPASSABLE` as LoS-blocking.

Probe:

```text
battlefield_has_los_through_ruins True
calculator_has_los_through_ruins True
```

Impact:

Scenario shooting can target through ruins/woods even under the completed F2.13 baseline. This is distinct from F2.18's more nuanced future ruins/woods behavior: the current done spec says these terrain types block LoS, and the code does not.

Recommendation:

Choose and document one behavior for the current baseline:

- if keeping F2.13 simplified behavior, make `RUINS` and `WOODS` block LoS consistently in both LoS implementations;
- if intentionally moving toward F2.18 behavior, update F2.13 docs/status and add the actual F2.18 footprint model/tests before relying on it.

### CR-11-I1 — LoS cache is stale after `set_terrain()` changes the map

Severity: Important

Files:

- `backend/state/map.py:97-103`
- `backend/state/map.py:269-318`

Evidence:

`BattlefieldMap.has_los()` caches results. `set_terrain()` mutates terrain but does not call `clear_los_cache()`.

Probe:

```text
initial_los True
after_set_impassable_cached_los True
after_clear_cache_los False
```

Impact:

Any flow that computes LoS before map generation/editing is complete can keep stale visibility results. This is especially dangerous for future strategic map editing and any dynamic terrain/scenario setup.

Recommendation:

- Call `self.clear_los_cache()` inside `set_terrain()` after mutation.
- Add a regression test: clear LoS -> add blocker -> LoS must change without manual cache clearing.

### CR-11-I2 — Ignores Cover and Indirect Fire helpers are not integrated into scenario shooting

Severity: Important

Files:

- `backend/engine/combat.py:627-646`
- `backend/engine/scenario.py:558-566`
- `docs/features/f2.13-cover-terrain.md:153-167`

Evidence:

`Scenario._shooting_phase()` always passes:

```python
ignores_cover=False
```

There is no weapon tag/ability extraction for `Ignores Cover`, and `apply_indirect_fire()` is not called by scenario shooting.

Impact:

F2.13 mechanics exist as isolated helper code but are not actually enforced in the game loop. Weapons with Ignores Cover cannot cancel cover in autoplay/scenario shooting, and Indirect Fire behavior is not applied in target validation/hit probability.

Recommendation:

- Normalize weapon tags/abilities and map `ignores_cover` from the actual weapon being resolved.
- Integrate Indirect Fire into shooting target validation and hit modifiers.
- Add integration tests that go through `Scenario._shooting_phase()`, not only helper tests.

### CR-11-I3 — F2.18 full terrain model is absent; this is a planned gap, not a current regression

Severity: Important / Planned Work

Files:

- `docs/features/f2.18-terrain-mechanics-10e.md`
- `backend/state/map.py`
- `backend/state/line_of_sight.py`
- `backend/engine/combat.py`
- `backend/engine/scenario.py`

Evidence:

Search for F2.18 APIs/models returned no implementation:

```text
TerrainFeature: not found
TerrainCategory: not found
has_10e_visibility: not found
line_intersects_feature: not found
engagement_range_inches: not found
Plunging: not found
```

Gap list versus F2.18 acceptance:

- Terrain features with footprint/elevation: missing.
- Ruins footprint LoS: missing.
- Woods not-fully-visible/cover rule: missing.
- Crater infantry-only footprint cover: missing.
- Barricade infantry cover within 3": missing.
- Barricade 2" engagement: missing.
- Debris/hill cover: missing.
- Aircraft/towering exceptions: missing.
- Ignores Cover integration: missing.
- AP0 cover restriction: failing, see C2.
- Plunging Fire: missing.
- Terrain effect replay logs: missing.
- No-terrain backward compatibility: current tests cover some baseline behavior but not F2.18 no-op compatibility.

Impact:

The project should not mark F2.18 as implemented or assume 10e terrain accuracy. Since the feature spec is still `pending`, this should remain planned work until explicitly implemented and tested.

Recommendation:

Keep F2.18 pending and add a dedicated implementation task/test suite before any claim of 10e terrain support.

### CR-11-I4 — Tests pass but do not cover the failing terrain integration paths

Severity: Important

Files:

- `tests/test_map.py`
- `tests/test_line_of_sight.py`
- `tests/test_combat.py`
- `tests/test_modifiers.py`

Evidence:

Focused tests passed:

```text
52 passed in 11.96s
```

But the probes above expose failures that the suite does not assert:

- scenario call order into `_has_cover()`;
- AP0 3+ save restriction;
- ruins/woods LoS behavior under F2.13;
- LoS cache invalidation after `set_terrain()`;
- Scenario integration for Ignores Cover / Indirect Fire.

Impact:

The current test suite verifies helper behavior and basic map behavior, but not the end-to-end terrain rules used in actual simulations.

Recommendation:

Add `tests/test_cover_terrain.py` or `tests/test_terrain_mechanics_10e.py` with helper-level and scenario-level assertions.

## Security review

No direct security issue found in this scope. Terrain/LoS code does not process external credentials or execute user-provided code. Main risks are gameplay correctness and state integrity.

## Performance review

- Bresenham ray casting is acceptable for current small maps.
- `BattlefieldMap.has_los()` caching is reasonable, but cache invalidation is currently incorrect after terrain mutation.
- Future F2.18 footprint LoS may need careful caching keyed by terrain feature version/revision, not only coordinates.

## Architecture review

Architecture is currently split across multiple partially overlapping abstractions:

- `GameState.terrain_map` grid;
- `BattlefieldMap.terrain` grid;
- `BattlefieldMap.has_los()`;
- `LineOfSightCalculator.has_line_of_sight()`;
- `combat._has_cover()`;
- `deployment._has_cover_at()`.

This increases drift risk. F2.18 should centralize terrain feature rules behind a dedicated terrain/visibility API and keep scenario/combat/deployment as callers.

## Recommended remediation order

1. Fix scenario cover call order and add integration regression.
2. Fix AP0 cover restriction and avoid double-applying AP/save modifiers.
3. Decide current F2.13 LoS behavior for `RUINS`/`WOODS` and make both LoS implementations consistent.
4. Invalidate LoS cache in `set_terrain()`.
5. Integrate `Ignores Cover` and `Indirect Fire` through actual weapon tags/abilities in scenario shooting.
6. Keep F2.18 as explicit planned work; implement `TerrainFeature`/`TerrainCategory` only in a dedicated feature branch/task.

## Final status

- Verdict: REQUEST CHANGES
- Critical findings: 3
- Important findings: 4
- Suggestions: 0
- Production code changed: no
- Review artifact created: `docs/reviews/2026-05-09/CR-11-terrain-cover-and-los-review.md`
