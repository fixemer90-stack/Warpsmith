---
title: "Task 5.3 — Fix terrain/LoS movement-related blockers"
parent: remediation-plan
status: pending
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

- [ ] `set_terrain()` invalidates LoS cache.
- [ ] Cover helper argument order is correct.
- [ ] AP0 cover cap is enforced.

## Files likely touched

- `backend/engine/scenario.py`
- `backend/state/game_state.py`
- `backend/state/map.py`
- `backend/engine/ai/decision.py`
- `tests/test_movement*.py`
- `tests/test_scenario.py`
- `tests/test_autoplay.py`

## Verification

- [ ] `uv run python -m pytest tests/test_terrain*.py tests/test_scenario.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
