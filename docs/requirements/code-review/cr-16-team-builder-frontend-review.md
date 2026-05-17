---
title: "CR-16 — Team Builder frontend review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-16
tags: [requirements, code-review, atomic-review]
---

# CR-16 — Team Builder frontend review

**Objective:** проверить Team Builder Alpine state, unit modal, roster save/edit, Warlord UI, PTS UI.

**Files:**
- Review: `web/templates/team_builder.html`
- Review: `web/static/team_builder.js`
- Review: `web/static/unit_modal.js`
- Review: `web/templates/partials/*.html` related to units/rosters
- Output: `docs/reviews/2026-05-10/CR-16-team-builder-frontend-review.md`

**Steps:**
1. Выполнить `node -c` для involved JS files.
2. Проверить Alpine null-safety in templates.
3. Проверить no Jinja2/Alpine `{{ }}` conflicts.
4. Проверить Warlord crown visible and save disabled until valid.
5. Проверить PTS formula UI parity.
6. Проверить edit mode metadata hydration.
7. Browser smoke: `/team-builder`, console errors, key tokens present.

**Acceptance:** Team Builder работает без JS syntax/runtime errors and saves valid roster payloads.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-10/CR-16-team-builder-frontend-review.md`

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

- **Verdict:** Request Changes — current live Team Builder Warlord/PTS smoke passed, but stale duplicate modal code and placeholder modal tests make the CR-16 acceptance unsafe.
- **Critical:** 0
- **Important:** 2
- **Suggestions:** 2
- **Blocked by:** —
- **Report:** `docs/reviews/2026-05-10/CR-16-team-builder-frontend-review.md`
- **Completed at:** 2026-05-10

## Triage summary

- [CR-16 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-16)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.

## Regression evidence — Task 2.1 (canonical PTS formula)

**2026-05-17.** (co-owned — CR-12, CR-16, CR-17, CR-19). One canonical `calculate_squad_pts()`.

Changes:
- `roster.py`: canonical PTS function `(points/minSquad + loadoutPts)*squadSize + nobPts`.
- `api_rosters.py`: create/update/generate use canonical formula, expose `total_pts` + `squad_pts` in API responses.
- 11 new tests covering all formula scenarios.

Tests: 33 passed in test_roster.py (22 pre-existing + 11 new). Lint/format/diff-check clean.
## Regression evidence — Task 2.3

Date: 2026-05-17

Task 2.3 fixed shared server-side feature gates for roster create-like paths and gated public updates. Free rosters are limited to one, Premium uses `max_rosters=None` for unlimited, duplicate/generated-save paths share the create gate, and public updates are checked and persisted. Parallel create race remains an accepted SQLite/pet-project limitation pending production transaction/constraint hardening.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- `uv run python -m pytest tests/ -q` → 562 passed, 3 skipped, 60 warnings.
- `uv run ruff check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.
- `uv run ruff format --check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.
- `git diff --check -- backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.

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

## Phase 2 checkpoint evidence

Date: 2026-05-17

Phase 2 roster-validator checkpoint is complete: Task 2.1 canonical PTS formula, Task 2.2 Warlord semantics, and Task 2.3 feature gates are verified and synchronized.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- `uv run python -m pytest tests/ -q` → 562 passed, 3 skipped, 60 warnings.
- Ruff lint/format clean for Phase 2 Python files.
