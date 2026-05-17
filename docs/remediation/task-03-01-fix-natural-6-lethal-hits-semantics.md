---
title: "Task 3.1 — Fix natural 6 / Lethal Hits semantics"
parent: remediation-plan
status: pending
phase: "3 — Combat math"
task_id: "3.1"
source: remediation-plan.md
---

# Task 3.1 — Fix natural 6 / Lethal Hits semantics

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [2.3 — Enforce plan/feature gates consistently](task-02-03-enforce-plan-feature-gates-consistently.md)
**Next:** [3.2 — Fix AP/save application and Devastating Wounds](task-03-02-fix-ap-save-application-and-devastating-wounds.md)

## Phase context

**Phase:** 3 — Combat math
**Purpose:** fix core hit/wound/save/damage/FNP math before tuning gameplay or AI.
**Primary CRs:** CR-07, CR-11.
**Dependencies:** Phase 1 checkpoint

## Objective

natural 6 auto-wounds only when Lethal Hits applies.

## Acceptance criteria

- [ ] Plain natural 6 to hit does not auto-wound.
- [ ] Lethal Hits natural 6 does auto-wound.
- [ ] Critical Hit detection is separate from Lethal Hits resolution.
- [ ] Plain Critical Hits do not increment wound count unless another rule explicitly says so.
- [ ] Lethal Hits applies per attack/weapon/profile, not globally to the attacker unless sourced that way.
- [ ] Automatic wounds from Lethal Hits bypass the wound roll but still proceed to save/damage steps normally.
- [ ] Do not implement this as “natural 6 always auto-wounds”; Lethal Hits must be an explicit active rule on the attack.
- [ ] Tests cover plain hit roll of natural 6 still requiring a wound roll, failed wound roll after plain natural 6 producing no wound, Lethal Hits natural 6 skipping wound roll and creating one wound, non-6 successful hit with Lethal Hits rolling to wound normally, and a mixed attack pool with one natural 6 and one normal hit resolving correctly.

## Combat semantics contract

- A natural 6 to Hit is still only a successful Hit unless the attack has Lethal Hits.
- Only attacks with active Lethal Hits convert Critical Hits into automatic wounds.
- Automatic wounds from Lethal Hits bypass the wound roll but still proceed to save/damage steps normally.

## Non-goals

- Devastating Wounds changes are not in scope.
- AP/save behavior changes are not in scope.
- Feel No Pain changes are not in scope.
- Sustained Hits changes are not in scope.
- Wound allocation changes are not in scope.

## Files likely touched

- `backend/engine/combat.py`
- `backend/engine/modifiers.py`
- `backend/engine/scenario.py`
- `tests/test_combat*.py`
- `tests/test_modifiers.py`

## Verification

- [ ] `uv run python -m pytest tests/test_combat*.py tests/test_modifiers.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
