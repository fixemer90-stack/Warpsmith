---
title: "CR-12 — Roster validation and points review"
parent: code-review
status: pending
source: ../code-review-plan.md#cr-12
tags: [requirements, code-review, atomic-review]
---

# CR-12 — Roster validation and points review

**Objective:** проверить PTS formula, Warlord, squad size, battleline caps, generated roster validity.

**Files:**
- Review: `backend/state/roster.py`
- Review: `web/routes/api_rosters.py`
- Review: `web/static/team_builder.js`
- Review: `tests/test_rosters.py`, `tests/test_generate_roster.py`
- Output: `docs/reviews/YYYY-MM-DD/CR-12-roster-validation-points.md`

**Steps:**
1. Проверить PTS formula: `points / minSquad * squadSize`.
2. Проверить frontend/backend formula parity.
3. Проверить `squad_size` source from YAML, not `model_count` fallback where invalid.
4. Проверить explicit Warlord requirement for multiple Characters.
5. Проверить generated roster exactly-one-Warlord.
6. Проверить 3× cap and Battleline detection.
7. Запустить roster/generator tests.

**Acceptance:** save/play rosters валидны и не расходятся между UI/backend.

---

---

## Execution Status

**Status:** Pending

**Review report target:** `docs/reviews/YYYY-MM-DD/CR-12-roster-validation-and-points-review.md`

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
