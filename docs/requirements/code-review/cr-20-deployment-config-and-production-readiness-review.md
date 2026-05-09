---
title: "CR-20 — Deployment, config and production readiness review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-20
tags: [requirements, code-review, atomic-review]
---

# CR-20 — Deployment, config and production readiness review

**Objective:** проверить Docker/Railway/env/security headers/rate limit/logging.

**Files:**
- Review: `Dockerfile`
- Review: `docker-compose.yml`, if present
- Review: `railway.json`
- Review: `Procfile`
- Review: `backend/security/`
- Review: `backend/logging_setup.py`
- Review: `main.py`
- Output: `docs/reviews/YYYY-MM-DD/CR-20-deployment-config-production.md`

**Steps:**
1. Проверить Docker includes wiki and required runtime deps.
2. Проверить `$PORT`/host assumptions against Railway config.
3. Проверить `/api/health` and root health behavior.
4. Проверить CORS/security headers.
5. Проверить rate limits and retry headers.
6. Проверить logging does not include secrets.
7. Run local server smoke and curl `/api/health`.

**Acceptance:** local/prod startup path documented and no obvious production crash/security regression.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-20-deployment-config-and-production-readiness-review.md`

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
