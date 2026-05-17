---
title: "CR-07 — Combat engine review"
parent: code-review
status: request-changes
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

**Status:** Request Changes

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

#

## Result

- **Report:** `docs/reviews/2026-05-09/CR-07-combat-engine-review.md`
- **Outcome:** Verdict: REQUEST CHANGES. Critical 3, Important 4, Suggestions 1. Natural 6 auto-wounds without Lethal Hits, Devastating Wounds bypasses all saves, AP applied twice, Sustained Hits does not add resolved hits.

## Triage summary

- [CR-07 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-07)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
