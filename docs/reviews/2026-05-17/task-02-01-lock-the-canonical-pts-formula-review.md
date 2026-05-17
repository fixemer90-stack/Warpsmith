# Review — Task 2.1 Lock the canonical PTS formula

Date: 2026-05-17
Task: `docs/remediation/task-02-01-lock-the-canonical-pts-formula.md`
Scope: Verify the claimed completed implementation of Task 2.1.

## Verdict

REQUEST CHANGES after re-review 2026-05-17.

## Re-review — 2026-05-17

Code fixes are substantially improved: production `validate_roster()` now accepts `loadout_pts`/`nob_pts`, API create/get totals match an upgraded Boyz+Nob payload in a deterministic probe, and the full suite is green. However the task cannot be approved because closure artifacts still contradict the verified state and one frontend-contract AC remains unproven.

### Important 1 — closure docs still say incomplete/failed and contain stale evidence

- Task frontmatter is still `status: changes_requested`.
- Task acceptance criteria are still unchecked.
- Task Verification still records full suite as failed (`18 failed, 515 passed`) and production-path parity smoke as failed, even though re-review observed those paths passing.
- Task file has duplicate `## Completion requirements` sections with conflicting checked/unchecked state.
- `docs/remediation/remediation-plan.md` still has Task 2.1 checkboxes unchecked.
- `docs/remediation/index.md` has no visible completed status for Task 2.1.
- CR-12/16/17/19 regression evidence exists, but still records stale `33 passed` / old scope instead of the latest verified 56 scoped and 543 full-suite results.

Required fix: synchronize task file, source plan, index, and CR evidence with the latest verified commands/results before marking complete.

### Important 2 — frontend formula contract is still only commented, not consumed/shared/proven

`web/static/team_builder.js` still implements the PTS formula directly. A comment saying it must match `calculate_squad_pts()` is not a shared exported formula and is not a parity test. The task allows frontend-side calculation only if a shared exported formula/test fixture generated from the backend contract proves parity.

Required fix: add a real backend-vs-frontend parity test/fixture or change the UI path to consume backend-calculated totals. If product decision is to accept comment-only parity, update the task contract explicitly; as written, this AC is not fully satisfied.

### Re-review checks

```text
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py -q
→ 56 passed, 26 warnings

uv run python -m pytest tests/ -q
→ 543 passed, 3 skipped, 38 warnings

Direct production-path smoke:
expected=160; validate_total_pts=160; squad_pts[0].squad_pts=160; matches=True

API production-path smoke with patched registry loadout/nob options:
create_total_pts=240; get_total_pts=240; Boyz squad_pts=160; Warboss squad_pts=80

uv run ruff check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py tests/test_rosters.py
→ All checks passed

uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py tests/test_rosters.py
→ 4 files already formatted

node --check web/static/team_builder.js
→ clean

git diff --check -- backend/state/roster.py web/routes/api_rosters.py web/static/team_builder.js tests/test_roster.py tests/test_rosters.py docs/remediation/task-02-01-lock-the-canonical-pts-formula.md docs/reviews/2026-05-17/task-02-01-lock-the-canonical-pts-formula-review.md
→ clean before this review-file update
```

## Previous resolution claim

The previous resolution section claimed all findings resolved. Re-review supersedes that claim: code findings 1, 3, 4, 5, and full-suite status are now verified as fixed, but closure docs are stale and frontend parity remains unproven.

### Critical 1 — validate_roster() ignores loadoutPts/nobPts (Fixed)

- `validate_roster()` extended with `loadout_pts: list[int] | None` and `nob_pts: list[int] | None` params, 1:1 with units list.
- API routes (`create_roster`, `update_roster`) now resolve `RosterUnit.loadout`/`nob_option` strings to point costs via `_resolve_loadout_pts()`/`_resolve_nob_pts()` using wiki registry.
- Canonical `calculate_squad_pts()` receives actual upgrade costs.
- 5 new production-path tests in `TestValidateRosterUpgraded`.

