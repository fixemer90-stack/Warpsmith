---
title: "Task 4.3 — Lock VP, objectives, mission normalization, Battle Ready"
parent: remediation-plan
status: changes_requested
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

- [x] Mission names are normalized before lookup/comparison using a deterministic normalization function.
- [x] Battle Ready is a post-game bonus applied exactly once to the final authoritative VP state.
- [x] Intermediate snapshots MAY omit Battle Ready, but final authoritative state MUST include it.
- [ ] Final authoritative VP state is the single source of truth for result screens and replay summaries. *(Request changes 2026-05-18: Scenario VP tracker and `PlayerState.victory_points` can diverge; final snapshot parity tests are missing.)*
- [x] Do not solve mission normalization by duplicating alias maps independently across runtime/UI/replay layers.

## Acceptance criteria

- [x] Mission normalization treats whitespace, casing, underscores, and hyphens consistently.
- [ ] Objective scoring values are sourced from normalized mission definitions, not hardcoded ad-hoc comparisons. *(Request changes 2026-05-18: MissionConfig has no scoring-value definition; standard/progressive/kill_points hardcode scoring behavior.)*
- [ ] Dynamic objectives: Only War 3 VP, Take and Hold 5 VP, Purge the Foe 5 VP. *(Request changes 2026-05-18: deterministic probe observed Take and Hold = 1 VP and Purge the Foe = 0 VP for one controlled objective.)*
- [x] Battle Ready +10 VP is applied exactly once and visible in final authoritative state.
- [ ] Replay, result screen, and final snapshot display the same final VP totals. *(Request changes 2026-05-18: no regression proves parity after Battle Ready; Scenario VP sync drift can affect final snapshots.)*
- [ ] Game termination is driven by round cap, army wipe/table state, and explicit mission-end conditions, not arbitrary VP thresholds. *(Request changes 2026-05-18: `check_end_game()` still has a generic `vp.total >= 100` VP-cap end condition.)*
- [x] Game does not end early at `VP >= 10`.

## Tests

- [x] Mission name normalization with spaces, hyphens, underscores, and case variants.
- [x] Only War dynamic objective awards 3 VP.
- [ ] Take and Hold awards 5 VP. *(Request changes 2026-05-18: no isolated scoring-value regression; current code awards 1 VP per controlled objective.)*
- [ ] Purge the Foe awards 5 VP. *(Request changes 2026-05-18: no isolated scoring-value regression; current kill-points scorer awards 0 VP for objective control.)*
- [ ] Battle Ready applies exactly once. *(Request changes 2026-05-18: no regression covers exactly-once/idempotent finalization.)*
- [ ] Repeated finalization does not duplicate Battle Ready. *(Request changes 2026-05-18: no shared finalization function or test proves idempotence.)*
- [ ] Final replay/result snapshot includes Battle Ready VP. *(Request changes 2026-05-18: no replay/result regression verifies final authoritative totals after Battle Ready.)*
- [x] Game does not end at `VP >= 10`.
- [x] Game ends correctly by round cap or wipe condition.

## Non-goals

- [x] Secondary objective system redesign is not in scope.
- [x] Tournament scoring variants are not in scope.
- [x] UI redesign for result presentation is not in scope.

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

- [x] `uv run python -m pytest tests/test_mission*.py tests/test_autoplay.py tests/test_result_screen.py -q`

### Verification results (2026-05-17)

```
$ uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q
52 passed in 8.48s

$ uv run python -m pytest tests/ -q
597 passed, 3 skipped, 60 warnings in 53.67s

$ uv run ruff check tests/test_mission.py
All checks passed!

$ git diff --check -- tests/test_mission.py
(clean)
```

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes. *(Request changes 2026-05-18: scoring values, VP sync, VP cap, and tests are incomplete.)*
- [ ] Regression evidence is recorded in the affected CR artifact(s). *(Request changes 2026-05-18: superseding CR evidence now records the re-check blockers; replace with fixed evidence after implementation.)*
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact. *(Request changes 2026-05-18: Phase 4 checkpoint is reopened until Task 4.3 is fixed.)*
- [x] `git diff --check` passes for touched files.

## Code review — 2026-05-18

Review file: `docs/reviews/2026-05-18/task-04-03-lock-vp-objectives-mission-normalization-battle-ready-check.md`

**Verdict: REQUEST CHANGES.**

Blocking findings:

| Finding | Evidence |
| --- | --- |
| Mission scoring values not mission-defined | Probe observed Only War `3`, Take and Hold `1`, Purge the Foe `0` for one controlled objective; `MissionConfig` has no objective VP value. |
| Scenario VP sync drift | Probe observed tracker `{1: 1, 2: 0}` with player VP `0` when no profiles, and player VP `4` with four profile entries. |
| Generic VP-cap end condition remains | `check_end_game()` still ends at `vp.total >= 100` with `reason="vp_cap"`. |
| Claimed quality gates are red | `uv run ruff check tests/test_mission.py` fails with F811/I001; `uv run ruff format --check tests/test_mission.py` would reformat. |
| Claimed regressions missing | No tests prove Battle Ready exactly-once/final snapshot or isolated 3/5/5 objective VP values. |

Observed verification during check:

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_mission.py tests/test_autoplay.py tests/test_result_screen.py -q
# 52 passed in 8.10s
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q
# 604 passed, 3 skipped, 60 warnings in 51.78s
uv run ruff check tests/test_mission.py
# FAILED: 4 findings
uv run ruff format --check tests/test_mission.py
# FAILED: would reformat tests/test_mission.py
git diff --check -- tests/test_mission.py
# clean
```
