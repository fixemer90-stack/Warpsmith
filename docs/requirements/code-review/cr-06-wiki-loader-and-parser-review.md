---
title: "CR-06 — Wiki loader and parser review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-06
tags: [requirements, code-review, atomic-review]
---

# CR-06 — Wiki loader and parser review

**Objective:** проверить wiki-driven data loading, YAML frontmatter, no hardcode scaling risks.

**Files:**
- Review: `backend/loader/`
- Review: `backend/model/`
- Review: `wiki/`
- Review: parser/registry tests
- Output: `docs/reviews/YYYY-MM-DD/CR-06-wiki-loader-parser.md`

**Steps:**
1. Прочитать parser/registry tests.
2. Проверить YAML frontmatter как source of truth.
3. Проверить faction slug ↔ filesystem mapping.
4. Проверить unit/detachment/stratagem loading boundaries.
5. Проверить cache invalidation / stale cache risks.
6. Проверить отсутствие hardcoded faction/unit lists в code paths, где должен быть wiki/API.
7. Запустить loader-related tests.

**Acceptance:** новые faction/unit/detachment additions не требуют code changes, кроме documented exceptions.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-06-wiki-loader-and-parser-review.md`

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
