---
title: "CR-09 — Movement, charge and melee review"
status: request-changes
review_task: CR-09
date: 2026-05-09
source: ../../requirements/code-review/cr-09-movement-charge-and-melee-review.md
---

# CR-09 — Movement, charge and melee review

## Verdict

REQUEST CHANGES / CHARGE AND MELEE STATE ARE STILL NOT RELIABLE

The current implementation contains the intended fixes for some earlier regressions — `_is_valid_move()` blocks occupied cells, charge attempts no longer intentionally move onto an enemy cell on the common horizontal case, melee resolution checks adjacency instead of exact-position equality, and melee damage log lines use the summary-compatible `"hits ... for ... damage"` format. However, targeted probes show melee-focused rosters can still fail or produce invalid combat:

- A valid vertical charge can silently fail because `_charge_phase()` computes the target's occupied cell when attacker and target have the same x-coordinate.
- Charge movement only tries one adjacent cell and has no fallback if that cell is occupied, terrain-blocked, or clamped into an invalid square.
- Melee target resolution can select and damage friendly units because it searches all players and only excludes `unit != attacking_unit`.
- Successful charge marks only the charger engaged; the charged target is not eligible for an independent Fight phase activation.
- Mirror/same-name rosters are unsafe because movement/damage APIs identify units only by `unit_id`; auto-play creates both players' unit IDs from unit names, so duplicate unit names across players mutate the first matching player unit.
- Existing tests pass because they assert mostly "does not crash" and do not assert successful charge, legal engagement symmetry, enemy-only melee target selection, or replay/result charge counters.

## Scope reviewed

- `backend/engine/scenario.py`
- `backend/state/game_state.py`
- `backend/engine/ai/autoplay.py`
- `tests/test_scenario.py`
- `tests/test_game_state.py`
- `tests/test_phase_transitions.py`
- `tests/test_autoplay.py`
- CR-08 carry-forward finding: asymmetric charge engagement state
- Warpsmith project references/skill context for movement/charge/melee, result summary parsing, and full-code-review execution

## Automated checks run

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_scenario.py tests/test_game_state.py tests/test_phase_transitions.py tests/test_autoplay.py -q
```

Result:

```text
31 passed in 6.19s
```

Targeted probes:

```text
VERTICAL_CHARGE_POS (3, 6) CHARGER_ENGAGED False TARGET_ENGAGED False
VERTICAL_CHARGE_LOGS ['Charge phase: units may charge']

HORIZONTAL_CHARGE_POS (4, 3) CHARGER_ENGAGED True TARGET_ENGAGED False
HORIZONTAL_CHARGE_LOGS ['Charge phase: units may charge', 'Charger moved to (4, 3)', 'Charger charges Target (rolled 12 ≥ 3) — engaged!']

BLOCKED_ADJ_CHARGE_POS (6, 3) CHARGER_ENGAGED False BLOCKER_POS (4, 3)
BLOCKED_ADJ_LOGS ['Charge phase: units may charge']

ASYM_FIGHT_WOUNDS {'charger': 9, 'target': 9} TARGET_ENGAGED_AFTER False
ASYM_FIGHT_LOGS ['Charger hits Target for 1 damage', 'Target hits Charger for 1 damage', 'Charger fought in melee']

WOUNDS {'a': 4, 'friend': 4, 'enemy': 5}
LOGS ['Friendly took 1 damage', 'Attacker hits Friendly for 1 damage', 'Attacker took 1 damage', 'Friendly hits Attacker for 1 damage']

