---
title: "CR-15 — AI decision engine and faction profile review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-15
tags: [requirements, code-review, atomic-review]
---

# CR-15 — AI decision engine and faction profile review

**Objective:** проверить greedy decisions, faction AI profiles, behavior activation, deployment integration.

**Files:**
- Review: `backend/engine/ai/`
- Review: `wiki/factions/*.md`
- Review: AI tests
- Output: `docs/reviews/YYYY-MM-DD/CR-15-ai-decision-faction-profiles.md`

**Steps:**
1. Проверить decision tests first.
2. Проверить `load_profile`, cache isolation, fuzzy faction matching.
3. Проверить phase weights and behavior activation.
4. Проверить target multipliers for shooting/charge.
5. Проверить deployment profiles are loaded before deploy_game.
6. Проверить melee/ranged faction-specific movement behavior.
7. Запустить AI tests.

**Acceptance:** Orks/Tau/AdMech behavior profiles реально используются в autoplay decisions.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-15-ai-decision-engine-and-faction-profile-review.md`

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
