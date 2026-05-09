---
title: "CR-18 — Pages/templates/navigation review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-18
tags: [requirements, code-review, atomic-review]
---

# CR-18 — Pages/templates/navigation review

**Objective:** проверить base navigation, pricing/auth pages, static assets, favicon, mode toggles.

**Files:**
- Review: `web/templates/`
- Review: `web/routes/pages.py`
- Review: `web/static/`
- Output: `docs/reviews/YYYY-MM-DD/CR-18-pages-templates-navigation.md`

**Steps:**
1. Проверить all page routes return 200 or expected auth redirect.
2. Проверить base.html includes required assets once.
3. Проверить no stale navigation links.
4. Проверить favicon/static files reachable.
5. Проверить Progressive Disclosure body classes and toggle behavior.
6. Проверить no Alpine template runtime errors in common pages.
7. Browser/curl smoke for key pages.

**Acceptance:** navigation and common templates do not break app shell.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-18-pages-templates-navigation-review.md`

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
