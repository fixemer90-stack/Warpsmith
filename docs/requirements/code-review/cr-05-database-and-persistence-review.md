---
title: "CR-05 — Database and persistence review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-05
tags: [requirements, code-review, atomic-review]
---

# CR-05 — Database and persistence review

**Objective:** проверить schema, migrations/init, JSON parsing, SQLite concurrency assumptions.

**Files:**
- Review: `backend/db/database.py`
- Review: DB usage in `web/routes/*.py`
- Review: tests touching rosters/replays/users
- Output: `docs/reviews/YYYY-MM-DD/CR-05-database-persistence.md`

**Steps:**
1. Проверить `connect()` и DB path creation.
2. Проверить parameterized SQL везде.
3. Проверить JSON columns parse/dump boundaries.
4. Проверить transaction/commit/rollback behavior.
5. Проверить SQLite WAL/shm cleanup assumptions in tests.
6. Проверить schema backward compatibility.
7. Запустить DB-related tests.

**Acceptance:** DB layer не содержит SQL injection, data loss, JSON string/list mismatch или ownership bypass.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-05-database-and-persistence-review.md`

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
