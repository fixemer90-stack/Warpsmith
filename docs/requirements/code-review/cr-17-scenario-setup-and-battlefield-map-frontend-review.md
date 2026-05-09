---
title: "CR-17 — Scenario Setup and battlefield map frontend review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-17
tags: [requirements, code-review, atomic-review]
---

# CR-17 — Scenario Setup and battlefield map frontend review

**Objective:** проверить mission/format selection, generated opponent, strategic map, simulation launch.

**Files:**
- Review: `web/templates/scenario_setup.html`
- Review: `web/static/scenario_setup.js`
- Review: `web/static/battlefield_map.js`
- Review: `web/templates/partials/battlefield_map.html`
- Output: `docs/reviews/YYYY-MM-DD/CR-17-scenario-setup-map.md`

**Steps:**
1. Выполнить `node -c` для involved JS files.
2. Проверить mission options against real `MISSIONS`.
3. Проверить game format map sizes.
4. Проверить objectives count and placement per mission.
5. Проверить roster dropdown compatibility filter.
6. Проверить generated opponent save-and-play flow.
7. Browser smoke: switch mission/format, inspect console, run/prepare simulation if data available.

**Acceptance:** user can configure scenario and launch simulation without stale mission/map/generated-roster bugs.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-17-scenario-setup-and-battlefield-map-frontend-review.md`

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
