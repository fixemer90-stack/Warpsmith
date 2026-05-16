---
title: "Task 4.3 — Lock VP, objectives, mission normalization, Battle Ready"
parent: remediation-plan
status: pending
phase: "4 — Game state / VP / phase invariants"
task_id: "4.3"
source: remediation-plan.md
---

# Task 4.3 — Lock VP, objectives, mission normalization, Battle Ready

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [4.2 — Lock CP and battle-shock reset semantics](task-04-02-lock-cp-and-battle-shock-reset-semantics.md)
**Next:** [5.1 — Fix charge destination and engagement identity](task-05-01-fix-charge-destination-and-engagement-identity.md)

## Phase context

**Phase:** 4 — Game state / VP / phase invariants
**Purpose:** lock 10e phase flow, CP/VP, battle-shock, objective control, and end-game invariants.
**Primary CRs:** CR-08, CR-10, CR-14, CR-24.
**Dependencies:** [4.2 — Lock CP and battle-shock reset semantics](task-04-02-lock-cp-and-battle-shock-reset-semantics.md)

## Objective

VP source is deterministic and 10e-aligned.

## Acceptance criteria

- [ ] Mission names normalize spaces and hyphens.
- [ ] Dynamic objectives: Only War 3, Take and Hold/Purge the Foe 5.
- [ ] Battle Ready +10 VP applied exactly once and visible in final authoritative state.
- [ ] Game ends by rounds/wipe/mission cap, not early VP>=10.

## Files likely touched

- `backend/state/game_state.py`
- `backend/state/mission.py`
- `backend/engine/scenario.py`
- `backend/engine/ai/autoplay.py`
- `tests/test_game_state.py`
- `tests/test_scenario.py`
- `tests/test_mission*.py`
- `tests/test_autoplay.py`

## Verification

- [ ] `uv run python -m pytest tests/test_mission*.py tests/test_autoplay.py tests/test_result_screen.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
