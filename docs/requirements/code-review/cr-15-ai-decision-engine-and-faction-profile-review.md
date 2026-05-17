---
title: "CR-15 — AI decision engine and faction profile review"
parent: code-review
status: request-changes
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

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-09/CR-15-ai-decision-engine-and-faction-profile-review.md`

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
- **Completed at:** 2026-05-09T23:22:36+03:00

### Finding summary

- F3.1 greedy decision engine is not used by live Scenario/autoplay phases.
- Faction behavior `action_override` is retrieved but never applied.
- `choose_action_with_faction_ai()` does not set `ctx.faction_profile`, so target-priority scoring remains disabled in the wrapper.
- Target-priority multipliers below 1.0 are ignored.
- `get_weights()` mutates behavior cooldown/one-shot state while acting like a getter.
- Live autoplay deployment passes `objectives=[]`.
- Tests pass but do not prove live faction-specific decisions.

## Triage summary

- [CR-15 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-15)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
