---
title: "CR-03 — Auth and session review"
parent: code-review
status: pending
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

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-03-auth-and-session-review.md`

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
