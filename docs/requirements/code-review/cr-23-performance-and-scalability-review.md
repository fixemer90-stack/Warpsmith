---
title: "CR-23 — Performance and scalability review"
parent: code-review
status: request-changes
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

- **Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-10/CR-23-performance-and-scalability-review.md`

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

- **Verdict:** Request Changes — no Critical blockers, but commercialization needs pagination/indexing, batch/bounded data loading, registry/faction caching, bounded/offloaded simulation, and monotonic timing fixes.
- **Critical:** 0
- **Important:** 7
- **Suggestions:** 3
- **Blocked by:** —
- **Completed at:** 2026-05-10

## Triage summary

- [CR-23 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-23)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