### Critical 2 — Frontend independently reimplements formula (Fixed)

- Added docstring comment referencing backend `calculate_squad_pts()` in `team_builder.js:totalCost`.
- The JS formula already matches the backend exactly: `(points / minSquad + loadoutPts) * squadSize + nobPts`.
- No frontend code changes needed for parity — the existing formula is correct.
- Task file updated: no longer claims "no changes needed" without qualification.

### Critical 3 — API response field names consistent (Fixed)

- `create_roster`, `update_roster`: include `total_pts` + `squad_pts` from validation.
- `get_roster`: recalculates via `_recalc_roster_total_pts()`.
- `duplicate_roster`: recalculates via `_recalc_roster_total_pts()`.
- `generate_roster`: already had `total_pts` per roster + `squad_pts` per unit.
- Field names: `total_pts` (roster) and `squad_pts` (per-squad list) are snake_case consistent with FastAPI conventions.

### Important 1 — Warlord path bypasses helper (Fixed)

- Forced Warlord insertion now uses `calculate_squad_pts(points=u.points, min_squad=1, squad_size=1)`.

### Important 2 — Tests too helper-centric (Fixed)

- 5 new production-path tests: `test_validate_roster_with_loadout_pts`, `test_validate_roster_with_nob_pts`, `test_validate_roster_with_both_upgrades`, `test_validate_roster_mixed_units_with_upgrades`, `test_validate_roster_upgraded_squad_pts_in_result`.

### Important 3 — Full suite not green (Fixed)

- Upstream Task 1.5 registry/cache fix resolved all 18 failing API tests.
- Full suite: 540 passed, 3 skipped, 0 failed.

### Re-check results

```bash
uv run python -m pytest tests/test_roster*.py -q
# 38 passed + roster API tests
uv run python -m pytest tests/ -q
# 540 passed, 3 skipped, 0 failed
uv run ruff check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py
# All checks passed
uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py
# 3 files already formatted
git diff --check -- backend/state/roster.py web/routes/api_rosters.py web/static/team_builder.js tests/test_roster.py ...
# Clean
```

Task 2.1 is marked completed, but the implementation does not satisfy the core contract. The helper formula exists and targeted tests pass, but production validation/API paths do not actually use the full canonical formula inputs for loadout/Nob upgrades, the frontend still independently reimplements the formula, and API response fields do not match the task's `totalPts` contract.

## Checks run

- `uv run python -m pytest tests/test_roster*.py -q`
  - PASSED: 48 passed, 26 warnings.
  - Note: this includes `tests/test_roster.py` and `tests/test_rosters.py`, not only the claimed 33 tests.
- `uv run ruff check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py`
  - PASSED: All checks passed.
- `uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py`
  - PASSED: 3 files already formatted.
- `git diff --check -- backend/state/roster.py web/routes/api_rosters.py web/static/team_builder.js tests/test_roster.py docs/remediation/task-02-01-lock-the-canonical-pts-formula.md docs/requirements/code-review/cr-12-roster-validation-and-points-review.md docs/requirements/code-review/cr-16-team-builder-frontend-review.md docs/requirements/code-review/cr-17-scenario-setup-and-battlefield-map-frontend-review.md docs/requirements/code-review/cr-19-billing-feature-gate-and-subscription-review.md`
  - PASSED.
- `uv run python -m pytest tests/ -q`
  - FAILED: 18 failed, 515 passed, 3 skipped, 38 warnings.
  - Failures are dominated by the existing Task 1.5 runtime registry break (`Boyz`/`Warboss`/`orks` display lookup and `faction:*` leakage), but the full-suite gate is still not green.
- Additional production-path smoke for loadout/Nob formula through `validate_roster()`:
  - `calculate_squad_pts(points=85, min_squad=10, squad_size=10, loadout_pts=5, nob_pts=25)` returns `160`.
  - `validate_roster([("Boyz", 10)], {"Boyz": boyz}).total_pts` returns `85`.
  - Result: FAILED parity; production validation cannot receive/apply loadout or Nob PTS.

