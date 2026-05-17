---
title: "CR-03 — Auth and session review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-03
tags: [requirements, code-review, atomic-review]
---

# CR-03 — Auth and session review

**Objective:** проверить регистрацию, вход, logout, JWT cookie, OAuth boundaries.

**Files:**
- Review: `backend/auth/`
- Review: `web/routes/auth.py`
- Review: `backend/db/database.py`
- Review: `tests/test_auth*.py`, если есть
- Output: `docs/reviews/YYYY-MM-DD/CR-03-auth-session.md`

**Steps:**
1. Прочитать auth-related tests.
2. Проверить password hashing и отсутствие plaintext storage.
3. Проверить JWT lifetime, httponly/Secure/SameSite behavior.
4. Проверить logout cookie deletion.
5. Проверить OAuth provider interface и account linking.
6. Проверить error messages на отсутствие credential leaks.
7. Запустить targeted auth tests.

**Acceptance:** auth endpoints имеют корректный auth/session/security verdict.

---

---

## Execution Status

**Status:** Request Changes

**Review report:** `docs/reviews/2026-05-09/CR-03-auth-and-session-review.md`

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

- **Verdict:** REQUEST CHANGES / AUTH SESSION FIXES REQUIRED
- **Critical:** 1
- **Important:** 5
- **Suggestions:** 3
- **Blocked by:** —
- **Report:** `docs/reviews/2026-05-09/CR-03-auth-and-session-review.md`
- **Completed at:** 2026-05-09

## Triage summary

- [CR-03 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-03)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
