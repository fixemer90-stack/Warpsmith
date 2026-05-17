---
title: "Task 7.4 — Production hardening pass"
parent: remediation-plan
status: pending
phase: "7 — API/auth/persistence hardening"
task_id: "7.4"
source: remediation-plan.md
---

# Task 7.4 — Production hardening pass

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [7.3 — Enforce billing/feature gates consistently](task-07-03-enforce-billing-feature-gates-consistently.md)
**Next:** [8.1 — Use decision engine in live scenario phases](task-08-01-use-decision-engine-in-live-scenario-phases.md)

## Phase context

**Phase:** 7 — API/auth/persistence hardening
**Purpose:** close release blockers around public boundaries, auth/ownership, billing gates, deployment safety, and DB persistence.
**Primary CRs:** CR-02, CR-03, CR-04, CR-05, CR-13, CR-19, CR-20, CR-22.
**Dependencies:** [7.3 — Enforce billing/feature gates consistently](task-07-03-enforce-billing-feature-gates-consistently.md)

## Objective

deployment route and runtime safety issues are closed.

## Acceptance criteria

- [ ] Public `/sentry-debug` is disabled outside local/dev explicit mode.
- [ ] CSP decision is documented and tested; if enabled, browser still works.
- [ ] Rate limiting is production-appropriate or accepted with explicit deployment guardrail.
- [ ] Error responses include request id where expected.

## Files likely touched

- `backend/auth/__init__.py`
- `backend/auth/providers/*`
- `backend/billing/*`
- `backend/db/database.py`
- `web/routes/api.py`
- `web/routes/api_rosters.py`
- `web/routes/api_replays.py`
- `web/routes/auth.py`
- `main.py`
- `tests/test_auth*.py`
- `tests/test_billing*.py`
- `tests/test_api*.py`
- `tests/test_deployment*.py`

## Verification

- [ ] `uv run python -m pytest tests/test_deployment*.py tests/test_api*.py -q`

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
