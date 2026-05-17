---
title: "Task 2.3 — Enforce plan/feature gates consistently"
parent: remediation-plan
status: complete
phase: "2 — Roster validator"
task_id: "2.3"
source: remediation-plan.md
---

# Task 2.3 — Enforce plan/feature gates consistently

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [2.2 — Enforce exactly one Warlord when required](task-02-02-enforce-exactly-one-warlord-when-required.md)
**Next:** [3.1 — Fix natural 6 / Lethal Hits semantics](task-03-01-fix-natural-6-lethal-hits-semantics.md)

## Phase context

**Phase:** 2 — Roster validator
**Purpose:** make roster validation authoritative and shared across API, generated rosters, saved rosters, and UI expectations.
**Primary CRs:** CR-12, CR-16, CR-17, CR-19.
**Dependencies:** [2.2 — Enforce exactly one Warlord when required](task-02-02-enforce-exactly-one-warlord-when-required.md)

## Objective

Free/Premium roster limits cannot be bypassed through duplicate/import paths.

## Acceptance criteria

- [x] Create, duplicate, import/generate-save paths share one validator. *(Fixed: Free limit set to 1; 5 feature-gate tests added.)*
- [x] Free limit matches product requirement and UI. *(Fixed: `max_rosters: 3 → 1` in `backend/billing/plans.py`.)*
- [x] Public roster creation respects feature flags. *(Fixed: Premium `update_roster` now persists `is_public` in SQL; Free update→public rejected.)*

## Verified

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- [x] `uv run python -m pytest tests/test_rosters.py -q` → 26 passed, 48 warnings.
- [x] `uv run python -m pytest tests/ -q` → 562 passed, 3 skipped, 60 warnings.
- [x] `uv run ruff check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.
- [x] `uv run ruff format --check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → 3 files already formatted.
- [x] `git diff --check -- backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.

## Review result

### Changes implemented

- `web/routes/api_rosters.py`:
  - `_check_roster_limits()` now documents authoritative server-side gates without implying ordinary updates should run count checks.
  - Count enforcement uses `features.get("max_rosters")` and skips the count gate when `max_rosters is None`, so Premium can be unlimited.
  - Public roster updates still run the public gate with `check_count=False` and persist `is_public` in the update SQL.
  - Race condition for parallel create-like requests is documented as an accepted SQLite/pet-project limitation; production hardening should use a transaction or database constraint.
- `backend/billing/plans.py`:
  - Free `max_rosters` remains aligned to product/UI requirement: `1`.
  - Premium `max_rosters` is `None` for unlimited.
- `tests/test_rosters.py`:
  - Added feature-gate coverage for create at limit, duplicate at limit, generated roster save at limit, private update at limit, Free public update rejection, Premium public update persistence, and Premium unlimited count behavior.

## Code review — 2026-05-17

**Verdict:** REQUEST CHANGES → FIXED 2026-05-17
**Report:** `docs/reviews/2026-05-17/task-02-03-enforce-plan-feature-gates-consistently-review.md`

All blocking findings resolved:

| Finding | Fix |
| --- | --- |
| Free roster limit contradicted product/UI | Free backend limit is `1`; regression tests assert second Free create returns 403. |
| Premium public update was checked but not persisted | Update SQL now writes `is_public`; tests assert Premium update and subsequent GET return public. |
| Missing feature-gate tests / stale commands | Added focused tests in `tests/test_rosters.py`; Verification now uses existing commands. |
| Closure docs incomplete | Task, review, source plan, index, and CR evidence are synchronized for Task 2.3. Phase 2 checkpoint remains open because Task 2.2 is still not complete. |

## Files likely touched

- `backend/state/roster.py`
- `web/routes/api_rosters.py`
- `web/static/team_builder.js`
- `web/templates/team_builder.html`
- `tests/test_roster*.py`
- `tests/test_api_rosters.py`

## Verification

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- [x] `uv run python -m pytest tests/test_rosters.py -q` → 26 passed, 48 warnings.
- [x] `uv run python -m pytest tests/ -q` → 562 passed, 3 skipped, 60 warnings.
- [x] `uv run ruff check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.
- [x] `uv run ruff format --check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → 3 files already formatted.
- [x] `git diff --check -- backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.

## Completion requirements

- [x] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] Phase checkpoint not updated: Task 2.2 remains open, so Phase 2 is not complete yet.
- [x] `git diff --check` passes for touched files.
