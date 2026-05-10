---
title: "CR-16 — Team Builder frontend review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-16
tags: [requirements, code-review, atomic-review]
---

# CR-16 — Team Builder frontend review

**Objective:** проверить Team Builder Alpine state, unit modal, roster save/edit, Warlord UI, PTS UI.

**Files:**
- Review: `web/templates/team_builder.html`
- Review: `web/static/team_builder.js`
- Review: `web/static/unit_modal.js`
- Review: `web/templates/partials/*.html` related to units/rosters
- Output: `docs/reviews/2026-05-10/CR-16-team-builder-frontend-review.md`

**Steps:**
1. Выполнить `node -c` для involved JS files.
2. Проверить Alpine null-safety in templates.
3. Проверить no Jinja2/Alpine `{{ }}` conflicts.
4. Проверить Warlord crown visible and save disabled until valid.
5. Проверить PTS formula UI parity.
6. Проверить edit mode metadata hydration.
7. Browser smoke: `/team-builder`, console errors, key tokens present.

**Acceptance:** Team Builder работает без JS syntax/runtime errors and saves valid roster payloads.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-10/CR-16-team-builder-frontend-review.md`

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

- **Verdict:** Request Changes — current live Team Builder Warlord/PTS smoke passed, but stale duplicate modal code and placeholder modal tests make the CR-16 acceptance unsafe.
- **Critical:** 0
- **Important:** 2
- **Suggestions:** 2
- **Blocked by:** —
- **Report:** `docs/reviews/2026-05-10/CR-16-team-builder-frontend-review.md`
- **Completed at:** 2026-05-10

## Triage summary

- [CR-16 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-16)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
