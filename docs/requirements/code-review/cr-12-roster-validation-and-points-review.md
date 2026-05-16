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

## Regression evidence — Task 0.1 (runtime unit identity)

**2026-05-16.** `RosterState.units` changed from `dict[str, Unit]` → `list[tuple[str, Unit]]`.
Duplicate unit names within a single roster are now representable. Updated consumers:
`_roster_to_player_state`, `_build_unit_models`, `units_from_db`, `make_test_roster`,
`test_roster_to_player_state_preserves_two_identical_units`. Runtime IDs (`p1:Boyz:0`,
`p1:Boyz:1`) ensure stable uniqueness even when display names collide.

Verification: `uv run python -m pytest tests/ -q` → 471 passed, 3 skipped, 0 failures.

## Regression evidence — Task 0.2 (canonical GameState serializer)

**2026-05-16.** Canonical snapshot serializer in `game_state.py`. Roster validation unchanged.
Unit snapshots now include `player_id`; VP at top-level only. 478 tests pass.

## Regression evidence — Task 0.3 (non-destructive DB/replay)

**2026-05-16.** Non-destructive DB migration. Roster persistence boundaries unchanged. 484 tests pass.

## Regression evidence — Task 1.1 (content contract tests)

**2026-05-16.** Content contract tests validate squad_size, points, model_count for all
wiki units. content.v1 Pydantic schema validates unit records including roster-relevant
fields. 14 tests pass.
