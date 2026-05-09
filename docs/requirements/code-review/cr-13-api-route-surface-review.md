---
title: "CR-13 — API route surface review"
parent: code-review
status: pending
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

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-13-api-route-surface-review.md`

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
