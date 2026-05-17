---
title: "CR-19 — Billing, feature gate and subscription review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-19
tags: [requirements, code-review, atomic-review]
---

# CR-19 — Billing, feature gate and subscription review

**Objective:** проверить monetization boundaries and free/premium gates.

**Files:**
- Review: `backend/billing/`
- Review: billing/auth routes
- Review: pricing templates
- Review: billing tests
- Output: `docs/reviews/2026-05-10/CR-19-billing-feature-gate-and-subscription-review.md`

**Steps:**
1. Проверить plan definitions and user features.
2. Проверить Free tier roster limit enforcement.
3. Проверить Premium bypasses limits where intended.
4. Проверить Stripe webhook handling and signature validation if implemented.
5. Проверить no secret leakage in logs/config/docs.
6. Проверить downgrade semantics.
7. Запустить billing tests.

**Acceptance:** subscription model cannot be bypassed by simple API calls and does not leak billing secrets.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-10/CR-19-billing-feature-gate-and-subscription-review.md`

### Status checklist

- [x] Scope confirmed
- [x] Requirements/specs reviewed
- [x] Tests reviewed first
- [x] Production code reviewed
- [x] Correctness checked
- [x] Readability checked
- [x] Architecture checked
- [x] Security checked
- [x] Performance checked
- [x] Verification commands executed
- [x] Findings report written
- [x] Triage status updated in `docs/requirements/code-review/code-review.md`

### Result

- **Verdict:** Request Changes
- **Critical:** 3
- **Important:** 8
- **Suggestions:** 1
- **Blocked by:** —
- **Completed at:** 2026-05-10

## Triage summary

- [CR-19 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-19)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 2.1 (canonical PTS formula)

**2026-05-17.** (co-owned — CR-12, CR-16, CR-17, CR-19). One canonical `calculate_squad_pts()`.

Changes:
- `roster.py`: canonical PTS function `(points/minSquad + loadoutPts)*squadSize + nobPts`.
- `api_rosters.py`: create/update/generate use canonical formula, expose `total_pts` + `squad_pts`.
- 11 new tests covering all formula scenarios.

Tests: 33 passed in test_roster.py (22 pre-existing + 11 new). Lint/format/diff-check clean.
## Regression evidence — Task 2.3

Date: 2026-05-17

Task 2.3 fixed shared server-side feature gates for roster create-like paths and gated public updates. Free rosters are limited to one, Premium uses `max_rosters=None` for unlimited, duplicate/generated-save paths share the create gate, and public updates are checked and persisted. Parallel create race remains an accepted SQLite/pet-project limitation pending production transaction/constraint hardening.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- `uv run python -m pytest tests/ -q` → 562 passed, 3 skipped, 60 warnings.
- `uv run ruff check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.
- `uv run ruff format --check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.
- `git diff --check -- backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.
