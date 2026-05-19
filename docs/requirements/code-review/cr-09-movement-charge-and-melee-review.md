---
title: "CR-09 — Movement, charge and melee review"
parent: code-review
status: request-changes
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

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-09/CR-09-movement-charge-and-melee-review.md`

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
- **Important:** 3
- **Suggestions:** 0
- **Blocked by:** —
- **Report:** `docs/reviews/2026-05-09/CR-09-movement-charge-and-melee-review.md`
- **Completed at:** 2026-05-09

## Triage summary

- [CR-09 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-09)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 5.1 (charge destination + engagement identity)

Date: 2026-05-18

Fixed charge destination to enumerate all 8 adjacent cells (not just left/right X-axis). Same-X/different-Y scenarios now find valid adjacent cells. Melee combat scoped to opponent units only. Added 6 regression tests (charge cell avoidance, occupied alternate, same-X, opponent-only targeting, same-name mirrored units, runtime ID logging).

Verification: focused 10 passed, full 610 passed, 3 skipped. Ruff/format/diff-check clean.

## Regression evidence — Task 5.2 (melee target selection + damage logging)

Date: 2026-05-18

Melee combat now uses the combat engine via `simulate_unit_attack()` with melee weapons. Counter-attack also uses proper combat resolution. Damage logs use `hits ... for ... damage` pattern with runtime unit IDs. Added 3 regression tests (adjacent resolution, log format, same-name attribution).

Verification: scoped 19 passed, full 613 passed, 3 skipped. Ruff/format/diff-check clean.

## Regression evidence — Task 5.3 (terrain/LoS/cover blockers)

Date: 2026-05-18 (Phase 5 checkpoint)

set_terrain() now invalidates LoS cache. Cover argument order fixed in scenario shooting (target first). AP0 cover cap: SV3+ with cover vs AP0 stays at SV3+ (SV2+ unaffected). Added 9 regression tests.

Phase 5 closed: 22 scoped passed, 622 full passed. Ruff/format/diff-check clean.
