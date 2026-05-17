---
title: "CR-18 — Pages/templates/navigation review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-18
tags: [requirements, code-review, atomic-review]
---

# CR-18 — Pages/templates/navigation review

**Objective:** проверить base navigation, pricing/auth pages, static assets, favicon, mode toggles.

**Files:**
- Review: `web/templates/`
- Review: `web/routes/pages.py`
- Review: `web/static/`
- Output: `docs/reviews/2026-05-10/CR-18-pages-templates-navigation-review.md`

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

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-10/CR-18-pages-templates-navigation-review.md`

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

- **Verdict:** Request Changes — common routes/static assets load, but pricing CTA is broken, shared CSS helper classes do not apply under Tailwind CDN, Progressive Disclosure has a localStorage failure path, and tests miss these CR-18 contracts.
- **Critical:** 0
- **Important:** 4
- **Suggestions:** 1
- **Blocked by:** Codex CLI unavailable (`codex: command not found`); review completed with direct inspection, probes, browser smoke, and delegated independent reviewer.
- **Completed at:** 2026-05-10

## Triage summary

- [CR-18 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-18)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
