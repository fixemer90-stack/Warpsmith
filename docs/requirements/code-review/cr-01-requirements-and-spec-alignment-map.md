---
title: "CR-01 — Requirements and spec alignment map"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-01
tags: [requirements, code-review, atomic-review]
---

# CR-01 — Requirements and spec alignment map

**Objective:** составить карту «требование → код → тесты», чтобы review не был проверкой на ощущениях.

**Files:**
- Read: `docs/requirements/SRS.md`
- Read: `docs/requirements/UX.md`
- Read: `docs/features/*.md`
- Read: `docs/architecture/C4.md`
- Read: `ROADMAP.md`
- Output: `docs/reviews/YYYY-MM-DD/CR-01-requirements-map.md`

**Steps:**
1. Выделить реализованные фичи со статусом done/in-progress.
2. Для каждой фичи найти primary code paths.
3. Для каждой фичи найти test files.
4. Отметить фичи без тестов.
5. Отметить specs, которые выглядят stale относительно кода.
6. Сформировать таблицу coverage map.

**Acceptance:** есть таблица `Feature / Requirement / Code paths / Tests / Review owner / Risk`.

---

---

## Execution Status

**Status:** Request Changes

**Review report:** `docs/reviews/2026-05-09/CR-01-requirements-and-spec-alignment-map.md`

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

- **Verdict:** REQUEST CHANGES / DOC ALIGNMENT REQUIRED
- **Critical:** 0
- **Important:** 5
- **Suggestions:** 4
- **Blocked by:** —
- **Report:** `docs/reviews/2026-05-09/CR-01-requirements-and-spec-alignment-map.md`
- **Completed at:** 2026-05-09

## Triage summary

- [CR-01 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-01)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
