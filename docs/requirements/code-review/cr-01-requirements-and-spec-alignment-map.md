---
title: "CR-01 — Requirements and spec alignment map"
parent: code-review
status: pending
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

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-01-requirements-and-spec-alignment-map.md`

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
