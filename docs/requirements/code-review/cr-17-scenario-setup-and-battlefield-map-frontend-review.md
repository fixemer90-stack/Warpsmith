---
title: "CR-17 — Scenario Setup and battlefield map frontend review"
parent: code-review
status: request-changes
source: ../code-review-plan.md#cr-17
tags: [requirements, code-review, atomic-review]
---

# CR-17 — Scenario Setup and battlefield map frontend review

**Objective:** проверить mission/format selection, generated opponent, strategic map, simulation launch.

**Files:**
- Review: `web/templates/scenario_setup.html`
- Review: `web/static/scenario_setup.js`
- Review: `web/static/battlefield_map.js`
- Review: `web/templates/partials/battlefield_map.html`
- Output: `docs/reviews/2026-05-10/CR-17-scenario-setup-and-battlefield-map-frontend-review.md`

**Steps:**
1. Выполнить `node -c` для involved JS files.
2. Проверить mission options against real `MISSIONS`.
3. Проверить game format map sizes.
4. Проверить objectives count and placement per mission.
5. Проверить roster dropdown compatibility filter.
6. Проверить generated opponent save-and-play flow.
7. Browser smoke: switch mission/format, inspect console, run/prepare simulation if data available.

**Acceptance:** user can configure scenario and launch simulation without stale mission/map/generated-roster bugs.

---

---

## Execution Status

**Status:** Request Changes

**Review report target:** `docs/reviews/2026-05-10/CR-17-scenario-setup-and-battlefield-map-frontend-review.md`

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
- **Critical:** 0
- **Important:** 4
- **Suggestions:** 1
- **Blocked by:** —
- **Completed at:** 2026-05-10

Report: `docs/reviews/2026-05-10/CR-17-scenario-setup-and-battlefield-map-frontend-review.md`

Review found that Scenario Setup renders and can launch a happy-path simulation, but mission deployment, Game Format, and First Turn controls are not wired into the launch contract. The strategic battlefield map also previews mission-agnostic left/right deploy zones while mission cards advertise mission-specific deployment.

## Regression evidence — Task 2.1 (canonical PTS formula)

**2026-05-17.** (co-owned — CR-12, CR-16, CR-17, CR-19). One canonical `calculate_squad_pts()`.

Changes:
- `roster.py`: canonical PTS function `(points/minSquad + loadoutPts)*squadSize + nobPts`.
- `api_rosters.py`: create/update/generate use canonical formula, expose `total_pts` + `squad_pts`.
- 11 new tests covering all formula scenarios.

Tests: 33 passed in test_roster.py (22 pre-existing + 11 new). Lint/format/diff-check clean.

## Triage summary

- [CR-17 triage entry](../../reviews/2026-05-10/triage-summary.md#cr-17)
- Current release triage verdict: not-release-ready until open Critical/Important findings are fixed/re-reviewed or explicitly accepted where allowed.
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

## Regression evidence — Task 2.3 check update

Date: 2026-05-18

Verdict: REQUEST CHANGES on closure metadata only after independent Task 2.3 check. The feature-gate behavior itself passed re-review, but Task 2.3 cannot claim Phase 2 checkpoint completion while Task 2.2 remains REQUEST CHANGES. This section supersedes the older Phase 2 checkpoint evidence that said Phase 2 was complete.

Observed Task 2.3 behavior:
- Free limits: first create `200`, second create `403`, duplicate at limit `403`, update-to-public `403`, generated-save at limit `403`.
- Premium limits: multiple creates `200`, update-to-public `200`, GET confirms `is_public=1`.

Observed verification during check:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 70 passed, 48 warnings.
- `uv run python -m pytest tests/ -q` → 604 passed, 3 skipped, 60 warnings.
- `uv run ruff check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → clean.
- `uv run ruff format --check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py` → 3 files already formatted.
- `git diff --check -- backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py docs/remediation/task-02-03-enforce-plan-feature-gates-consistently.md docs/remediation/remediation-plan.md docs/remediation/index.md` → clean.

## Regression evidence — Phase 2 closure sync

Date: 2026-05-18

Phase 2 closure metadata is consistent after Task 2.2 + Task 2.3 re-check completion; Task 2.3 no longer carries `REQUEST CHANGES` status and checkpoint 2 is marked complete.

Latest verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py tests/test_generate_roster.py tests/test_team_builder.py -q` → 82 passed, 48 warnings.
- `uv run python -m pytest tests/ -q` → 604 passed, 3 skipped, 60 warnings.

## Regression evidence — Task 2.2 re-check resolution

Date: 2026-05-18

Verdict: COMPLETE after follow-up fixes. Keyword-only `CHARACTER` units are Warlord-eligible in shared validation, Team Builder zero-eligible Character rosters are invalid with a specific warning, frontend candidate logic includes keywords/tags/category/is_leader/can_be_warlord parity, and regression coverage now includes backend keyword-only and frontend zero-eligible/keyword cases.

Verification:
- `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py tests/test_generate_roster.py tests/test_team_builder.py -q` → 82 passed, 48 warnings.
- `uv run python -m pytest tests/ -q` → 604 passed, 3 skipped, 60 warnings.
- `uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_generate_roster.py tests/test_team_builder.py` → clean.
- `uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_generate_roster.py tests/test_team_builder.py` → clean.
- `git diff --check` → clean for Task 2.2 touched code, tests, and docs.
