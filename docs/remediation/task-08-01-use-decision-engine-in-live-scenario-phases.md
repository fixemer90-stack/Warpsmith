---
title: "Task 8.1 — Use decision engine in live scenario phases"
parent: remediation-plan
status: pending
phase: "8 — AI integration"
task_id: "8.1"
source: remediation-plan.md
---

# Task 8.1 — Use decision engine in live scenario phases

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [7.4 — Production hardening pass](task-07-04-production-hardening-pass.md)
**Next:** [8.2 — Fix behavior overrides and target priorities](task-08-02-fix-behavior-overrides-and-target-priorities.md)

## Phase context

**Phase:** 8 — AI integration
**Purpose:** wire AI decisions into already-stable movement/combat/game-state contracts.
**Primary CRs:** CR-15, CR-17.
**Dependencies:** Phase 6 checkpoint

## Objective

F3.1/F3.2 decision logic is not dead code.

## Acceptance criteria

- [ ] Movement/shooting/charge phases call decision engine or a documented adapter.
- [ ] `EvaluationContext.faction_profile` reaches scoring functions.
- [ ] Tests prove a faction profile changes decisions.

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

- [ ] `uv run python -m pytest tests/test_ai_decision.py tests/test_faction_ai.py tests/test_autoplay.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
