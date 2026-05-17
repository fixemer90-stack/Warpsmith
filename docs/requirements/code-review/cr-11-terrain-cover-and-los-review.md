---
title: "CR-11 — Terrain, cover and LoS review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-11
tags: [requirements, code-review, atomic-review]
---

# CR-11 — Terrain, cover and LoS review

**Objective:** проверить текущую F2.13 модель и gaps относительно F2.18 Terrain Mechanics 10e.

**Files:**
- Read: `docs/features/f2.13-cover-terrain.md`
- Read: `docs/features/f2.18-terrain-mechanics-10e.md`
- Review: `backend/state/map.py`
- Review: `backend/state/line_of_sight.py`
- Review: `backend/engine/combat.py`
- Review: terrain/LoS tests
- Output: `docs/reviews/YYYY-MM-DD/CR-11-terrain-cover-los.md`

**Steps:**
1. Зафиксировать, что реализовано сейчас: F2.13 baseline или F2.18 full terrain.
2. Проверить Bresenham/ray casting correctness.
3. Проверить cover +1 save and AP0 restriction if present.
4. Проверить `Ignores Cover` and `Indirect Fire` interactions.
5. Проверить map bounds and terrain tile handling.
6. Составить explicit gap list к F2.18: ruins, woods, craters, barricades, debris, hills, Plunging Fire.
7. Запустить terrain/LoS tests.

**Acceptance:** review не путает baseline F2.13 с pending F2.18; gaps оформлены как planned work, а regressions — как findings.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-09/CR-11-terrain-cover-and-los-review.md`

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
- **Important:** 4
- **Suggestions:** 0
- **Blocked by:** —
- **Completed at:** 2026-05-09T22:34:24+03:00

## Triage summary

- [CR-11 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-11)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 1.1 (content contract tests)

**2026-05-16.** Content contract tests validate all wiki units against content.v1
Pydantic schema. Terrain/cover/LoS code unchanged; structural content quality gate added.
14 tests (incl. schema validation, squad_size, source-level duplicates).

## Regression evidence — Task 1.5 (frontmatter canonical IDs)

**2026-05-17.** (co-owned — CR-06, CR-11, CR-12, CR-21). Frontmatter `canonical_id` support.

Changes:
- Unit model: `source_path` field, parser passes source path.
- Compiler: canonical_id format validation, source_path in records, pre-write fatal collision check.
- 12 new tmp_path tests.

Tests: 36 passed (24 + 12 new). Lint/format/diff-check clean.

## Regression evidence — Task 3.2 (AP/save application and Devastating Wounds)

**2026-05-17.** (co-owned — CR-07, CR-11). Core save resolution and Devastating Wounds fixes.

Changes:
- `backend/engine/combat.py`: fixed AP applied twice — removed duplicate `save_target - weapon.ap`. Cover applied at correct stage after single AP application. `ignores_cover` weapon tag now propagated via modifier check in save resolution.
- `backend/engine/modifiers.py`: `devastating_wounds` no longer sets `ignore_save` unconditionally in `apply_modifiers` — only `handle_critical_hit` triggers it on Critical Wounds.

Tests: 9 new focused tests covering AP exactly once, cover+AP interaction, cover+AP+ignores_cover, normal save path vs Devastating Wounds bypass, Dev Wounds only on Critical Wounds, Dev Wounds reaching FNP.

```
$ uv run python -m pytest tests/test_combat.py tests/test_modifiers.py -q
44 passed in 13.07s

$ uv run python -m pytest tests/ -q
571 passed, 3 skipped, 60 warnings in 71.50s
```

Lint/format/diff-check: clean.
