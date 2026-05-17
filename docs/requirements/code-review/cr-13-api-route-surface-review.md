---
title: "CR-13 — API route surface review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-13
tags: [requirements, code-review, atomic-review]
---

# CR-13 — API route surface review

**Objective:** проверить FastAPI route structure, method correctness, route ordering, response contracts.

**Files:**
- Review: `web/routes/api.py`
- Review: `web/routes/api_detachments.py`
- Review: `web/routes/api_rosters.py`
- Review: `web/routes/api_replays.py`
- Review: `web/routes/pages.py`
- Output: `docs/reviews/YYYY-MM-DD/CR-13-api-route-surface.md`

**Steps:**
1. Составить list of routes from app.
2. Проверить route ordering: static paths before `{id}` paths.
3. Проверить GET/POST/PUT/DELETE alignment with frontend fetch.
4. Проверить auth dependencies on private endpoints.
5. Проверить error status codes and JSON body consistency.
6. Проверить no duplicate route ownership.
7. Запустить API-related tests and curl smoke for `/api/health`.

**Acceptance:** нет 405/401/404 из-за method/order/register bugs; routes имеют clear module ownership.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-09/CR-13-api-route-surface-review.md`

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
- **Critical:** 3
- **Important:** 5
- **Suggestions:** 0
- **Blocked by:** —
- **Completed at:** 2026-05-09T22:58:10+03:00

## Triage summary

- [CR-13 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-13)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
