---
title: "CR-07 — Combat engine review"
status: request-changes
review_task: CR-07
date: 2026-05-09
source: ../../requirements/code-review/cr-07-combat-engine-review.md
---

# CR-07 — Combat engine review

## Verdict

REQUEST CHANGES / CORE COMBAT MATH FIXES REQUIRED

The combat engine has useful structure and a broad test suite, but the current attack-resolution math has several correctness blockers. The most severe: every natural 6 hit is treated as an auto-wound even without Lethal Hits; Devastating Wounds bypasses saves for every successful wound rather than only critical wounds; AP appears to be applied twice in the save path; and Sustained Hits does not add extra resolved hits/damage. These are core Warhammer 40,000 10e mechanics, so combat output cannot be trusted for balance or AI decisions until fixed.

## Scope inspected

- `backend/engine/combat.py`
- `backend/engine/dice.py`
- `backend/engine/modifiers.py`
- `backend/model/unit.py`
- `tests/test_combat.py`
- `tests/test_weapon_keywords_phase2.py`
- `tests/test_weapon.py`
- `tests/test_modifiers.py`
- `tests/test_line_of_sight.py`

## Verification commands

Initial attempted test command included stale filenames and failed before collection:

```text
uv run python -m pytest tests/test_combat.py tests/test_weapon_keywords_phase2.py tests/test_weapon.py tests/test_f2_8_cover_terrain.py -q
```

Corrected targeted command:

```text
uv run python -m pytest tests/test_combat.py tests/test_weapon_keywords_phase2.py tests/test_weapon.py tests/test_modifiers.py tests/test_line_of_sight.py -q
```

Result:

```text
58 passed in 12.19s
```

Additional smoke probes:

```text
AP1_MEAN 0.2752
NAT6_NO_LETHAL_MEAN 0.0277
DEV_WOUNDS_MEAN 2.9967
```

## Findings

### Critical: natural 6 hit auto-wounds even without Lethal Hits

Evidence:

- `backend/engine/combat.py:143` resolves hit roll.
- `backend/engine/combat.py:148-150` passes `hit_result.is_crit` as `auto_wound` into `_resolve_wound_chain`.
- There is no check that the weapon actually has `lethal_hits`.

Relevant flow:

```text
hit_result, _hit_modifiers = _resolve_hit_roll(...)
...
wound_result = _resolve_wound_chain(..., hit_result.is_crit)
```

Smoke probe:

```text
NAT6_NO_LETHAL_MEAN 0.0277
```

A BS6 S1 weapon into T10 Sv2 should need hit + wound + failed save. Current result is consistent with natural 6 hit skipping wound logic.

Required change:

- Natural 6 to hit should only auto-wound when Lethal Hits applies.
- `_resolve_hit_roll` should return critical metadata, but `_resolve_attack_chain` must call/use `handle_critical_hit(..., 'hit_roll', ...)` and only set `auto_wound=True` when `CriticalEffect.auto_wound` is true.
- Add deterministic tests:
  - natural 6 without lethal still rolls to wound;
  - natural 6 with lethal bypasses wound roll;
  - lethal + sustained both apply correctly.

### Critical: Devastating Wounds ignores saves on all wounds, not just critical wounds

Evidence:

- `backend/engine/modifiers.py:177-178` sets `result.ignore_save = True` whenever a `devastating_wounds` modifier is present on `wound_roll`.
- `backend/engine/combat.py:186-188` combines `wound_modifiers.ignore_save` with critical wound effect.
- This means any successful wound from a Devastating Wounds weapon bypasses saves.

Relevant flow:

```text
elif modifier.operation == "devastating_wounds":
    result.ignore_save = True
...
ignore_save = wound_modifiers.ignore_save or wound_critical.ignore_save
```

Smoke probe:

```text
DEV_WOUNDS_MEAN 2.9967
```

For a multi-shot AP0 weapon into Sv2, this is far too high if only critical wounds bypass saves.

Required change:

- Do not set `ignore_save` in generic `apply_modifiers` for Devastating Wounds.
- Only `handle_critical_hit(..., 'wound_roll', ...)` should set `ignore_save=True` when `wound_result.is_crit`.
- Add deterministic tests for normal successful wound vs critical wound with Devastating Wounds.

