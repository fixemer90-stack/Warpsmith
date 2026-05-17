---
title: "CR-21 — Documentation consistency review"
parent: code-review
status: request-changes
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
- Output: `docs/reviews/2026-05-10/CR-21-documentation-consistency-review.md`

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

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-10/CR-21-documentation-consistency-review.md`

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
- **Critical:** 0
- **Important:** 8
- **Suggestions:** 2
- **Blocked by:** —
- **Completed at:** 2026-05-10

## Triage summary

- [CR-21 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-21)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 1.1 (content contract tests)

**2026-05-16.** Content contract tests + content.v1 schema serve as documentation
consistency gate — any wiki change that breaks required fields/weapons/squad_size
is caught. 14 tests cover all 160+ wiki units.

## Regression evidence — Task 1.5 (frontmatter canonical IDs)

**2026-05-17.** (co-owned — CR-06, CR-11, CR-12, CR-21). Frontmatter `canonical_id` support.

Changes:
- Unit model: `source_path` field, parser passes source path.
- Compiler: canonical_id format validation, source_path in records, pre-write fatal collision check.
- 12 new tmp_path tests.

Tests: 36 passed (24 + 12 new). Lint/format/diff-check clean.
