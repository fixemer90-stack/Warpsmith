---
title: "Task 3.2 — Fix AP/save application and Devastating Wounds"
parent: remediation-plan
status: pending
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

- [ ] AP is applied exactly once regardless of terrain/modifier combinations.
- [ ] Cover bonuses are not double-applied with save modifiers.
- [ ] Cover/save modifiers are applied at the correct stage according to the canonical modifier pipeline.
- [ ] Normal save path and Devastating Wounds path are separated and tested independently.
- [ ] Combat logs/debug state clearly identify when Devastating Wounds triggered if combat logging exists.
- [ ] Do not solve AP duplication by suppressing later save modifiers globally.
- [ ] Tests cover AP modifying save exactly once, cover modifying save at the correct stage, AP and cover interaction producing expected effective save, normal wound using standard save path, Critical Wound without Devastating Wounds using standard save path, Critical Wound with Devastating Wounds bypassing normal save path, and Devastating Wounds damage reaching post-damage mitigation/FNP layers if implemented.

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

- [ ] `uv run python -m pytest tests/test_combat*.py tests/test_terrain*.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
