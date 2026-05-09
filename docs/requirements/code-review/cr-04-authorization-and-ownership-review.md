---
title: "CR-04 — Authorization and ownership review"
parent: code-review
status: pending
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

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-04-authorization-and-ownership-review.md`

### Status checklist

- [ ] Scope confirmed
- [ ] Requirements/specs reviewed
- [ ] Tests reviewed first
- [ ] Production code reviewed
- [ ] Correctness checked
- [ ] Readability checked
- [ ] Architecture checked
- [ ] Security checked
- [ ] Performance checked
- [ ] Verification commands executed
- [ ] Findings report written
- [ ] Triage status updated in `docs/requirements/code-review/code-review.md`

### Result

- **Verdict:** Not started
- **Critical:** 0 known before execution
- **Important:** 0 known before execution
- **Suggestions:** 0 known before execution
- **Blocked by:** —
- **Completed at:** —
