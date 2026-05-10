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
