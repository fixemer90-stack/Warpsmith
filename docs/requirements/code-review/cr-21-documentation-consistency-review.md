---
title: "CR-21 — Documentation consistency review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-21
tags: [requirements, code-review, atomic-review]
---

# CR-21 — Documentation consistency review

**Objective:** проверить, что docs не расходятся с кодом после review baseline.

**Files:**
- Review: `README.md`
- Review: `DEV_INDEX.md`
- Review: `AGENTS.md`
- Review: `CHANGELOG.md`
- Review: `ROADMAP.md`
- Review: `ROADMAP.html`
- Review: `docs/architecture/C4.md`
- Review: `docs/features/*.md`
- Output: `docs/reviews/YYYY-MM-DD/CR-21-documentation-consistency.md`

**Steps:**
1. Проверить test counts against collect-only/full tests.
2. Проверить phase counts and feature statuses.
3. Проверить code paths named in docs exist.
4. Проверить API module ownership statements.
5. Проверить docs for stale 6-phase / old mission / old map / old Warlord behavior claims.
6. Выполнить corruption scan: `^||`, read_file line prefixes.
7. Выполнить `git diff --check` for docs after any doc edits.

**Acceptance:** docs describe current code, not historical implementation.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-21-documentation-consistency-review.md`

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