ERROR None
ROUNDS 2
CHARGE_LINES 0
FAIL_CHARGE_LINES 4
MELEE_DAMAGE_LINES 6
MOVED_LINES 6
SUMMARY {'winner': 1, 'total_kills': {'1': 2}, 'total_damage': {'2': 6.0}, 'charge_count': {}, 'rounds_played': 2, 'armies': {'1': {'name': 'orks melee roster', 'faction': 'orks'}, '2': {'name': 'orks melee roster', 'faction': 'orks'}}}
```

## Findings

### Critical — Valid vertical charges silently fail by trying to move onto the occupied target cell

Location:

- `backend/engine/scenario.py:604-630`
- `backend/state/game_state.py:169-194`

Current charge-position logic chooses the adjacent x-side only when the target x-coordinate differs from the charger x-coordinate:

```python
charge_pos = (
    closest.position[0] - 1
    if closest.position[0] > unit.position[0]
    else closest.position[0] + 1
    if closest.position[0] < unit.position[0]
    else closest.position[0],
    closest.position[1],
)
```

When attacker and target are vertically aligned (`same x`, different y), this computes `(target.x, target.y)`, i.e. the occupied target cell. `GameState.move_unit()` correctly rejects occupied cells, so the charge fails even with a guaranteed 12 on 2D6. No failure message is logged because the failed `move_unit()` branch is empty.

Verified:

```text
VERTICAL_CHARGE_POS (3, 6) CHARGER_ENGAGED False TARGET_ENGAGED False
VERTICAL_CHARGE_LOGS ['Charge phase: units may charge']
```

Recommendation:

- Generate candidate charge destinations around the target using all legal adjacent squares, not one hardcoded horizontal square.
- Prefer a legal square that is within the charge distance and closest to the attacker's current line of approach.
- Reject occupied/impassable/out-of-bounds candidates before calling `move_unit()`.
- Log an explicit failed-charge reason if the dice roll succeeds but no legal engagement position exists.
- Add regression tests for horizontal, vertical, diagonal, edge-of-map, and occupied-adjacent-cell charge attempts.

### Critical — Melee combat can target and damage friendly units

Location:

- `backend/engine/scenario.py:690-730`

`_resolve_melee_combat()` loops through every player and every unit and only excludes the attacking unit itself:

```python
for player in self.state.players.values():
    for unit in player.units.values():
        if unit.is_alive and unit != attacking_unit and adjacent:
            enemy_unit = unit
```

It does not identify the attacker's owning player and does not restrict candidates to opponent units. If a friendly unit is adjacent and appears first in dict iteration, the attacker hits the friendly model and the friendly model deals counter-damage.

Verified:

```text
WOUNDS {'a': 4, 'friend': 4, 'enemy': 5}
LOGS ['Friendly took 1 damage', 'Attacker hits Friendly for 1 damage', 'Attacker took 1 damage', 'Friendly hits Attacker for 1 damage']
```

Recommendation:

- Resolve the attacker's owner first.
- Search only opposing players' living units for melee targets.
- If multiple enemy units are adjacent, apply deterministic target selection (closest, lowest wounds, or explicit charge target stored on the charger).
- Add a regression test with an adjacent friendly and adjacent enemy; only the enemy may take melee damage.

### Critical — Duplicate unit IDs across players corrupt movement/damage in mirror or same-name rosters

Location:

- `backend/engine/ai/autoplay.py:183-196`
- `backend/engine/ai/autoplay.py:206-213`
- `backend/state/game_state.py:169-180`
- `backend/state/game_state.py:196-211`

Auto-play builds `UnitState.unit_id` from `unit_name`, and both players can legally have the same unit names, especially mirror matches or generated rosters. `GameState.move_unit()` and `GameState.deal_damage()` then search players in insertion order and mutate the first matching `unit_id`.

The existing `test_ork_vs_ork()` only checks `result.error is None`, so it misses that movement and damage can apply to the wrong player's unit and logs become ambiguous (`orks melee 0 hits orks melee 0`).

Verified in an Orks-vs-Orks melee smoke:

```text
ERROR None
CHARGE_LINES 0
MELEE_DAMAGE_LINES 6
SUMMARY {'total_kills': {'1': 2}, 'total_damage': {'2': 6.0}, ...}
SAMPLE_RELEVANT included same-name/self-looking melee lines.
```

Recommendation:

- Make `UnitState.unit_id` globally unique in auto-play, e.g. prefix with player id: `p1::<unit_name>` / `p2::<unit_name>`.
- Keep display `name` separate from identity.
- Store `unit_models` by the same globally unique unit_id.
- Update summary ownership parsing to use stable ids where possible instead of name-only lookup.
- Add mirror-match regression tests that assert player 2 movement/damage never mutates player 1 units with the same display name.

### Important — Charge engagement state is asymmetric

Location:

- `backend/engine/scenario.py:626-630`
- `backend/engine/scenario.py:637-689`

On successful charge, only the charger is marked engaged:

```python
if self.state.move_unit(unit.unit_id, charge_pos):
    unit.is_engaged = True
