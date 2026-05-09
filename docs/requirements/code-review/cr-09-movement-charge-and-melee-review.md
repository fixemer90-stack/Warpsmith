---
title: "CR-09 — Movement, charge and melee review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-09
tags: [requirements, code-review, atomic-review]
---

# CR-09 — Movement, charge and melee review

**Objective:** проверить, что melee units реально сближаются, charge возможен, melee damage логируется.

**Files:**
- Review: `backend/engine/scenario.py`
- Review: movement/charge/melee tests
- Output: `docs/reviews/YYYY-MM-DD/CR-09-movement-charge-melee.md`

**Steps:**
1. Прочитать tests вокруг movement/charge.
2. Проверить `_is_valid_move` и occupied-cell handling.
3. Проверить adjacent charge position, а не move onto target cell.
4. Проверить engagement distance.
5. Проверить melee target resolution по adjacency, не exact position only.
6. Проверить melee damage log format compatible with summary parser.
7. Запустить targeted tests/autoplay smoke.

**Acceptance:** melee-focused rosters не застревают без charge/fight damage.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-09-movement-charge-and-melee-review.md`

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
