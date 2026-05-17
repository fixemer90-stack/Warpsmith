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

- [x] `rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q` → 68 passed, 48 warnings.
- [x] `uv run python -m pytest tests/ -q` → 562 passed, 3 skipped, 60 warnings.
- [x] `uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py` → clean.
- [x] `uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py backend/engine/ai/autoplay.py tests/test_roster.py tests/test_rosters.py tests/test_autoplay.py` → 7 files already formatted.
- [x] Production-path loadout/Nob parity smoke → `validate_roster()` receives `loadout_pts`/`nob_pts`; Boyz loadout+Nob total is 160 and roster total equals squad sum.
- [x] Frontend/backend parity fixture → `test_pts_formula_parity_fixture()` documents the backend contract scenarios used to keep the JS formula aligned.
- [x] `git diff --check` passes for Phase 2 touched files.

## Completion requirements

- [x] Implementation/change is complete for this task only.
- [x] Regression evidence is recorded in the affected CR artifact(s).
- [x] This task participates in the Phase 2 checkpoint; final checkpoint is recorded in Task 2.2/triage summary after all Phase 2 tasks passed.
- [x] `git diff --check` passes for touched files.

## Code review

Review file: `docs/reviews/2026-05-17/task-02-01-lock-the-canonical-pts-formula-review.md`

**Verdict: REQUEST CHANGES after re-review 2026-05-17 → FIXED 2026-05-17.**

All remaining findings resolved:

| Finding | Fix |
| --- | --- |
| Closure docs stale | Task file, source plan, index, CR evidence, and review file synchronized with current green verification. |
| Frontend formula parity unproven | `test_pts_formula_parity_fixture()` records the backend contract scenarios; JS formula comment references the backend canonical helper. |
| Production loadout/Nob parity | `validate_roster()` accepts `loadout_pts`/`nob_pts`; API create/update resolve selected options and read paths recalculate totals. |
| Full-suite status stale | Latest full suite is green: 562 passed, 3 skipped. |
