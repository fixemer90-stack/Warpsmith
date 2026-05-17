---
title: "CR-04 — Authorization and ownership review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-04
tags: [requirements, code-review, atomic-review]
---

# CR-04 — Authorization and ownership review

**Objective:** проверить, что пользователь видит и меняет только свои rosters/replays/subscriptions.

**Files:**
- Review: `web/routes/api_rosters.py`
- Review: `web/routes/api_replays.py`
- Review: `backend/billing/`
- Review: `backend/db/database.py`
- Review: `tests/test_rosters.py`, `tests/test_replay*.py`, billing tests
- Output: `docs/reviews/YYYY-MM-DD/CR-04-authorization-ownership.md`

**Steps:**
1. Прочитать tests на owner isolation.
2. Проверить каждый CRUD endpoint на `user_id` filter.
3. Проверить guest/local fallback отдельно от authenticated flow.
4. Проверить public/private roster semantics.
5. Проверить delete/update/duplicate ownership.
6. Проверить replay access по owner.
7. Запустить targeted tests.

**Acceptance:** нет endpoint, который позволяет читать/изменять чужие данные без явного public contract.

---

---

## Execution Status

**Status:** Request Changes

**Review report:** `docs/reviews/2026-05-09/CR-04-authorization-and-ownership-review.md`

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

- **Verdict:** REQUEST CHANGES / OWNERSHIP BYPASS FIXES REQUIRED
- **Critical:** 2
- **Important:** 3
- **Suggestions:** 3
- **Blocked by:** —
- **Report:** `docs/reviews/2026-05-09/CR-04-authorization-and-ownership-review.md`
- **Completed at:** 2026-05-09

## Triage summary

- [CR-04 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-04)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
