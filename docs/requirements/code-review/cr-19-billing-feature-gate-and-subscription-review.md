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
