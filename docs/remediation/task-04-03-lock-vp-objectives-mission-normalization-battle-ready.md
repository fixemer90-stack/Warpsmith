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

VP source is deterministic, 10e-aligned, and shared by runtime, replay, result screen, and autoplay.

## VP / mission scoring contract

- [ ] Primary/dynamic VP scoring uses one canonical scoring pipeline shared by runtime, replay, result screen, and autoplay.
- [ ] Mission names are normalized before lookup/comparison using a deterministic normalization function.
- [ ] Battle Ready is a post-game bonus applied exactly once to the final authoritative VP state.
- [ ] Intermediate snapshots MAY omit Battle Ready, but final authoritative state MUST include it.
- [ ] Final authoritative VP state is the single source of truth for result screens and replay summaries.
- [ ] Do not solve mission normalization by duplicating alias maps independently across runtime/UI/replay layers.

## Acceptance criteria

- [ ] Mission normalization treats whitespace, casing, underscores, and hyphens consistently.
- [ ] Objective scoring values are sourced from normalized mission definitions, not hardcoded ad-hoc comparisons.
- [ ] Dynamic objectives: Only War 3 VP, Take and Hold 5 VP, Purge the Foe 5 VP.
- [ ] Battle Ready +10 VP is applied exactly once and visible in final authoritative state.
- [ ] Replay, result screen, and final snapshot display the same final VP totals.
- [ ] Game termination is driven by round cap, army wipe/table state, and explicit mission-end conditions, not arbitrary VP thresholds.
- [ ] Game does not end early at `VP >= 10`.

## Tests

- [ ] Mission name normalization with spaces, hyphens, underscores, and case variants.
- [ ] Only War dynamic objective awards 3 VP.
- [ ] Take and Hold awards 5 VP.
- [ ] Purge the Foe awards 5 VP.
- [ ] Battle Ready applies exactly once.
- [ ] Repeated finalization does not duplicate Battle Ready.
- [ ] Final replay/result snapshot includes Battle Ready VP.
- [ ] Game does not end at `VP >= 10`.
- [ ] Game ends correctly by round cap or wipe condition.

## Non-goals

- [ ] Secondary objective system redesign is not in scope.
- [ ] Tournament scoring variants are not in scope.
- [ ] UI redesign for result presentation is not in scope.

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