```

The target remains `is_engaged=False`. Current `_resolve_melee_combat()` applies immediate counter-damage, but `_fight_phase()` determines independent activation eligibility from `unit.is_engaged`; therefore a charged target is not eligible for its own activation later in the phase.

Verified:

```text
HORIZONTAL_CHARGE_POS (4, 3) CHARGER_ENGAGED True TARGET_ENGAGED False
ASYM_FIGHT_WOUNDS {'charger': 9, 'target': 9} TARGET_ENGAGED_AFTER False
ASYM_FIGHT_LOGS ['Charger hits Target for 1 damage', 'Target hits Charger for 1 damage', 'Charger fought in melee']
```

Recommendation:

- Mark both charger and charged target engaged on successful charge.
- Store the charge target/engagement pair so Fight phase can resolve legal enemy targets deterministically.
- Use `has_fought` or a clear phase-local fought set; do not overload `is_fighting` as the fought marker.
- Add a regression test that a charged target is eligible to activate if alive and has not fought.

### Important — Charge pathing only tries one adjacent square and silently consumes the charge on placement failure

Location:

- `backend/engine/scenario.py:611-635`

Even when the dice roll succeeds, the implementation tries exactly one destination. If that square is occupied, impassable, out of bounds, or clamped into the target cell, the unit does not move, does not engage, and still receives `has_charged=True`. No log line explains the failed placement.

Verified:

```text
BLOCKED_ADJ_CHARGE_POS (6, 3) CHARGER_ENGAGED False BLOCKER_POS (4, 3)
BLOCKED_ADJ_LOGS ['Charge phase: units may charge']
```

Recommendation:

- Treat successful roll and legal placement as separate checks in logs.
- Try all adjacent engagement candidates before failing the charge.
- Only set `has_charged=True` after the charge attempt is fully resolved and recorded; failed attempts may still count as attempted, but the log must say why.

### Important — Existing tests do not assert movement/charge/melee correctness

Location:

- `tests/test_scenario.py:18-58`
- `tests/test_phase_transitions.py:54-114`
- `tests/test_autoplay.py:88-239`

The targeted test command passes, but coverage is too weak for this CR's acceptance criteria:

- `test_run_round()` only checks round/phase advancement.
- `test_fight_phase_alternating_activations()` places both units on the same coordinate, which normal movement forbids, and only asserts some damage occurred.
- `test_melee_only_unit()` only asserts auto-play has no error; it does not assert any successful charge, legal melee target, engagement symmetry, or summary `charge_count`.
- `test_ork_vs_ork()` does not catch duplicate unit IDs or same-name log/ownership corruption.

Recommendation:

- Add deterministic unit tests around `_charge_phase()` and `_resolve_melee_combat()` using patched dice.
- Add an auto-play smoke for melee-only Orks vs a ranged opponent that asserts at least one successful charge and at least one melee damage line when deployment/distance makes that expected.
- Add a mirror-roster identity test.

## Positive notes

- `GameState._is_valid_move()` correctly rejects occupied cells, so the original "move directly onto enemy" bug is not hidden by permissive movement validation.
- Horizontal charge into a free adjacent cell can succeed.
- Melee resolution now checks adjacency rather than exact same position, which is the right direction for grid-based engagement.
- Melee damage log lines use the parser-compatible `"hits ... for ... damage"` format.
- The targeted legacy tests pass; the problem is missing assertions, not a crashing baseline.

## Required fixes before closing CR-09

1. Replace one-cell charge placement with a candidate search over legal adjacent target squares.
2. Log and test the dice-success/no-legal-placement case.
3. Mark both charger and target engaged on successful charge.
4. Restrict melee target selection to enemy units only and make target selection deterministic.
5. Make auto-play unit IDs globally unique across players and keep names display-only.
6. Add targeted deterministic charge/melee tests and meaningful melee auto-play smoke assertions.
