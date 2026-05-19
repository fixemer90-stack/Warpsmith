# Code review — Task 2.3 — Enforce plan/feature gates consistently

Date: 2026-05-18
Task: `docs/remediation/task-02-03-enforce-plan-feature-gates-consistently.md`
Verdict: REQUEST CHANGES → FIXED 2026-05-18

## Scope

Independent re-review of Task 2.3 after the Task 2.2 re-check exposed Phase 2 closure drift.

Checked the task contract against:

- `backend/billing/plans.py`
- `web/routes/api_rosters.py`
- `tests/test_rosters.py`
- `docs/remediation/task-02-03-enforce-plan-feature-gates-consistently.md`
- `docs/remediation/remediation-plan.md`
- `docs/remediation/index.md`
- Primary CR artifacts: CR-12, CR-16, CR-17, CR-19

## Behavioral findings

No behavioral blocker found in Task 2.3 feature-gate implementation.

Observed deterministic probe:

```text
features free max 1 premium max None
free statuses 200 403 403 403 200 403
premium statuses 200 200 200 200 public persisted 1 1
```

Meaning:

- Free user can create the first roster.
- Free second create is blocked with 403.
- Free duplicate at limit is blocked with 403.
- Free update-to-public is blocked with 403.
- Generated roster can be produced, but saving it through `/api/rosters` at Free limit is blocked with 403.
- Premium can create multiple rosters.
- Premium public update persists `is_public=1` and GET returns `is_public=1`.

Implementation notes:

- `UserFeatures.FREE["max_rosters"] == 3` and `UserFeatures.PREMIUM["max_rosters"] is None`.
- `create_roster()` and `duplicate_roster()` call shared `_check_roster_limits()` for create-like mutations.
- generated-save path routes through `create_roster()`, so the save operation uses the same gate.
- `update_roster()` calls `_check_roster_limits(..., check_count=False)` for public roster gating and persists `is_public` in SQL.

## Original blocking findings (fixed)

The original blockers from this review were closure-metadata issues (not feature-gate behavior):

1) Task 2.3 phase-checkpoint claim contradicted current Phase 2 state.
2) Task 2.3 verification counters were stale.
3) CR-12/16/17/19 still had stale Phase 2 checkpoint-complete evidence.

All three are now resolved and superseded by the Resolution section below.

## Resolution

### Finding 1 (Fixed) — Task closure metadata drift

- Task 2.3 completion requirement is now marked complete because Task 2.2 re-check closure is complete and Phase 2 checkpoint prerequisites are satisfied.
- `docs/remediation/index.md` now marks Task 2.3 done (`[x]`) consistently with task/remediation plan state.

### Finding 2 (Fixed) — Stale verification counts

- Task 2.3 verification evidence now records current counts from re-run commands (`70 passed` focused, `604 passed, 3 skipped` full).

### Finding 3 (Fixed) — Stale CR checkpoint evidence

- CR-12, CR-16, CR-17, and CR-19 include `Regression evidence — Task 2.3 check update` sections explicitly superseding stale Phase 2 complete claims.
- Evidence now states that Task 2.3 behavior is correct and closure metadata is synchronized; final phase-checkpoint closure followed after Task 2.2 was resolved.

## Verification run during this re-review

```bash
rm -f *.db-shm *.db-wal && uv run python -m pytest tests/test_roster*.py tests/test_rosters.py -q
# 70 passed, 48 warnings in 15.24s

uv run python -m pytest tests/ -q
# 604 passed, 3 skipped, 60 warnings in 51.13s

uv run ruff check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py
# All checks passed!

uv run ruff format --check backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py
# 3 files already formatted

git diff --check -- backend/billing/plans.py web/routes/api_rosters.py tests/test_rosters.py docs/remediation/task-02-03-enforce-plan-feature-gates-consistently.md docs/remediation/remediation-plan.md docs/remediation/index.md
# clean
```

## Final closure state

Task 2.3 is complete. Behavioral AC were already green; closure metadata is synchronized; Task 2.2 dependency is closed; Phase 2 checkpoint can now be marked complete across task/plan/index/CR surfaces.
