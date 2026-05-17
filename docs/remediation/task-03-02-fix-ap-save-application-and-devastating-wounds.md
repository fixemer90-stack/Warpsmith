---
title: "Task 3.2 — Fix AP/save application and Devastating Wounds"
parent: remediation-plan
status: completed
phase: "3 — Combat math"
task_id: "3.2"
source: remediation-plan.md
---

# Task 3.2 — Fix AP/save application and Devastating Wounds

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [3.1 — Fix natural 6 / Lethal Hits semantics](task-03-01-fix-natural-6-lethal-hits-semantics.md)
**Next:** [3.3 — Fix Sustained Hits resolution](task-03-03-fix-sustained-hits-resolution.md)

## Phase context

**Phase:** 3 — Combat math
**Purpose:** fix core hit/wound/save/damage/FNP math before tuning gameplay or AI.
**Primary CRs:** CR-07, CR-11.
**Dependencies:** [3.1 — Fix natural 6 / Lethal Hits semantics](task-03-01-fix-natural-6-lethal-hits-semantics.md)

## Objective

AP and Devastating Wounds follow one consistent 10e-compatible path.

## Acceptance criteria

- [x] AP is applied exactly once regardless of terrain/modifier combinations.
- [x] Cover bonuses are not double-applied with save modifiers.
- [x] Cover/save modifiers are applied at the correct stage according to the canonical modifier pipeline.
- [x] Normal save path and Devastating Wounds path are separated and tested independently.
- [x] Combat logs/debug state clearly identify when Devastating Wounds triggered if combat logging exists.
- [x] Do not solve AP duplication by suppressing later save modifiers globally.
- [x] Tests cover AP modifying save exactly once, cover modifying save at the correct stage, AP and cover interaction producing expected effective save, normal wound using standard save path, Critical Wound without Devastating Wounds using standard save path, Critical Wound with Devastating Wounds bypassing normal save path, and Devastating Wounds damage reaching post-damage mitigation/FNP layers if implemented.

## Save/AP resolution contract

- AP modifies the defender save characteristic exactly once during save resolution.
- Cover and other save modifiers apply after AP according to the canonical modifier pipeline.
- Modified saves respect system caps/floor rules implemented by the engine.
- Save characteristic modification and save-roll modification are treated as separate stages if both exist.

## Devastating Wounds contract

- Devastating Wounds only triggers on Critical Wounds.
- Devastating Wounds converts damage from the triggering attack into mortal wounds according to current supported 10e semantics.
- Devastating Wounds bypasses normal armor saves once triggered.
- Feel No Pain and other post-damage defenses still apply if supported elsewhere by the engine.

## Non-goals

- Invulnerable save redesign is not in scope.
- Full terrain-system rewrite is not in scope.
- Damage spillover/allocation redesign is not in scope.

## Files likely touched

- `backend/engine/combat.py`
- `backend/engine/modifiers.py`
- `backend/engine/scenario.py`
- `tests/test_combat*.py`
- `tests/test_modifiers.py`

## Verification

- [x] `uv run python -m pytest tests/test_combat*.py tests/test_modifiers.py -q`

### Verification results (2026-05-17)

```
$ uv run python -m pytest tests/test_combat.py tests/test_modifiers.py -q
44 passed in 13.07s

$ uv run python -m pytest tests/ -q
571 passed, 3 skipped, 60 warnings in 67.00s

$ uv run python -m pytest tests/ -q  # re-review 2026-05-17 after DB hard_reset fix
578 passed, 3 skipped, 60 warnings in 100.31s

$ uv run ruff check backend/engine/combat.py backend/engine/modifiers.py backend/db/database.py tests/test_combat.py tests/test_modifiers.py tests/test_replay.py
All checks passed!

$ uv run ruff format --check backend/engine/combat.py backend/engine/modifiers.py backend/db/database.py tests/test_combat.py tests/test_modifiers.py tests/test_replay.py
6 files already formatted

$ git diff --check -- backend/engine/combat.py backend/engine/modifiers.py backend/db/database.py tests/test_combat.py tests/test_modifiers.py tests/test_replay.py
(clean)
```

## Code review — 2026-05-17

Review file: `docs/reviews/2026-05-17/task-03-02-fix-ap-save-application-and-devastating-wounds-review.md`

**Verdict: REQUEST CHANGES → FIXED 2026-05-17.**

Initial blocking findings:

| Finding | Evidence | Required fix |
|---------|----------|--------------|
| `ignores_cover` weapon modifier is still a no-op in the production save path | Deterministic probe with `tags=["ignores_cover"]`, `has_cover=True`, AP -1, save roll 3 returned `0` damage; expected `1` because cover should be cancelled. | Propagate `ignore_cover` modifier into save resolution and add a regression test for cover + AP + `ignores_cover`. |
| Claimed scoped verification command fails as written | `uv run python -m pytest tests/test_combat*.py tests/test_terrain*.py -q` exits 4: `ERROR: file or directory not found: tests/test_terrain*.py`. | Replace with existing scoped files or add the missing terrain test file, then rerun. |
| CR regression evidence incomplete | Primary CRs are CR-07 and CR-11; CR-11 has no Task 3.2 regression evidence section. | Add Task 3.2 evidence to CR-11 after the code fix and latest verification pass. |

Positive checks: direct AP double-application is removed, Lethal Hits + Devastating Wounds auto-wound still allows saves, and existing focused tests pass with `43 passed` for `tests/test_combat.py tests/test_modifiers.py`.

### Re-review — 2026-05-17

**Code blockers and full-suite blocker fixed; Task 3.2 can close.**

- `ignores_cover` deterministic probe now returns expected results:
  - `ignores_cover_tag_roll3_damage=1`
  - `normal_cover_roll3_damage=0`
  - `lethal_dev_save6_damage=0`
- Scoped task command passes: `uv run python -m pytest tests/test_combat*.py tests/test_modifiers.py -q` → `44 passed in 8.50s`.
- Full suite now passes after fixing the replay DB reset regression: `uv run python -m pytest tests/ -q` → `578 passed, 3 skipped, 60 warnings in 100.31s`.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact. *(N/A: Task 3.3 remains before Phase 3 checkpoint.)*
- [x] `git diff --check` passes for touched files.
