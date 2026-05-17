---
title: "Task 2.3 — Enforce plan/feature gates consistently"
parent: remediation-plan
status: changes_requested
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

- [ ] Create, duplicate, import/generate-save paths share one validator. *(Request changes: helper exists for create/duplicate/update, but feature-gate regression tests are missing and import/generate-save closure is not proven.)*
- [ ] Free limit matches product requirement and UI. *(Request changes: backend Free limit is 3; UI/ADR/UX/product requirement say 1.)*
- [ ] Public roster creation respects feature flags. *(Request changes: Free public create is blocked, but Premium public update is validated then silently not persisted.)*

## Verified

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 57 passed, 26 warnings.
- [x] `uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py tests/test_roster.py tests/test_rosters.py` → clean.
- [x] `uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py tests/test_roster.py tests/test_rosters.py` → clean.
- [ ] `uv run python -m pytest tests/test_api_rosters.py tests/test_billing*.py -q` → failed, exit 4 (`tests/test_api_rosters.py` not found; no `tests/test_billing*.py`).
- [ ] `uv run python -m pytest tests/ -q` → failed: 6 failed, 544 passed, 3 skipped, 38 warnings.
- [ ] `git diff --check -- ... backend/billing/plans.py ...` → failed because `backend/billing/plans.py` has CRLF/trailing-whitespace diff-check errors.

## Review result

### Changes claimed

- `web/routes/api_rosters.py`:
  - Added `_check_roster_limits(user, is_public, check_count)` — shared helper enforcing Free tier max_rosters and `public_rosters_create` feature gate.
  - `create_roster`: replaces manual check with `_check_roster_limits(user, is_public=data.is_public)`.
  - `duplicate_roster`: added `_check_roster_limits(user)`.
  - `update_roster`: added `_check_roster_limits(user, is_public=data.is_public, check_count=False)`.

## Code review — 2026-05-17

**Verdict:** REQUEST CHANGES
**Report:** `docs/reviews/2026-05-17/task-02-03-enforce-plan-feature-gates-consistently-review.md`

### Blocking findings

1. Free roster limit still does not match product/UI requirement: backend `UserFeatures.FREE["max_rosters"]` is 3, while UI/ADR/UX/user product requirement say 1 roster.
2. Premium public update is checked but not persisted: `update_roster()` validates `data.is_public` but its SQL update never writes `is_public`.
3. Verification command is not reproducible: `tests/test_api_rosters.py` does not exist and there are no `tests/test_billing*.py` files.
4. Closure docs are incomplete: completion requirements are unchecked, source plan/checkpoint remain unchecked, CR evidence is missing, and Phase 2 cannot be complete while Task 2.2 remains `changes_requested`.

### Review verification

- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 57 passed, 26 warnings.
- `uv run python -m pytest tests/test_api_rosters.py tests/test_billing*.py -q` → failed, exit 4 (`tests/test_api_rosters.py` not found).
- `uv run python -m pytest tests/ -q` → failed: 6 failed, 544 passed, 3 skipped, 38 warnings.
- `uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py tests/test_roster.py tests/test_rosters.py` → clean.
- `uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py tests/test_roster.py tests/test_rosters.py` → clean.
- `git diff --check -- ... backend/billing/plans.py ...` → failed because `backend/billing/plans.py` has CRLF/trailing-whitespace diff-check errors.

## Files likely touched

- `backend/state/roster.py`
- `web/routes/api_rosters.py`
- `web/static/team_builder.js`
- `web/templates/team_builder.html`
- `tests/test_roster*.py`
- `tests/test_api_rosters.py`

## Verification

- [ ] `uv run python -m pytest tests/test_api_rosters.py tests/test_billing*.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
