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

## Regression evidence — Task 1.3 (squad_size authority)

**2026-05-17.** `validate_squad_size()` and `_roster_to_player_state()` now use
`unit.squad_size` from frontmatter (not `model_count`). `model_count` is per-model
grouping only (e.g. swarms). 2 new tests: squad_size validation + step divisibility.

## Regression evidence — Task 1.5 (frontmatter canonical IDs)

**2026-05-17.** (co-owned — CR-06, CR-11, CR-12, CR-21). Frontmatter `canonical_id` support.

Changes:
- Unit model: `source_path` field, parser passes source path.
- Compiler: canonical_id format validation, source_path in records, pre-write fatal collision check.
- 12 new tmp_path tests.

Tests: 36 passed (24 + 12 new). Lint/format/diff-check clean.

## Regression evidence — Task 2.1 (canonical PTS formula)

**2026-05-17.** One canonical `calculate_squad_pts()` function in `roster.py`.

Changes:
- `backend/state/roster.py`: added `calculate_squad_pts()` implementing `(points / minSquad + loadoutPts) * squadSize + nobPts`; added `squad_pts` breakdown to `RosterValidationResult`; `validate_roster()` uses canonical formula.
- `web/routes/api_rosters.py`: create/update/generate roster endpoints use canonical PTS and expose `total_pts` + `squad_pts` in responses.
- 11 new tests covering Boyz min, expanded, loadout, Nob upgrades, Nobz, single-model vehicle, roster totalPts sum, squad_pts breakdown, PTS exceeded error.

Tests: 33 passed in test_roster.py (22 pre-existing + 11 new). Lint/format/diff-check clean.

## Regression evidence — Task 2.2

Date: 2026-05-17

Task 2.2 verified Warlord validation across shared backend validation, API save/update, generated rosters, and Team Builder expectations.

Changes verified:
- `backend/state/roster.py`: shared `is_unit_eligible_warlord()` and `validate_roster(..., is_warlord=...)` enforce zero eligible invalid, no Warlord invalid for 2+ eligible Characters, two Warlords invalid, and non-eligible Warlord invalid.
- `web/routes/api_rosters.py`: create/update pass Warlord flags to shared validation; generated Orks/T'au rosters produce exactly one valid Warlord.
- `web/static/team_builder.js` / `web/templates/team_builder.html`: Warlord crown UI, warning, and save-disabled behavior present.

Test results:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- `uv run python -m pytest tests/ -q` → 562 passed, 3 skipped, 60 warnings.
- Ruff lint/format clean for Phase 2 Python files; `git diff --check` clean.

## Regression evidence — Task 2.3

Date: 2026-05-17

Task 2.3 fixed shared server-side feature gates for roster create-like paths and gated public updates. Free rosters are limited to one, Premium uses `max_rosters=None` for unlimited, duplicate/generated-save paths share the create gate, and public updates are checked and persisted. Parallel create race remains an accepted SQLite/pet-project limitation pending production transaction/constraint hardening.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- `uv run python -m pytest tests/ -q` → 562 passed, 3 skipped, 60 warnings.
- `uv run ruff check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.
- `uv run ruff format --check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.
- `git diff --check -- backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.

## Phase 2 checkpoint evidence

Date: 2026-05-17

Phase 2 roster-validator checkpoint is complete: Task 2.1 canonical PTS formula, Task 2.2 Warlord semantics, and Task 2.3 feature gates are verified and synchronized.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- `uv run python -m pytest tests/ -q` → 562 passed, 3 skipped, 60 warnings.
- Ruff lint/format clean for Phase 2 Python files.

## Regression evidence — Task 2.2 check update

Date: 2026-05-17

Verdict: REQUEST CHANGES after independent Task 2.2 check.

Findings:
- Keyword-only `CHARACTER` units are not Warlord-eligible in `is_unit_eligible_warlord()` because the helper ignores `unit.keywords`.
- Team Builder treats zero eligible Characters as UI-valid even though backend validation rejects zero eligible Characters under the corrected core-rule contract.
- Regression coverage must be extended for keyword-only Character eligibility and frontend zero-eligible Warlord state.

Observed verification during check:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- `uv run python -m pytest tests/ -q` → 593 passed, 3 skipped, 60 warnings.
- Ruff check/format clean for the checked Phase 2 Python/test files.
- `git diff --check` clean for the Task 2.2 review/update files.