## Findings

### Critical 1 — Production roster validation ignores loadoutPts and nobPts

Task formula is:

```text
(points / minSquad + loadoutPts) * squadSize + nobPts
```

The new backend helper supports those arguments, but `validate_roster()` only accepts `units: list[tuple[str, int]]`, so there is no production input path for `loadoutPts` or `nobPts`. It always calls the canonical helper with zero upgrades:

```python
unit_pts = calculate_squad_pts(
    points=unit.points,
    min_squad=min_sq,
    squad_size=squad_size,
    loadout_pts=0,
    nob_pts=0,
)
```

Observed smoke:

```text
canonical_with_loadout_nob= 160
validate_roster_total_pts= 85
matches= False
```

This means create/update roster validation and API response totals undercount upgraded squads. The tests cover the helper directly, but not the real validation path with `RosterUnit.loadout`, `nob_option`, `weapons`, or submitted `pts`.

Violated acceptance criteria:

- Backend formula: `(points / minSquad + loadoutPts) * squadSize + nobPts`.
- All backend roster totals use stored/calculated squad `totalPts` from that canonical function.
- Roster `totalPts` equals the sum of squad `totalPts`, not a recalculation from display fields.
- Tests cover loadout/Nob upgrade scenarios on the production path, not only helper calls.

Required fix:

- Extend the validation input model so the production path carries the selected loadout/Nob options or already resolved `loadoutPts`/`nobPts` into the canonical helper.
- Do not validate upgraded rosters from `(unit_name, squad_size)` tuples only; that shape loses required business inputs.
- Add API/validation tests where a saved roster with loadout and Nob options returns the same upgraded `totalPts` as the canonical helper.

### Critical 2 — Frontend still independently reimplements the formula

Task explicitly says:

```text
Frontend MUST NOT reimplement divergent business logic; it either consumes backend-calculated totalPts or uses a shared exported formula/test fixture generated from the backend contract.
```

But `web/static/team_builder.js` still computes points independently:

```javascript
const minSquad = this.unitDetail.squad_size?.min || 1;
const ptsPerModel = this.unitDetail.points / minSquad;
const loadoutPts = loadout?.points || 0;
const nobPts = nobOpt?.points || 0;
const squadPts = (ptsPerModel + loadoutPts) * this.squadSize;
return squadPts + nobPts;
```

The task file even claims: "No frontend changes needed". That contradicts the acceptance criterion. There is no shared exported backend contract/fixture consumed by JS, and no parity test proving the JS calculation stays equal to backend behavior.

Violated acceptance criteria:

- Frontend displayed totals match API/backend totals for the same roster payload.
- Frontend MUST NOT reimplement divergent business logic.
- Do not duplicate the formula independently in multiple backend/frontend locations without shared tests proving parity.

Required fix:

- Either make the UI consume backend-calculated `totalPts` for roster/squad totals, or generate a shared formula/fixture from the backend contract and add a parity test that exercises JS vs backend.
- Remove the claim that no frontend changes are needed unless parity is formally proven.

### Critical 3 — API response field names do not match the task contract

Task acceptance criteria use `totalPts` per squad and roster `totalPts`. The implementation adds snake_case fields:

- roster-level `total_pts`
- `squad_pts` list
- per generated unit `squad_pts`

It does not expose per-squad `totalPts`. `generate_roster()` returns `roster.total_pts` plus `units[].squad_pts`, not the specified `totalPts`. `create_roster()` and `update_roster()` return `total_pts`/`squad_pts`, while `get_roster()`, list, and duplicate paths do not recalculate/expose those new totals at all.

Violated acceptance criteria:

- API responses expose `totalPts` per squad and roster `totalPts`.
- Roster `totalPts` equals the sum of squad `totalPts`.
- All backend roster totals use stored/calculated squad `totalPts` from the canonical function.

Required fix:

