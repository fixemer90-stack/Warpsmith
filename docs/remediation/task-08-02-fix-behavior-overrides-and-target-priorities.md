---
title: "Task 8.2 — Fix behavior overrides and target priorities"
parent: remediation-plan
status: pending
phase: "8 — AI integration"
task_id: "8.2"
source: remediation-plan.md
---

# Task 8.2 — Fix behavior overrides and target priorities

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [8.1 — Use decision engine in live scenario phases](task-08-01-use-decision-engine-in-live-scenario-phases.md)
**Next:** [8.3 — Verify deployment objectives and faction styles](task-08-03-verify-deployment-objectives-and-faction-styles.md)

## Phase context

**Phase:** 8 — AI integration
**Purpose:** wire AI decisions into already-stable movement/combat/game-state contracts.
**Primary CRs:** CR-15, CR-17.
**Dependencies:** [8.1 — Use decision engine in live scenario phases](task-08-01-use-decision-engine-in-live-scenario-phases.md)

## Objective

faction profile weights/overrides affect runtime behavior predictably.

## Acceptance criteria

- [ ] `action_override` is honored or removed from schema/docs.
- [ ] Target multipliers below 1.0 can de-prioritize targets.
- [ ] Behavior activation marks behavior used once as intended.

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

- [ ] `uv run python -m pytest tests/test_faction_ai.py tests/test_ai_decision.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
