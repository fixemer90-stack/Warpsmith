---
title: "Task 2.1 — Lock the canonical PTS formula"
parent: remediation-plan
status: pending
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

- [ ] Backend formula: `(points / minSquad + loadoutPts) * squadSize + nobPts`.
- [ ] There is exactly one canonical backend function for squad total points.
- [ ] All backend roster totals use stored/calculated squad `totalPts` from that canonical function.
- [ ] API responses expose `totalPts` per squad and roster `totalPts`.
- [ ] Frontend displayed totals match API/backend totals for the same roster payload.
- [ ] Frontend MUST NOT reimplement divergent business logic; it either consumes backend-calculated `totalPts` or uses a shared exported formula/test fixture generated from the backend contract.
- [ ] Do not duplicate the formula independently in multiple backend/frontend locations without shared tests proving parity.
- [ ] Roster `totalPts` equals the sum of squad `totalPts`, not a recalculation from display fields.
- [ ] Tests cover Boyz minimum squad without upgrades, Boyz expanded squad, Boyz with per-model loadout upgrade, Boyz with Nob flat upgrade, Boyz with loadout + Nob upgrade together, Nobz squad if their minSquad/squadSize behavior differs, single-model vehicle with `minSquad=1` and `squadSize=1`, and roster `totalPts` summing squad `totalPts`.

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

- [ ] `uv run python -m pytest tests/test_roster*.py -q`
- [ ] Browser/API smoke if frontend changed.

## Completion requirements

- [ ] Implementation/change is complete for this task only; do not batch unrelated fixes.
- [ ] Regression evidence is recorded in the affected CR artifact(s).
- [ ] If this task completes a phase checkpoint, update `docs/reviews/2026-05-10/triage-summary.md`, affected `docs/requirements/code-review/cr-XX-*.md`, and `docs/requirements/code-review/code-review.md` with the phase completion artifact.
- [ ] `git diff --check` passes for touched files.
