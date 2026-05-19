---
title: "Task 5.2 — Fix melee target selection and damage logging"
parent: remediation-plan
status: completed
phase: "5 — Movement / charge / melee identity"
task_id: "5.2"
source: remediation-plan.md
---

# Task 5.2 — Fix melee target selection and damage logging

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [5.1 — Fix charge destination and engagement identity](task-05-01-fix-charge-destination-and-engagement-identity.md)
**Next:** [5.3 — Fix terrain/LoS movement-related blockers](task-05-03-fix-terrain-los-movement-related-blockers.md)

## Phase context

**Phase:** 5 — Movement / charge / melee identity
**Purpose:** make movement, charge, engagement, melee damage, and unit identity coherent before replay/result and AI.
**Primary CRs:** CR-09, CR-11, CR-14, CR-15.
**Dependencies:** [5.1 — Fix charge destination and engagement identity](task-05-01-fix-charge-destination-and-engagement-identity.md)

## Objective

melee resolves adjacent targets and logs parsable damage with actor/target identity.

## Acceptance criteria

- [x] Adjacent melee attacks resolve.
- [x] Damage log/event uses `hits ... for ... damage` or structured equivalent. *(Fixed 2026-05-19: `_parse_log_events()` now parses `hits ... for ... damage in melee` as structured `fight` events with runtime IDs.)*
- [x] Summary attribution is not name-based. *(Fixed 2026-05-19: same-name melee regression verifies attacker/target runtime IDs are preserved for melee hit events.)*

## Resolution

### AC 1 — adjacent melee resolves

`_resolve_melee_combat()` now uses the combat engine via `simulate_unit_attack()` with melee weapons from the unit model. Falls back to simplified `max(1, models//2)` damage when no model or no melee weapons are available. Counter-attack (enemy strikes back) also uses the combat engine when models are available.

### AC 2 — damage log format

Melee logs use `"{name} hits {name} for {damage} damage in melee{identity}"` — consistent with the shooting damage pattern. The `identity` suffix carries runtime unit IDs.

### AC 3 — attribution not name-based

All melee log entries include `format_event_identity(actor_id=..., target_id=...)` tags with authoritative runtime unit IDs (`p1:Boyz:0`, `p2:Boyz:0`). Same-name units on opposite sides are disambiguated by their player-prefixed runtime IDs.

## Files likely touched

- `backend/engine/scenario.py` — `_resolve_melee_combat()` rewritten to use combat engine
- `tests/test_movement.py` — 3 new melee regression tests

## Verification

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_scenario.py tests/test_result_screen.py tests/test_movement.py -q` → 19 passed in 0.72s.
- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/ -q` → 626 passed, 3 skipped, 60 warnings in 49.02s.
- [x] `uv run ruff check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py` → All checks passed.
- [x] `uv run ruff format --check backend/engine/scenario.py tests/test_movement.py tests/test_scenario.py tests/test_result_screen.py` → 4 files already formatted.
- [x] `git diff --check -- web/routes/api_replays.py tests/test_parse_log_events.py tests/test_replay.py tests/test_result_screen.py tests/test_scenario.py tests/test_movement.py docs/remediation/task-05-02-fix-melee-target-selection-and-damage-logging.md docs/remediation/remediation-plan.md docs/remediation/index.md docs/reviews/2026-05-19/task-05-02-fix-melee-target-selection-and-damage-logging-review.md` → clean.
- [x] Deterministic parser probe → adjacent melee resolves; authoritative hit line is parsed as structured `fight` event with `actor_id=p1:Boyz:0`, `target_id=p2:Boyz:0`.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s). *(Updated 2026-05-19 in CR-09/11/14/15.)*
- [x] Phase checkpoint N/A — Task 5.3 remains before Phase 5 checkpoint.
- [x] `git diff --check` passes for touched files.


## Code review — 2026-05-19

Review file: `docs/reviews/2026-05-19/task-05-02-fix-melee-target-selection-and-damage-logging-review.md`

**Verdict: REQUEST CHANGES → FIXED 2026-05-19.**

Blocking findings:

| Finding | Evidence |
| --- | --- |
| Melee hit log is not parsed as structured event | `_parse_log_events()` parses `Boyz hits Boyz for 1 damage in melee [actor_id=...; target_id=...]` as generic `info`. |
| Summary attribution is still not proven non-name-based | Same-name probe loses attacker runtime ID in parsed damage events; target-side `took damage` event cannot attribute damage to `p1:Boyz:0`. |
| Claimed diff gate is red | `git diff --check` fails on `tests/test_result_screen.py` CRLF/trailing whitespace. |
| Source-plan/index closure was inconsistent | Task/index claimed complete while `remediation-plan.md` still had Task 5.2 unchecked before this review. |
