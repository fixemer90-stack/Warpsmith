---
title: "CR-07 — Combat engine review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-07
tags: [requirements, code-review, atomic-review]
---

# CR-07 — Combat engine review

**Objective:** проверить core combat correctness: Hit → Wound → Save → Damage → FNP.

**Files:**
- Review: `backend/engine/combat.py`
- Review: `backend/engine/dice.py`
- Review: `backend/engine/modifiers.py`
- Review: `tests/test_combat*.py`, keyword tests
- Output: `docs/reviews/YYYY-MM-DD/CR-07-combat-engine.md`

**Steps:**
1. Прочитать combat tests первыми.
2. Проверить deterministic seed usage where required.
3. Проверить natural 1/6 и modifier caps.
4. Проверить weapon keyword ordering.
5. Проверить multi-weapon/multi-model aggregation.
6. Проверить AP/save/FNP interactions.
7. Запустить combat test subset.

**Acceptance:** combat math соответствует specs/tests; edge cases явно покрыты.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-07-combat-engine-review.md`

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
