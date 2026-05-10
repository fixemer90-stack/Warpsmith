---
title: "CR-22 — Test suite quality review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-22
tags: [requirements, code-review, atomic-review]
---

# CR-22 — Test suite quality review

**Objective:** проверить не только что тесты проходят, но что они ловят реальные regressions.

**Files:**
- Review: `tests/`
- Output: `docs/reviews/2026-05-10/CR-22-test-suite-quality-review.md`

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

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-10/CR-22-test-suite-quality-review.md`

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
- **Critical:** 2
- **Important:** 9
- **Suggestions:** 2
- **Blocked by:** —
- **Completed at:** 2026-05-10

## Triage summary

- [CR-22 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-22)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
