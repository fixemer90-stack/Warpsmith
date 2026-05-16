---
title: "CR-20 — Deployment, config and production readiness review"
parent: code-review
status: request-changes
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
- Output: `docs/reviews/2026-05-10/CR-20-deployment-config-and-production-readiness-review.md`

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

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-10/CR-20-deployment-config-and-production-readiness-review.md`

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
- **Critical:** 2
- **Important:** 7
- **Suggestions:** 1
- **Blocked by:** —
- **Completed at:** 2026-05-10

## Triage summary

- [CR-20 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-20)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 0.1 (runtime unit identity)

**2026-05-16.** No direct findings fixed in CR-20 scope. Runtime unit identity contract
established in `backend/state/runtime_id.py`; no deployment/config changes.
Full regression: 471 tests passed, lint/formatter clean.

## Regression evidence — Task 0.2 (canonical GameState serializer)

**2026-05-16.** Canonical snapshot serializer. No deployment/config changes.
Single source of truth for GameState shape reduces snapshot divergence risk. 478 tests pass.
