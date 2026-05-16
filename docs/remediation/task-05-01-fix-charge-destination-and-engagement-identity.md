---
title: "Task 5.1 — Fix charge destination and engagement identity"
parent: remediation-plan
status: pending
phase: "5 — Movement / charge / melee identity"
task_id: "5.1"
source: remediation-plan.md
---

# Task 5.1 — Fix charge destination and engagement identity

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [4.3 — Lock VP, objectives, mission normalization, Battle Ready](task-04-03-lock-vp-objectives-mission-normalization-battle-ready.md)
**Next:** [5.2 — Fix melee target selection and damage logging](task-05-02-fix-melee-target-selection-and-damage-logging.md)

## Phase context

**Phase:** 5 — Movement / charge / melee identity
**Purpose:** make movement, charge, engagement, melee damage, and unit identity coherent before replay/result and AI.
**Primary CRs:** CR-09, CR-11, CR-14, CR-15.
**Dependencies:** Phase 4 checkpoint

## Objective

charge moves to adjacent legal cell and marks scoped units as engaged.

## Acceptance criteria

- [ ] Charge never attempts to occupy enemy cell.
- [ ] Engagement uses runtime ids, not names.
- [ ] Same-name mirrored units can engage independently.

## Files likely touched

- `backend/engine/scenario.py`
- `backend/state/game_state.py`
- `backend/state/map.py`
- `backend/engine/ai/decision.py`
- `tests/test_movement*.py`
- `tests/test_scenario.py`
- `tests/test_autoplay.py`

## Verification

- [ ] `uv run python -m pytest tests/test_movement*.py tests/test_scenario.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
