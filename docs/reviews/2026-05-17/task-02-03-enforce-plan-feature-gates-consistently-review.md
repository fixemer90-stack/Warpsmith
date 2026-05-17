# Review — Task 2.3: Enforce plan/feature gates consistently

Date: 2026-05-17
Verdict: REQUEST CHANGES

## Summary

Task 2.3 is not ready to close. A shared helper was added to `web/routes/api_rosters.py`, but the implementation still does not satisfy the documented product contract and the closure artifacts contain unreproducible verification commands.

## Findings

### Important 1 — Free roster limit still contradicts product/UI requirement

Task AC says: “Free limit matches product requirement and UI.” It does not.

Evidence:

- `backend/billing/plans.py` sets `UserFeatures.FREE["max_rosters"] = 3`.
- `web/templates/my_rosters.html` shows `Free tier: .../1 roster`.
- `docs/architecture/ADR.md` and `docs/requirements/UX.md` document `max_rosters: 1`.
- Deterministic API probe with a real Free user allowed a second roster and a duplicate:

```text
features_free {'max_rosters': 3, ...}
create1 200
create2 200
duplicate_after_existing 200
```

Why this blocks closure:

- Violates: `Free limit matches product requirement and UI`.
- Violates the task objective: Free/Premium roster limits can still be bypassed relative to the intended Free limit of 1 roster.

Required fix:

- Set the backend Free plan limit to the product/UI source of truth (`max_rosters = 1`) or update all product/UI docs if 3 is now intentional.
- Add regression tests for create and duplicate at the Free limit using a forced Free user, not localhost auto-Premium.

### Important 2 — Premium public update is checked but not persisted

`update_roster()` calls `_check_roster_limits(user, is_public=data.is_public, check_count=False)`, but the SQL update does not write `is_public`.

Evidence from deterministic API probe:

```text
premium_create_private 200
premium_update_public 200 returned_is_public= 0
premium_get_after_update_is_public= 0
```

Why this blocks closure:

- The gate executes, but the requested public roster state is silently discarded.
- The endpoint behavior is inconsistent with `RosterCreate.is_public` and the public-roster feature gate.

Required fix:

- Persist `is_public` in the update SQL when `data.is_public` is supplied.
- Add tests for Premium setting public true and Free being rejected.

### Important 3 — Task verification references missing test files and no feature-gate tests exist

Evidence:

```text
uv run python -m pytest tests/test_api_rosters.py tests/test_billing*.py -q
→ exit 4: ERROR: file or directory not found: tests/test_api_rosters.py
```

Additional evidence:

- There is no `tests/test_billing*.py` file in the current tree.
- `tests/test_rosters.py` has no assertions for Free max-roster limit, duplicate limit bypass, Free public create rejection, or Premium public update persistence.

Why this blocks closure:

- Verification evidence is not reproducible as written.
- The exact bypasses from the task objective are not covered by tests.

Required fix:

- Add focused feature-gate tests to existing `tests/test_rosters.py` or create the referenced test files.
- Update the task Verification section with commands that exist and actual results.

### Important 4 — Closure docs are not synced for Task 2.3 / Phase 2

Evidence:

- `docs/remediation/task-02-03-enforce-plan-feature-gates-consistently.md` has `status: completed`, but Completion requirements remain unchecked.
- `docs/remediation/remediation-plan.md` still has Task 2.3 AC and Checkpoint 2 unchecked.
- There is no Task 2.3 regression evidence section in the affected CR artifacts.
- The task claims “Phase 2 complete” while Task 2.2 remains `changes_requested` and Task 2.3 is not verified.

Required fix:

- Keep Task 2.3 as `changes_requested` until code, tests, source plan, index, CR evidence, and phase checkpoint artifacts are all synchronized.

## Verification run during review

```text
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q
→ 57 passed, 26 warnings

uv run python -m pytest tests/test_api_rosters.py tests/test_billing*.py -q
→ failed, exit 4: tests/test_api_rosters.py does not exist

uv run python -m pytest tests/ -q
→ failed: 6 failed, 544 passed, 3 skipped, 38 warnings
  - 5 combat/modifier failures unrelated to Task 2.3 scope
  - 1 tests/test_rosters.py::TestRosterCRUD::test_delete_roster auth failure observed in full-suite context

uv run ruff check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py tests/test_roster.py tests/test_rosters.py
→ All checks passed

uv run ruff format --check backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py tests/test_roster.py tests/test_rosters.py
→ 5 files already formatted

git diff --check -- backend/state/roster.py web/routes/api_rosters.py backend/billing/plans.py ...
→ failed: backend/billing/plans.py has CRLF/trailing-whitespace diff-check errors
```

## Verdict

REQUEST CHANGES. Do not mark Task 2.3 or Phase 2 complete until Free limit parity, public update persistence, real feature-gate tests, and closure docs are fixed.
