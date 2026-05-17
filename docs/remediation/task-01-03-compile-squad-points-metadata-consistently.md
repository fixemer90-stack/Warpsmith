---
title: "Task 1.3 — Compile squad/points metadata consistently"
parent: remediation-plan
status: completed
phase: "1 — Content compiler / schemas"
task_id: "1.3"
source: remediation-plan.md
---

# Task 1.3 — Compile squad/points metadata consistently

**Index:** [index.md](index.md)
**Previous:** [1.2 — Replace unsafe/stale cache behavior](task-01-02-replace-unsafe-stale-cache-behavior.md)

## Phase context

**Phase:** 1 — Content compiler / schemas
**Primary CRs:** CR-06, CR-11, CR-12, CR-21.
**Dependencies:** [1.2 — Replace unsafe/stale cache behavior](task-01-02-replace-unsafe-stale-cache-behavior.md)

## Objective

one canonical squad metadata shape feeds roster validation and UI.

## Acceptance criteria

- [x] `unit.squad_size` from YAML/frontmatter is authoritative.
- [x] `model_count` is not used as roster min/max replacement.
- [x] Single-model vehicles and transport capacity cannot be misread as squad size.

## Files changed

- `backend/state/roster.py` — `validate_squad_size()` uses `unit.squad_size` from frontmatter (was `unit.model_count`)
- `backend/engine/ai/autoplay.py` — `_roster_to_player_state()` uses `squad_size.min` (was `model_count[0]`)
- `tests/test_content_contracts.py` — 2 new tests: `test_squad_size_is_authoritative_not_model_count`, `test_squad_size_step_valid`

## Verification

- [x] `uv run python -m pytest tests/test_content_contracts.py -q` — 23 passed.
- [x] `uv run python -m pytest tests/ -q` — 504 passed, 3 skipped.
- [x] `uv run ruff check backend/state/roster.py backend/engine/ai/autoplay.py` — All checks passed.

## Completion requirements

- [x] Implementation/change is complete for this task only.
- [x] Regression evidence in CR artifacts.
- [ ] Phase checkpoint — N/A (Phase 1 has more tasks).
- [x] `git diff --check` passes.
