---
title: "CR-23 — Performance and scalability review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-23
tags: [requirements, code-review, atomic-review]
---

# CR-23 — Performance and scalability review

**Objective:** проверить obvious bottlenecks before commercialization.

**Files:**
- Review: loaders, API list endpoints, DB queries, frontend rendering loops.
- Output: `docs/reviews/YYYY-MM-DD/CR-23-performance-scalability.md`

**Steps:**
1. Проверить unbounded DB queries/list endpoints.
2. Проверить pagination needs for rosters/replays/wiki lists.
3. Проверить repeated registry loads/cache misses.
4. Проверить N+1 patterns in route handlers.
5. Проверить frontend loops over all units/detachments without debounce/memoization.
6. Проверить simulation runtime assumptions vs NFR `< 30 sec`.
7. Run lightweight timing smoke for critical endpoints.

**Acceptance:** performance risks separated into Critical/Important/Suggestion with measured evidence where possible.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-23-performance-and-scalability-review.md`

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
