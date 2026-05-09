---
title: "CR-11 — Terrain, cover and LoS review"
parent: code-review
status: pending
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

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-11-terrain-cover-and-los-review.md`

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
