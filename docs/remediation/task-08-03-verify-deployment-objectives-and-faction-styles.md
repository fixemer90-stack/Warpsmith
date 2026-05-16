---
title: "Task 8.3 — Verify deployment objectives and faction styles"
parent: remediation-plan
status: pending
phase: "8 — AI integration"
task_id: "8.3"
source: remediation-plan.md
---

# Task 8.3 — Verify deployment objectives and faction styles

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [8.2 — Fix behavior overrides and target priorities](task-08-02-fix-behavior-overrides-and-target-priorities.md)
**Next:** [9.1 — Run final CR-24 regression gate and reconcile review metadata](task-09-01-final-cr-24-regression-gate.md)

## Phase context

**Phase:** 8 — AI integration
**Purpose:** wire AI decisions into already-stable movement/combat/game-state contracts.
**Primary CRs:** CR-15, CR-17.
**Dependencies:** [8.2 — Fix behavior overrides and target priorities](task-08-02-fix-behavior-overrides-and-target-priorities.md)

## Objective

Orks, Tau, and AdMech exhibit distinct deployment/movement tendencies from profile weights.

## Acceptance criteria

- [ ] Orks melee units bias toward engagement.
- [ ] Tau ranged units prefer ranged positioning/targets.
- [ ] Deployment uses faction profile role preferences.

## Files likely touched

- `backend/engine/ai/decision.py`
- `backend/engine/ai/faction_ai.py`
- `backend/engine/ai/deployment.py`
- `backend/engine/ai/autoplay.py`
- `backend/engine/scenario.py`
- `wiki/factions/*.md`
- `tests/test_faction_ai.py`
- `tests/test_ai_decision.py`
- `tests/test_autoplay.py`

## Verification

- [ ] `uv run python -m pytest tests/test_autoplay.py tests/test_faction_ai.py -q`
- [ ] Deterministic scenario probes with fixed seed.

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
