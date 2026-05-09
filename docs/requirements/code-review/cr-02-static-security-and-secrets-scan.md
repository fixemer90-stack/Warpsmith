---
title: "CR-02 — Static security and secrets scan"
parent: code-review
status: pending
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

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-02-static-security-and-secrets-scan.md`

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
