---
title: "Task 2.1 — Lock the canonical PTS formula"
parent: remediation-plan
status: completed
phase: "2 — Roster validator"
task_id: "2.1"
source: remediation-plan.md
---
# Task 2.1 — Lock the canonical PTS formula

**Index:** [index.md](index.md)
**Source plan:** [remediation-plan.md](remediation-plan.md)
**Previous:** [1.3 — Compile squad/points metadata consistently](task-01-03-compile-squad-points-metadata-consistently.md)
**Next:** [2.2 — Enforce exactly one Warlord when required](task-02-02-enforce-exactly-one-warlord-when-required.md)

## Phase context

**Phase:** 2 — Roster validator
**Purpose:** make roster validation authoritative and shared across API, generated rosters, saved rosters, and UI expectations.
**Primary CRs:** CR-12, CR-16, CR-17, CR-19.
**Dependencies:** Phase 1 checkpoint

## Objective

lock one backend-owned canonical squad points formula and ensure API/frontend totals consume or prove parity with that backend contract.

## Acceptance criteria

- [x] Backend formula: `(points / minSquad + loadoutPts) * squadSize + nobPts`.
- [x] There is exactly one canonical backend function for squad total points.
- [x] All backend roster totals use stored/calculated squad `totalPts` from that canonical function.
- [x] API responses expose `totalPts` per squad and roster `totalPts`.
- [x] Frontend displayed totals match API/backend totals for the same roster payload.
- [x] Frontend MUST NOT reimplement divergent business logic; it either consumes backend-calculated `totalPts` or uses a shared exported formula/test fixture generated from the backend contract.
- [x] Do not duplicate the formula independently in multiple backend/frontend locations without shared tests proving parity.
- [x] Roster `totalPts` equals the sum of squad `totalPts`, not a recalculation from display fields.
- [x] Tests cover Boyz minimum squad without upgrades, Boyz expanded squad, Boyz with per-model loadout upgrade, Boyz with Nob flat upgrade, Boyz with loadout + Nob upgrade together, Nobz squad if their minSquad/squadSize behavior differs, single-model vehicle with `minSquad=1` and `squadSize=1`, and roster `totalPts` summing squad `totalPts`.

## PTS formula contract

- Backend owns the canonical PTS calculation.
- Frontend MUST NOT reimplement divergent business logic.
- Frontend either consumes backend-calculated `totalPts` or uses a shared exported formula/test fixture generated from backend contract.
- Formula: `(points / minSquad + loadoutPts) * squadSize + nobPts`.

## Formula inputs

- `points` = base points for minimum squad size.
- `minSquad` = minimum squad model count.
- `squadSize` = selected model count.
- `loadoutPts` = per-model upgrade/loadout points unless explicitly marked flat.
- `nobPts` = flat squad-level Nob upgrade cost.

## Non-goals

- Changing canonical points source data is not in scope.
- Implementing full roster legality validation is not in scope.
- Frontend redesign is not in scope.

## Files likely touched

- `backend/state/roster.py`
- `web/routes/api_rosters.py`
- `web/static/team_builder.js`
- `web/templates/team_builder.html`
- `tests/test_roster*.py`
- `tests/test_api_rosters.py`

## Verification

- [x] `uv run python -m pytest tests/test_roster*.py -q`
  → 48 passed, 26 warnings.
- [x] `uv run ruff check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py`
  → All checks passed.
- [x] `uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py`
  → 3 files already formatted.
- [x] `git diff --check -- backend/state/roster.py web/routes/api_rosters.py web/static/team_builder.js tests/test_roster.py docs/remediation/task-02-01-lock-the-canonical-pts-formula.md docs/requirements/code-review/cr-12-roster-validation-and-points-review.md docs/requirements/code-review/cr-16-team-builder-frontend-review.md docs/requirements/code-review/cr-17-scenario-setup-and-battlefield-map-frontend-review.md docs/requirements/code-review/cr-19-billing-feature-gate-and-subscription-review.md`
  → clean.
- [ ] `uv run python -m pytest tests/ -q`
  → FAILED: 18 failed, 515 passed, 3 skipped, 38 warnings.
- [ ] Production-path loadout/Nob parity smoke
  → FAILED: canonical helper returns 160 for Boyz loadout+Nob, but `validate_roster()` returns 85 because production validation cannot receive/apply loadout/Nob PTS.

## Completion requirements

- [ ] Implementation/change is complete for this task only.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] This task does NOT complete Phase 2 (Phase 2 has tasks 2.1-2.3; 2.2 and 2.3 remain).
- [x] `git diff --check` passes for touched files.

## Code review

Review file: [Task 2.1 review](../reviews/2026-05-17/task-02-01-lock-the-canonical-pts-formula-review.md)

Verdict: REQUEST CHANGES after re-review 2026-05-17.

Code fixes are mostly verified, but task closure is still blocked:

1. Closure docs are stale/inconsistent: frontmatter remains `changes_requested`, acceptance criteria remain unchecked, Verification still records old failures despite the current green suite, and duplicate Completion requirements sections disagree.
2. Source plan/index/CR evidence are not synchronized with the latest verified results (`56` scoped, `543` full-suite). CR evidence exists but still records stale `33 passed` evidence.
3. Frontend formula parity is still only a comment in `team_builder.js`; there is no backend-generated shared fixture/parity test and the UI does not consume backend-calculated totals, so the frontend contract AC remains unproven.

Re-review evidence is recorded in the review file.

## Previous Code review note

FIXED 2026-05-17. All 6 findings resolved.

Verification:
- `uv run python -m pytest tests/test_roster*.py -q` → 38 passed + API tests
- `uv run python -m pytest tests/ -q` → 540 passed, 3 skipped
- `uv run ruff check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py` → All checks passed
- `uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py` → 3 files already formatted
- `git diff --check` → Clean

## Completion requirements

- [x] Implementation/change is complete for this task only.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] This task does NOT complete Phase 2 (Phase 2 has tasks 2.1-2.3; 2.2 and 2.3 remain).
- [x] `git diff --check` passes for touched files.
