---
title: "CR-02 — Static security and secrets scan"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-02
tags: [requirements, code-review, atomic-review]
---

# CR-02 — Static security and secrets scan

**Objective:** найти блокирующие security issues до ручного review.

**Files:**
- Scope: весь repo, кроме `.git`, venv/cache/build artifacts.
- Output: `docs/reviews/YYYY-MM-DD/CR-02-static-security-scan.md`

**Steps:**
1. Проверить hardcoded secrets: `api_key`, `secret`, `password`, `token`, `passwd`.
2. Проверить shell injection patterns: `os.system`, `subprocess.*shell=True`.
3. Проверить dangerous eval/exec.
4. Проверить unsafe deserialization: `pickle.loads`, `pickle.load`.
5. Проверить SQL string interpolation near `execute(...)`.
6. Проверить печать cookies/JWT/password в logs/tests.
7. Зафиксировать false positives отдельно, не удаляя их из отчёта.

**Acceptance:** каждый finding классифицирован как `Critical`, `Important`, `Suggestion` или `False Positive`.

---

---

## Execution Status

**Status:** Request Changes

**Review report:** `docs/reviews/2026-05-09/CR-02-static-security-and-secrets-scan.md`

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

- **Verdict:** REQUEST CHANGES / SECURITY FIXES REQUIRED
- **Critical:** 2
- **Important:** 7
- **Suggestions:** 4
- **False positives:** 5
- **Blocked by:** —
- **Report:** `docs/reviews/2026-05-09/CR-02-static-security-and-secrets-scan.md`
- **Completed at:** 2026-05-09

## Triage summary

- [CR-02 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-02)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
