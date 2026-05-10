---
title: "CR-12 — Roster validation and points review"
parent: code-review
status: request-changes
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

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-09/CR-12-roster-validation-and-points-review.md`

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
- **Completed at:** 2026-05-09T22:45:59+03:00
- **Report:** `docs/reviews/2026-05-09/CR-12-roster-validation-and-points-review.md`
- **Verification:** `45 passed, 26 warnings in 8.78s` for `tests/test_roster.py tests/test_rosters.py tests/test_generate_roster.py`
- **Notes:** API accepts client-side points totals that exceed `pts_limit`, generated rosters can return success with no Warlord when no legal roster fits, and core validation cannot represent explicit Warlord selection.

## Triage summary

- [CR-12 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-12)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
