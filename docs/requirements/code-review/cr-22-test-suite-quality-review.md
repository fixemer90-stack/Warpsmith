---
title: "CR-22 — Test suite quality review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-22
tags: [requirements, code-review, atomic-review]
---

# CR-22 — Test suite quality review

**Objective:** проверить не только что тесты проходят, но что они ловят реальные regressions.

**Files:**
- Review: `tests/`
- Output: `docs/reviews/YYYY-MM-DD/CR-22-test-suite-quality.md`

**Steps:**
1. Сгруппировать tests by subsystem.
2. Найти tests that only assert status code but not behavior.
3. Найти flaky/random tests without seed.
4. Найти duplicate tests with same coverage.
5. Найти important code paths without tests.
6. Проверить fixtures for isolation and DB cleanup.
7. Запустить full suite and capture warnings.

**Acceptance:** есть prioritized list of missing/weak tests by risk.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-22-test-suite-quality-review.md`

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