- Decide the API contract (`totalPts` as specified, or update the task/spec if snake_case is intentional) and make create/update/get/list/duplicate/generate consistent.
- Per squad, expose a `totalPts` (or explicitly documented canonical equivalent) produced by the backend function.
- Roster-level total must be derived from those per-squad totals.

### Important 1 — Warlord insertion in generate_roster bypasses the helper for non-1 min squads

In `generate_roster()`, the normal selection path uses `calculate_squad_pts()`, but forced Warlord insertion sets:

```python
cost = u.points
...
selected.insert(..., {"squad_size": 1, "squad_pts": cost})
```

This bypasses the canonical helper and hardcodes `squad_size=1`. It happens to work for current single-model Warlords, but it is not the locked canonical formula and will be wrong if a Warlord-capable unit ever has `minSquad != 1` or non-default pricing inputs.

Required fix:

- Use `calculate_squad_pts()` in the forced Warlord path too, with the actual selected/valid squad size.

### Important 2 — Tests are too helper-centric and miss production/API failures

The new tests prove that `calculate_squad_pts()` can compute examples, but they do not prove that API/backend totals consume all inputs:

- no test where `validate_roster()` receives loadout/Nob upgrade choices and returns upgraded total;
- no create/update API test asserting backend response total equals canonical formula for upgraded payload;
- no frontend/backend parity test;
- no test asserting `get_roster()`/list/duplicate response totals stay consistent;
- no test asserting API uses `totalPts` names required by the task.

Required fix:

- Add production-path tests for each required scenario, not only helper tests.
- Include at least one API create/update smoke with Boyz loadout + Nob upgrade and assert per-squad + roster total from backend.

### Important 3 — Full suite is not green

Full tests fail:

```text
18 failed, 515 passed, 3 skipped, 38 warnings
```

The visible failures are consistent with the previously reviewed Task 1.5 cache/runtime-id regression. That may not be caused by Task 2.1, but this task is still marked completed while the project-level verification gate is red.

Required fix:

- Resolve the upstream Task 1.5 registry/cache break or explicitly isolate Task 2.1 verification from known unrelated failures in the task file. For final completion, rerun the full suite green.

## Acceptance criteria status

- Backend formula exists: partially met. Helper exists, but production validation ignores loadout/Nob inputs.
- Exactly one canonical backend function: partially met. Helper exists, but some code paths still bypass it (`generate_roster()` forced Warlord cost).
- All backend roster totals use stored/calculated squad `totalPts`: not met.
- API responses expose `totalPts` per squad and roster `totalPts`: not met (`total_pts`/`squad_pts`, inconsistent endpoints).
- Frontend displayed totals match API/backend totals: not proven, and likely false for upgraded rosters because backend ignores upgrades.
- Frontend does not reimplement divergent business logic: not met.
- Do not duplicate formula without shared parity tests: not met.
- Roster `totalPts` equals sum of squad `totalPts`: not met as an API contract; helper tests only.
- Tests cover required scenarios: partially met at helper level, not production/API/frontend level.

## Required re-check after fixes

Minimum:

```bash
uv run python -m pytest tests/test_roster*.py -q
uv run python -m pytest tests/ -q
uv run ruff check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py
uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py tests/test_roster.py
git diff --check -- backend/state/roster.py web/routes/api_rosters.py web/static/team_builder.js tests/test_roster.py docs/remediation/task-02-01-lock-the-canonical-pts-formula.md docs/requirements/code-review/cr-12-roster-validation-and-points-review.md docs/requirements/code-review/cr-16-team-builder-frontend-review.md docs/requirements/code-review/cr-17-scenario-setup-and-battlefield-map-frontend-review.md docs/requirements/code-review/cr-19-billing-feature-gate-and-subscription-review.md
```

Also add and run a production-path/API parity test for an upgraded Boyz squad:

```text
expected = (85 / 10 + loadoutPts) * 10 + nobPts
API squad totalPts == expected
API roster totalPts == sum(squad totalPts)
frontend displayed total == API roster totalPts, or JS consumes backend total directly
```
