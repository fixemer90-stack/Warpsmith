---
title: "Task 3.3 — Fix Sustained Hits resolution"
parent: remediation-plan
status: complete
phase: "3 — Combat math"
task_id: "3.3"
source: remediation-plan.md
---

# Task 3.3 — Fix Sustained Hits resolution

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [3.2 — Fix AP/save application and Devastating Wounds](task-03-02-fix-ap-save-application-and-devastating-wounds.md)
**Next:** [4.1 — Assert 5-phase 10e loop invariants](task-04-01-assert-5-phase-10e-loop-invariants.md)

## Phase context

**Phase:** 3 — Combat math
**Purpose:** fix core hit/wound/save/damage/FNP math before tuning gameplay or AI.
**Primary CRs:** CR-07, CR-11.
**Dependencies:** [3.2 — Fix AP/save application and Devastating Wounds](task-03-02-fix-ap-save-application-and-devastating-wounds.md)

## Objective

extra hits are resolved as real hit results, not dropped/no-op metadata.

## Acceptance criteria

- [x] Sustained Hits adds correct additional hits.
- [x] Downstream wound/save/damage counts include the extra hits.
- [x] Hit resolution output includes both original hits and Sustained Hits extra hits.
- [x] Downstream wound pool consumes the expanded hit count.
- [x] Combat trace/log, if present, distinguishes original hits from Sustained Hits extra hits.
- [x] Sustained Hits and Lethal Hits can coexist without dropping either effect.
- [x] Do not represent Sustained Hits only as metadata; the extra hits must become downstream-resolvable hit entries or counts.
- [x] Tests cover no Critical Hits producing no extra hits, one Critical Hit with Sustained Hits 1 producing two total hits, one Critical Hit with Sustained Hits 2 producing three total hits, extra hits rolling to wound normally, extra hits not being treated as auto-wounds from Lethal Hits, a mixed pool with normal hits/Critical Hits/misses, and Sustained Hits + Lethal Hits on the same natural 6 where the original Critical Hit can auto-wound via Lethal Hits while extra Sustained Hits roll to wound normally.

## Sustained Hits contract

- [x] Sustained Hits triggers only on Critical Hits.
- [x] Sustained Hits X adds X additional hit results for each triggering Critical Hit.
- [x] Additional hits are normal successful hits, not Critical Hits.
- [x] Additional hits continue into wound/save/damage resolution.
- [x] Additional hits do not recursively trigger Sustained Hits or other Critical Hit effects.

## Non-goals

- [x] Changing Lethal Hits semantics is not in scope.
- [x] Changing Devastating Wounds/AP/save behavior is not in scope.
- [x] Full combat log redesign is not in scope.

## Files likely touched

- `backend/engine/combat.py`
- `backend/engine/modifiers.py`
- `backend/engine/scenario.py`
- `tests/test_combat*.py`
- `tests/test_modifiers.py`

## Verification

- [x] `uv run python -m pytest tests/test_modifiers.py tests/test_combat*.py -q`

### Verification results (2026-05-17)

```
$ uv run python -m pytest tests/test_combat.py tests/test_modifiers.py -q
50 passed in 8.75s

$ uv run python -m pytest tests/ -q
578 passed, 3 skipped, 60 warnings in 55.90s

$ uv run ruff check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py
All checks passed!

$ uv run ruff format --check backend/engine/combat.py backend/engine/modifiers.py tests/test_combat.py tests/test_modifiers.py
4 files already formatted

$ git diff --check -- backend/engine/combat.py tests/test_modifiers.py
(clean)
```

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [x] `git diff --check` passes for touched files.
