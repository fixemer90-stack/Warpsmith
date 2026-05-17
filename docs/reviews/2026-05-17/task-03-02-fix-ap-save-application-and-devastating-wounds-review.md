# Task 3.2 — Fix AP/save application and Devastating Wounds — Review

Date: 2026-05-17
Task: `docs/remediation/task-03-02-fix-ap-save-application-and-devastating-wounds.md`
Verdict: REQUEST CHANGES

## Summary

The implementation fixes the direct AP double-application in `_resolve_wound_chain()` and improves Devastating Wounds handling so it only bypasses saves on Critical Wounds. However, Task 3.2 cannot be closed yet because one save-modifier path is still wrong, the task's claimed verification command is stale and fails, and required CR evidence is incomplete.

## Findings

### Important 1 — `ignores_cover` weapon modifier is still a no-op in the production save path

`backend/engine/modifiers.py` maps the weapon tag `ignores_cover` to `Modifier("save_roll", "ignore_cover")`, but `apply_modifiers()` never applies that operation to the `ModifierContext`, and `_resolve_wound_chain()` only checks `context.ignores_cover`.

Production consequence: callers that rely on weapon tags / `build_weapon_modifiers()` still give the defender cover even when the weapon has `ignores_cover`.

Deterministic probe:

```text
Weapon: AP-1 + ignores_cover
Defender: SV3+, has_cover=True
Rolls: hit 3, wound 4, save 3
Expected: 1 damage because Ignores Cover cancels cover, AP-1 makes save target 4+, save roll 3 fails.
Observed: 0 damage because cover was still applied, target became 3+, save roll 3 passed.
```

Observed command output:

```bash
$ uv run python - <<'PY'
from backend.engine.combat import _resolve_attack_chain
from backend.engine.modifiers import ModifierContext, build_weapon_modifiers
from backend.model.unit import Unit, Weapon

class SequenceRNG:
    def __init__(self, *values): self.values=list(values); self.idx=0
    def integers(self, low, high=None, size=None):
        import numpy as np
        val=self.values[min(self.idx, len(self.values)-1)]
        self.idx += 1
        if size is None: return val
        return np.full(size, val, dtype=int)

def unit(name='U'):
    return Unit(name=name, faction='x', category='Infantry', movement=6, toughness=4, save=3, wounds=2, leadership=6, objective_control=2, model_count=(1,1))

def weapon(tags=None, ap=0):
    return Weapon(name='W', type='ranged', range_max=24, attacks_dice=(0,0,1), skill=3, strength=4, ap=ap, damage_dice=(0,0,1), tags=tags or [])

w=weapon(['ignores_cover'], ap=-1)
a=unit('A'); d=unit('D')
ctx=ModifierContext(a,d,w,12,False,1,has_cover=True)
print(_resolve_attack_chain(SequenceRNG(3,4,3), w, d, build_weapon_modifiers(w), ctx))
PY
0
```

Required fix: make the `ignore_cover` modifier affect save resolution (for example by deriving an effective `ignores_cover` from modifiers during save resolution), and add a regression test where `tags=["ignores_cover"]`, `has_cover=True`, AP is present, and a borderline save roll fails only when cover is correctly ignored.

### Important 2 — The task's claimed scoped verification command fails as written

The task marks this command complete:

```bash
uv run python -m pytest tests/test_combat*.py tests/test_terrain*.py -q
```

But there is no `tests/test_terrain*.py` file, so pytest exits with code 4 before running tests.

Observed output:

```text
ERROR: file or directory not found: tests/test_terrain*.py
collected 0 items
no tests ran
```

Required fix: update the task's verification command to existing scoped test files and rerun it, or add the missing terrain test file if the original command is intentional. Do not mark the verification checkbox complete while the documented command fails.

### Important 3 — Required CR evidence is incomplete for the task's Primary CRs

Task 3.2 lists Primary CRs: CR-07 and CR-11. CR-07 contains a Task-03-01/3.2-related resolution note, but `docs/requirements/code-review/cr-11-terrain-cover-and-los-review.md` has no Task 3.2 regression evidence section.

Required fix: after code and verification pass, add Task 3.2 regression evidence to both affected CR artifacts, including the latest exact test results.

## Positive checks

The direct AP double-application fix is present in `backend/engine/combat.py`: `_resolve_wound_chain()` now uses `defender.best_save(weapon.ap)` without subtracting `weapon.ap` again.

The Lethal Hits + Devastating Wounds boundary still passes the deterministic regression:

```text
lethal_dev_save6_damage=0
```

The author's focused tests currently pass when using existing files:

```bash
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_combat.py tests/test_modifiers.py -q
43 passed in 10.24s
```

## Re-check commands run

```bash
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_combat*.py tests/test_terrain*.py -q
# exit 4 — ERROR: file or directory not found: tests/test_terrain*.py

$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_combat.py tests/test_modifiers.py -q
# 43 passed in 10.24s

$ uv run python - <<'PY'
# deterministic probe for Lethal Hits + Devastating Wounds and ignores_cover tag
PY
# lethal_dev_save6_damage= 0
# ignores_cover_tag_roll3_damage= 0
```

## Required before approval

- Fix `ignore_cover` modifier propagation in save resolution.
- Add a regression test for `tags=["ignores_cover"]` + `has_cover=True` + AP borderline save.
- Replace or satisfy the stale `tests/test_terrain*.py` verification command.
- Add Task 3.2 regression evidence to CR-11 as well as CR-07, with latest passing command output.
- Re-run scoped tests, full suite, ruff, format check, and `git diff --check` before marking complete again.

## Re-review — 2026-05-17

Verdict: REQUEST CHANGES after re-review.

The Task 3.2 combat implementation is now substantially fixed, but the task still cannot be closed because the latest full suite is red.

### Previous finding: `ignores_cover` weapon modifier no-op — Fixed

- `_resolve_wound_chain()` now derives `effective_ignores_cover` from either `context.ignores_cover` or a `save_roll`/`ignore_cover` modifier built from weapon tags.
- Added regression test `test_ignores_cover_tag_cancels_cover_bonus()` covering AP -1, cover, `tags=["ignores_cover"]`, and a borderline save roll.

Deterministic probe now passes:

```text
ignores_cover_tag_roll3_damage=1
normal_cover_roll3_damage=0
lethal_dev_save6_damage=0
```

### Previous finding: stale scoped verification command — Fixed

- Task verification now uses existing scoped test files: `tests/test_combat*.py tests/test_modifiers.py`.

```bash
$ rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_combat*.py tests/test_modifiers.py -q
44 passed in 8.50s
```

### Previous finding: missing CR-11 evidence — Fixed

- `docs/requirements/code-review/cr-11-terrain-cover-and-los-review.md` now has `Regression evidence — Task 3.2`.
- CR-07 also records Task 3.2 resolution, including AP, Devastating Wounds, and Ignores Cover notes.

### Remaining blocker: latest full suite fails

```bash
$ uv run python -m pytest tests/ -q
1 failed, 571 passed, 3 skipped, 59 warnings in 59.03s

FAILED tests/test_replay.py::test_db_init_preserves_existing_replay_rows
AttributeError: 'NoneType' object has no attribute 'executescript'
```

Focused combat implementation is approved from a Task 3.2 behavior standpoint, but project closure remains REQUEST CHANGES until the full-suite failure is resolved or explicitly accepted as unrelated baseline debt.