### Critical: AP is applied twice in save resolution

Evidence:

- `backend/model/unit.py:166-171` `best_save(ap)` already applies AP:

```text
modified_save = self.save - ap
```

- `backend/engine/combat.py:190-193` calls `defender.best_save(weapon.ap)`, then applies `save_target - weapon.ap` again:

```text
save_target = defender.best_save(weapon.ap)
...
save_target = max(1, min(6, save_target - weapon.ap))
```

Risk:

- AP-1 behaves like AP-2, AP-3 behaves like AP-6 after invulnerable handling edge cases.
- Combat output, roster balance and AI decisions are materially wrong.

Smoke probe:

```text
AP1_MEAN 0.2752
```

Required change:

- Use either `best_save(ap)` or raw `save` + AP, not both.
- Preserve invulnerable save semantics.
- Add deterministic save tests for AP0/AP-1/AP-3 with and without invulnerable saves.

### Important: Sustained Hits does not add extra resolved hits/damage

Evidence:

- `backend/engine/modifiers.py:170-171` records `extra_rolls`.
- `backend/engine/combat.py:242-249` rolls extra dice but only sets `success = True` on extra success.
- `_resolve_attack_chain` returns one wound/damage chain per attack, so extra hits are not resolved as additional wound/save/damage chains.

Risk:

- Sustained Hits weapons underperform and tests only check loose mean ranges, not exact effect.

Required change:

- Represent hit count, not boolean success, in the hit step.
- Resolve wound/save/damage for each generated hit.
- Add deterministic tests for Sustained Hits 1/2 with fixed natural 6 hit roll.

### Important: avg_damage_per_success is computed with wrong numerator

Evidence:

- `backend/engine/combat.py:401`:

```text
avg_damage_per_success=avg_hits / avg_attacks if avg_attacks > 0 else 0
```

This is hit rate, not damage per successful unsaved wound/attack.

Required change:

- Rename if intended as hit rate, or compute real damage-per-success from simulation data.

### Important: tests encode known-wrong expectations

Evidence:

- `tests/test_combat.py:344-347` comments say an overcharged plasma hand calculation should be ~0.11 but the test asserts 1.40-1.60 because the actual result is different.
- This hides the AP/save math bug rather than catching it.

Required change:

- Replace loose Monte Carlo expectations with deterministic or analytically bounded expectations after fixing mechanics.
- Add tests that fail on double AP and all-wounds Devastating behavior.

### Important: fallback default weapon can mask parser/content gaps

Evidence:

- `backend/engine/combat.py:434-450` creates a `Default Weapon` when a unit has no parsed weapons.
- CR-06 found 45 loaded units with no weapons.

Risk:

- Simulation silently invents a weapon profile instead of surfacing invalid/incomplete content.

Required change:

- Make fallback explicit and visible in result metadata, or reject simulation of weaponless units unless requirements say otherwise.

### Suggestion: performance is adequate for tests but combat loops are scalar Monte Carlo

Evidence:

- Targeted combat tests passed in 12.19s.
- `DicePool.simulate` runs Python function calls per iteration.

Recommendation:

- Fix correctness first.
- Later consider vectorized batch simulation for API responsiveness if combat calculator becomes user-facing at scale.

## Positive notes

- Dice pool is seedable and deterministic tests are possible.
- Modifier system is factored separately from combat orchestration.
- Existing tests cover many keywords at smoke level: Blast, Heavy, Torrent, Melta, Rapid Fire, Lance, One Shot, Precision, Pistol.
- Line-of-sight and modifier tests pass.

## Required follow-up before approval

1. Fix hit critical logic so natural 6 does not auto-wound unless Lethal Hits applies.
2. Fix Devastating Wounds to ignore saves only on critical wounds.
3. Fix save/AP application to avoid double AP.
4. Implement Sustained Hits as extra resolved hits, not boolean success.
5. Replace known-wrong loose expected-value tests with deterministic mechanics tests.
6. Decide whether default weapon fallback is allowed; if kept, expose it as a warning.

## Status update

CR-07 remains request-changes.
